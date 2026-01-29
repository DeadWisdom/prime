# Loom Design: Messaging, Actors, and Supervision

A design specification for Loom's core systems. This document covers the inter-agent message format, actor lifecycle, and supervision architecture. It is intended to be concrete enough to build from.

---

## 1. Message Schema (Activity Streams 2.0 / JSON-LD)

### 1.1 Context Definition

Every Loom message is a compact JSON-LD Activity Streams 2.0 document. A shared `@context` is used for all messages, extending AS2 with Loom-specific vocabulary.

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
      "loom": "https://loom.local/ns#",
      "loom:Spawn": { "@id": "loom:Spawn", "@type": "@id" },
      "loom:Assign": { "@id": "loom:Assign", "@type": "@id" },
      "loom:Briefing": { "@id": "loom:Briefing", "@type": "@id" },
      "loom:Escalate": { "@id": "loom:Escalate", "@type": "@id" },
      "loom:Heartbeat": { "@id": "loom:Heartbeat", "@type": "@id" },
      "loom:Kill": { "@id": "loom:Kill", "@type": "@id" },
      "loom:role": { "@id": "loom:role", "@type": "xsd:string" },
      "loom:sessionId": { "@id": "loom:sessionId", "@type": "xsd:string" },
      "loom:affair": { "@id": "loom:affair", "@type": "@id" },
      "loom:workingDirectory": { "@id": "loom:workingDirectory", "@type": "xsd:string" },
      "loom:exitCode": { "@id": "loom:exitCode", "@type": "xsd:integer" },
      "loom:state": { "@id": "loom:state", "@type": "xsd:string" },
      "loom:priority": { "@id": "loom:priority", "@type": "xsd:string" },
      "loom:allowedTools": { "@id": "loom:allowedTools", "@container": "@list" },
      "loom:parentActor": { "@id": "loom:parentActor", "@type": "@id" },
      "loom:deadline": { "@id": "loom:deadline", "@type": "xsd:dateTime" }
    }
  ]
}
```

In practice, this context is stored once and referenced by URL or inlined. Every message includes it. For brevity in the examples below, `"@context"` is shown but its body is omitted.

### 1.2 Actors

Every participant in the system is an AS2 Actor.

**Crown (the user):**

```json
{
  "@context": "...",
  "type": "Person",
  "id": "loom:actor/crown",
  "name": "The Crown",
  "preferredUsername": "crown"
}
```

**Prime Minister (persistent supervisor):**

```json
{
  "@context": "...",
  "type": "Application",
  "id": "loom:actor/prime",
  "name": "Prime Minister",
  "loom:role": "prime",
  "loom:state": "running",
  "loom:sessionId": "sess_abc123"
}
```

**Spawned agent (e.g., a Scribe):**

```json
{
  "@context": "...",
  "type": "Application",
  "id": "loom:actor/scribe-7f3a",
  "name": "Scribe 7f3a",
  "loom:role": "scribe",
  "loom:state": "idle",
  "loom:sessionId": "sess_def456",
  "loom:affair": "loom:affair/faction-map",
  "loom:workingDirectory": "/home/user/projects/faction-map",
  "loom:parentActor": "loom:actor/prime"
}
```

Actor IDs follow the pattern `loom:actor/{role}-{short_id}` for spawned agents, and `loom:actor/{name}` for singleton actors (crown, prime).

### 1.3 Activity Type Mapping

| Loom Operation | AS2 Type | Notes |
|---|---|---|
| Crown sends a task | `loom:Assign` | Custom. AS2 `Offer` is close but implies optionality. Assign is a directive. |
| Agent delegates work | `loom:Assign` | Same type. `actor` is the delegator, `to` is the delegate. |
| Agent reports completion | `Announce` | `object` is a summary `Note`. |
| Agent asks a question | `Question` | AS2 native. `oneOf`/`anyOf` for choices, or open-ended. |
| Crown/agent answers | `Accept` or `Note` | `Accept` with `inReplyTo` for choosing an option; `Create` + `Note` for open answers. |
| Agent escalates a problem | `loom:Escalate` | Custom. Semantically distinct from a question -- this is "I am blocked." |
| Prime broadcasts a briefing | `loom:Briefing` | Custom. A structured status report. |
| Spawn a new agent | `loom:Spawn` | Custom. No AS2 equivalent for process creation. |
| Kill an agent | `loom:Kill` | Custom. Terminate a running actor. |
| Update project state | `Update` | AS2 native. `object` is the updated resource. |
| Flag a concern | `Flag` | AS2 native. Something needs attention. |
| General message | `Create` + `Note` | AS2 native. Free-form communication. |
| Heartbeat / ping | `loom:Heartbeat` | Custom. Supervisor liveness check. |

### 1.4 Message Envelope

Every message follows this structure:

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T143022_a1b2c3",
  "type": "...",
  "actor": "loom:actor/prime",
  "to": ["loom:actor/scribe-7f3a"],
  "cc": ["loom:actor/crown"],
  "published": "2026-01-28T14:30:22Z",
  "object": { },
  "inReplyTo": "loom:message/msg_...",
  "loom:affair": "loom:affair/faction-map"
}
```

**Routing rules:**

- `to` -- primary recipients. The message is delivered to their inbox queues.
- `cc` -- informed recipients. Also delivered, but signals lower urgency.
- `bcc` -- silent delivery. Used sparingly (e.g., logging/audit actors).
- If `to` is omitted, the message is broadcast to all actors (only Prime should do this).

**Message IDs** follow the pattern `loom:message/msg_{ISO8601compact}_{random6}` to be both unique and chronologically sortable.

### 1.5 Concrete Message Flow Examples

#### Crown assigns a task to Prime

The Crown tells Prime to implement a new feature on the Faction Map project.

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T100000_x1y2z3",
  "type": "loom:Assign",
  "actor": "loom:actor/crown",
  "to": ["loom:actor/prime"],
  "published": "2026-01-28T10:00:00Z",
  "object": {
    "type": "Note",
    "content": "Implement projection morphing on the Faction Map. The globe should smoothly transition between Mercator and orthographic projections.",
    "loom:priority": "high"
  },
  "loom:affair": "loom:affair/faction-map"
}
```

#### Prime delegates to a Scribe

Prime spawns a Scribe and assigns it the work. This is two messages: a Spawn, then an Assign.

**Spawn:**

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T100030_a2b3c4",
  "type": "loom:Spawn",
  "actor": "loom:actor/prime",
  "to": ["loom:actor/prime"],
  "published": "2026-01-28T10:00:30Z",
  "object": {
    "type": "Application",
    "id": "loom:actor/scribe-7f3a",
    "name": "Scribe 7f3a",
    "loom:role": "scribe",
    "loom:affair": "loom:affair/faction-map",
    "loom:workingDirectory": "/home/user/projects/faction-map",
    "loom:allowedTools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
  }
}
```

**Assign:**

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T100045_d4e5f6",
  "type": "loom:Assign",
  "actor": "loom:actor/prime",
  "to": ["loom:actor/scribe-7f3a"],
  "cc": ["loom:actor/crown"],
  "published": "2026-01-28T10:00:45Z",
  "object": {
    "type": "Note",
    "content": "Implement smooth projection morphing between Mercator and orthographic on the globe component. The transition should animate over 500ms using D3's projection interpolation. See src/globe.js for the current projection setup.",
    "loom:priority": "high"
  },
  "inReplyTo": "loom:message/msg_20260128T100000_x1y2z3",
  "loom:affair": "loom:affair/faction-map"
}
```

#### Scribe reports completion

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T104500_g7h8i9",
  "type": "Announce",
  "actor": "loom:actor/scribe-7f3a",
  "to": ["loom:actor/prime"],
  "cc": ["loom:actor/crown"],
  "published": "2026-01-28T10:45:00Z",
  "object": {
    "type": "Note",
    "content": "Projection morphing implemented. Added `morphProjection(from, to, duration)` to `src/globe.js`. Uses D3 `geoProjection` interpolation with a 500ms CSS-eased transition. Tested with Mercator <-> orthographic and Natural Earth <-> orthographic. Committed as `feat: add projection morphing`.",
    "name": "Task Complete: Projection Morphing"
  },
  "inReplyTo": "loom:message/msg_20260128T100045_d4e5f6",
  "loom:affair": "loom:affair/faction-map"
}
```

#### Agent escalates a problem to Prime

The Scribe hits a blocking issue it cannot resolve.

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T103000_j1k2l3",
  "type": "loom:Escalate",
  "actor": "loom:actor/scribe-7f3a",
  "to": ["loom:actor/prime"],
  "published": "2026-01-28T10:30:00Z",
  "object": {
    "type": "Note",
    "content": "D3 v7 removed `geoInterpolate` for projection morphing. The recommended approach uses `d3-geo-projection` but that package conflicts with our current D3 import setup. I need guidance: (1) restructure imports to use modular D3, or (2) use a different interpolation approach.",
    "name": "Blocked: D3 projection interpolation unavailable"
  },
  "loom:affair": "loom:affair/faction-map"
}
```

#### Prime broadcasts a briefing to the Crown

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T180000_m4n5o6",
  "type": "loom:Briefing",
  "actor": "loom:actor/prime",
  "to": ["loom:actor/crown"],
  "published": "2026-01-28T18:00:00Z",
  "object": {
    "type": "Note",
    "name": "Evening Briefing",
    "content": "Your Majesty.\n\nThe realm stands in reasonable order. Three affairs saw movement today.\n\n**Faction Map** — Projection morphing is complete. The Scribe encountered a D3 versioning issue which I resolved by directing a switch to modular imports. The feature is committed and working.\n\n**Column SMS** — The Herald deployed the final build. Invoice sent. Awaiting payment.\n\n**Loom** — Design specifications are drafted. Prototype work can begin tomorrow.\n\nI am at your disposal should you wish to discuss any matter further."
  },
  "loom:affair": null
}
```

Note: `loom:affair` is `null` for cross-cutting briefings.

#### Agent spawns a child agent

Prime spawns a Scholar to research a technical question.

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T103100_p7q8r9",
  "type": "loom:Spawn",
  "actor": "loom:actor/prime",
  "published": "2026-01-28T10:31:00Z",
  "object": {
    "type": "Application",
    "id": "loom:actor/scholar-2c4d",
    "name": "Scholar 2c4d",
    "loom:role": "scholar",
    "loom:affair": "loom:affair/faction-map",
    "loom:workingDirectory": "/home/user/projects/faction-map",
    "loom:allowedTools": ["Read", "Glob", "Grep", "WebFetch", "WebSearch"]
  }
}
```

Immediately followed by the assignment:

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T103115_s1t2u3",
  "type": "loom:Assign",
  "actor": "loom:actor/prime",
  "to": ["loom:actor/scholar-2c4d"],
  "published": "2026-01-28T10:31:15Z",
  "object": {
    "type": "Note",
    "content": "Research the current state of D3 v7 projection interpolation. Specifically: what replaced geoInterpolate, how to use d3-geo-projection as a standalone module, and whether there are conflicts with bundled D3 imports. Report findings."
  },
  "inReplyTo": "loom:message/msg_20260128T103000_j1k2l3",
  "loom:affair": "loom:affair/faction-map"
}
```

#### Question from agent to Crown, Crown responds

A Scribe needs a design decision:

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T110000_v4w5x6",
  "type": "Question",
  "actor": "loom:actor/scribe-7f3a",
  "to": ["loom:actor/crown"],
  "cc": ["loom:actor/prime"],
  "published": "2026-01-28T11:00:00Z",
  "name": "Projection selector UI",
  "content": "Should the projection selector be a dropdown menu or a set of toggle buttons? The dropdown is more compact but the buttons allow showing small preview thumbnails of each projection.",
  "oneOf": [
    { "type": "Note", "name": "Dropdown menu" },
    { "type": "Note", "name": "Toggle buttons with thumbnails" }
  ],
  "loom:affair": "loom:affair/faction-map"
}
```

Crown responds:

```json
{
  "@context": "...",
  "id": "loom:message/msg_20260128T111500_y7z8a9",
  "type": "Accept",
  "actor": "loom:actor/crown",
  "to": ["loom:actor/scribe-7f3a"],
  "cc": ["loom:actor/prime"],
  "published": "2026-01-28T11:15:00Z",
  "object": { "type": "Note", "name": "Toggle buttons with thumbnails" },
  "inReplyTo": "loom:message/msg_20260128T110000_v4w5x6",
  "loom:affair": "loom:affair/faction-map"
}
```

### 1.6 Redis Storage

Messages are stored in Redis as JSON strings. Two structures:

1. **Per-actor inbox** -- a Redis List. Key: `loom:inbox:{actor_id}`.
   Messages are `RPUSH`ed by senders and `LPOP`ed by the recipient's processing loop.

2. **Message log** -- a Redis Sorted Set. Key: `loom:messages:{affair_id}` (or `loom:messages:global` for cross-cutting messages). Score is the Unix timestamp of `published`. Value is the full JSON message.
   This enables chronological querying of all messages for a project or globally.

   Note: storing full JSON as the sorted set member means two messages with identical content would deduplicate. This is acceptable at Loom's expected scale; if storage pressure arises, switch to storing message IDs as members with a separate lookup.

3. **Message by ID** -- a Redis String. Key: `loom:message:{message_id}`. Stores the full JSON as a string value. Used for `inReplyTo` resolution.

Messages are compact JSON-LD as defined above. No expansion is needed at runtime; the context is for semantic interoperability, not for runtime processing.

---

## 2. Actor Lifecycle

### 2.1 State Machine

```
                 ┌─────────┐
                 │ spawned  │
                 └────┬─────┘
                      │ (process created, awaiting first message)
                      v
                 ┌─────────┐
          ┌─────>│  idle    │<────────────┐
          │      └────┬─────┘             │
          │           │ (message received) │
          │           v                   │
          │      ┌─────────┐              │
          │      │ running  │─────────────┘
          │      └────┬─────┘   (work complete, no pending messages)
          │           │
          │           ├── (waiting on external input)
          │           v
          │      ┌─────────┐
          │      │ waiting  │
          │      └────┬─────┘
          │           │ (input received)
          │           v
          │      ┌─────────┐
          │      │ running  │
          │      └────┬─────┘
          │           │
          │           ├── (task finished successfully)
          │           v
          │      ┌───────────┐
          │      │ completed  │ ── (terminal for task actors)
          │      └────────────┘
          │
          │           ├── (error / crash)
          │           v
          │      ┌─────────┐
          │      │ failed   │ ── (supervisor decides: restart or kill)
          │      └────┬─────┘
          │           │ (restart)
          │           v
          │      ┌──────────┐
          └──────│ resuming │
                 └──────────┘
                      │ (session restored via --resume)
                      v
                 ┌─────────┐
                 │  idle    │
                 └──────────┘

  External kill:
  Any state ──> killed (terminal)
```

States: `spawned`, `idle`, `running`, `waiting`, `completed`, `failed`, `killed`, `resuming`.

Terminal states: `completed`, `killed`. An actor in `failed` is not terminal -- the supervisor decides its fate.

Prime is special: it never enters `completed`. It cycles between `idle` and `running` indefinitely until explicitly killed.

### 2.2 Spawn

**Who can spawn:**
- The Crown can spawn any actor (via the UI, which sends a `loom:Spawn` to Prime, who executes it).
- Prime can spawn any actor directly.
- Any running actor can request a spawn by sending a `loom:Spawn` message to Prime. Prime validates and executes it.

Only Prime actually creates subprocesses. Other actors request spawns; Prime fulfills them. This keeps subprocess management centralized.

**Spawn parameters:**

| Parameter | Source | Required |
|---|---|---|
| `loom:role` | Spawn message | Yes |
| `loom:affair` | Spawn message or inherited from parent | No (Prime has none) |
| `loom:workingDirectory` | Spawn message, or derived from affair | Yes for non-Prime |
| `loom:allowedTools` | Role defaults, overridable in spawn message | No (role defaults used) |
| System prompt | Derived from role | Automatic |
| Actor ID | Generated: `{role}-{random4hex}` | Automatic |

**Role defaults for `allowedTools`:**

- **Scribe:** `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `NotebookEdit`
- **Scholar:** `Read`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `Bash(git log:git diff:git show)`
- **Chancellor:** `Read`, `Write`, `Glob`, `Grep`, `WebFetch`, `WebSearch`
- **Herald:** `Read`, `Bash`, `Glob`, `Grep`
- **Page:** `Read`, `Bash`, `Glob`, `Grep`

**Spawn execution (what Prime does):**

1. Generate actor ID.
2. Create actor record in the registry (see Section 3).
3. Start a Claude Code CLI subprocess:
   ```
   claude -p "You are awake. Await your first assignment." \
     --output-format json \
     --append-system-prompt "{role_system_prompt}" \
     --allowedTools "{tools}"
   ```
   Subprocess `cwd` is set to `loom:workingDirectory`.
4. Capture the session ID from the CLI's JSON output.
5. Store session ID in the actor record.
6. Set state to `idle`.
7. Deliver any queued messages.

### 2.3 Receive

When a message arrives for an actor:

1. The message is `RPUSH`ed to `loom:inbox:{actor_id}` in Redis.
2. A Redis Pub/Sub notification is published to `loom:notify:{actor_id}`.
3. The backend's **dispatcher** (a Python asyncio task per active actor) is listening on that channel.
4. The dispatcher checks the actor's state:
   - If `idle`: transition to `running`, deliver the message (see 2.4).
   - If `running`: the message stays queued. The actor will check its inbox when it finishes its current work.
   - If `waiting`: deliver immediately (this is probably the response it's waiting for).
   - If `completed` or `killed`: bounce the message back to the sender with an error Note.
   - If `failed`: queue the message. The supervisor will decide whether to restart.

**Message delivery** means invoking the CLI with the message content as the prompt, using `--resume` with the actor's session ID:

```
claude -p "{message_json}" \
  --resume {session_id} \
  --output-format json
```

When resuming a session, `--allowedTools` and `--append-system-prompt` are not re-specified; the resumed session retains these from the original spawn.

The message JSON is passed as the prompt text. The actor's system prompt (set at spawn) already instructs it on how to parse and respond to Loom messages.

### 2.4 Act

The actor "acts" by executing inside the Claude Code CLI subprocess. From Loom's perspective:

1. The CLI process runs, potentially using tools (file edits, bash commands, web searches, etc.).
2. The CLI produces JSON output when it finishes.
3. The backend captures this output.

**Output parsing:**

The CLI's JSON output contains the assistant's response. The backend parses this for:
- **Outbound messages:** The actor's system prompt instructs it to emit Loom messages as JSON code blocks tagged `loom-message`. The backend extracts these and routes them.
- **State signals:** If the output contains a structured completion or error signal, the backend updates the actor's state accordingly.

**System prompt contract (injected via `--append-system-prompt`):**

Each role's system prompt includes instructions like:

> You are a {role} in the Loom system. You communicate with other actors by emitting JSON messages in fenced code blocks tagged `loom-message`. When you receive a message, parse the JSON and act on it. When you need to communicate, emit a message block. You may emit multiple message blocks in a single response.
>
> To send a message:
> ```loom-message
> { "type": "Announce", "to": ["loom:actor/prime"], ... }
> ```
>
> Your actor ID is {actor_id}. You are working on affair {affair_name} in {working_directory}.

The backend's output parser extracts all `loom-message` blocks, fills in `actor`, `published`, and `id` fields (the agent does not need to generate these), and routes them.

### 2.5 Send

Sending is the backend's responsibility, not the actor's directly. The flow:

1. Actor emits a `loom-message` block in its CLI output.
2. Backend extracts the block, validates it, and fills in envelope fields (`id`, `actor`, `published`).
3. Backend stores the message in Redis (inbox of recipients, message log, message-by-ID).
4. Backend publishes a Pub/Sub notification for each recipient.
5. Backend forwards the message to any connected WebSocket clients (for the UI).

The actor never directly touches Redis or the network. All I/O is mediated by the backend.

### 2.6 Die

Actors terminate in several ways:

**Graceful completion:**
The actor signals it is done (its output includes a completion message or it simply has no more work). The backend sets state to `completed`. The CLI process has already exited.

**Idle timeout:**
Task actors (non-Prime) that remain `idle` for longer than 10 minutes are killed. The session ID is preserved in the registry so it can be resumed if needed.

**Explicit kill:**
A `loom:Kill` message from Prime or the Crown. The backend sends SIGTERM to the CLI subprocess, waits 5 seconds, then SIGKILL if needed. State is set to `killed`.

**Crash / failure:**
The CLI process exits with a non-zero code, or the output indicates an error. State is set to `failed`. The supervisor (Prime) is notified.

On death, the actor's registry entry is preserved (for resume and audit), but its dispatcher task is stopped and its inbox stops accepting messages.

### 2.7 Resume

A dead actor can be revived if its session ID is still valid:

1. A `loom:Spawn` message with the existing actor ID triggers a resume instead of a fresh spawn.
2. The backend invokes the CLI with `--resume {session_id}` and delivers the new prompt.
3. State transitions to `resuming`, then `running`.
4. If `--resume` fails (session expired or corrupted), a fresh spawn occurs with a new session. The old actor record is marked `killed` and a new one is created.

Session IDs are stored indefinitely in the registry. Claude Code CLI session persistence is file-based (in `~/.claude/`), so sessions survive backend restarts.

---

## 3. Actor Registry and Supervision Tree

### 3.1 Registry

The actor registry lives in Redis as a Hash per actor and a Set for enumeration.

**Actor record** -- Key: `loom:actor:{actor_id}`

```json
{
  "id": "loom:actor/scribe-7f3a",
  "role": "scribe",
  "name": "Scribe 7f3a",
  "state": "running",
  "sessionId": "sess_def456",
  "pid": 48201,
  "affair": "loom:affair/faction-map",
  "workingDirectory": "/home/user/projects/faction-map",
  "parentActor": "loom:actor/prime",
  "allowedTools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
  "spawnedAt": "2026-01-28T10:00:30Z",
  "lastActiveAt": "2026-01-28T10:42:15Z",
  "restartCount": 0,
  "error": null
}
```

**Enumeration sets:**
- `loom:actors:all` -- Set of all actor IDs, all time.
- `loom:actors:alive` -- Set of actor IDs not in a terminal state.
- `loom:actors:by-affair:{affair_id}` -- Set of actor IDs working on a specific affair.
- `loom:actors:by-role:{role}` -- Set of actor IDs with a specific role.

**Why Redis, not markdown?**

The registry is runtime state that changes rapidly (state transitions, heartbeats, PID tracking). Redis is the right tool. Durable project knowledge (affairs, decisions, ledgers) stays in markdown + git. The registry is ephemeral -- if Redis is flushed, actors are re-spawned from the affair files, which are the source of truth for what work exists.

### 3.2 Supervision Tree

```
Crown (Person)
  │
  └── Prime (Application, persistent)
        │
        ├── Scribe-7f3a (task, affair: faction-map)
        │     └── Page-b1c2 (subtask, spawned by scribe via prime)
        │
        ├── Scholar-2c4d (task, affair: faction-map)
        │
        ├── Herald-9e0f (task, affair: column-sms)
        │
        └── Chancellor-5g6h (task, affair: loom)
```

Prime is the root supervisor. All actors are children of Prime (even if requested by another actor, Prime performs the actual spawn). The `parentActor` field tracks the logical parent -- who requested the spawn -- for routing escalations back up the chain.

### 3.3 Restart Policies

When an actor enters `failed`:

1. Prime is notified via a system-generated `Flag` message.
2. Prime evaluates the failure:
   - **Transient error (exit code 1, no meaningful error message):** Restart with `--resume`. Increment `restartCount`.
   - **Repeated failure (restartCount >= 3):** Do not restart. Escalate to Crown. Mark as `killed`.
   - **Resource error (rate limit, out of context):** Do not restart immediately. Wait for the rate limit window to pass (tracked by the backend), then restart.
   - **Explicit failure message from agent ("I cannot complete this task"):** Do not restart. Report to Crown.

Prime does not need complex policy configuration. It is an intelligent agent -- it reads the error, the context, and makes a judgment call. The restart count cap is the only hard rule enforced by the backend.

### 3.4 Session Management

Session IDs are the key to actor continuity. They are managed as follows:

- **On spawn:** The CLI's JSON output includes a session ID. Stored in the actor record.
- **On resume:** The same session ID is passed via `--resume`. If it works, the actor picks up where it left off.
- **On session expiry:** If `--resume` fails, a new session is created. The actor loses its conversation history but retains its role, affair, and any messages re-delivered to it.
- **Cleanup:** Session IDs for actors in terminal states (`completed`, `killed`) older than 7 days are eligible for cleanup. A background task removes them from the registry and deletes the CLI session files from `~/.claude/`.

### 3.5 Project / Affair Association

This addresses the open question: "How is an actor's working directory / project association specified?"

**The affair is the anchor.** Each affair in `affairs/` corresponds to a project directory somewhere on disk. The mapping is stored in a simple config file:

`affairs/manifest.json`:

```json
{
  "faction-map": {
    "directory": "/home/user/projects/faction-map",
    "repo": "git@github.com:user/faction-map.git"
  },
  "column-sms": {
    "directory": "/home/user/projects/column-sms",
    "repo": "git@github.com:user/column-sms.git"
  },
  "loom": {
    "directory": "/home/user/projects/loom",
    "repo": "git@github.com:user/loom.git"
  }
}
```

When Prime spawns an actor for an affair, it reads the manifest to set `workingDirectory`. If an affair has no entry in the manifest, Prime asks the Crown.

Agents are not permanently bound to affairs. An agent spawned for `faction-map` works in that directory and focuses on that project, but it can read files elsewhere if needed. The affair association is a default scope, not a sandbox.

---

## 4. Open Questions Resolved

### 4.1 Prime's Continuous Iteration Loop

Prime runs as a persistent actor managed by a dedicated backend coroutine. The loop:

```
LOOP:
  1. Check inbox (LPOP from loom:inbox:loom:actor/prime)
     - If messages exist: deliver them to Prime CLI via --resume, process output.
     - If no messages: proceed to step 2.

  2. Check wall clock against schedule:
     - Every 15 minutes: Prime gets a "pulse" -- a system-generated Heartbeat
       containing a summary of current actor states (who's alive, who's idle,
       any failures since last pulse).
     - Morning (09:00 local): Prime generates a morning briefing for the Crown.
     - Evening (18:00 local): Prime generates an evening briefing.

  3. Sleep for 2 seconds, then repeat.
```

**Wake triggers (bypass the sleep):**

- Any message arriving in Prime's inbox triggers an immediate wake via Redis Pub/Sub.
- Any actor entering `failed` state triggers an immediate wake.
- Any Crown message (from the UI) triggers an immediate wake.

The 2-second sleep is only reached when nothing is happening. In practice, Prime will mostly be event-driven.

**Rate limit awareness:**

Prime tracks usage against the Max plan's rolling window. If usage is high, Prime extends sleep intervals and defers non-urgent work. It does not spawn new agents when the pool is depleted. This logic lives in the backend, not in Prime's AI reasoning -- the backend simply refuses spawn requests when usage is above 80% of the estimated window.

### 4.2 Git Integration

**Approach: Agent-initiated commits with guidelines, not automatic.**

- Agents (specifically Scribes and Heralds) are instructed in their system prompts to commit their work at meaningful checkpoints, not after every file change.
- Prime does not auto-commit. It reviews agent output and may instruct an agent to commit if it detects uncommitted work.
- The affair markdown files (in `affairs/`) are committed to the Prime repo separately, not to project repos. Prime commits changes to affairs after processing (updating status, ledger entries, etc.).
- There is no automatic git commit on state changes in Redis. Redis state is ephemeral.

**Rationale:** Auto-committing on every state change produces noisy, meaningless git history. Agents are intelligent enough to commit at the right times when instructed to do so.

### 4.3 User Authentication

**Phase 1: Simple bearer tokens.**

Each user is assigned a static token stored in a server-side config file. The token is sent as a Bearer token in the WebSocket handshake and HTTP requests. No database, no OAuth flow.

```json
{
  "tokens": {
    "crown_abc123": { "name": "Crown", "role": "crown" },
    "friend_def456": { "name": "Alice", "role": "guest" }
  }
}
```

Roles:
- `crown` -- full access. Can spawn, kill, assign, read all messages.
- `guest` -- can send messages to specific affairs they've been granted access to. Cannot spawn or kill agents. Cannot read messages from other affairs.

**Phase 2 (when needed):** OAuth via Cloudflare Access. The Cloudflare Tunnel already provides the infrastructure. This adds proper identity without building an auth system.

**Phase 3 (if ever):** Per-affair access control lists. Each affair specifies which users can interact with it. But this is premature -- start simple.

---

## Appendix A: Redis Key Reference

| Key Pattern | Type | Purpose |
|---|---|---|
| `loom:inbox:{actor_id}` | List | Actor's message queue |
| `loom:notify:{actor_id}` | Pub/Sub channel | Wake signal for actor dispatcher |
| `loom:message:{message_id}` | String (JSON) | Full message by ID |
| `loom:messages:{affair_id}` | Sorted Set (by timestamp) | Message log per affair |
| `loom:messages:global` | Sorted Set (by timestamp) | Cross-cutting message log |
| `loom:actor:{actor_id}` | Hash | Actor registry record |
| `loom:actors:all` | Set | All actor IDs |
| `loom:actors:alive` | Set | Non-terminal actor IDs |
| `loom:actors:by-affair:{affair_id}` | Set | Actors for an affair |
| `loom:actors:by-role:{role}` | Set | Actors by role |
| `loom:usage:window` | String (JSON) | Current rate limit tracking |

## Appendix B: System Prompt Templates (Abridged)

These are appended via `--append-system-prompt`. They do not replace Claude Code's built-in system prompt.

**Prime Minister:**

> You are the Prime Minister of the Loom. You coordinate all affairs of state, supervise other agents, and advise the Crown. You receive messages in Loom's Activity Streams format. Parse them and act accordingly. To send a message, emit a fenced code block tagged `loom-message` containing valid JSON. You may emit multiple messages in one response. Your actor ID is loom:actor/prime. You serve continuously. You never declare yourself complete.

**Scribe:**

> You are a Scribe in the Loom system. You write and edit code. You receive assignments as Loom messages and report completion or problems back via `loom-message` blocks. Your actor ID is {actor_id}. You are working on {affair_name} in {working_directory}. Commit your work at meaningful checkpoints with clear commit messages.

**Scholar:**

> You are a Scholar in the Loom system. You research, read, and gather intelligence. You receive research assignments as Loom messages and report findings via `loom-message` blocks. Your actor ID is {actor_id}. Do not modify files. Report what you learn.

(Chancellor, Herald, Page follow the same pattern.)

---

*This document serves as the implementable specification for Loom's messaging, actor, and supervision systems. It is a living document -- update it as decisions are refined during prototyping.*
