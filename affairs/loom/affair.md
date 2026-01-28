# Loom

status: active
priority: high
domain: personal

## Brief

A browser-based orchestration system for coordinating multiple Claude agents across projects. The Prime Minister operates from the Loom, weaving threads of work together across affairs of state.

**Core concept:** Agents send messages to each other as a way of communicating. No shared conversation context — instead, an inter-agent messaging protocol.

## Architecture

**True Actor Model.** Agents are the fundamental unit. They are specialized by role, not by project. A project can have many agents running, including multiples of the same type. Agents can spawn other agents.

**Prime Minister** runs continuously — iterating on a schedule and waking when messages arrive. Prime coordinates across all projects and agents.

**Runtime: Claude Code CLI on Max plan**
- Each agent invocation = a `claude -p` subprocess with `--output-format json`
- Session resume (`--resume {session_id}`) maintains agent context across messages
- Working directory set via subprocess cwd (no `--cwd` flag)
- Tool control via `--allowedTools` with prefix matching
- Role defined via `--append-system-prompt` (preserves built-in Claude Code behavior)
- Fixed monthly cost; all CLI usage shares pool with web chat
- Max 5x ($100/mo) ≈ 50–200 code prompts per 5-hour rolling window + weekly ceiling
- Multiple concurrent instances allowed but drain pool faster
- Options for scaling: multiple Max accounts, or enable "extra usage" (overflow to API rates)
- Agent SDK exists but uses API keys (pay-per-use only) — Anthropic prohibits subscription auth for third-party agents

**Backend (FastAPI)**
- Agent loop watches Redis, dispatches messages as CLI invocations
- Prime as a persistent supervisor actor
- Message bus (Upstash Redis) for inter-agent communication
- WebSocket connections for real-time streaming to frontend
- Persistence: Redis for runtime state, markdown files + git for durable project state
- Multi-user: any user can connect and converse with agents about projects

**Infrastructure**
- Runs on home machine
- Cloudflare Tunnel for external access
- Upstash Redis for managed message bus
- No Kubernetes, no Cloud Functions, no Docker (for now)
- Migration path: move FastAPI process to single Cloud Run instance if needed

**Frontend (Lit + plain CSS)**
- Multi-pane interface for switching between project conversations
- "Loom view" where Prime can see and coordinate across all threads
- Chat interface per project/agent
- Message history and context display

**Inter-agent messaging**
- Agents send messages to each other (true actor model)
- Messages are queued in Redis and delivered when the recipient processes
- Prime can broadcast to all agents or address specific ones
- Agents can escalate to Prime or spawn new agents
- Agents can read any file on disk but will typically focus on their own project

## Decisions Made

- **Actor model** — agents are specialized by role, not coupled to projects. Many agents per project, agents can spawn agents.
- **Prime runs continuously** — iterates on a schedule, wakes on incoming messages.
- **File access is open** — agents can read anything, but will mostly focus on their project.
- **Persistence: Redis + markdown + git** — Redis for runtime/message state, markdown files in git for durable project knowledge.
- **Multi-user** — friends, family, clients can connect and talk to agents. Data governance deferred.

## Matters Pending

- [ ] Define message schema
- [ ] Define actor lifecycle (spawn, receive, act, send, die)
- [ ] Design the actor registry / supervision tree
- [ ] Sketch UI wireframes
- [ ] Prototype backend with two actors + Prime
- [ ] Build minimal frontend

## The Court

**Initial actor types:**
- **Prime Minister** — Coordinator and strategist. Runs continuously. The sovereign's advisor.
- **Scribe** — Writes and edits code. The hands that do the crafting.
- **Scholar** — Researches, reads, gathers intelligence.
- **Chancellor** — Manages correspondence and external communications.
- **Herald** — Deploys, ships, announces to the world.

**Future roles (when needed):**
- **Auditor** — Reviews code, documents, plans for quality and correctness.
- **Steward** — Manages infrastructure, databases, environments.
- **Page** — Lightweight runner for quick, simple tasks.

**Terminology:**
- **Crown** — The user. The sovereign.
- **Court** — The collection of all active agents.
- **Thread** — A conversation or task being woven on the Loom.

## Long-Term Vision

**Voice Interface**
- Speak to the court. Issue commands, receive briefings, converse with agents by voice.
- Details TBD.

**The Realm View (Late Medieval Rimworld-style)**
- Graphical interface where agents appear as pawns moving through a medieval court
- Agents visibly working, idle, communicating — the state of the kingdom at a glance
- Late medieval aesthetic — illuminated manuscript meets colony sim
- Not a gimmick. A spatial, intuitive way to see what's happening across all projects
- Infrastructure and tools become objects in the world:
  - Redis → messenger's relay post
  - Git → the royal archives
  - Cloudflare Tunnel → the castle gate
  - Deployments → heralds riding out to distant territories
  - Failed builds → heralds returning with bad news
- Projects become holdings:
  - The Loom → the castle itself
  - Each project → a workshop, trading post, district
- The sovereign gazes upon their kingdom and sees everything

## Open Questions

- How is an actor's working directory / project association specified?
- What does Prime's continuous iteration loop look like? (poll interval, wake triggers)
- Git integration: auto-commit on state changes, or manual?
- How do users authenticate? (simple tokens, OAuth, open?)

## Ledger

**2026-01-26** — Affair opened. Name chosen: Loom (weaving threads together). Core architectural decision: agents communicate via messages to each other rather than shared context or Prime querying sessions.

**2026-01-27** — Key architectural decisions made: true actor model (agents are role-specialized, many per project, can spawn children), Prime runs continuously, file access open to all agents, persistence via Redis + markdown + git, multi-user support planned. Court roles defined (Prime Minister, Scribe, Scholar, Chancellor, Herald). Critical cost decision: use Claude Code CLI on Max plan as agent runtime rather than Anthropic API — agents are CLI subprocess invocations with session resume. Infrastructure: home machine + Cloudflare Tunnel + Upstash Redis. No Kubernetes. Scholar research completed: CLI supports `-p` mode with JSON output, `--resume` for sessions, `--allowedTools` for tool control, `--append-system-prompt` for role definition. Max plan limits shared across all usage (~50-200 prompts per 5-hour window on Max 5x). Multiple accounts or "extra usage" overflow are viable scaling paths. Agent SDK exists but requires API keys (pay-per-use), not subscription. Long-term vision added: voice interface and Realm View (late medieval Rimworld-style graphical interface where agents are pawns, infrastructure is world objects, projects are holdings).
