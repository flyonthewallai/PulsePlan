"""
PulsePlan FastAPI Application
Main application entry point with startup/shutdown events
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console to handle Unicode characters
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Load environment variables FIRST, before any other imports
load_dotenv()

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import socketio
import asyncio
import time

from app.api.v1.api import api_router
from app.config.core.settings import get_settings
from app.services.auth.token_refresh import token_refresh_service
from app.core.infrastructure.websocket import websocket_manager


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set more detailed logging for LLM services
logging.getLogger('app.core.llm').setLevel(logging.INFO)
logging.getLogger('app.agents.core.llm_service').setLevel(logging.INFO)

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
        # Initialize Redis client (optional - app can run without it)
        logger.info("Initializing Redis client...")
        try:
            from app.config.cache.redis_client import get_redis_client
            redis_client = await get_redis_client()
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.warning(f"Redis initialization failed (app will continue without Redis): {e}")
        
        # Start background services
        logger.info("Starting background token refresh service...")
        try:
            await token_refresh_service.start_background_refresh()
            logger.info("Token refresh service started")
        except Exception as e:
            logger.warning(f"Token refresh service failed to start: {e}")
        
        # Start timezone-aware scheduler for briefings
        logger.info("Starting timezone-aware scheduler...")
        try:
            from app.workers.scheduling.timezone_scheduler import get_timezone_scheduler
            timezone_scheduler = get_timezone_scheduler()
            await timezone_scheduler.start()
            
            # Store scheduler in app state for cleanup
            app.state.timezone_scheduler = timezone_scheduler
            logger.info("Timezone scheduler started")
        except Exception as e:
            logger.warning(f"Timezone scheduler failed to start: {e}")
        
        # Dialog system removed - replaced by unified agent system
        logger.info("Using unified agent system (dialog system deprecated)")

        # Additional startup tasks can be added here
        logger.info("Application startup completed successfully")
        
        yield  # Application runs here
        
    finally:
        # Shutdown
        logger.info("Shutting down PulsePlan application...")
        
        try:
            # Stop background services
            logger.info("Stopping background token refresh service...")
            try:
                await token_refresh_service.stop_background_refresh()
                logger.info("Token refresh service stopped")
            except Exception as e:
                logger.warning(f"Error stopping token refresh service: {e}")
            
            # Stop timezone scheduler
            logger.info("Stopping timezone-aware scheduler...")
            try:
                if hasattr(app.state, 'timezone_scheduler'):
                    await app.state.timezone_scheduler.stop()
                    logger.info("Timezone scheduler stopped")
            except Exception as e:
                logger.warning(f"Error stopping timezone scheduler: {e}")
            
            # Close Redis connections
            logger.info("Closing Redis connections...")
            try:
                from app.config.cache.redis_client import close_redis_client
                await close_redis_client()
                logger.info("Redis connections closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connections: {e}")
            
            # Additional cleanup tasks can be added here
            logger.info("Application shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to add request timeouts"""
    
    def __init__(self, app, timeout: float = 120.0):
        super().__init__(app)
        self.timeout = timeout
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Different timeouts for different endpoints
            path = request.url.path
            if "/health" in path:
                timeout = 10.0  # 10 seconds for health checks
            elif "/agents/unified" in path:
                timeout = 60.0  # 60 seconds for unified agent requests
            elif "/websocket" in path:
                timeout = 300.0  # 5 minutes for websocket
            else:
                timeout = self.timeout  # Default 2 minutes
            
            # Execute request with timeout
            response = await asyncio.wait_for(
                call_next(request), 
                timeout=timeout
            )
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout ({timeout}s) for {request.url.path}")
            return Response(
                content='{"error": "Request timeout", "message": "The server took too long to respond"}',
                status_code=504,
                media_type="application/json"
            )
        except Exception as e:
            logger.error(f"Request processing error for {request.url.path}: {str(e)}")
            return Response(
                content='{"error": "Internal server error"}',
                status_code=500,
                media_type="application/json"
            )


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
    
    # Add timeout middleware first (should be first middleware)
    app.add_middleware(TimeoutMiddleware, timeout=120.0)
    
    # Setup error handlers
    from app.core.observability.error_handlers import setup_error_handlers
    setup_error_handlers(app)
    
    # Validate and setup security
    from app.core.auth.security import validate_security_config, setup_security_middleware
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