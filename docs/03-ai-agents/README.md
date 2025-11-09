# AI Agents Documentation

**Documentation specifically for AI development assistants (Claude Code, GitHub Copilot, etc.)**

## Documents in this Directory

### [`CLAUDE.md`](./CLAUDE.md) 🤖
**AI assistant instructions** - Primary instructions for Claude Code.

**Contents:**
- Architecture overview
- Development commands (backend, frontend, testing)
- Key architectural components
- Environment configuration
- Code conventions and quality gates
- Agent workflow execution
- Required change workflow
- Module organization decision table

**Who uses this:** Claude Code AI assistant (primary consumer)

---

### [`CONTEXT.md`](./CONTEXT.md) 🗺️
**Context routing guide** - Maps tasks to required documentation.

**Contents:**
- Task type mappings (Intent Classification, Scheduling, API, Repository, etc.)
- Context loading strategy by change size
- Document interdependencies
- Prompt templates for Claude

**Who uses this:** AI assistants for determining which docs to load

---

## Usage for AI Assistants

### When starting a new task:
1. Read [`CONTEXT.md`](./CONTEXT.md) to determine which docs are relevant
2. Follow the context loading strategy
3. Reference [`CLAUDE.md`](./CLAUDE.md) for workflow and conventions

### Example Context Loading:

**Task: "Add new scheduling constraint"**
```
CONTEXT.md says:
→ Required Reading:
  - 02-architecture/ARCHITECTURE.md (Scheduling patterns)
  - 02-architecture/RULES.md (Where to add code)
  - 02-architecture/INTERFACES.md (SchedulingRequest interface)
  - 04-development/EXAMPLES.md (Scheduling pattern)
  - 05-systems/scheduling/ (System docs)
```

---

**Last Updated:** 11/05/25
