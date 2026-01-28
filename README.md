# Prime

A simple, LLM-powered project management system. Your projects are affairs of state; Claude serves as Prime Minister, briefing you on matters requiring your attention.

## Philosophy

- **Portable**: It's just markdown files in a git repo
- **Human-readable**: grep, cat, vim — everything works
- **LLM-augmented**: Intelligence when you need it, not when you don't
- **Minimal**: No databases, no web apps, no dependencies beyond Python and the Anthropic SDK

*"I serve at Your Majesty's pleasure."*

## Structure

```
prime/
├── affairs/              # Your projects (affairs of state)
│   ├── taxes.md          # Simple affair — single file
│   ├── loom/             # Complex affair — directory
│   │   ├── affair.md     #   The affair itself
│   │   ├── design.md     #   Supporting documents
│   │   └── ...
│   └── ...
├── memory/               # Standing knowledge (preferences, context, reference)
│   ├── preferences.md
│   ├── tech-stack.md
│   └── ...
├── inbox.md              # Quick capture for loose thoughts and tasks
├── scripts/              # Scripts for integration or to perform various tasks
├── CLAUDE.md             # Instructions for your Prime Minister
└── .env                  # ANTHROPIC_API_KEY
```

## Project Format

Each affair is either a single markdown file or a directory. Simple affairs are one file; complex affairs that accumulate supporting documents (design specs, iteration plans, etc.) are promoted to a directory with `affair.md` as the main file.

Either way, the affair file follows these light conventions:

```markdown
# Project Name

status: active | paused | complete | abandoned
priority: critical | high | normal | low
domain: work | personal | creative

## Brief

One paragraph on what this is and why it matters.

## Matters Pending

- [ ] Task one
- [ ] Task two
- [x] Completed task

## Ledger

Notes, decisions, links, whatever you need to remember.
```

## Memory Format

Memory files in `memory/` are freeform markdown — no required structure. Use them for any standing knowledge:

- `preferences.md` — How you like things done
- `tech-stack.md` — Your tools and technologies  
- `contacts.md` — People and relationships
- `decisions.md` — Past decisions worth remembering

The PM reads these before every briefing.

## Usage

Run Claude Code from the project directory:

```bash
claude
```

Then simply converse with your Prime Minister:

- **"Give me a briefing"** — Get a summary of all active affairs
- **"Add X to the inbox"** — Quick capture without deciding where it belongs
- **"Process the inbox"** — Triage captured items into affairs
- **"Create a new affair for X"** — Start a new project
- **"What's the status of X?"** — Check on a specific affair

The PM reads `CLAUDE.md` for instructions and `memory/` for standing context before each session.

## Dependencies

This project uses [uv](https://github.com/astral-sh/uv) for package management.
