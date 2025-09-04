# FastAPI Backend Migration Plan

## Executive Summary

This document outlines a comprehensive plan to migrate PulsePlan from its current Node.js/Express backend to a production-ready FastAPI backend with embedded agent workflows. The migration will replace external N8N workflows with internal LangGraph-based agent orchestration while maintaining all existing functionality.

## Current System Analysis

### Node.js Backend Structure
- **Framework**: Express.js with TypeScript
- **Database**: Supabase (PostgreSQL)
- **Auth**: Google OAuth, Microsoft OAuth, Canvas LTI
- **Agent System**: External N8N workflows at `https://pulseplan-agent.fly.dev`
- **Real-time**: WebSocket for status updates
- **Cache**: Redis via Upstash
- **Job Scheduling**: Node-cron for email scheduling

### Key Services Currently Implemented
1. **Authentication**: Google/Microsoft OAuth, Canvas integration
2. **Calendar Integration**: Google Calendar, Microsoft Outlook
3. **Email Processing**: Gmail API integration
4. **Agent Services**: N8N-based workflows for briefings, scheduling, chat
5. **Task Management**: Intelligent scheduling and optimization
6. **Canvas Integration**: LMS data retrieval and analysis
7. **Caching**: Redis-based caching for performance
8. **Real-time Updates**: WebSocket status broadcasting

### N8N Workflow Mapping
Current external workflows that need to be embedded:
- **Daily Briefing**: `/agents/briefing` - Analyzes emails, calendar, tasks
- **Weekly Pulse**: `/agents/weekly-pulse` - Weekly planning and review
- **Chat Agent**: `/agents/chat` - Natural language processing
- **Schedule Generation**: `/agents/schedule` - Intelligent scheduling
- **Task Analysis**: `/agents/analyze-tasks` - Task optimization

## FastAPI Architecture Design

### Core Stack
```
FastAPI + Uvicorn (ASGI)
├── LangGraph (Agent Orchestration)
├── PostgreSQL (Supabase)
├── Redis + Dramatiq (Job Queue)
├── Authlib (OAuth)
├── httpx + Tenacity (HTTP with retries)
├── OpenTelemetry + Sentry (Observability)
└── SlowAPI (Rate Limiting)
```

### Project Structure
```
pulseplan-fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── core/
│   │   ├── config.py              # Settings and configuration
│   │   ├── security.py            # JWT and OAuth handling
│   │   ├── database.py            # Database connection
│   │   ├── redis.py               # Redis connection
│   │   └── logging.py             # Logging configuration
│   ├── api/
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py        # Authentication endpoints
│   │   │   │   ├── calendar.py    # Calendar endpoints
│   │   │   │   ├── agent.py       # Agent endpoints
│   │   │   │   ├── tasks.py       # Task endpoints
│   │   │   │   ├── gmail.py       # Gmail endpoints
│   │   │   │   ├── canvas.py      # Canvas endpoints
│   │   │   │   └── webhooks.py    # Webhook endpoints
│   │   │   └── api.py             # API router
│   │   └── deps.py                # Dependencies
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── graphs/
│   │   │   ├── briefing_graph.py  # Daily briefing workflow
│   │   │   ├── chat_graph.py      # Chat agent workflow
│   │   │   ├── scheduling_graph.py # Scheduling workflow
│   │   │   └── base.py            # Base graph utilities
│   │   ├── tools/
│   │   │   ├── calendar.py        # Calendar tool implementations
│   │   │   ├── email.py           # Email tool implementations
│   │   │   ├── canvas.py          # Canvas tool implementations
│   │   │   ├── notion.py          # Notion tool implementations
│   │   │   └── web.py             # Web scraping tools
│   │   ├── models.py              # Agent data models
│   │   └── orchestrator.py       # Main agent orchestrator
│   ├── services/
│   │   ├── auth_service.py        # Authentication logic
│   │   ├── calendar_service.py    # Calendar integration
│   │   ├── email_service.py       # Email processing
│   │   ├── cache_service.py       # Redis caching
│   │   ├── token_service.py       # Token management
│   │   └── notification_service.py # WebSocket notifications
│   ├── models/
│   │   ├── user.py                # User models
│   │   ├── task.py                # Task models
│   │   ├── calendar.py            # Calendar models
│   │   └── agent.py               # Agent models
│   ├── schemas/
│   │   ├── user.py                # Pydantic schemas
│   │   ├── task.py
│   │   ├── calendar.py
│   │   └── agent.py
│   ├── middleware/
│   │   ├── rate_limit.py          # Rate limiting
│   │   ├── auth.py                # Auth middleware
│   │   └── logging.py             # Request logging
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── agent_worker.py        # Agent job processing
│   │   ├── email_worker.py        # Email job processing
│   │   └── scheduler_worker.py    # Scheduled job processing
│   └── utils/
│       ├── http.py                # HTTP utilities
│       ├── crypto.py              # Encryption utilities
│       └── validation.py         # Validation utilities
├── tests/
├── alembic/                       # Database migrations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

## Key Components Design

### 1. Agent Orchestration (LangGraph)

Replace N8N workflows with embedded LangGraph control flows:

```python
# agents/graphs/briefing_graph.py
from langgraph import StateGraph, END
from typing import Dict, Any

class BriefingState(TypedDict):
    user_id: str
    user_email: str
    date: str
    calendar_events: List[Dict]
    emails: List[Dict]
    tasks: List[Dict]
    weather: Dict
    briefing_content: str

def create_briefing_graph() -> StateGraph:
    workflow = StateGraph(BriefingState)
    
    # Nodes
    workflow.add_node("fetch_calendar", fetch_calendar_events)
    workflow.add_node("fetch_emails", fetch_recent_emails)
    workflow.add_node("fetch_tasks", fetch_pending_tasks)
    workflow.add_node("fetch_weather", fetch_weather_data)
    workflow.add_node("generate_briefing", generate_briefing_content)
    
    # Edges with conditions
    workflow.add_edge("fetch_calendar", "fetch_emails")
    workflow.add_edge("fetch_emails", "fetch_tasks")
    workflow.add_edge("fetch_tasks", "fetch_weather")
    workflow.add_edge("fetch_weather", "generate_briefing")
    workflow.add_edge("generate_briefing", END)
    
    workflow.set_entry_point("fetch_calendar")
    
    return workflow.compile()
```

### 2. Job Queue System (Dramatiq)

```python
# workers/agent_worker.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from agents.orchestrator import AgentOrchestrator

redis_broker = RedisBroker(host="localhost", port=6379, db=0)
dramatiq.set_broker(redis_broker)

@dramatiq.actor(max_retries=3, min_backoff=1000, max_backoff=30000)
def process_agent_request(job_id: str, user_id: str, request_type: str, payload: dict):
    """Process agent requests asynchronously"""
    orchestrator = AgentOrchestrator()
    
    try:
        result = orchestrator.execute_workflow(request_type, payload)
        
        # Store result and update status
        redis_client.hset(f"job:{job_id}", "status", "completed")
        redis_client.hset(f"job:{job_id}", "result", json.dumps(result))
        
        # Broadcast completion via WebSocket
        broadcast_agent_status(user_id, request_type, "completed", result)
        
    except Exception as e:
        redis_client.hset(f"job:{job_id}", "status", "failed")
        redis_client.hset(f"job:{job_id}", "error", str(e))
        
        broadcast_agent_status(user_id, request_type, "error", {"error": str(e)})
```

### 3. API Endpoints

```python
# api/v1/endpoints/agent.py
from fastapi import APIRouter, Depends, BackgroundTasks
from uuid import uuid4
from workers.agent_worker import process_agent_request

router = APIRouter()

@router.post("/run")
async def run_agent(
    request: AgentRequest,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks
):
    """Enqueue agent job and return job_id immediately"""
    job_id = str(uuid4())
    
    # Store job metadata
    redis_client.hset(f"job:{job_id}", "status", "queued")
    redis_client.hset(f"job:{job_id}", "user_id", current_user.id)
    redis_client.expire(f"job:{job_id}", 3600)  # 1 hour TTL
    
    # Enqueue job
    process_agent_request.send(job_id, current_user.id, request.type, request.payload)
    
    return {"job_id": job_id, "status": "queued"}

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Poll job progress and results"""
    job_data = redis_client.hgetall(f"job:{job_id}")
    
    if not job_data:
        raise HTTPException(404, "Job not found")
    
    if job_data["user_id"] != current_user.id:
        raise HTTPException(403, "Access denied")
    
    return {
        "job_id": job_id,
        "status": job_data["status"],
        "result": json.loads(job_data.get("result", "{}")),
        "error": job_data.get("error")
    }
```

### 4. Rate Limiting & Security

```python
# middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis

redis_client = redis.Redis(host="localhost", port=6379, db=1)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/1",
    default_limits=["100/minute"]
)

# Per-user rate limits
@limiter.limit("5/minute")  # 5 agent requests per minute
async def agent_rate_limit():
    pass

# Per-integration limits stored in Redis
def check_integration_rate_limit(user_id: str, integration: str):
    key = f"rate_limit:{user_id}:{integration}"
    current = redis_client.get(key)
    
    if current and int(current) >= INTEGRATION_LIMITS[integration]:
        raise RateLimitExceeded("Integration rate limit exceeded")
    
    redis_client.incr(key)
    redis_client.expire(key, 60)  # 1 minute window
```

### 5. Decision Tracing

```python
# models/agent.py
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class DecisionTrace(Base):
    __tablename__ = "decision_traces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    inputs = Column(JSON, nullable=False)
    steps = Column(JSON, nullable=False)  # List of tool executions
    policy_checks = Column(JSON, nullable=False)  # Security validations
    summary = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def add_step(self, tool: str, args: dict, result_meta: dict):
        step = {
            "tool": tool,
            "args": args,
            "result_meta": result_meta,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.steps is None:
            self.steps = []
        
        self.steps.append(step)
```

## Migration Strategy

### Phase 1: Infrastructure Setup (Week 1-2)
1. **Docker Environment**
   - FastAPI + Uvicorn container
   - Redis container for jobs and cache
   - PostgreSQL (reuse existing Supabase)
   - Dramatiq worker containers

2. **Core Framework**
   - FastAPI application structure
   - Database models and migrations
   - Authentication system (JWT + OAuth)
   - Basic health checks and monitoring

### Phase 2: Agent System Migration (Week 3-4)
1. **LangGraph Implementation**
   - Convert N8N workflows to LangGraph
   - Implement tool interfaces (calendar, email, canvas, etc.)
   - Create agent orchestrator
   - Add decision tracing

2. **Job Queue System**
   - Dramatiq workers for agent processing
   - Job status tracking
   - WebSocket notifications for real-time updates

### Phase 3: API Migration (Week 5-6)
1. **Core Endpoints**
   - Authentication endpoints
   - Agent execution endpoints
   - Job status endpoints
   - Webhook endpoints for integrations

2. **Integration Services**
   - Calendar service (Google, Microsoft)
   - Email service (Gmail)
   - Canvas LTI integration
   - Token management and refresh

### Phase 4: Advanced Features (Week 7-8)
1. **Performance Optimization**
   - Redis caching strategies
   - Rate limiting implementation
   - Request/response optimization
   - Database query optimization

2. **Observability**
   - OpenTelemetry tracing
   - Structured logging
   - Error monitoring (Sentry)
   - Performance metrics

### Phase 5: Testing & Deployment (Week 9-10)
1. **Testing**
   - Unit tests for all components
   - Integration tests for workflows
   - Load testing for performance
   - Security testing

2. **Deployment**
   - Production Docker setup
   - CI/CD pipeline
   - Monitoring and alerting
   - Rollback procedures

## Data Migration Plan

### Authentication Tokens
```sql
-- Migrate encrypted tokens from existing calendar_connections
SELECT 
    user_id,
    provider,
    access_token,
    refresh_token,
    expires_at,
    email
FROM calendar_connections;
```

### User Preferences
```sql
-- Migrate user settings and preferences
SELECT 
    id as user_id,
    name,
    subscription_status,
    timezone,
    city,
    preferences,
    working_hours,
    study_preferences,
    work_preferences
FROM users;
```

### Task and Schedule Data
```sql
-- Migrate existing tasks and schedule blocks
SELECT * FROM tasks;
SELECT * FROM schedule_blocks;
```

## Risk Mitigation

### 1. Parallel Deployment
- Run FastAPI backend alongside Node.js
- Gradual traffic migration with feature flags
- Rollback capability to Node.js system

### 2. Data Consistency
- Database-level constraints and validations
- Idempotency keys for critical operations
- Transaction boundaries for multi-step operations

### 3. Integration Continuity
- Maintain existing OAuth configurations
- Preserve webhook endpoints during transition
- Cache integration data during migration

### 4. Performance Monitoring
- Real-time performance dashboards
- Alert thresholds for response times
- Automated scaling based on load

## Expected Benefits

### Performance Improvements
- **Response Time**: 30-50% faster API responses
- **Concurrency**: Better handling of concurrent requests
- **Memory Usage**: Lower memory footprint
- **Agent Processing**: Embedded workflows reduce latency

### Development Benefits
- **Type Safety**: Full Python type checking
- **Testing**: Better testing ecosystem
- **Debugging**: Clearer error traces and debugging
- **Maintainability**: More structured codebase

### Operational Benefits
- **Observability**: Better monitoring and tracing
- **Scalability**: Horizontal scaling capabilities
- **Reliability**: Robust error handling and retries
- **Security**: Enhanced security controls

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 2 weeks | Infrastructure setup, basic FastAPI app |
| Phase 2 | 2 weeks | Agent system migration, LangGraph workflows |
| Phase 3 | 2 weeks | API endpoints, integration services |
| Phase 4 | 2 weeks | Performance optimization, observability |
| Phase 5 | 2 weeks | Testing, deployment, production readiness |

**Total Duration**: 10 weeks

## Success Metrics

- [ ] All existing API endpoints functional
- [ ] Agent response time < 2 seconds for simple operations
- [ ] 99.9% uptime during migration
- [ ] Zero data loss during migration
- [ ] All integrations (Google, Microsoft, Canvas) working
- [ ] WebSocket real-time updates functional
- [ ] Rate limiting and security controls active
- [ ] Full observability and monitoring in place