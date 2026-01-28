# Firestore Store for ActivityPub Objects

researched: 2025-01-26
status: complete
tags: firestore, activitypub, python, database, storage

## Executive Summary

A generic async Firestore service for persisting ActivityPub-style objects. Objects are stored as dicts with an `id` field, and storage location is independent of object identity, enabling denormalized data patterns and federation caching.

## Background

This Store class provides a collection-agnostic interface for Firestore. The key insight is separating object identity (`id`) from storage location. An object can be stored in any collection regardless of what its `id` says, enabling linking objects into multiple collections, storing references to external objects, and caching federated content locally.

## Key Findings

### Core Concepts

**Object Identity vs Storage Location:**

```python
# Object with ID pointing to one place
obj = {
    "id": "/users/abc123/notes/289hf",
    "type": "Note",
    "content": "..."
}

# Can usually be retrieved at canonical location:
await store.get("/users/abc123/notes/289hf")

# But can be stored elsewhere (denormalized)
await store.add("/users/someoneelse/likes", obj)

# Retrieved from that collection
await store.get("/users/someoneelse/likes", "/users/abc123/notes/289hf")
```

**Document ID Strategy:**

Firestore document IDs depend on canonical vs non-canonical storage:

- **Canonical location** (object ID is direct child of collection path):
  - Use last segment of `id` as document ID
  - `/chats/abc123` stored in `/chats` -> document ID `abc123`

- **Non-canonical location** (stored elsewhere):
  - Hash the full `id` to create document ID
  - `/chats/abc/messages/msg1` stored in `/users/bob/likes` -> document ID `784cb1320e46fb7e`

Benefits:
- Human-readable document IDs for canonical objects
- O(1) lookups by ID
- Idempotent upserts
- Collision-free storage

### API

**add(path: str, obj: dict) -> dict**

Add or update an object in a collection:

```python
message = {
    "@context": "https://www.w3.org/ns/activitystreams",
    "id": "/chats/abc123/messages/msg001",
    "type": "Message",
    "content": "Hello, world",
    "published": "2025-01-15T10:00:00Z"
}

result = await store.add("/chats/abc123/messages", message)
```

**get(id: str) -> dict | None**

Get by full ID (searches all collections):

```python
message = await store.get("/chats/abc123/messages/msg001")
```

**get(path: str, id: str) -> dict | None**

Get from specific collection by ID:

```python
obj = await store.get("/chats/xyz/attachments", "/users/abc/favorites/item1")
```

**list(path: str, **filters) -> list[dict]**

List objects with optional filters:

```python
# All messages
messages = await store.list("/chats/abc123/messages")

# Filter by field
messages = await store.list(
    "/chats/abc123/messages",
    attributedTo="/users/xyz789"
)

# Order by field
messages = await store.list(
    "/chats/abc123/messages",
    order_by="published"
)
```

**delete(id: str) -> None**

Delete by full ID:

```python
await store.delete("/chats/abc123/messages/msg001")
```

**delete(path: str, id: str) -> None**

Delete from specific collection:

```python
await store.delete("/chats/xyz/attachments", "/users/abc/item")
```

### Normalization

Objects are normalized before storage using `ld.normalize()`:
- Consistent field formats
- Proper JSON-LD structure
- `@context` preserved explicitly

### Usage Example

```python
from datetime import datetime, timezone
from srv.services.store import Store

store = Store()

# Create a chat
chat = {
    "@context": "https://www.w3.org/ns/activitystreams",
    "id": f"/chats/{nanoid()}",
    "type": "OrderedCollection",
    "name": "Chat with Sovereign",
    "attributedTo": "/users/anonymous",
    "published": datetime.now(timezone.utc).isoformat(),
    "totalItems": 0
}
await store.add("/chats", chat)

# Add a message
message = {
    "@context": "https://www.w3.org/ns/activitystreams",
    "id": f"{chat['id']}/messages/{nanoid()}",
    "type": "Message",
    "attributedTo": "/users/anonymous",
    "context": chat["id"],
    "content": "What is the meaning of life?",
    "published": datetime.utcnow().isoformat() + "Z"
}
await store.add(f"{chat['id']}/messages", message)

# Retrieve
messages = await store.list(f"{chat['id']}/messages", order_by="published")
```

### Firestore Structure

```
/{collection_path}/{hashed_document_id}
  - @context: string
  - id: string (original full ID)
  - type: string | list
  - ... other fields
```

## Practical Implications

- Separation of identity and storage enables flexible data patterns
- Canonical storage provides readable Firestore browsing
- Hashed IDs for non-canonical storage prevent collisions
- Objects can drift from canonical values; resolve via dereferencing with caching
- Normalization ensures consistent storage format

## Sources & Further Reading

- Firestore Documentation: https://firebase.google.com/docs/firestore
- ActivityStreams 2.0: https://www.w3.org/TR/activitystreams-core/

## Open Questions

- Strategies for keeping denormalized copies in sync
- Pagination patterns for large collections
- Caching strategies for frequently accessed objects
