"""
PulsePlan FastAPI Application
Main application entry point with startup/shutdown events
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables FIRST, before any other imports
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import socketio

from app.api.v1.api import api_router
from app.config.settings import get_settings
from app.services.token_refresh import token_refresh_service
from app.core.websocket import websocket_manager


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Log environment variable loading status
logger.info(f"Environment loaded - OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")
if os.getenv('OPENAI_API_KEY'):
    logger.info(f"OPENAI_API_KEY starts with: {os.getenv('OPENAI_API_KEY')[:15]}...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting PulsePlan FastAPI application...")
    
    try:
        # Initialize Redis client first
        logger.info("Initializing Redis client...")
        from app.config.redis_client import get_redis_client
        redis_client = await get_redis_client()
        
        # Start background services
        logger.info("Starting background token refresh service...")
        await token_refresh_service.start_background_refresh()
        
        # Start timezone-aware scheduler for briefings
        logger.info("Starting timezone-aware scheduler...")
        from app.workers.timezone_scheduler import get_timezone_scheduler
        timezone_scheduler = get_timezone_scheduler()
        await timezone_scheduler.start()
        
        # Store scheduler in app state for cleanup
        app.state.timezone_scheduler = timezone_scheduler
        
        # Additional startup tasks can be added here
        logger.info("Application startup completed successfully")
        
        yield  # Application runs here
        
    finally:
        # Shutdown
        logger.info("Shutting down PulsePlan application...")
        
        try:
            # Stop background services
            logger.info("Stopping background token refresh service...")
            await token_refresh_service.stop_background_refresh()
            
            # Stop timezone scheduler
            logger.info("Stopping timezone-aware scheduler...")
            if hasattr(app.state, 'timezone_scheduler'):
                await app.state.timezone_scheduler.stop()
            
            # Close Redis connections
            logger.info("Closing Redis connections...")
            from app.config.redis_client import close_redis_client
            await close_redis_client()
            
            # Additional cleanup tasks can be added here
            logger.info("Application shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="PulsePlan API",
        description="Intelligent productivity assistant with LangGraph workflows",
        version="2.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan
    )
    
    # Setup error handlers
    from app.core.error_handlers import setup_error_handlers
    setup_error_handlers(app)
    
    # Validate and setup security
    from app.core.security import validate_security_config, setup_security_middleware
    validate_security_config()
    setup_security_middleware(app)
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Add health check endpoint at root
    @app.get("/")
    async def root():
        """Root endpoint for basic health check"""
        return {
            "message": "PulsePlan API is running",
            "version": "2.0.0",
            "status": "healthy"
        }
    
    # Add WebSocket status endpoint
    @app.get("/api/v1/websocket/stats")
    async def websocket_stats():
        """Get WebSocket manager statistics"""
        return websocket_manager.get_stats()
    
    # Mount Socket.IO app for WebSocket support
    sio_app = socketio.ASGIApp(websocket_manager.sio, app)
    
    return sio_app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )