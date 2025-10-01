<div align="center">
  <img src="https://www.pulseplan.app/assets/logo.png" alt="PulsePlan Logo" width="90px" />
  <h1>PulsePlan – AI-Powered Academic Planner</h1>
</div>

PulsePlan is an intelligent academic planning assistant powered by LangGraph agents that integrates with Canvas, Google Calendar, Microsoft Outlook, and other academic platforms. Built for students, it provides conversational AI assistance, automated scheduling, and comprehensive productivity analytics through a sophisticated multi-agent system.

> 📱 Your personal AI academic agent.

---

## ✨ Key Features

### 🤖 **LangGraph AI Agent System**

- **Multi-Agent Architecture** – Specialized agents for different workflows (chat, scheduling, briefings)
- **Conversational AI** – Natural language task management and scheduling assistance
- **Context-Aware Intelligence** – Agents understand your preferences, patterns, and constraints
- **Tool-Based Execution** – 15+ specialized tools for comprehensive productivity management

### 📚 **Academic Integration**

- **Canvas LMS Sync** – Automated assignment, course, and grade synchronization
- **Calendar Intelligence** – Google Calendar and Microsoft Outlook bidirectional sync
- **Smart Scheduling** – AI-powered time-blocking with conflict resolution
- **Assignment Analytics** – Deadline tracking and priority management

### 💡 **Intelligent Features**

- **Memory System** – Semantic memory with vector storage for personalized assistance
- **Weekly Pulse** – AI-generated productivity insights and performance analytics
- **Automated Jobs** – Nightly Canvas sync and data processing workflows
- **Preference Management** – Structured user constraints and scheduling rules

### 🔧 **Advanced Capabilities**

- **Real-Time Processing** – WebSocket connections for live updates
- **Caching Strategy** – Multi-layer Redis caching for optimal performance
- **Background Jobs** – Automated synchronization and data processing
- **Security First** – Encrypted token storage and comprehensive auth system

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
├── backend/                    # Python FastAPI backend with LangGraph agents
│   ├── app/
│   │   ├── agents/            # LangGraph agent system
│   │   │   ├── graphs/        # Specialized workflow graphs
│   │   │   ├── nodes/         # Agent execution nodes
│   │   │   ├── tools/         # 15+ AI agent tools
│   │   │   └── orchestrator.py
│   │   ├── api/v1/           # REST API endpoints
│   │   ├── jobs/             # Background job system
│   │   ├── memory/           # Vector memory system
│   │   ├── scheduler/        # Intelligent scheduling engine
│   │   ├── services/         # Business logic layer
│   │   └── workers/          # Background task processing
│   ├── docs/                 # Technical documentation
│   └── tests/               # Comprehensive test suite
├── src/                     # React Native mobile app (Expo)
│   ├── app/                # App router and screens
│   ├── components/         # Reusable UI components
│   ├── contexts/          # State management
│   ├── hooks/            # Custom React hooks
│   └── services/        # API integration layer
└── server/             # Legacy Node.js server (being migrated)
```

---

## 🔠 Tech Stack

| Layer                 | Technology                                       |
| --------------------- | ------------------------------------------------ |
| **AI Agents**         | LangGraph + OpenAI GPT-4o + Google Gemini        |
| **Backend API**       | Python FastAPI + Pydantic + asyncio              |
| **Agent Tools**       | Custom tool ecosystem (15+ specialized tools)    |
| **Scheduling Engine** | OR-Tools CP-SAT + Constraint Programming + ML    |
| **Memory System**     | Dual-layer: pgvector + Redis + OpenAI Embeddings |
| **Learning Models**   | Contextual Bandits + Logistic Regression         |
| **Frontend**          | React Native (Expo 53) + TypeScript              |
| **Database**          | Supabase (PostgreSQL) + Row Level Security       |
| **Caching**           | Redis + Multi-layer caching strategy             |
| **Authentication**    | Supabase Auth + JWT + OAuth2                     |
| **Background Jobs**   | Python asyncio + APScheduler                     |
| **Real-time**         | WebSockets + Server-Sent Events                  |
| **Integrations**      | Canvas LMS + Google APIs + Microsoft Graph       |
| **Deployment**        | Docker + Kubernetes ready                        |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional)
- Supabase account
- OpenAI API key
- Google/Microsoft OAuth credentials (for integrations)

### Backend Setup (LangGraph Agents)

```bash
# 1. Clone repository
git clone https://github.com/flyonthewall-dev/pulseplan.git
cd PulsePlan/backend

# 2. Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Environment configuration
cp .env.example .env
# Edit .env with your credentials

# 4. Database setup
# Configure Supabase connection in .env
python -m app.database.migrations

# 5. Start the backend
python main.py
```

### Frontend Setup (React Native)

```bash
# 1. Frontend dependencies
cd ../src
npm install

# 2. Configure app.json with backend URL and Supabase credentials

# 3. Start Expo development server
npx expo start
```

### Docker Setup (Recommended)

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

### **Automated Jobs**

- **Nightly Canvas Sync** – Automated assignment and course synchronization with batch processing
- **Calendar Refresh** – OAuth token refresh and calendar event updates
- **Memory Processing** – Semantic indexing, embedding generation, and namespace management
- **Analytics Generation** – Weekly pulse analytics and productivity insights
- **Learning Model Updates** – Completion prediction and bandit model training
- **Cache Management** – Intelligent cache warming, cleanup, and optimization
- **Profile Snapshots** – Periodic user behavior analysis and preference updates

### **Job Configuration**

```python
# Configurable job schedules
CANVAS_SYNC_SCHEDULE = "0 2 * * *"        # Daily at 2 AM
WEEKLY_PULSE_SCHEDULE = "0 6 * * 1"       # Monday at 6 AM
CALENDAR_SYNC_SCHEDULE = "*/30 * * * *"    # Every 30 minutes
MODEL_UPDATE_SCHEDULE = "0 4 * * *"       # Daily at 4 AM
PROFILE_SNAPSHOT_SCHEDULE = "0 3 * * 0"   # Weekly on Sunday at 3 AM
```

---

## 🧠 Memory System

### **Semantic Memory Architecture**

- **Vector Database** – ChromaDB with OpenAI embeddings
- **Multi-Namespace Storage** – Organized by data type and user context
- **Intelligent Retrieval** – Context-aware memory search
- **Auto-Ingestion** – Automated processing of assignments, tasks, and interactions

### **Memory Categories**

- **Tasks & Assignments** – Academic work and deadlines
- **Calendar Events** – Meetings and scheduled activities
- **User Interactions** – Chat history and preferences
- **Academic Data** – Course information and grades
- **Productivity Insights** – Performance patterns and analytics

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

- **Calendar Sync Service** – Bidirectional Google/Microsoft Calendar integration
- **Canvas Service** – Automated LMS synchronization with error handling
- **Token Service** – OAuth token lifecycle management and refresh
- **Preferences Service** – User constraint and preference management

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

### **Agent Interactions**

- `POST /api/v1/agents/chat` – Conversational AI interface
- `POST /api/v1/agents/task` – Task management operations
- `POST /api/v1/agents/schedule` – Scheduling requests
- `GET /api/v1/agents/status` – Agent system health

### **Integration Management**

- `POST /api/v1/integrations/canvas/sync` – Manual Canvas sync
- `GET /api/v1/integrations/calendar/events` – Calendar data
- `POST /api/v1/integrations/oauth/connect` – OAuth setup

### **Analytics & Insights**

- `GET /api/v1/analytics/weekly-pulse` – Productivity insights
- `GET /api/v1/analytics/performance` – Performance metrics
- `POST /api/v1/analytics/generate` – Custom report generation

---

## 📚 Documentation

- **[Backend API Documentation](backend/README.md)** – Complete FastAPI setup guide
- **[LangGraph Workflows](backend/docs/LANGGRAPH_AGENT_WORKFLOWS.md)** – Agent system architecture
- **[Memory System](backend/docs/MEMORY_SYSTEM_DOCUMENTATION.md)** – Vector memory implementation
- **[Frontend Development](README_FRONTEND.md)** – React Native app guide
- **[Agent Tools Reference](backend/app/agents/tools/README.md)** – Complete tool documentation

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

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Workflow**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### **Code Standards**

- **Python** – Black formatting, type hints, comprehensive tests
- **TypeScript** – ESLint + Prettier, strict type checking
- **Documentation** – Clear docstrings and API documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🏢 About

PulsePlan is built by **Fly on the Wall** – creating AI-powered products with personality.

- **Website**: [flyonthewalldev.com](https://flyonthewalldev.com)
- **App**: [pulseplan.app](https://pulseplan.app)
- **Contact**: [hello@flyonthewalldev.com](mailto:hello@flyonthewalldev.com)

---

_Built with ❤️ for students who want their schedule to find its rhythm._
