# JSON-LD Primer

researched: 2025-01-26
status: complete
tags: json-ld, linked-data, semantic-web, activitypub, json

## Executive Summary

JSON-LD (JavaScript Object Notation for Linked Data) encodes Linked Data using JSON by mapping keys to globally unique identifiers (IRIs). It adds semantic meaning to JSON documents, enabling data interchange between systems with shared understanding.

## Background

JSON-LD solves the problem of giving JSON data global, unambiguous meaning. Without it, a `name` field in one system might mean something different in another. By mapping properties to IRIs (Internationalized Resource Identifiers), JSON-LD ensures properties have unique, global definitions.

## Key Findings

### The @context Field

The `@context` defines how to interpret keys:

```json
{
  "@context": {
    "name": "https://schema.org/name",
    "homepage": "https://schema.org/url"
  },
  "name": "Alice",
  "homepage": "https://alice.example.com"
}
```

Reference external contexts by URL:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Person",
  "name": "Alice"
}
```

Combine multiple contexts:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
      "customField": "https://example.org/ns/customField"
    }
  ]
}
```

### Field Uniqueness via IRIs

Every property maps to a unique IRI. Two vocabularies can both have a `name` field, but they're distinct:

```json
{
  "@context": {
    "displayName": "https://schema.org/name",
    "asName": "https://www.w3.org/ns/activitystreams#name"
  }
}
```

This prevents collisions when mixing vocabularies.

### Multi-Value Properties

Any property can have multiple values using an array:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Note",
  "to": [
    "https://example.org/users/bob",
    "https://example.org/users/charlie"
  ],
  "tag": [
    {
      "type": "Mention",
      "href": "https://example.org/users/bob",
      "name": "@bob"
    },
    {
      "type": "Hashtag",
      "href": "https://example.org/tags/json",
      "name": "#json"
    }
  ]
}
```

When processing JSON-LD, always handle properties as potentially having multiple values.

### Functional vs Non-Functional Properties

**Functional properties** (should only have one value):
- `id` - unique identifier
- `published` - publication date
- `startTime` / `endTime` - temporal bounds
- `duration`

**Non-functional properties** (can have multiple values):
- `to`, `cc`, `bcc` - recipients
- `tag` - attached tags/mentions
- `attachment` - media attachments

### ActivityStreams Examples

**Creating an Activity:**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Create",
  "id": "https://example.org/activities/1",
  "actor": "https://example.org/users/alice",
  "published": "2024-01-15T10:30:00Z",
  "to": ["https://www.w3.org/ns/activitystreams#Public"],
  "cc": ["https://example.org/users/alice/followers"],
  "object": {
    "type": "Note",
    "id": "https://example.org/notes/1",
    "content": "Hello, world!",
    "attributedTo": "https://example.org/users/alice"
  }
}
```

**A Person Actor:**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Person",
  "id": "https://example.org/users/alice",
  "name": "Alice",
  "preferredUsername": "alice",
  "inbox": "https://example.org/users/alice/inbox",
  "outbox": "https://example.org/users/alice/outbox"
}
```

**A Collection:**
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "OrderedCollection",
  "id": "https://example.org/users/alice/outbox",
  "totalItems": 42,
  "first": "https://example.org/users/alice/outbox?page=1"
}
```

## Practical Implications

1. **Always include @context** - Without it, JSON has no semantic meaning

2. **Use established vocabularies** - ActivityStreams, Schema.org, and others provide well-defined terms

3. **Normalize when processing** - Use a JSON-LD library to expand documents to canonical form

4. **Handle arrays defensively** - Even single values might come as arrays:
   ```typescript
   const toArray = (value) => Array.isArray(value) ? value : [value];
   const recipients = toArray(activity.to);
   ```

5. **Use `@id` for references** - Link to other objects by IRI rather than embedding:
   ```json
   { "actor": "https://example.org/users/alice" }
   ```

6. **Compact vs Expanded form** - JSON-LD can be processed in expanded form (full IRIs) or compacted (using context). Choose based on your needs.

## Sources & Further Reading

- JSON-LD Spec: https://www.w3.org/TR/json-ld11/
- JSON-LD Playground: https://json-ld.org/playground/
- Schema.org: https://schema.org/
- ActivityStreams Context: https://www.w3.org/ns/activitystreams

## Open Questions

- Performance implications of JSON-LD expansion in high-throughput systems
- Best practices for versioning custom contexts
- Handling context resolution failures gracefully
