"""
Main User Management Router
Consolidates all user-related endpoints
"""
from fastapi import APIRouter

# Import individual routers
from .users import router as users_router
from .contacts import router as contacts_router
from .preferences import router as preferences_router
from .subscriptions import router as subscriptions_router

# Create main user management router
router = APIRouter()

# Include sub-routers with appropriate prefixes
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(contacts_router, prefix="/contacts", tags=["contacts"])
router.include_router(preferences_router, prefix="/preferences", tags=["user-preferences"])
router.include_router(subscriptions_router, prefix="/subscriptions", tags=["subscriptions"])