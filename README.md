<div align="center">
  <img src="https://www.pulseplan.app/assets/logo.png" alt="PulsePlan Logo" width="90px" />
  <h1>PulsePlan – AI-Powered Scheduling Agent</h1>
</div>

PulsePlan is an intelligent academic planning assistant powered by LangGraph agents that integrates with Canvas, Google Calendar, Microsoft Outlook, and other academic platforms. Built for students, it provides conversational AI assistance, automated scheduling, and comprehensive productivity analytics through a sophisticated multi-agent system.

> Your personal AI scheduling agent.

---

## ✨ Key Features

### 🤖 **Advanced AI Agent System**

- **Multi-Agent Architecture** – Specialized LangGraph agents for different workflows (chat, scheduling, email, briefings)
- **Natural Language Understanding** – Custom-trained intent classification model with 95%+ accuracy
- **Conversational AI** – Context-aware dialogue with clarification, slot-filling, and multi-turn planning
- **Intent Processing** – Sophisticated NLU pipeline with entity extraction and ambiguity resolution
- **Tool Ecosystem** – 20+ specialized tools for comprehensive productivity management
- **Action Executors** – Domain-specific action handlers for calendar, tasks, emails, search, and more

### 📚 **Academic Integration**

- **Canvas LMS Sync** – Automated assignment, course, and grade synchronization
- **Calendar Intelligence** – Google Calendar and Microsoft Outlook bidirectional sync
- **Smart Scheduling** – AI-powered time-blocking with conflict resolution
- **Assignment Analytics** – Deadline tracking and priority management

### 💡 **Intelligent Features**

- **Memory System** – Dual-layer semantic memory (pgvector + Redis) for personalized assistance
- **Daily Briefings** – AI-generated morning briefings with agenda, priorities, and insights
- **Weekly Pulse** – Comprehensive productivity analytics and performance tracking
- **Focus Sessions** – Pomodoro timer with entity matching and productivity tracking
- **Slash Commands** – Quick actions with natural language command parsing
- **Smart Scheduling** – Context-aware time suggestions with conflict resolution
- **Timeblocks** – Visual schedule representation merging tasks and calendar events

### 🔧 **Advanced Capabilities**

- **Real-Time Updates** – WebSocket connections for live calendar, task, and notification updates
- **Multi-Platform** – Web app (React), mobile app (React Native), and REST API
- **Repository Pattern** – Clean data layer with domain-specific repositories
- **Background Workers** – Automated Canvas sync, calendar sync, briefings, and notifications
- **Usage Tracking** – Token usage monitoring with configurable limits and quotas
- **Admin Tools** – NLU monitoring dashboard and system health metrics
- **Subscription Management** – RevenueCat integration for premium features
- **Multi-Provider Email** – Unified email interface supporting Gmail and Outlook
- **Caching Strategy** – Multi-layer Redis caching with intelligent invalidation
- **Security First** – Encrypted token storage, OAuth flows, and comprehensive auth system

---

## 🏗️ LangGraph Agent Architecture

### **Multi-Agent System**

PulsePlan uses LangGraph to orchestrate specialized agents for different workflows:

```python
# Core Agent Graphs
├── ChatGraph          # Conversational AI interactions
├── TaskGraph          # Task management and CRUD operations
├── SchedulingGraph     # Intelligent scheduling and optimization
├── CalendarGraph       # Calendar integration and sync
└── BriefingGraph       # Data aggregation and insights
```

### **Agent Tools Ecosystem**

**📋 Task Management**

- `TaskCRUDTool` – Create, read, update, delete tasks
- `TaskSchedulingTool` – Intelligent task scheduling with AI optimization

**📅 Calendar Integration**

- `GoogleCalendarTool` – Google Calendar operations and sync
- `MicrosoftCalendarTool` – Outlook calendar integration

**📧 Communication**

- `EmailManagerTool` – Smart email routing and management
- `GmailUserTool` / `OutlookUserTool` – Provider-specific email handling
- `SystemEmailTool` – Automated system notifications

**🎓 Academic Integration**

- `CanvasLMSTool` – Manual Canvas sync requests
- `WeeklyPulseTool` – Productivity analytics and insights generation

**🧠 Memory & Intelligence**

- `MemoryTool` – Semantic memory search and storage
- `PreferencesTool` – User constraints and preference management
- `ContactsManagerTool` – Google Contacts integration

**🔍 Information & Research**

- `WebSearchTool` – Tavily API-powered web search
- `NewsSearchTool` / `ResearchTool` – Specialized information retrieval
- `DataAggregatorTool` / `ContentSynthesizerTool` – Content processing

### **Intelligent Orchestration**

```python
# Agent execution flow
User Query → Agent Router → Specialized Graph → Tool Execution → Response Synthesis
```

- **Dynamic Tool Selection** – Agents choose appropriate tools based on context
- **Cross-Agent Communication** – Graphs can delegate to other specialized agents
- **State Management** – Persistent conversation state and user context
- **Error Recovery** – Graceful handling of API failures and edge cases

---

## 🗺️ Project Structure

```
PulsePlan/
├── backend/                           # Python FastAPI backend with LangGraph agents
│   ├── app/
│   │   ├── agents/                   # LangGraph multi-agent system
│   │   │   ├── core/                 # Core orchestration layer
│   │   │   │   ├── orchestration/   # Intent processing, driver, gates, continuation
│   │   │   │   ├── services/        # LLM service, user context, action routing
│   │   │   │   ├── conversation/    # Conversation state management
│   │   │   │   └── state/           # Workflow state containers
│   │   │   ├── graphs/              # Workflow implementations
│   │   │   │   ├── briefing_graph.py    # Daily briefing generation
│   │   │   │   ├── calendar_graph.py    # Calendar operations
│   │   │   │   ├── email_graph.py       # Email management
│   │   │   │   ├── event_graph.py       # Event CRUD operations
│   │   │   │   ├── scheduling_graph.py  # Intelligent scheduling
│   │   │   │   ├── search_graph.py      # Web search & research
│   │   │   │   └── task_graph.py        # Task management
│   │   │   ├── nlu/                 # Natural language understanding
│   │   │   │   ├── classifier_contrastive.py  # Intent classification model
│   │   │   │   ├── extractors/      # Entity extraction (date, time, duration, etc.)
│   │   │   │   └── param_extractor.py   # Parameter extraction
│   │   │   ├── services/            # Agent services layer
│   │   │   │   ├── action_executor.py       # Action execution coordinator
│   │   │   │   ├── action_executors/        # Domain-specific action handlers
│   │   │   │   ├── planning/                # Multi-step planning & execution
│   │   │   │   ├── conversational_responses.py  # Response generation
│   │   │   │   ├── llm_clarification.py     # Ambiguity resolution
│   │   │   │   └── nlu_service.py           # NLU integration service
│   │   │   ├── tools/               # Agent tools ecosystem
│   │   │   │   ├── communication/   # Briefings, notifications, email
│   │   │   │   ├── data/            # Tasks, todos, events, memory
│   │   │   │   ├── integrations/    # Calendar, Canvas, email providers
│   │   │   │   ├── scheduling/      # Transparent scheduler
│   │   │   │   └── search/          # Web search capabilities
│   │   │   └── orchestrator.py      # Main agent orchestrator
│   │   ├── api/v1/                  # REST API endpoints
│   │   │   ├── endpoints/
│   │   │   │   ├── admin.py         # Admin & NLU monitoring
│   │   │   │   ├── agent_modules/   # Conversation, workflows, briefings, commands, gates
│   │   │   │   ├── auth_modules/    # OAuth, tokens, refresh
│   │   │   │   ├── calendar_modules/    # Calendar events, timeblocks, webhooks
│   │   │   │   ├── focus_modules/       # Focus sessions, pomodoro, entity matching
│   │   │   │   ├── infrastructure_modules/  # Health, usage tracking
│   │   │   │   ├── integrations_modules/    # Calendar, Canvas, email settings
│   │   │   │   ├── payments_modules/        # Subscriptions, RevenueCat
│   │   │   │   ├── task_modules/    # Tasks, todos, tags
│   │   │   │   └── user_modules/    # Users, contacts, courses, hobbies
│   │   │   └── api.py               # API router configuration
│   │   ├── database/                # Repository pattern & data layer
│   │   │   ├── repositories/        # Domain-specific repositories
│   │   │   │   ├── calendar_repositories/   # Calendar, timeblocks, sync status
│   │   │   │   ├── integration_repositories/    # OAuth, Canvas, emails, briefings
│   │   │   │   ├── task_repositories/       # Tasks, todos, tags
│   │   │   │   └── user_repositories/       # Users, courses, focus, hobbies
│   │   │   ├── base_repository.py   # Base repository class
│   │   │   ├── manager.py           # Database connection manager
│   │   │   └── models.py            # Database models
│   │   ├── integrations/            # External integrations
│   │   │   └── providers/           # Calendar/email provider abstraction
│   │   │       └── google/          # Google Calendar client & mapping
│   │   ├── jobs/                    # Background job runners
│   │   │   ├── calendar/            # Calendar sync workers
│   │   │   ├── canvas/              # Canvas backfill, delta sync, nightly jobs
│   │   │   ├── notifications/       # Notification delivery
│   │   │   └── usage_aggregation.py # Usage metrics aggregation
│   │   ├── memory/                  # Dual-layer memory system
│   │   │   ├── core/                # Chat memory, vector storage
│   │   │   ├── processing/          # Ingestion, summarization
│   │   │   └── retrieval/           # Semantic search, embeddings
│   │   ├── scheduler/               # OR-Tools scheduling engine
│   │   │   ├── core/                # Service, domain models, features
│   │   │   ├── optimization/        # Constraints, objectives, CP-SAT solver
│   │   │   ├── diagnostics/         # Quality analysis, constraint checking
│   │   │   ├── learning/            # Completion models, bandits, safety rails
│   │   │   ├── monitoring/          # Telemetry, distributed tracing
│   │   │   └── io/                  # Repository layer, DTOs
│   │   ├── services/                # Business logic layer
│   │   │   ├── analytics/           # PostHog analytics integration
│   │   │   ├── auth/                # Token management, refresh, OAuth
│   │   │   ├── commands/            # Slash command handlers
│   │   │   ├── focus/               # Focus sessions, entity matching
│   │   │   ├── infrastructure/      # Cache, preferences, user settings
│   │   │   ├── integrations/        # Calendar sync, Canvas, email
│   │   │   ├── notifications/       # iOS notifications, push delivery
│   │   │   ├── pomodoro/            # Pomodoro settings
│   │   │   ├── scheduling/          # Smart slot finding
│   │   │   ├── usage/               # Token tracking, usage limits
│   │   │   ├── user/                # Hobby parsing, user utilities
│   │   │   └── workers/             # Job runner implementations
│   │   ├── workers/                 # APScheduler worker processes
│   │   │   ├── calendar_scheduler.py    # Calendar sync scheduling
│   │   │   ├── canvas_scheduler.py      # Canvas sync scheduling
│   │   │   └── focus_profile_worker.py  # Focus analytics
│   │   ├── core/                    # Core infrastructure
│   │   │   ├── auth/                # Authentication & security
│   │   │   ├── infrastructure/      # WebSocket, cache, circuit breaker
│   │   │   ├── llm/                 # Tracked LLM for observability
│   │   │   └── utils/               # Timezone utils, error handlers
│   │   ├── middleware/              # HTTP middleware
│   │   ├── models/                  # Domain models
│   │   │   ├── auth/                # OAuth tokens
│   │   │   ├── calendar/            # Timeblocks
│   │   │   ├── integrations/        # Integration settings
│   │   │   └── user/                # User hobbies
│   │   ├── config/                  # Configuration management
│   │   └── security/                # Encryption, secrets management
│   ├── migrations/                  # Database migrations
│   ├── scripts/                     # Utility scripts
│   ├── docs/                        # Technical documentation
│   │   ├── 01-getting-started/      # Setup guides
│   │   ├── 02-architecture/         # System architecture
│   │   ├── 03-ai-agents/            # Agent system docs
│   │   ├── 04-development/          # Development guidelines
│   │   ├── 05-systems/              # System-specific docs
│   │   ├── 06-security/             # Security documentation
│   │   ├── 07-mobile/               # Mobile platform docs
│   │   └── 08-plans/                # Future plans & roadmap
│   └── tests/                       # Comprehensive test suite
├── web/                             # React web application (Vite + TypeScript)
│   ├── src/
│   │   ├── components/              # Reusable UI components
│   │   │   ├── ui/                  # Base UI components (shadcn/ui)
│   │   │   ├── layout/              # Layout components
│   │   │   └── tasks/               # Task-specific components
│   │   ├── features/                # Feature modules
│   │   │   ├── calendar/            # Calendar views (daily, weekly, monthly)
│   │   │   └── tasks/               # Task management, kanban
│   │   ├── pages/                   # Page components
│   │   │   ├── HomePage.tsx         # Dashboard
│   │   │   ├── CalendarPage.tsx     # Calendar interface
│   │   │   ├── ChatPage.tsx         # AI chat interface
│   │   │   ├── TaskboardPage.tsx    # Task board
│   │   │   ├── PomodoroPage.tsx     # Pomodoro timer
│   │   │   ├── IntegrationsPage.tsx # Integration management
│   │   │   ├── PricingPage.tsx      # Subscription tiers
│   │   │   └── AdminNLUPage.tsx     # NLU monitoring (admin)
│   │   ├── contexts/                # React context providers
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── services/                # API integration layer
│   │   ├── lib/                     # Utilities & helpers
│   │   │   ├── api/                 # API SDK
│   │   │   ├── commands/            # Command parsing
│   │   │   ├── utils/               # Utilities
│   │   │   └── validation/          # Input validation
│   │   └── types/                   # TypeScript types
│   └── public/                      # Static assets
├── mobile/                          # React Native mobile app (Expo)
│   ├── app/                         # Expo Router pages
│   ├── components/                  # Mobile-specific components
│   ├── contexts/                    # Mobile state management
│   └── services/                    # Mobile API integration
├── ml/                              # Machine learning models
│   └── intent_classifier/           # Intent classification model
│       ├── scripts/                 # Training & inference scripts
│       ├── data/                    # Training data
│       ├── outputs/                 # Trained models
│       └── docs/                    # ML documentation
├── data/                            # Training data & datasets
│   └── intents/                     # Intent classification datasets
├── docs/                            # Root documentation
└── tests/                           # Integration tests
```

---

## 🔠 Tech Stack

| Layer                    | Technology                                                 |
| ------------------------ | ---------------------------------------------------------- |
| **AI Agents**            | LangGraph + OpenAI GPT-4o + Google Gemini                  |
| **NLU**                  | Custom Sentence Transformers + Contrastive Learning        |
| **Backend API**          | Python FastAPI + Pydantic + asyncio                        |
| **Agent Tools**          | Custom tool ecosystem (20+ specialized tools)              |
| **Intent Classification**| Fine-tuned BERT model (95%+ accuracy)                      |
| **Entity Extraction**    | Custom extractors (date/time, duration, participants, etc.)|
| **Scheduling Engine**    | OR-Tools CP-SAT + Constraint Programming + ML              |
| **Memory System**        | Dual-layer: pgvector + Redis + OpenAI Embeddings          |
| **Learning Models**      | Contextual Bandits + Logistic Regression                   |
| **Web Frontend**         | React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui   |
| **Mobile App**           | React Native + Expo Router + TypeScript                    |
| **Database**             | Supabase (PostgreSQL) + Row Level Security                 |
| **Data Layer**           | Repository Pattern + Domain-driven design                  |
| **Caching**              | Redis + Multi-layer caching strategy                       |
| **Authentication**       | Supabase Auth + JWT + OAuth2 (Google, Microsoft)           |
| **Background Jobs**      | Python asyncio + APScheduler + Worker processes            |
| **Real-time**            | WebSockets + Server-Sent Events                            |
| **Email Integration**    | Provider abstraction (Gmail, Outlook, System)              |
| **Calendar Integration** | Google Calendar + Microsoft Outlook + Provider pattern     |
| **LMS Integration**      | Canvas API + Automated sync jobs                           |
| **Analytics**            | PostHog + Custom telemetry                                 |
| **Payments**             | RevenueCat + Subscription management                       |
| **Observability**        | Sentry + Structured logging + Health checks                |
| **Deployment**           | Docker + Kubernetes ready + Multi-environment support      |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (for caching)
- Supabase account
- OpenAI API key
- Google OAuth credentials (for Calendar integration)
- Canvas API key (for LMS integration)

### Easy Setup (Recommended)

```bash
# Clone repository
git clone https://github.com/flyonthewall-dev/pulseplan.git
cd PulsePlan

# Run automated setup script (cross-platform)
./setup.sh

# Follow the interactive prompts to configure:
# - Python environment
# - Node.js dependencies
# - Environment variables
# - Database migrations
```

### Manual Setup

#### Backend (Python FastAPI + LangGraph)

```bash
cd backend

# 1. Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys and credentials

# 4. Start backend server
python main.py
# Backend runs on http://localhost:8000
```

#### Frontend (React Web App)

```bash
cd web

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env
# Edit .env with backend URL and Supabase credentials

# 3. Start development server
npm run dev
# Frontend runs on http://localhost:5173
```

### Docker Setup (Alternative)

```bash
# Full stack with Docker Compose
docker-compose up --build

# Backend only
cd backend
docker build -t pulseplan-backend .
docker run -p 8000:8000 pulseplan-backend
```

---

## 🤖 Agent System Details

### **Available Agents**

1. **ChatGraph** - Conversational AI for general queries
2. **TaskGraph** - Task management and CRUD operations
3. **SchedulingGraph** - Intelligent scheduling with optimization
4. **CalendarGraph** - Calendar sync and event management
5. **BriefingGraph** - Data aggregation and insight generation

### **Agent Tool Categories**

**Academic Integration (4 tools)**

- Canvas LMS sync and assignment management
- Weekly productivity pulse generation
- Academic calendar integration
- Grade and course tracking

**Calendar & Scheduling (6 tools)**

- Multi-provider calendar sync (Google, Microsoft)
- Intelligent task scheduling
- Event conflict resolution
- Time-blocking optimization

**Communication (4 tools)**

- Smart email routing and management
- Multi-provider email integration
- System notification handling
- Contact management

**Intelligence & Memory (3 tools)**

- Semantic memory with vector search
- User preference management
- Web search and research capabilities

### **Key Agent Capabilities**

- **Natural Language Processing** – Understand complex scheduling requests
- **Context Awareness** – Remember user preferences and past interactions
- **Multi-Tool Coordination** – Execute complex workflows across multiple tools
- **Error Recovery** – Graceful handling of API failures and edge cases
- **Real-Time Adaptation** – Respond to calendar changes and task updates

---

## 🧮 Advanced Scheduling Engine

### **Constraint Programming Optimization**

PulsePlan features a sophisticated scheduling system built on OR-Tools constraint programming:

**Core Algorithm Components:**

- **CP-SAT Solver** – Google's constraint satisfaction solver for optimal task assignment
- **Time Discretization** – Converts continuous time to discrete 15-30 minute slots
- **Constraint Modeling** – Hard constraints (deadlines, conflicts) vs soft constraints (preferences)
- **Multi-Objective Optimization** – Balances completion probability, user satisfaction, and efficiency

**Machine Learning Integration:**

- **Completion Prediction Model** – Logistic regression predicts task completion likelihood
- **Contextual Bandits** – Thompson Sampling for adaptive penalty weight tuning
- **Feature Engineering** – Time of day, task characteristics, user patterns, historical data
- **Online Learning** – Models update based on actual user behavior and outcomes

### **Scheduling Constraints**

**Hard Constraints (Must Be Satisfied):**

- Temporal conflicts with existing calendar events
- Deadline adherence for all academic assignments
- Block size limits (minimum/maximum work periods)
- Task dependencies and prerequisites
- Daily/weekly effort capacity limits

**Soft Constraints (Optimized via Penalties):**

- Time preferences alignment with user's optimal hours
- Context switching minimization
- Work block fragmentation reduction
- Workload balance across days and weeks
- Fair distribution across academic courses

### **Intelligent Features**

- **Fallback Mechanisms** – Greedy heuristic when optimization times out
- **Rescheduling Intelligence** – Adaptive strategies for missed or conflicting tasks
- **Quality Metrics** – Schedule evaluation and improvement recommendations
- **Performance Monitoring** – Solve times, feasibility rates, user satisfaction tracking

---

## 🧠 Dual-Layer Memory Architecture

### **Semantic Memory System**

**Vector Database (pgvector + PostgreSQL):**

- **Multi-Namespace Storage** – Organized by content type (tasks, assignments, interactions)
- **Semantic Search** – OpenAI embeddings with cosine similarity
- **Context Retrieval** – MMR (Maximal Marginal Relevance) reranking for diversity
- **Auto-Ingestion Pipeline** – Automated processing of academic data

**Ephemeral Chat Memory (Redis):**

- **Session-Based Storage** – Recent conversation context per user
- **TTL Management** – Automatic cleanup of expired conversations
- **Fast Access** – Sub-millisecond retrieval for active sessions
- **Token Budget Management** – Efficient context window utilization

### **Memory Categories & Namespaces**

- **Academic Data** – Assignments, courses, grades, deadlines
- **Calendar Events** – Meetings, classes, scheduled activities
- **Task Information** – User-created tasks, priorities, progress
- **User Interactions** – Chat history, preferences, behavior patterns
- **Profile Snapshots** – Periodic user behavior and preference summaries
- **Productivity Insights** – Performance analytics and trend data

---

## 📊 Background Job System

### **Automated Jobs (APScheduler)**

**Calendar Sync Workers:**
- **Incremental Pulls** – Every 20 minutes during user active hours (respects timezone + working_hours)
- **Watch Renewals** – Every hour for Google Calendar webhook channels expiring within 12 hours
- **Discovery** – Periodic calendar discovery and primary write calendar setup

**Canvas Integration:**
- **Backfill Job** – Initial full sync of courses, assignments, and submissions
- **Delta Sync** – Incremental updates based on last sync timestamp
- **Auto-Ingestion** – Processes academic data into memory system

**Memory & Analytics:**
- **Memory Processing** – Semantic indexing, embedding generation, and namespace management
- **Analytics Generation** – Weekly pulse analytics and productivity insights
- **Profile Snapshots** – Periodic user behavior analysis and preference updates

**System Maintenance:**
- **Cache Management** – Intelligent cache warming, cleanup, and optimization
- **Token Refresh** – OAuth token refresh for Google/Microsoft/Canvas
- **Learning Model Updates** – Completion prediction and bandit model training

---

## 📅 Calendar Integration

### **Centralized Calendar System**

**Provider Support:**
- **Google Calendar** – Full OAuth integration with bidirectional sync
- **Microsoft Outlook** – Calendar integration (configurable)
- **Provider Abstraction** – Extensible interface for additional calendar providers

**Sync Architecture:**
- **Incremental Sync** – Uses sync tokens for delta updates (falls back to window sync)
- **Webhook Integration** – Google Calendar watch channels for real-time change notifications
- **Conflict Resolution** – Source-of-truth logic (calendar/task/latest_update) in `calendar_links` table
- **Premium Gating** – Push operations and write-enabled calendars require active subscription

**Key Features:**
- **Unified Timeblocks API** – Merges tasks + calendar events into single view
- **Primary Write Calendar** – One designated calendar for task → event sync
- **Active Hours Scheduling** – Respects user timezone and working hours for sync jobs
- **Auto-Renewal** – Watch channels automatically renewed before expiration

---

## 🔧 Backend Services & Features

### **Core Services**

**Authentication & Security:**

- **Multi-Provider OAuth** – Google, Microsoft, Canvas LMS integration
- **JWT Token Management** – Automated refresh and secure storage
- **Encrypted Token Vault** – AES-256 encryption for API credentials
- **Row Level Security** – Database-level access control with Supabase
- **Rate Limiting** – Request throttling and abuse protection

**Integration Services:**

- **Google Calendar Client** – OAuth token auto-refresh, incremental sync, webhook watch channels
- **Canvas Service** – Automated LMS synchronization with backfill and delta sync jobs
- **Token Service** – OAuth token lifecycle management with encryption
- **Integration Settings Service** – User preferences for Canvas/Google/Microsoft integrations
- **NLU Service** – Natural language understanding for intent classification

**Data Processing:**

- **Email Service** – Smart routing between user/agent email handling
- **Cache Service** – Multi-layer Redis caching with intelligent invalidation
- **Embedding Service** – OpenAI embedding generation for semantic search
- **Summarization Service** – Periodic content summarization for memory optimization

### **Advanced Features**

**Observability & Monitoring:**

- **Health Checks** – Comprehensive system health monitoring with alerts
- **Structured Logging** – Correlation IDs and contextual log data
- **Performance Metrics** – Request timing, success rates, and resource usage
- **Sentry Integration** – Automated error tracking and performance monitoring

**Scalability & Performance:**

- **Async Architecture** – Full asyncio support for concurrent operations
- **Connection Pooling** – Optimized database and Redis connections
- **Background Workers** – Dedicated task processing with queue management
- **Horizontal Scaling** – Stateless design for multi-instance deployment

**API Architecture:**

- **FastAPI Framework** – High-performance async web framework
- **Pydantic Validation** – Comprehensive input/output validation and serialization
- **OpenAPI Documentation** – Automatic API documentation generation
- **CORS Configuration** – Secure cross-origin resource sharing

### **Security Hardening**

**Data Protection:**

- **Encryption at Rest** – Sensitive data encrypted in database
- **Token Encryption** – All OAuth tokens encrypted with user-specific keys
- **Secure Headers** – HSTS, CSP, and other security headers
- **Input Sanitization** – Comprehensive XSS and injection prevention

**Access Control:**

- **Role-Based Permissions** – Granular access control system
- **API Key Management** – Service-to-service authentication
- **Session Management** – Secure session handling with Redis
- **Audit Logging** – Comprehensive access and operation logging

---

## 🔐 Security & Authentication

### **Multi-Layer Security**

- **Supabase Auth** – Google OAuth and JWT session management
- **Row Level Security** – Database-level access control
- **Encrypted Storage** – Secure token and credential management
- **API Rate Limiting** – Request throttling and abuse protection
- **CORS Configuration** – Secure cross-origin resource sharing

### **Data Privacy**

- **Local-First Approach** – Sensitive data processed locally when possible
- **Minimal Data Collection** – Only necessary information stored
- **User Control** – Full data export and deletion capabilities
- **Compliance Ready** – GDPR and educational privacy standards

---

## 📈 Performance & Monitoring

### **Caching Strategy**

- **Multi-Layer Caching** – Redis + in-memory LRU cache
- **Intelligent Invalidation** – Smart cache updates on data changes
- **90%+ Cache Hit Rate** – Optimized query performance

### **Observability**

- **Structured Logging** – Comprehensive request/response tracking
- **Health Monitoring** – System health checks and alerts
- **Performance Metrics** – Agent execution time and success rates
- **Error Tracking** – Automated error reporting and analysis

---

## 🔧 API Endpoints

### **Agent System**
- `POST /api/v1/agent/chat` – Conversational AI interface
- `POST /api/v1/agent/workflows` – Execute specific workflows
- `GET /api/v1/agent/conversations/{id}` – Get conversation history
- `POST /api/v1/agent/briefings` – Generate daily briefings
- `POST /api/v1/agent/commands` – Execute slash commands
- `GET /api/v1/agent/gates` – Get workflow gate status

### **Tasks & Todos**
- `GET /api/v1/tasks` – List tasks with filters
- `POST /api/v1/tasks` – Create new task
- `PUT /api/v1/tasks/{id}` – Update task
- `DELETE /api/v1/tasks/{id}` – Delete task
- `GET /api/v1/todos` – List todos
- `POST /api/v1/todos` – Create todo
- `GET /api/v1/tags` – List tags
- `POST /api/v1/tags` – Create tag

### **Calendar & Events**
- `GET /api/v1/calendar/events` – List calendar events
- `POST /api/v1/calendar/events` – Create event
- `PUT /api/v1/calendar/events/{id}` – Update event
- `DELETE /api/v1/calendar/events/{id}` – Delete event
- `GET /api/v1/calendar/timeblocks` – Get merged schedule view
- `POST /api/v1/calendar/webhooks` – Handle calendar webhooks

### **Focus & Productivity**
- `GET /api/v1/focus/sessions` – List focus sessions
- `POST /api/v1/focus/sessions` – Start focus session
- `PUT /api/v1/focus/sessions/{id}` – Update session
- `GET /api/v1/focus/pomodoro/settings` – Get pomodoro settings
- `PUT /api/v1/focus/pomodoro/settings` – Update settings

### **Integrations**
- `POST /api/v1/integrations/canvas/sync` – Manual Canvas sync
- `GET /api/v1/integrations/canvas/courses` – List courses
- `POST /api/v1/integrations/calendar/connect` – Connect calendar
- `GET /api/v1/integrations/settings` – Get integration settings
- `POST /api/v1/integrations/oauth/{provider}` – OAuth flow

### **User Management**
- `GET /api/v1/users/me` – Get current user profile
- `PUT /api/v1/users/me` – Update user profile
- `GET /api/v1/users/contacts` – List contacts
- `GET /api/v1/users/courses` – List courses
- `GET /api/v1/users/hobbies` – List hobbies
- `POST /api/v1/users/hobbies` – Add hobby

### **Admin & Monitoring**
- `GET /api/v1/admin/nlu/monitoring` – NLU performance metrics
- `GET /api/v1/infrastructure/health` – System health check
- `GET /api/v1/infrastructure/usage` – Usage statistics

### **Payments**
- `POST /api/v1/payments/subscriptions` – Manage subscriptions
- `POST /api/v1/payments/revenuecat/webhook` – RevenueCat webhook

---

## 📚 Documentation

**Getting Started:**
- **[Setup Guide](docs/01-getting-started/SETUP.md)** – Complete installation and configuration guide
- **[Development Guide](docs/01-getting-started/DEVELOPMENT.md)** – Local development environment setup

**Architecture & Design:**
- **[System Architecture](docs/02-architecture/ARCHITECTURE.md)** – Overall system design and patterns
- **[Interface Design](docs/02-architecture/INTERFACES.md)** – API and integration interfaces
- **[Development Rules](docs/02-architecture/RULES.md)** – Coding standards and best practices

**AI Agent System:**
- **[Agent Overview](docs/03-ai-agents/README.md)** – Multi-agent architecture overview
- **[Agent Workflows](docs/05-systems/agents/AGENT_WORKFLOW_SYSTEM.md)** – LangGraph workflow implementations
- **[Conversation System](docs/05-systems/agents/CONVERSATION_CONTINUATION_SYSTEM.md)** – Conversation state management
- **[Acceptance Gates](docs/05-systems/agents/ACCEPTANCE_GATE.md)** – Quality assurance gates

**Systems Documentation:**
- **[Calendar System](docs/05-systems/integrations/CALENDAR_SYSTEM.md)** – Calendar integration architecture
- **[Canvas Integration](docs/05-systems/integrations/CANVAS_INTEGRATION.md)** – Canvas LMS integration
- **[Email Security](docs/05-systems/integrations/EMAIL_SECURITY_IMPLEMENTATION.md)** – Email integration security
- **[Memory System](docs/05-systems/infrastructure/MEMORY_SYSTEM_DOCUMENTATION.md)** – Dual-layer memory architecture
- **[Scheduler](docs/05-systems/scheduling/SCHEDULER_SYSTEM_DOCUMENTATION.md)** – OR-Tools scheduling engine
- **[Timeblocks](docs/05-systems/scheduling/TIMEBLOCKS_ARCHITECTURE.md)** – Time blocking system
- **[WebSocket Implementation](docs/05-systems/infrastructure/WEBSOCKET_IMPLEMENTATION.md)** – Real-time updates

**Development:**
- **[API Organization](docs/04-development/API_ENDPOINTS_ORGANIZATION.md)** – API structure and conventions
- **[Service Layer Patterns](docs/04-development/SERVICE_LAYER_PATTERNS.md)** – Service architecture patterns
- **[Testing Guide](docs/04-development/TESTING.md)** – Testing strategies and examples
- **[Common Pitfalls](docs/04-development/PITFALLS.md)** – Known issues and solutions
- **[Web Guidelines](docs/04-development/WEB_RULES.md)** – Frontend development rules

**Security:**
- **[Security Overview](docs/06-security/SECURITY.md)** – Security architecture and practices
- **[Gmail OAuth](docs/06-security/GMAIL_OAUTH_SECURITY_STATUS.md)** – OAuth implementation status
- **[KMS Setup](docs/05-systems/infrastructure/KMS_SETUP_GUIDE.md)** – Encryption key management

**Job Systems:**
- **[Briefing Jobs](docs/05-systems/scheduling/BRIEFING_JOB_SYSTEM.md)** – Daily briefing generation
- **[Canvas Jobs](docs/05-systems/integrations/CANVAS_JOB_SYSTEM.md)** – Canvas sync automation
- **[Calendar Jobs](docs/05-systems/integrations/CALENDAR_AUTOSYNC_SYSTEM.md)** – Calendar sync automation
- **[Focus Jobs](docs/05-systems/observability/FOCUS_JOB_SYSTEM.md)** – Focus tracking automation
- **[Notification Jobs](docs/05-systems/notifications/NOTIFICATION_JOB_SYSTEM.md)** – Notification delivery
- **[Usage Jobs](docs/05-systems/infrastructure/USAGE_JOB_SYSTEM.md)** – Usage tracking and limits

**ML & NLU:**
- **[Intent Classifier](ml/intent_classifier/README.md)** – Intent classification model documentation
- **[Training Guide](ml/intent_classifier/docs/TRAINING_GUIDE.md)** – Model training instructions
- **[Dataset Summary](ml/intent_classifier/docs/DATASET_SUMMARY.md)** – Training data overview

---

## 🚀 Deployment

### **Production Deployment**

```bash
# Docker deployment
docker-compose -f docker-compose.prod.yml up -d

# Kubernetes deployment
kubectl apply -f k8s/

# Environment-specific configs
cp .env.production .env
```

### **Environment Configuration**

- **Development** – Local development with hot reload
- **Staging** – Pre-production testing environment
- **Production** – Optimized production deployment with monitoring

---

## 🏢 About

PulsePlan is built by **Fly on the Wall** – creating AI-powered products with personality.

- **Website**: [flyonthewall.xyz](https://flyonthewall.xyz)
- **App**: [pulseplan.app](https://pulseplan.app)
- **Contact**: [hello@flyonthewall.xyz](mailto:hello@flyonthewall.xyz)
