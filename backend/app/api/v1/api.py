from fastapi import APIRouter, Query, Depends, HTTPException, status
from typing import Optional
from app.api.v1.endpoints import agent, auth, tasks, integrations, infrastructure, users
from app.scheduler.scheduling.router import scheduler_router
from app.core.auth import get_current_user, CurrentUser
from app.agents.orchestrator import get_agent_orchestrator, AgentOrchestrator
from app.agents.models import AgentError

api_router = APIRouter()

# Include authentication endpoints (consolidated)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include infrastructure endpoints (consolidated)
api_router.include_router(infrastructure.router, prefix="/system", tags=["system"])

# Include integration endpoints (consolidated)
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])

# Include user management endpoints (consolidated)
api_router.include_router(users.router, prefix="/user-management", tags=["user-management"])

# Include unified agent endpoints
api_router.include_router(agent.router, prefix="/agents", tags=["agents"])

# Include task management endpoints (consolidated)
api_router.include_router(tasks.router, tags=["tasks"])

# Include scheduler endpoints
api_router.include_router(scheduler_router, tags=["scheduling"])
