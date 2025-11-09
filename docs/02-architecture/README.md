# Architecture Documentation

**Core architecture and design patterns for PulsePlan.**

## Documents in this Directory

### [`ARCHITECTURE.md`](./ARCHITECTURE.md) ⭐
**Living document** - Detailed architecture patterns and system design.

**Contents:**
- Repository organization and patterns
- Service layer architecture
- Agent system architecture
- Database patterns and best practices
- Migration history
- Common patterns checklist

**When to read:** Understanding system design, making architectural decisions

---

### [`RULES.md`](./RULES.md) 📋
**Enforcement rules** - Non-negotiable coding standards and architectural invariants.

**Contents:**
- Project structure rules
- Coding standards (type hints, async/await, error handling)
- Quality gates (ruff, black, mypy, pytest)
- Required change workflow
- Domain-specific rules (scheduler, agents, integrations)
- Module organization decision table
- Prohibited patterns

**When to read:** Before making any code changes, during code review

---

### [`INTERFACES.md`](./INTERFACES.md) 🔌
**Data contracts** - API specifications and type definitions.

**Contents:**
- Core data types (`UserContext`, `IntentRequest`, `WorkflowState`)
- Scheduling interfaces (`SchedulingRequest`, `SchedulingResponse`)
- Repository interfaces (`BaseRepository` with CRUD methods)
- API request/response contracts
- Database schemas
- External API expectations
- Type definitions and validation rules

**When to read:** Implementing new features, integrating systems, preventing type mismatches

---

## Quick Start

1. **New to the codebase?** Start with [`ARCHITECTURE.md`](./ARCHITECTURE.md)
2. **Making changes?** Check [`RULES.md`](./RULES.md) first
3. **Implementing integrations?** Review [`INTERFACES.md`](./INTERFACES.md)

---

**Last Updated:** 11/05/25
