# Systems Documentation

**Technical documentation for specific subsystems within PulsePlan.**

## Subsystems

### [agents/](./agents/) 🤖
**LangGraph Agent System**
- [`LANGGRAPH_AGENT_WORKFLOWS.md`](./agents/LANGGRAPH_AGENT_WORKFLOWS.md) - Multi-agent workflow architecture
- [`CONVERSATION_CONTINUATION_SYSTEM.md`](./agents/CONVERSATION_CONTINUATION_SYSTEM.md) - Multi-turn conversation management
- [`ACCEPTANCE_GATE.md`](./agents/ACCEPTANCE_GATE.md) - Quality gates for agent workflows

**When to read:** Working with LangGraph agents, implementing new workflows, debugging agent issues

---

### [scheduling/](./scheduling/) 📅
**Scheduling Engine and Optimization**
- [`SCHEDULER_SYSTEM_DOCUMENTATION.md`](./scheduling/SCHEDULER_SYSTEM_DOCUMENTATION.md) - Core scheduling system
- [`SMART_SCHEDULING_ARCHITECTURE.md`](./scheduling/SMART_SCHEDULING_ARCHITECTURE.md) - ML-based scheduling
- [`WEEK_SCHEDULING_SYSTEM.md`](./scheduling/WEEK_SCHEDULING_SYSTEM.md) - Week-level scheduling
- [`TIMEBLOCKS_ARCHITECTURE.md`](./scheduling/TIMEBLOCKS_ARCHITECTURE.md) - Timeblock management

**When to read:** Working on scheduling features, understanding OR-Tools constraints, optimizing schedules

---

### [integrations/](./integrations/) 🔌
**External Service Integrations**
- [`CALENDAR_SYSTEM.md`](./integrations/CALENDAR_SYSTEM.md) - Google/Microsoft Calendar integration
- [`CANVAS_INTEGRATION.md`](./integrations/CANVAS_INTEGRATION.md) - Canvas LMS integration
- [`REAL_TIME_SYNC_SYSTEM.md`](./integrations/REAL_TIME_SYNC_SYSTEM.md) - Real-time sync architecture
- [`EMAIL_SECURITY_IMPLEMENTATION.md`](./integrations/EMAIL_SECURITY_IMPLEMENTATION.md) - Email security

**When to read:** Adding new integrations, debugging sync issues, understanding OAuth flows

---

### [infrastructure/](./infrastructure/) ⚙️
**Core Infrastructure Components**
- [`MEMORY_SYSTEM_DOCUMENTATION.md`](./infrastructure/MEMORY_SYSTEM_DOCUMENTATION.md) - Dual-layer memory (PostgreSQL + Redis)
- [`WEBSOCKET_IMPLEMENTATION.md`](./infrastructure/WEBSOCKET_IMPLEMENTATION.md) - Real-time WebSocket system
- [`KMS_SETUP_GUIDE.md`](./infrastructure/KMS_SETUP_GUIDE.md) - Key management setup

**When to read:** Working with memory/caching, WebSocket features, encryption/security

---

### [observability/](./observability/) 📊
**Analytics and Tracking**
- [`POSTHOG_ANALYTICS.md`](./observability/POSTHOG_ANALYTICS.md) - PostHog analytics integration
- [`USAGE_TRACKING_INTEGRATION_EXAMPLE.md`](./observability/USAGE_TRACKING_INTEGRATION_EXAMPLE.md) - Usage tracking patterns
- [`FOCUS_SESSION_TRACKING.md`](./observability/FOCUS_SESSION_TRACKING.md) - Focus session analytics

**When to read:** Adding analytics events, understanding user tracking, debugging metrics

---

## Navigation Tips

### "I'm working on feature X, which system docs should I read?"

**Calendar features** → [integrations/CALENDAR_SYSTEM.md](./integrations/CALENDAR_SYSTEM.md)

**Task scheduling** → [scheduling/](./scheduling/) (all docs)

**Chat/AI interactions** → [agents/](./agents/) (all docs)

**Canvas sync** → [integrations/CANVAS_INTEGRATION.md](./integrations/CANVAS_INTEGRATION.md)

**Caching/memory** → [infrastructure/MEMORY_SYSTEM_DOCUMENTATION.md](./infrastructure/MEMORY_SYSTEM_DOCUMENTATION.md)

**Real-time updates** → [infrastructure/WEBSOCKET_IMPLEMENTATION.md](./infrastructure/WEBSOCKET_IMPLEMENTATION.md)

**Analytics** → [observability/](./observability/) (all docs)

---

**Last Updated:** 11/05/25
