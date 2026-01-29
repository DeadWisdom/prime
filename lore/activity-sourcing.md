# Activity Sourcing

A REST-based architecture combining Activity Streams 2.0 with Event Sourcing principles. Read operations use conventional REST endpoints. All write operations flow through a single `/outbox` endpoint as Activity objects, creating a complete event log and natural CQRS separation.

```
READS (Query Side)           WRITES (Command Side)
──────────────────           ────────────────────
GET  /factions               POST /outbox
GET  /factions/:id           
GET  /relations              (that's it)
GET  /activities
```

## Core Principles

1. **Single write endpoint**: All mutations are Activities posted to `/outbox`
2. **Activities are immutable facts**: Once published, activities never change
3. **Activity log is the source of truth**: Read models are projections derived from activities
4. **REST for reads only**: GET endpoints query projections, not the event store
5. **Additive evolution**: Prefer adding new activity types over versioning existing ones

## Activity Structure

Activities follow [Activity Streams 2.0](https://www.w3.org/TR/activitystreams-core/) vocabulary:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "id": "activity:a1b2c3",
  "type": "Create",
  "actor": "user:deadwisdom",
  "published": "2026-01-29T14:30:00Z",
  "object": {
    "type": "Faction",
    "name": "Venetian Republic"
  }
}
```

### Required Fields

| Field | Description |
|-------|-------------|
| `type` | Activity type (Create, Update, Delete, or domain-specific) |
| `actor` | URI identifying who performed the activity |
| `object` | The target of the activity (inline object or URI reference) |

### Server-Assigned Fields

| Field | Description |
|-------|-------------|
| `id` | Unique activity identifier (if not client-provided) |
| `published` | ISO 8601 timestamp when activity was processed |

### Optional Fields

| Field | Description |
|-------|-------------|
| `target` | Destination for Add/Remove activities |
| `result` | Outcome or changeset for Update activities |
| `summary` | Human-readable description |

## Writing: The Outbox

### POST /outbox

Post an activity with a client-provided `id` for idempotency:

**Request:**
```http
POST /outbox
Content-Type: application/activity+json

{
  "id": "client:op-12345",
  "type": "Create",
  "actor": "user:deadwisdom",
  "object": {
    "type": "Faction",
    "name": "Venetian Republic",
    "government": "oligarchy"
  }
}
```

**Response (201 Created):**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "id": "client:op-12345",
  "type": "Create",
  "actor": "user:deadwisdom",
  "published": "2026-01-29T14:30:00Z",
  "object": {
    "id": "faction:f4e5d6",
    "type": "Faction",
    "name": "Venetian Republic",
    "government": "oligarchy"
  }
}
```

The server enriches the activity with:
- `published` timestamp
- Generated `id` on the created object
- Any computed fields or side effects

### Idempotency

If you POST an activity with an `id` that already exists:

- **Same content**: Returns `200 OK` with the existing activity
- **Different content**: Returns `409 Conflict`

This enables safe retries and offline-first clients.

## Common Activity Types

### Create

Creates a new resource.

```json
{
  "id": "client:create-faction-001",
  "type": "Create",
  "actor": "user:deadwisdom",
  "object": {
    "type": "Faction",
    "name": "Ottoman Empire",
    "government": "monarchy",
    "capital": "Constantinople"
  }
}
```

### Update

Modifies an existing resource. Reference the object by URI, provide changes in `result`:

```json
{
  "id": "client:update-faction-002",
  "type": "Update",
  "actor": "user:deadwisdom",
  "object": "faction:ottoman",
  "result": {
    "capital": "Ankara"
  }
}
```

### Delete

Removes a resource:

```json
{
  "id": "client:delete-faction-003",
  "type": "Delete",
  "actor": "user:deadwisdom",
  "object": "faction:byzantine"
}
```

### Add

Adds an object to a collection:

```json
{
  "id": "client:add-to-alliance-004",
  "type": "Add",
  "actor": "user:deadwisdom",
  "object": "faction:venice",
  "target": "collection:italian-league"
}
```

### Remove

Removes an object from a collection:

```json
{
  "id": "client:remove-from-alliance-005",
  "type": "Remove",
  "actor": "user:deadwisdom",
  "object": "faction:florence",
  "target": "collection:italian-league"
}
```

### Domain-Specific Types

For richer semantics, define domain-specific activity types:

```json
{
  "id": "client:declare-war-006",
  "type": "DeclareWar",
  "actor": "user:deadwisdom",
  "object": "faction:france",
  "target": "faction:england",
  "summary": "France declares war on England"
}
```

```json
{
  "id": "client:sign-treaty-007",
  "type": "SignTreaty",
  "actor": "user:deadwisdom",
  "object": {
    "type": "Treaty",
    "name": "Peace of Westphalia",
    "parties": ["faction:france", "faction:spain", "faction:hre"]
  }
}
```

Domain-specific types make your event log self-documenting and enable richer projections.

## Undoing Activities

To retract or undo an activity, post an `Undo` referencing the original:

```json
{
  "id": "client:undo-war-008",
  "type": "Undo",
  "actor": "user:deadwisdom",
  "object": "client:declare-war-006"
}
```

The original activity remains in the log (immutable), but projections should reflect the undo.

## Reading: REST Endpoints

### Single Resource

**Request:**
```http
GET /factions/venice
```

**Response (200 OK):**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "id": "faction:venice",
  "type": "Faction",
  "name": "Republic of Venice",
  "government": "oligarchy",
  "capital": "Venice",
  "published": "2026-01-29T10:00:00Z",
  "updated": "2026-01-29T14:30:00Z"
}
```

### Collections

Use Activity Streams `Collection` for unordered sets:

**Request:**
```http
GET /factions
```

**Response (200 OK):**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Collection",
  "id": "https://api.example.com/factions",
  "summary": "All factions",
  "totalItems": 3,
  "items": [
    {
      "id": "faction:venice",
      "type": "Faction",
      "name": "Republic of Venice"
    },
    {
      "id": "faction:ottoman",
      "type": "Faction",
      "name": "Ottoman Empire"
    },
    {
      "id": "faction:france",
      "type": "Faction",
      "name": "Kingdom of France"
    }
  ]
}
```

### Ordered Collections

Use `OrderedCollection` when order matters (timelines, rankings, activity logs):

**Request:**
```http
GET /activities
```

**Response (200 OK):**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "OrderedCollection",
  "id": "https://api.example.com/activities",
  "summary": "Activity log",
  "totalItems": 147,
  "orderedItems": [
    {
      "id": "client:create-faction-001",
      "type": "Create",
      "actor": "user:deadwisdom",
      "published": "2026-01-29T14:30:00Z",
      "object": {
        "id": "faction:ottoman",
        "type": "Faction",
        "name": "Ottoman Empire"
      }
    },
    {
      "id": "client:declare-war-006",
      "type": "DeclareWar",
      "actor": "user:deadwisdom",
      "published": "2026-01-29T14:25:00Z",
      "object": "faction:france",
      "target": "faction:england"
    }
  ]
}
```

### Paginated Collections

For large collections, use `OrderedCollectionPage`:

**Request:**
```http
GET /activities?page=1
```

**Response (200 OK):**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "OrderedCollectionPage",
  "id": "https://api.example.com/activities?page=1",
  "partOf": "https://api.example.com/activities",
  "totalItems": 147,
  "next": "https://api.example.com/activities?page=2",
  "prev": null,
  "orderedItems": [
    { "id": "client:op-001", "type": "Create", "..." : "..." },
    { "id": "client:op-002", "type": "Update", "..." : "..." }
  ]
}
```

The base collection endpoint returns metadata with links to pages:

**Request:**
```http
GET /activities
```

**Response (200 OK):**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "OrderedCollection",
  "id": "https://api.example.com/activities",
  "totalItems": 147,
  "first": "https://api.example.com/activities?page=1",
  "last": "https://api.example.com/activities?page=8"
}
```

## Versioning

### Write Side (Activities)

Prefer additive evolution. When breaking changes are unavoidable, version via `@context`:

```json
{
  "@context": "https://example.com/schema/2026-01",
  "type": "Create",
  "...": "..."
}
```

Or use fully-qualified type URIs:

```json
{
  "type": "https://example.com/v2/ChangeGovernment",
  "...": "..."
}
```

### Read Side (GET endpoints)

Use query parameters with dated versions:

```http
GET /factions/venice?schema=2026-01
```

Avoid `/v1/` path prefixes—they version everything atomically when different resources evolve independently.

## Error Responses

Errors follow the Activity structure with `Reject` type:

**409 Conflict (duplicate activity with different content):**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Reject",
  "summary": "Activity with this ID already exists with different content",
  "object": {
    "id": "client:op-12345"
  }
}
```

**400 Bad Request (invalid activity):**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Reject",
  "summary": "Invalid activity: missing required field 'actor'",
  "object": {
    "type": "Create"
  }
}
```

**404 Not Found:**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Reject",
  "summary": "Resource not found",
  "object": "faction:atlantis"
}
```

## Implementation Notes

### Processing Activities

```
1. Validate activity structure and permissions
2. Check idempotency (has this activity ID been processed?)
3. Append to event store (immutable log)
4. Apply to projections (update read models)
5. Return enriched activity
```

### Projections

Read models are derived from the activity log. They can be:
- Rebuilt from scratch by replaying all activities
- Updated incrementally as new activities arrive
- Versioned independently from the activity schema

### Authorization

The outbox is your single chokepoint for all writes. Implement authorization as:

```
Can [actor] perform [activity.type] on [activity.object]?
```

### Content Types

- Request/Response: `application/activity+json` or `application/json`
- The `@context` field indicates Activity Streams vocabulary

## Quick Reference

| Operation | Method | Endpoint | Body |
|-----------|--------|----------|------|
| Create resource | POST | `/outbox` | `{ type: "Create", object: {...} }` |
| Update resource | POST | `/outbox` | `{ type: "Update", object: "uri", result: {...} }` |
| Delete resource | POST | `/outbox` | `{ type: "Delete", object: "uri" }` |
| Add to collection | POST | `/outbox` | `{ type: "Add", object: "uri", target: "collection-uri" }` |
| Remove from collection | POST | `/outbox` | `{ type: "Remove", object: "uri", target: "collection-uri" }` |
| Undo activity | POST | `/outbox` | `{ type: "Undo", object: "activity-uri" }` |
| Get resource | GET | `/{resources}/{id}` | — |
| List resources | GET | `/{resources}` | — |
| Get activity log | GET | `/activities` | — |

## Further Reading

- [Activity Streams 2.0 Core](https://www.w3.org/TR/activitystreams-core/)
- [Activity Vocabulary](https://www.w3.org/TR/activitystreams-vocabulary/)
- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
