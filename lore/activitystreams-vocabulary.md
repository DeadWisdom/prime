# ActivityStreams 2.0 and Activity Vocabulary

researched: 2025-01-26
status: complete
tags: activitypub, activitystreams, json-ld, federation, social-web

## Executive Summary

ActivityStreams 2.0 is a JSON-LD based format for describing social activities and content. It defines three fundamental categories: Objects (content), Activities (actions), and Actors (entities). This vocabulary powers ActivityPub and federated social networks.

## Background

ActivityStreams is a W3C standard that provides a common vocabulary for social web applications. Every ActivityStreams document uses the AS2 context (`https://www.w3.org/ns/activitystreams`) to define how JSON keys map to semantic meanings.

## Key Findings

### Basic Structure

Every ActivityStreams document requires the context:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Note",
  "id": "https://example.org/notes/1",
  "content": "Hello, world!"
}
```

### Common Properties

**Identity and Metadata:**
| Property | Description | Functional |
|----------|-------------|------------|
| `id` | Unique IRI identifier | Yes |
| `type` | Object type(s) | No |
| `name` | Display name | No |
| `summary` | Short description | No |
| `content` | Primary content (HTML allowed) | No |

**Temporal Properties:**
| Property | Description | Functional |
|----------|-------------|------------|
| `published` | When created | Yes |
| `updated` | Last modified | Yes |
| `startTime` | When activity begins | Yes |
| `endTime` | When activity ends | Yes |

**Attribution and Addressing:**
| Property | Description | Functional |
|----------|-------------|------------|
| `attributedTo` | Creator/author | No |
| `to` | Primary recipients | No |
| `cc` | Secondary recipients | No |
| `bcc` | Hidden recipients | No |
| `audience` | Intended audience | No |

### Object Types

Common content types: `Note`, `Article`, `Image`, `Video`, `Audio`, `Document`, `Page`, `Event`

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Note",
  "id": "https://example.org/notes/123",
  "attributedTo": "https://example.org/users/alice",
  "content": "<p>This is a <strong>note</strong>.</p>",
  "published": "2024-01-15T10:00:00Z",
  "to": ["https://www.w3.org/ns/activitystreams#Public"],
  "cc": ["https://example.org/users/alice/followers"]
}
```

### Activity Types

Activities describe actions with these core properties:
- `actor` - Who performed the activity
- `object` - What the activity affects
- `target` - Where the object is directed
- `result` - Outcome of the activity
- `origin` - Where the object came from

**Create:**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Create",
  "actor": "https://example.org/users/alice",
  "object": {
    "type": "Note",
    "content": "Hello!"
  }
}
```

**Like and Announce (boost/repost):**
```json
{
  "type": "Like",
  "actor": "https://example.org/users/bob",
  "object": "https://example.org/notes/123"
}
```

**Follow / Accept / Reject:**
```json
{
  "type": "Follow",
  "id": "https://example.org/activities/follow/1",
  "actor": "https://example.org/users/bob",
  "object": "https://example.org/users/alice"
}
```

Accept a follow by wrapping the follow activity:
```json
{
  "type": "Accept",
  "actor": "https://example.org/users/alice",
  "object": "https://example.org/activities/follow/1"
}
```

**Undo** reverses a previous activity:
```json
{
  "type": "Undo",
  "actor": "https://example.org/users/bob",
  "object": {
    "type": "Like",
    "actor": "https://example.org/users/bob",
    "object": "https://example.org/notes/123"
  }
}
```

Other activity types: `Add`, `Remove`, `Move`, `Block`, `Flag`, `Update`, `Delete`

### Actor Types

Actor types: `Person`, `Application`, `Group`, `Organization`, `Service`

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Person",
  "id": "https://example.org/users/alice",
  "name": "Alice",
  "preferredUsername": "alice",
  "inbox": "https://example.org/users/alice/inbox",
  "outbox": "https://example.org/users/alice/outbox",
  "followers": "https://example.org/users/alice/followers",
  "following": "https://example.org/users/alice/following"
}
```

### Collections

Collections are paginated lists:

```json
{
  "type": "OrderedCollection",
  "id": "https://example.org/users/alice/outbox",
  "totalItems": 100,
  "first": "https://example.org/users/alice/outbox?page=1"
}
```

**Collection pages:**
```json
{
  "type": "OrderedCollectionPage",
  "partOf": "https://example.org/users/alice/outbox",
  "next": "https://example.org/users/alice/outbox?page=2",
  "orderedItems": [...]
}
```

### Tags and Mentions

```json
{
  "type": "Note",
  "content": "Hello @bob, check out #activitypub",
  "tag": [
    {
      "type": "Mention",
      "href": "https://example.org/users/bob",
      "name": "@bob"
    },
    {
      "type": "Hashtag",
      "href": "https://example.org/tags/activitypub",
      "name": "#activitypub"
    }
  ]
}
```

### Public Addressing

The special IRI for public content: `https://www.w3.org/ns/activitystreams#Public`

- In `to` for fully public
- In `cc` for unlisted (public but not on public timelines)

## Practical Implications

1. **Always set `id`** - Objects should have unique, dereferenceable IRIs
2. **Normalize multi-value properties** - Properties like `to`, `cc`, `tag` can be single values or arrays:
   ```typescript
   const asArray = (v) => v == null ? [] : Array.isArray(v) ? v : [v];
   ```
3. **Handle `type` as array** - Objects can have multiple types
4. **Use `attributedTo` for authorship** - Don't assume `actor` on nested objects
5. **Check `mediaType`** - Content can be plain text or HTML
6. **Tombstones for deletions** - Replace deleted objects with a Tombstone type

## Sources & Further Reading

- W3C ActivityStreams 2.0: https://www.w3.org/TR/activitystreams-core/
- Activity Vocabulary: https://www.w3.org/TR/activitystreams-vocabulary/
- ActivityPub: https://www.w3.org/TR/activitypub/

## Open Questions

- Best practices for handling large collections with many pages
- Strategies for validating incoming ActivityStreams content
- Handling extensions and custom properties
