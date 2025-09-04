from fastapi import APIRouter
from app.api.v1.endpoints import health, tokens, agents, token_refresh, rate_limiting, oauth, users, email, contacts, user_preferences, subscriptions
from app.scheduler.api import scheduler_router

api_router = APIRouter()

# Include health check endpoints
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Include token/connection endpoints
api_router.include_router(tokens.router, prefix="/tokens", tags=["tokens"])

# Include OAuth authentication endpoints
api_router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])

# Include email management endpoints
api_router.include_router(email.router, prefix="/email", tags=["email"])

# Include contacts endpoints
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])

# Include user preferences endpoints
api_router.include_router(user_preferences.router, prefix="/user", tags=["user-preferences"])

# Include token refresh endpoints
api_router.include_router(token_refresh.router, prefix="/token-refresh", tags=["token-refresh"])

# Include rate limiting endpoints
api_router.include_router(rate_limiting.router, prefix="/rate-limiting", tags=["rate-limiting"])

# Include agent endpoints
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])

# Include agent endpoints with frontend compatibility prefix
api_router.include_router(agents.router, prefix="/agent", tags=["agent-compat"])

# Include user endpoints (at root level to match frontend expectations)
api_router.include_router(users.router, prefix="", tags=["users"])

# Include scheduler endpoints
api_router.include_router(scheduler_router, tags=["scheduling"])

# Include subscription endpoints
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])