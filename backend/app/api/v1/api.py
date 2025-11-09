from fastapi import APIRouter, Query, Depends, HTTPException, status
from typing import Optional
from app.api.v1.endpoints import agent, auth, tasks, integrations, infrastructure, users, admin, focus, calendar
from app.api.v1.endpoints.payments_modules import main as payments
from app.api.v1.endpoints.agent_modules import commands, briefings, gates
from app.scheduler.scheduling.router import scheduler_router
from app.core.auth import get_current_user, CurrentUser
from app.agents.orchestrator import get_agent_orchestrator, AgentOrchestrator
from app.agents.models import AgentError

api_router = APIRouter()

# Include authentication endpoints (consolidated)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include commands endpoints (deterministic shortcuts)
api_router.include_router(commands.router, prefix="/commands", tags=["commands"])

# Include infrastructure endpoints (consolidated - includes health, rate-limiting, usage)
api_router.include_router(infrastructure.router, prefix="/system", tags=["system"])

# Include integration endpoints (consolidated - includes canvas, calendar, email, settings)
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])

# Include user management endpoints (consolidated)
api_router.include_router(users.router, prefix="/user-management", tags=["user-management"])

# Include payment endpoints (consolidated)
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])

# Include unified agent endpoints
api_router.include_router(agent.router, prefix="/agents", tags=["agents"])

# Include task management endpoints (consolidated)
api_router.include_router(tasks.router, tags=["tasks"])

# Include scheduler endpoints
api_router.include_router(scheduler_router, tags=["scheduling"])

# Include calendar endpoints (consolidated - includes timeblocks and webhooks)
api_router.include_router(calendar.router, tags=["calendar"])

# Include briefings endpoints
api_router.include_router(briefings.router, prefix="/briefings", tags=["briefings"])

# Include gates endpoints
api_router.include_router(gates.router, prefix="/gates", tags=["gates"])

# Include admin endpoints (consolidated)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# Include focus endpoints (consolidated - includes pomodoro, sessions, entity-matching)
api_router.include_router(focus.router, tags=["focus"])
