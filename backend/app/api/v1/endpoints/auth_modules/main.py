"""
Main Auth Router
Consolidates all authentication-related endpoints
"""
from fastapi import APIRouter

# Import individual routers
from .oauth import router as oauth_router
from .tokens import router as tokens_router
from .token_refresh import router as token_refresh_router

# Create main auth router
router = APIRouter()

# Include sub-routers with appropriate prefixes
router.include_router(oauth_router, prefix="/oauth", tags=["oauth"])
router.include_router(tokens_router, prefix="/tokens", tags=["tokens"])
router.include_router(token_refresh_router, prefix="/token-refresh", tags=["token-refresh"])