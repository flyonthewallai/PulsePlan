# PulsePlan Documentation

**Welcome to the PulsePlan documentation system.** This is your central hub for all architectural, development, and system documentation.

## 📚 Documentation Structure

### [01-getting-started/](./01-getting-started/) 🚀

Quick start guides and initial setup instructions.

- Setup guide
- Development workflow
- Environment configuration

### [02-architecture/](./02-architecture/) ⭐

**Core architecture and design patterns** - START HERE for understanding the system.

- [`ARCHITECTURE.md`](./02-architecture/ARCHITECTURE.md) - Living document with detailed architecture patterns
- [`RULES.md`](./02-architecture/RULES.md) - Enforcement rules and coding standards
- [`INTERFACES.md`](./02-architecture/INTERFACES.md) - Data contracts and API specifications

### [03-ai-agents/](./03-ai-agents/) 🤖

**AI assistant and LLM-specific documentation** - For Claude and other AI development assistants.

- [`CLAUDE.md`](./03-ai-agents/CLAUDE.md) - Instructions for Claude Code AI assistant
- [`CONTEXT.md`](./03-ai-agents/CONTEXT.md) - Context routing guide for AI agents

### [04-development/](./04-development/) 🛠️

**Developer guides and best practices** - Essential for daily development work.

- [`WEB_RULES.md`](./04-development/WEB_RULES.md) ⭐ **Frontend enforcement rules** - **REQUIRED for all web changes**
- [`SERVICE_LAYER_PATTERNS.md`](./04-development/SERVICE_LAYER_PATTERNS.md) - Backend service patterns
- [`TESTING.md`](./04-development/TESTING.md) - Test strategy and coverage requirements
- [`EXAMPLES.md`](./04-development/EXAMPLES.md) - Reference implementation patterns
- [`PITFALLS.md`](./04-development/PITFALLS.md) - Common mistakes and known issues
- [`STYLES.md`](./04-development/STYLES.md) - Frontend design system and styling guide

### [05-systems/](./05-systems/) ⚙️

**Technical system documentation** - Deep dives into specific subsystems.

#### [agents/](./05-systems/agents/)

LangGraph agent system and workflows

- LangGraph agent workflows
- Conversation continuation system
- Acceptance gates

#### [scheduling/](./05-systems/scheduling/)

Scheduling engine and optimization

- Scheduler system documentation
- Smart scheduling architecture
- Week scheduling system
- Timeblocks architecture

#### [integrations/](./05-systems/integrations/)

External service integrations

- Calendar system (Google, Microsoft)
- Canvas LMS integration
- Real-time sync system
- Email security implementation

#### [infrastructure/](./05-systems/infrastructure/)

Core infrastructure components

- Memory system documentation
- WebSocket implementation
- KMS setup guide

#### [observability/](./05-systems/observability/)

Analytics and tracking

- PostHog analytics
- Usage tracking integration
- Focus session tracking

### [06-security/](./06-security/) 🔒

**Security documentation and guidelines**

- Security best practices
- Gmail OAuth security status

### [07-mobile/](./07-mobile/) 📱

**Mobile-specific documentation**

- iOS notification system

### [08-plans/](./08-plans/) 📋

**Implementation plans and design documents** - Future features and architectural designs.

- Agent implementation plan
- Conversational scheduling confirmation system
- Memory system plan
- Workflow plan

### [99-archive/](./99-archive/) 📦

**Historical documentation and analysis** - Archived for reference, not actively maintained.

---

## 🎯 Quick Navigation by Task

### "I want to understand the system architecture"

1. Read [02-architecture/ARCHITECTURE.md](./02-architecture/ARCHITECTURE.md)
2. Review [02-architecture/RULES.md](./02-architecture/RULES.md)
3. Check [02-architecture/INTERFACES.md](./02-architecture/INTERFACES.md)

### "I'm setting up my development environment"

1. Follow [01-getting-started/](./01-getting-started/)
2. Review [04-development/TESTING.md](./04-development/TESTING.md)

### "I'm working with the AI agent system"

1. Read [05-systems/agents/LANGGRAPH_AGENT_WORKFLOWS.md](./05-systems/agents/LANGGRAPH_AGENT_WORKFLOWS.md)
2. Check [03-ai-agents/CLAUDE.md](./03-ai-agents/CLAUDE.md) for AI assistant instructions

### "I'm working on the scheduling engine"

1. Read [05-systems/scheduling/SCHEDULER_SYSTEM_DOCUMENTATION.md](./05-systems/scheduling/SCHEDULER_SYSTEM_DOCUMENTATION.md)
2. Review [05-systems/scheduling/SMART_SCHEDULING_ARCHITECTURE.md](./05-systems/scheduling/SMART_SCHEDULING_ARCHITECTURE.md)

### "I'm adding a new integration"

1. Check [05-systems/integrations/](./05-systems/integrations/) for existing patterns
2. Review [04-development/EXAMPLES.md](./04-development/EXAMPLES.md) for code patterns
3. Follow [02-architecture/RULES.md](./02-architecture/RULES.md) for placement rules

### "I'm working on the web frontend"

1. **Read [04-development/WEB_RULES.md](./04-development/WEB_RULES.md)** - **REQUIRED for all web changes**
2. Review [04-development/STYLES.md](./04-development/STYLES.md) for design tokens
3. Check [02-architecture/INTERFACES.md](./02-architecture/INTERFACES.md) for API contracts
4. Follow [04-development/TESTING.md](./04-development/TESTING.md) for test requirements

### "I'm working on backend services"

1. Read [04-development/SERVICE_LAYER_PATTERNS.md](./04-development/SERVICE_LAYER_PATTERNS.md)
2. Follow [02-architecture/RULES.md](./02-architecture/RULES.md) for layering rules
3. Review [04-development/EXAMPLES.md](./04-development/EXAMPLES.md) for patterns

### "I'm using Claude or another AI assistant"

1. Start with [03-ai-agents/CONTEXT.md](./03-ai-agents/CONTEXT.md) for context routing
2. Review [03-ai-agents/CLAUDE.md](./03-ai-agents/CLAUDE.md) for AI-specific instructions
3. Reference [02-architecture/](./02-architecture/) for architectural patterns

---

## 📖 Documentation Maintenance

### Document Types

**Living Documents** (frequently updated):

- `02-architecture/ARCHITECTURE.md` - Update when architectural patterns change
- `02-architecture/RULES.md` - Update when adding new backend rules or invariants
- `04-development/WEB_RULES.md` - Update when adding new frontend rules or patterns
- `04-development/PITFALLS.md` - Add new issues as discovered
- `04-development/EXAMPLES.md` - Add new patterns as established

**Reference Documents** (stable):

- `02-architecture/INTERFACES.md` - Update when data contracts change
- `04-development/TESTING.md` - Update when test strategy changes
- `04-development/SERVICE_LAYER_PATTERNS.md` - Update when service patterns change
- `04-development/STYLES.md` - Update when design tokens change
- System docs in `05-systems/` - Update when systems are modified

**AI-Specific Documents**:

- `03-ai-agents/CLAUDE.md` - Update when changing AI assistant workflow
- `03-ai-agents/CONTEXT.md` - Update when adding new documentation categories

### When to Update Documentation

✅ **Always update when:**

- Adding new architectural patterns → Update `ARCHITECTURE.md`
- Adding backend enforcement rules → Update `RULES.md`
- Adding frontend enforcement rules → Update `WEB_RULES.md`
- Discovering bugs or pitfalls → Update `PITFALLS.md`
- Changing data contracts → Update `INTERFACES.md`
- Adding new systems → Create new doc in appropriate `05-systems/` subdirectory
- Changing design tokens → Update `STYLES.md`
- Changing AI workflow → Update `CLAUDE.md` and `CONTEXT.md`

---

## 🔗 External Documentation

- **Backend API**: See `backend/app/api/` for OpenAPI specs
- **Frontend Components**: See `web/src/components/` for component documentation
- **Database Schema**: See `backend/app/database/schemas/` for SQL schemas

---

**Last Updated:** 11/06/25
**Maintained By:** Development Team
