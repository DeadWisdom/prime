# Claude Code CLI Automation & Programmatic Use

researched: 2026-01-27
status: complete
tags: claude-code, cli, automation, agent-sdk, pipelines, sessions

## Executive Summary

Claude Code provides robust programmatic capabilities through its CLI (`-p` / `--print` mode) and the Claude Agent SDK (Python and TypeScript libraries). The CLI supports non-interactive execution with structured JSON output, session resumption, tool restrictions, custom system prompts, and piped input. The Agent SDK (formerly "Claude Code SDK") offers the same capabilities as a library, using API keys (pay-per-use) rather than subscription credits. Max plan users share a single usage pool across web and CLI with a 5-hour rolling window and weekly ceiling.

## Background

Claude Code is Anthropic's agentic coding tool. It operates in two primary modes: interactive (the default terminal experience) and non-interactive (`--print` mode for scripts and automation). The Agent SDK extracts the same agent loop, tools, and context management into importable Python and TypeScript packages for production use.

## Key Findings

### 1. CLI Flags and Modes

#### Print Mode (`-p` / `--print`)

The core flag for non-interactive use. Runs a single prompt and exits. All other CLI options work with `-p`.

```bash
claude -p "Find and fix the bug in auth.py" --allowedTools "Read,Edit,Bash"
```

Piped input is supported -- stdin becomes the prompt context:

```bash
gh pr diff "$1" | claude -p \
  --append-system-prompt "You are a security engineer. Review for vulnerabilities." \
  --output-format json
```

#### Output Formats (`--output-format`)

Only works with `--print`. Three modes:

| Format | Description |
|--------|-------------|
| `text` | Plain text (default). Human-readable. |
| `json` | Single JSON object with result, session ID, metadata, and cost info. |
| `stream-json` | Newline-delimited JSON. Real-time streaming of messages as they arrive. |

The **JSON output** includes these key fields:

- `result` -- The response content, structured as `{"content": [{"type": "text", "text": "..."}]}`
- `session_id` -- UUID for the session, usable with `--resume`
- `cost` -- Object with `total_cost_usd`, `total_duration_ms`, `total_api_duration_ms`, `total_lines_added`, `total_lines_removed`
- `structured_output` -- Present when `--json-schema` is provided; contains validated data matching the schema

Extract fields with jq:

```bash
# Get text result
claude -p "Summarize this project" --output-format json | jq -r '.result'

# Get structured output
claude -p "Extract function names from auth.py" \
  --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array","items":{"type":"string"}}},"required":["functions"]}' \
  | jq '.structured_output'
```

#### Session Resume (`--resume` / `--continue`)

- `--continue` (`-c`): Continues the most recent conversation in the current directory.
- `--resume <session_id>` (`-r`): Resumes a specific session by UUID.
- `--resume` (no argument): Opens an interactive picker of recent sessions.
- `--fork-session`: When used with `--resume` or `--continue`, creates a new session ID branching from the original.

Multi-step workflow pattern:

```bash
session_id=$(claude -p "Start a review" --output-format json | jq -r '.session_id')
claude -p "Continue that review" --resume "$session_id"
claude -p "Generate a summary of all issues found" --resume "$session_id"
```

#### System Prompt Flags

- `--system-prompt <prompt>`: Fully replaces the default system prompt (removes all Claude Code built-in instructions).
- `--append-system-prompt <prompt>`: Adds to the default prompt while preserving built-in behavior. **Recommended for most use cases.**
- These flags can be combined with `--resume`, though behavior on resume may vary. Using `--append-system-prompt` with `--resume` is the safer choice.
- `--system-prompt` and `--system-prompt-file` are mutually exclusive. The append variants can be combined with either replacement variant.

#### Tool Restrictions (`--allowedTools` / `--disallowedTools`)

Uses permission rule syntax with prefix matching:

```bash
# Allow specific tools
claude -p "Fix the tests" --allowedTools "Bash,Read,Edit"

# Allow specific command patterns (note: space before * is important)
claude -p "Create a commit" \
  --allowedTools "Bash(git diff *),Bash(git log *),Bash(git status *),Bash(git commit *)"

# Use --tools to specify the exact set of available built-in tools
claude -p "Analyze code" --tools "Read,Glob,Grep"

# Use "" to disable all tools
claude -p "Just answer a question" --tools ""
```

The trailing ` *` enables prefix matching. `Bash(git diff *)` matches any command starting with `git diff `. Without the space, `Bash(git diff*)` would also match `git diff-index`.

#### Model Selection (`--model`)

```bash
claude -p "Quick question" --model sonnet
claude -p "Complex task" --model opus
claude -p "Specific version" --model claude-sonnet-4-5-20250929
```

Aliases like `sonnet` and `opus` resolve to the latest version of that model.

#### Working Directory (`--add-dir`)

- `--add-dir <directories...>`: Adds additional directories the agent can access.
- Claude Code uses the current working directory by default; change it by running from the desired directory.
- There is no `--cwd` flag; use `cd /path && claude -p "..."` or set the cwd in your subprocess spawn.

#### Other Notable Flags

| Flag | Purpose |
|------|---------|
| `--max-budget-usd <amount>` | Cap API spending per invocation (print mode only) |
| `--no-session-persistence` | Don't save session to disk (print mode only) |
| `--session-id <uuid>` | Use a specific UUID for the session |
| `--mcp-config <configs...>` | Load MCP server configurations |
| `--strict-mcp-config` | Only use MCP servers from `--mcp-config`, ignoring others |
| `--permission-mode <mode>` | Choices: `default`, `acceptEdits`, `bypassPermissions`, `plan`, `delegate`, `dontAsk` |
| `--dangerously-skip-permissions` | Bypass all permission checks (sandboxes only) |
| `--json-schema <schema>` | JSON Schema for structured output validation |
| `--fallback-model <model>` | Auto-fallback when default model is overloaded (print mode only) |
| `--input-format stream-json` | Real-time streaming input (print mode only) |
| `--include-partial-messages` | Include partial chunks (with `stream-json` output) |
| `--settings <file-or-json>` | Load additional settings from file or JSON string |
| `--agents <json>` | Define custom agents inline as JSON |

### 2. Session Management

#### Storage Location

Sessions are stored under `~/.claude/`:

```
~/.claude/
  history.jsonl              # Session metadata index
  projects/                  # Conversation transcripts, organized by path
    -home-user-project-a/
      session-id-1.jsonl
      session-id-2.jsonl
  session-env/               # Session environment data
  todos/                     # Todo lists per session
```

A SQLite database in `~/.claude` also stores session data.

#### Session ID Generation

Each session gets a UUID. It can be captured from JSON output (`session_id` field) or specified explicitly with `--session-id <uuid>`.

#### Path-Based Organization

Sessions are organized by the working directory path. Moving projects or changing usernames makes old sessions invisible (the path-based key changes).

#### Session Cleanup

Sessions older than a configurable period are automatically removed. Controlled by `settings.cleanupPeriodDays`.

#### Programmatic Resume

Sessions can be resumed programmatically by capturing `session_id` from JSON output and passing it to `--resume`. The Agent SDK provides equivalent functionality through its `resume` option.

### 3. Rate Limits (Max Plan)

#### Shared Usage Pool

All Claude usage (web chat, Claude Code CLI, API via subscription) draws from a single shared pool. There is no separate allocation for CLI vs. web.

#### 5-Hour Rolling Window

| Plan | Approximate Messages | Approximate Code Prompts |
|------|---------------------|-------------------------|
| Pro ($20/mo) | ~45/5hr | ~10-40/5hr |
| Max 5x ($100/mo) | ~225/5hr | ~50-200/5hr |
| Max 20x ($200/mo) | ~900/5hr | ~200-800/5hr |

Exact numbers vary based on message length, conversation length, codebase size, model choice, and auto-accept settings.

#### Weekly Ceiling

A 7-day weekly limit caps total active compute hours alongside the 5-hour windows. Pro users get roughly 40-80 Claude Code hours per week; Max tiers scale proportionally.

#### Concurrent Instances

Multiple Claude Code instances **can** run concurrently. They all draw from the same shared usage pool, so parallel use burns through limits faster. There is no hard cap on instance count, but heavy parallel usage with Opus on large codebases will exhaust limits quickly.

#### When Limits Are Hit

Usage limits result in throttling or temporary inability to send messages. Max subscribers can enable "extra usage" which bills at standard API rates beyond the included allocation.

#### Multiple Accounts

The documentation does not explicitly address running multiple Max accounts on one machine, but authentication is per-login session. In principle, different terminal sessions could authenticate differently.

#### Recent Concerns (January 2026)

Users have reported what feels like a ~60% reduction in effective limits. Anthropic attributes this to a holiday usage bonus expiring and normal limits resuming.

### 4. Claude Agent SDK

#### What It Is

The Agent SDK (formerly "Claude Code SDK") packages the same agent loop, tools, and context management that power Claude Code into importable libraries. Available for Python (`claude-agent-sdk` on PyPI) and TypeScript (`@anthropic-ai/claude-agent-sdk` on npm).

#### Authentication: API Keys (Pay-Per-Use)

The Agent SDK uses **API keys**, not subscription credits. You set `ANTHROPIC_API_KEY` or configure third-party providers (AWS Bedrock, Google Vertex AI, Microsoft Foundry). This is pay-per-use at standard API rates.

Anthropic explicitly states: "Unless previously approved, we do not allow third party developers to offer Claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK."

#### Key Capabilities

- **Built-in tools**: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, AskUserQuestion
- **Hooks**: PreToolUse, PostToolUse, Stop, SessionStart, SessionEnd, UserPromptSubmit -- run custom code at lifecycle points
- **Subagents**: Spawn specialized agents for subtasks via the Task tool
- **MCP integration**: Connect external tools via Model Context Protocol
- **Permissions**: Fine-grained tool control, permission modes
- **Sessions**: Resume and fork sessions programmatically
- **Structured output**: JSON Schema validation on agent output
- **File checkpointing**: Automatic backups before modifications, with restore capability
- **Plugins**: Load custom commands, agents, skills, hooks, and MCP servers

#### Python API

Two interfaces:
- `query()` -- Simple text generation (no tool support)
- `ClaudeSDKClient` -- Full agentic API with session resume, tools, manual control

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find and fix the bug in auth.py",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"])
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

#### TypeScript API

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Find and fix the bug in auth.py",
  options: { allowedTools: ["Read", "Edit", "Bash"] }
})) {
  if ("result" in message) console.log(message.result);
}
```

#### CLI vs. Agent SDK

| Use Case | Best Choice |
|----------|-------------|
| Interactive development | CLI |
| One-off scripted tasks | CLI (`-p`) |
| CI/CD pipelines | Either (SDK preferred) |
| Custom applications | SDK |
| Production automation | SDK |
| Subscription-based usage | CLI |
| Pay-per-use / API billing | SDK |

The SDK requires Claude Code to be installed as its runtime.

### 5. Subprocess Automation Patterns

#### Basic Subprocess Invocation

```bash
# Simple invocation
result=$(claude -p "What does auth.py do?" --output-format json)

# With tool restrictions for safety
claude -p "Review this PR" \
  --allowedTools "Read,Glob,Grep" \
  --output-format json \
  --no-session-persistence

# Budget cap for cost control
claude -p "Refactor utils.py" \
  --max-budget-usd 0.50 \
  --allowedTools "Read,Edit,Bash" \
  --output-format json
```

#### Multi-Step Pipeline

```bash
#!/bin/bash
# Step 1: Analyze
session_id=$(claude -p "Analyze the codebase for security issues" \
  --output-format json \
  --allowedTools "Read,Glob,Grep" | jq -r '.session_id')

# Step 2: Fix (resuming context)
claude -p "Fix the most critical issue you found" \
  --resume "$session_id" \
  --allowedTools "Read,Edit,Bash" \
  --output-format json

# Step 3: Verify
claude -p "Run the tests to verify the fix" \
  --resume "$session_id" \
  --allowedTools "Bash(npm test *),Bash(pytest *),Read" \
  --output-format json
```

#### Gotchas and Considerations

1. **Working directory**: Claude Code inherits the cwd of the calling process. No `--cwd` flag exists; set it via `cd` or subprocess cwd option.
2. **Permission prompts**: In `-p` mode, if a tool isn't in `--allowedTools`, Claude may skip it or the invocation may hang waiting for input. Use `--dangerously-skip-permissions` only in sandboxed environments, or be explicit with `--allowedTools`.
3. **Session persistence**: By default, sessions are saved to disk even in `-p` mode. Use `--no-session-persistence` if you don't need resume capability and want to avoid disk accumulation.
4. **Exit codes**: Check exit codes in scripts. Non-zero may indicate errors or permission issues.
5. **Concurrent runs**: Multiple instances can run simultaneously but share the usage pool. No locking or coordination is built in.
6. **Large outputs**: Stream-json is preferable for long-running tasks to avoid buffering the entire response.
7. **Model overload**: Use `--fallback-model` to automatically switch models when the primary is overloaded.
8. **Stdin input**: Piped stdin is treated as context appended to the prompt. Works naturally with shell pipes.

## Practical Implications

**For scripted automation (CI/CD, bots, cron jobs):**
- Use `claude -p` with `--output-format json` and `--allowedTools` for predictable, parseable output.
- Use `--no-session-persistence` to avoid disk buildup.
- Use `--max-budget-usd` to prevent runaway costs (API key users).
- Capture `session_id` from JSON output for multi-step workflows.

**For production applications:**
- The Agent SDK (Python/TypeScript) is the intended path. It provides hooks, subagents, structured output, and programmatic session management.
- The SDK uses API keys (pay-per-use), not subscription credits. Budget accordingly.
- Claude Code must be installed as the SDK's runtime.

**For Max plan subscribers running automation:**
- All CLI usage counts against your shared subscription pool.
- Concurrent instances are possible but drain limits faster.
- The 5-hour rolling window and weekly ceiling both apply.
- Consider enabling "extra usage" (billed at API rates) if limits are a concern.
- Model choice matters: Opus consumes limits faster than Sonnet.

## Sources & Further Reading

- [Run Claude Code Programmatically (Official Docs)](https://code.claude.com/docs/en/headless) -- Primary reference for CLI automation
- [Agent SDK Overview (Official Docs)](https://platform.claude.com/docs/en/agent-sdk/overview) -- SDK capabilities, setup, comparison
- [Claude Agent SDK - Python (GitHub)](https://github.com/anthropics/claude-agent-sdk-python)
- [Claude Agent SDK - TypeScript (GitHub)](https://github.com/anthropics/claude-agent-sdk-typescript)
- [About Claude's Max Plan Usage (Help Center)](https://support.claude.com/en/articles/11014257-about-claude-s-max-plan-usage)
- [Using Claude Code with Pro/Max Plan (Help Center)](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)
- [Claude Code Limits (ClaudeLog)](https://claudelog.com/claude-code-limits/)
- [Session Management (Agent SDK Docs)](https://platform.claude.com/docs/en/agent-sdk/sessions)
- [Claude Code Internals: Session State Management (Medium)](https://kotrotsos.medium.com/claude-code-internals-part-6-session-state-management-e729f49c8bb9)

## Open Questions

1. **Exact JSON output schema**: The precise field names and nesting in `--output-format json` output are not fully documented in a formal schema. Testing with `jq` is recommended to confirm field paths.
2. **`--system-prompt` + `--resume` interaction**: Whether a custom system prompt overrides or appends when resuming is not explicitly documented. Empirical testing is advised.
3. **Session storage limits**: Whether there is a maximum number of sessions stored or a default cleanup period is not clearly documented.
4. **Concurrent instance coordination**: No built-in mechanism exists for coordinating multiple CLI instances working on the same codebase. File conflicts are possible.
5. **Max plan limit trajectory**: January 2026 reports of reduced limits suggest the effective allowance may continue to shift. Monitor Anthropic announcements.
6. **SDK subscription auth**: Anthropic explicitly disallows third-party use of Claude.ai login for SDK-built products. Whether Anthropic will offer a subscription-based SDK tier is unknown.
