from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.config.core.settings import settings
from app.config.database.supabase import supabase_client
from app.config.redis import redis_client
from app.security.encryption import encryption_service

# Import middleware and routers
from app.middleware.security import SecurityMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limiting import RateLimitMiddleware
from app.observability.logging import RequestIDMiddleware, RequestLoggingMiddleware, setup_logging
from app.observability.sentry_config import setup_sentry
from app.observability.health import health_manager
from app.api.v1.api import api_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting PulsePlan FastAPI application...")
    
    # Initialize observability
    setup_logging()
    setup_sentry()
    
    # Initialize health manager
    await health_manager.initialize()
    
    # Initialize Redis connection
    try:
        await redis_client.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        # Continue without Redis for development
    
    # Test encryption service
    if encryption_service.health_check():
        logger.info("Encryption service health check passed")
    else:
        logger.error("Encryption service health check failed")
    
    # Test Supabase connection
    if supabase_client.is_available():
        logger.info("Supabase client is available")
    else:
        logger.warning("Supabase client not available")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Close Redis connection
    try:
        await redis_client.close()
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")
    
    # Cleanup health manager
    await health_manager.cleanup()
    
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="PulsePlan API",
    description="Intelligent productivity and scheduling platform - FastAPI Backend",
    version="2.0.0",
    openapi_url="/api/v1/openapi.json" if settings.ENVIRONMENT != "production" else None,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Custom middleware (order matters - last added is executed first)
app.add_middleware(SecurityMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# Rate limiting middleware (optional)
if settings.ENABLE_RATE_LIMITING:
    app.add_middleware(RateLimitMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "PulsePlan API v2.0 - FastAPI Backend",
        "status": "operational",
        "documentation": "/docs" if settings.ENVIRONMENT != "production" else None,
        "environment": settings.ENVIRONMENT
    }

# Legacy health check endpoint (redirects to new API)
@app.get("/health")
async def legacy_health_check():
    """Legacy health check endpoint"""
    return await health_manager.basic_health()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        access_log=True
    )

