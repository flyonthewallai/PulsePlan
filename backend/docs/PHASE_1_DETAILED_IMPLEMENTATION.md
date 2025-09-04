# Phase 1: Foundation and Core Infrastructure - Detailed Implementation Guide

## Overview

Phase 1 establishes the foundational infrastructure for the FastAPI migration with a **simplified, MVP-focused approach**. This phase takes 2-3 weeks and builds exactly what you need now while maintaining clean upgrade paths for later scaling.

## Simplified Philosophy

- **Auth**: Use Supabase RLS (Row Level Security) instead of complex ABAC
- **Rate Limiting**: Simple per-user limits, not hierarchical  
- **Observability**: Structured logs + Sentry + health endpoint
- **Resilience**: API retry logic, not circuit breakers
- **Security**: Local encryption + Supabase built-in security

## Week 1: Core Infrastructure Setup

### Day 1-2: Project Structure and FastAPI Foundation

#### 1. Create FastAPI Project Structure
```bash
# Create new FastAPI project
mkdir fastapi-backend
cd fastapi-backend

# Project structure
fastapi-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Pydantic settings
│   │   ├── supabase.py         # Supabase client configuration
│   │   └── redis.py           # Redis configuration
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # Security utilities
│   │   └── dependencies.py     # FastAPI dependencies
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py            # API dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py         # API router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           ├── health.py
│   │           └── users.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── types.py           # Pydantic models for API requests/responses
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py            # Pydantic schemas
│   │   └── auth.py            # Auth schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication service
│   │   └── user.py            # User service
│   ├── security/
│   │   ├── __init__.py
│   │   ├── encryption.py      # Encryption service
│   │   ├── auth_helpers.py    # Simple auth utilities
│   │   └── token_service.py   # Token management
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── base.py           # Base workflow classes
│   │   └── nodes/            # Individual workflow nodes
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── logging.py        # Structured logging
│   │   └── health.py         # Health checks
│   └── middleware/
│       ├── __init__.py
│       ├── security.py       # Security middleware
│       └── observability.py  # Observability middleware
├── tests/
├── scripts/
├── docker/
├── requirements.txt
└── pyproject.toml
```

#### 2. Basic FastAPI Application Setup
```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.config.settings import settings
from app.config.supabase import supabase_client
from app.observability.sentry_config import setup_sentry
from app.observability.logging import setup_logging, RequestIDMiddleware
from app.observability.health import health_manager
from app.api.v1.api import api_router
from app.middleware.security import SecurityMiddleware
from app.ratelimit.simple_limiter import SimpleRateLimitMiddleware, SimpleRateLimiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting PulsePlan FastAPI application...")
    
    # Initialize monitoring (simplified approach)
    setup_logging()
    setup_sentry()  # Free tier: ~5k events/month
    
    # Initialize health checks
    await health_manager.initialize()
    
    print("✅ Application startup complete")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down application...")
    await health_manager.cleanup()
    print("✅ Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="PulsePlan API",
    description="Intelligent productivity and scheduling platform",
    version="2.0.0",
    openapi_url="/api/v1/openapi.json" if settings.ENVIRONMENT != "production" else None,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware (simplified)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RequestIDMiddleware)  # Request correlation IDs

# Simple rate limiting (optional)
if settings.ENABLE_RATE_LIMITING:
    from app.config.redis import redis_client
    rate_limiter = SimpleRateLimiter(redis_client.client)
    app.add_middleware(SimpleRateLimitMiddleware, rate_limiter=rate_limiter)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "PulsePlan API v2.0",
        "status": "operational",
        "documentation": "/docs" if settings.ENVIRONMENT != "production" else None
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        access_log=True
    )
```

#### 3. Configuration Management
```python
# app/config/settings.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "PulsePlan API"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Supabase (handles auth, RLS, and database)
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str  # For client-side auth
    SUPABASE_SERVICE_KEY: str  # For server-side operations
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 20
    
    # Encryption (Local only for Phase 1)
    MASTER_ENCRYPTION_KEY: str  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    ENCRYPTION_KEY_VERSION: int = 1
    
    # OAuth Providers
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    
    # Observability
    SENTRY_DSN: Optional[str] = None
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    HONEYCOMB_API_KEY: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # Rate Limiting (simplified)
    ENABLE_RATE_LIMITING: bool = False  # Simple per-user rate limiting: 60 req/min
    USER_RATE_LIMIT: int = 60  # Requests per minute per user
    ENABLE_WORKFLOWS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Day 3-4: Database and Redis Setup

#### 1. Supabase Configuration (Simplified Database + Auth)
```python
# app/config/supabase.py
from supabase import create_client, Client
from app.config.settings import settings

# Initialize Supabase client
supabase_client: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY  # Service key for server-side operations
)

# For client-side auth (frontend will use anon key)
def get_supabase_client() -> Client:
    """Get Supabase client for dependency injection"""
    return supabase_client

# Simple auth helper
async def get_current_user_from_token(authorization: str) -> dict:
    """Extract user from Supabase JWT token"""
    if not authorization.startswith("Bearer "):
        raise ValueError("Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify token with Supabase
        user_response = supabase_client.auth.get_user(token)
        if user_response.user:
            return {
                "id": user_response.user.id,
                "email": user_response.user.email,
                "is_admin": user_response.user.app_metadata.get("role") == "admin"
            }
        else:
            raise ValueError("Invalid token")
    except Exception:
        raise ValueError("Token verification failed")
```

#### 2. Enhanced Redis Configuration
```python
# app/config/redis.py
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from typing import Optional
import json
from app.config.settings import settings

class RedisClient:
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection pool"""
        self.pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        
        self.client = redis.Redis(
            connection_pool=self.pool,
            decode_responses=True
        )
        
        # Test connection
        await self.client.ping()
        print("✅ Redis connected successfully")
    
    async def close(self):
        """Close Redis connections"""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
    
    async def set_json(self, key: str, value: dict, ex: Optional[int] = None):
        """Set JSON value with optional expiration"""
        return await self.client.set(key, json.dumps(value), ex=ex)
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value"""
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

# Global Redis client instance
redis_client = RedisClient()

# Dependency for FastAPI
async def get_redis() -> redis.Redis:
    return redis_client.client
```

#### 3. Simple Auth Middleware (Uses Supabase RLS)
```python
# app/auth/simple_auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config.supabase import get_current_user_from_token
from typing import Optional

security = HTTPBearer()

class CurrentUser:
    def __init__(self, user_id: str, email: str, is_admin: bool = False):
        self.user_id = user_id
        self.email = email
        self.is_admin = is_admin

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """Get current user from Supabase JWT token"""
    try:
        user_data = await get_current_user_from_token(f"Bearer {credentials.credentials}")
        return CurrentUser(
            user_id=user_data["id"],
            email=user_data["email"],
            is_admin=user_data.get("is_admin", False)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_admin(current_user: CurrentUser = Depends(get_current_user)):
    """Require admin role"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Simple ownership check helper
def check_user_access(resource_user_id: str, current_user: CurrentUser):
    """Check if user can access resource (owns it or is admin)"""
    if resource_user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - you can only access your own data"
        )

# Supabase table schemas (managed via Supabase dashboard)
# Note: These are managed in Supabase dashboard, not code-based migrations

# oauth_tokens table (simplified):
# - id (uuid, primary key)
# - user_id (uuid, references auth.users)
# - provider (text: 'google', 'microsoft', 'canvas', 'notion')
# - encrypted_access_token (text)
# - encrypted_refresh_token (text, nullable)
# - expires_at (timestamptz, nullable)  
# - created_at (timestamptz, default now())
# - updated_at (timestamptz, default now())

# RLS Policy examples for oauth_tokens:
# CREATE POLICY "Users can access their own tokens" ON oauth_tokens
# FOR ALL USING (auth.uid() = user_id);

# CREATE POLICY "Admins can access all tokens" ON oauth_tokens  
# FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
```

### Day 5-7: Security Infrastructure

#### 1. Encryption Service Implementation (Local Only for Phase 1)
```python
# app/security/encryption.py
from cryptography.fernet import Fernet
import hashlib
import base64
import os
from typing import Optional
from app.config.settings import settings

class EncryptionService:
    def __init__(self):
        self.master_key = settings.MASTER_ENCRYPTION_KEY.encode()
        self.key_version = settings.ENCRYPTION_KEY_VERSION
        
        # For Phase 1: Always use local encryption
        print("✅ Local encryption service initialized")
    
    def derive_user_key(self, user_id: str, version: Optional[int] = None) -> bytes:
        """Derive user-specific encryption key using PBKDF2"""
        version = version or self.key_version
        salt = f"pulseplan:user:{user_id}:v{version}".encode()
        
        # Use PBKDF2 with 100,000 iterations (OWASP recommended)
        return hashlib.pbkdf2_hmac('sha256', self.master_key, salt, 100000)
    
    def encrypt_token(self, token: str, user_id: str) -> str:
        """Encrypt token with user-specific key (local only for Phase 1)"""
        return self._encrypt_locally(token, user_id)
    
    def decrypt_token(self, encrypted_token: str, user_id: str) -> str:
        """Decrypt token with appropriate method"""
        if encrypted_token.startswith("kms:"):
            # KMS tokens exist but not supported in Phase 1
            raise ValueError("KMS decryption not implemented in Phase 1")
        else:
            return self._decrypt_locally(encrypted_token, user_id)
    
    def _encrypt_locally(self, token: str, user_id: str) -> str:
        """Encrypt using local Fernet (AES-128 + HMAC)"""
        try:
            user_key = self.derive_user_key(user_id)
            # Fernet requires 32 bytes base64url-encoded key
            fernet = Fernet(base64.urlsafe_b64encode(user_key[:32]))
            
            encrypted = fernet.encrypt(token.encode())
            return f"v{self.key_version}:{encrypted.decode()}"
            
        except Exception as e:
            raise ValueError(f"Local encryption failed: {e}")
    
    def _decrypt_locally(self, encrypted_token: str, user_id: str) -> str:
        """Decrypt using local Fernet"""
        try:
            # Parse version and encrypted data
            if ':' not in encrypted_token:
                raise ValueError("Invalid token format")
            
            version_str, encrypted_data = encrypted_token.split(':', 1)
            
            if not version_str.startswith('v'):
                raise ValueError("Invalid version format")
            
            version = int(version_str[1:])  # Remove 'v' prefix
            
            # Derive key for the specific version
            user_key = self.derive_user_key(user_id, version)
            fernet = Fernet(base64.urlsafe_b64encode(user_key[:32]))
            
            # Decrypt and return
            decrypted = fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
            
        except Exception as e:
            # Don't leak details in error messages
            raise ValueError(f"Token decryption failed")
    
    def rotate_key_version(self, new_version: int):
        """Update key version (for future key rotation)"""
        self.key_version = new_version
        print(f"🔄 Encryption key version updated to v{new_version}")
    
    # KMS methods (stubbed for Phase 1, ready for Phase 2+)
    def _encrypt_with_kms(self, token: str, user_id: str) -> str:
        """KMS encryption (stubbed for Phase 1)"""
        raise NotImplementedError(
            "KMS encryption will be implemented in Phase 2. "
            "Set USE_KMS=false in settings for Phase 1."
        )
    
    def _decrypt_with_kms(self, encrypted_token: str, user_id: str) -> str:
        """KMS decryption (stubbed for Phase 1)"""
        raise NotImplementedError(
            "KMS decryption will be implemented in Phase 2. "
            "Existing KMS tokens need migration."
        )
    
    def health_check(self) -> bool:
        """Test encryption/decryption works"""
        try:
            test_user = "health-check-user"
            test_token = "test-token-123"
            
            encrypted = self.encrypt_token(test_token, test_user)
            decrypted = self.decrypt_token(encrypted, test_user)
            
            return decrypted == test_token
        except Exception:
            return False

# Global encryption service
encryption_service = EncryptionService()
```

#### 2. Simple Rate Limiting (Optional)
```python
# app/ratelimit/simple_limiter.py
import redis.asyncio as redis
import time
import json
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class SimpleRateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_rate_limit(self, user_id: str, limit: int = 60, window: int = 60) -> bool:
        """Simple rate limit: X requests per minute per user"""
        key = f"rate_limit:{user_id}"
        
        try:
            # Use Redis sliding window counter
            now = time.time()
            pipeline = self.redis.pipeline()
            
            # Remove old entries (outside window)
            pipeline.zremrangebyscore(key, 0, now - window)
            
            # Count current entries
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(now): now})
            
            # Set expiration
            pipeline.expire(key, window)
            
            results = await pipeline.execute()
            current_count = results[1]  # Count from zcard
            
            return current_count < limit
            
        except Exception as e:
            # Fail open on Redis errors
            print(f"Rate limiting error: {e}")
            return True

class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limiter: SimpleRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request, call_next):
        # Extract user ID from Authorization header
        user_id = await self._extract_user_id(request)
        
        if user_id:
            allowed = await self.rate_limiter.check_rate_limit(user_id, limit=60, window=60)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded: 60 requests per minute"}
                )
        
        response = await call_next(request)
        return response
    
    async def _extract_user_id(self, request) -> Optional[str]:
        """Extract user ID from Authorization header"""
        try:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                from app.config.supabase import get_current_user_from_token
                user_data = await get_current_user_from_token(auth_header)
                return user_data["id"]
        except Exception:
            pass
        return None
```

## Week 2: Observability and Middleware

### Day 8-10: Monitoring Setup (Simplified Approach)

#### 1. Error Tracking with Sentry (Free Tier)
```python
# app/observability/sentry_config.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from app.config.settings import settings

def setup_sentry():
    """Initialize Sentry error tracking (Free tier: ~5k events/month)"""
    if not settings.SENTRY_DSN:
        print("⚠️  Sentry DSN not configured")
        return
    
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        # Conservative sampling for free tier
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        
        integrations=[
            FastApiIntegration(auto_enabling_integrations=False),
            RedisIntegration(),
        ],
        
        before_send=filter_sensitive_data,
        send_default_pii=False,
        attach_stacktrace=True,
    )
    
    print("✅ Sentry initialized (free tier)")

def filter_sensitive_data(event, hint):
    """Filter sensitive data from Sentry events"""
    if 'request' in event:
        request = event['request']
        if 'headers' in request:
            headers = request['headers']
            if 'authorization' in headers:
                headers['authorization'] = '[Filtered]'
    return event
```


#### 3. Structured Logging with Request IDs
```python
# app/observability/logging.py
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.service_name = "pulseplan-api"
    
    def _create_log_entry(self, level: str, message: str, 
                         context: Optional[Dict[str, Any]] = None,
                         user_id: Optional[str] = None,
                         request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create structured log entry with correlation IDs"""
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "service": self.service_name,
            "logger": self.logger.name,
            # Get IDs from context or parameters
            "request_id": request_id or request_id_var.get(),
            "user_id": user_id or user_id_var.get(),
        }
        
        # Remove empty fields
        entry = {k: v for k, v in entry.items() if v}
        
        if context:
            entry["context"] = self._sanitize_log_data(context)
        
        return entry
    
    def _sanitize_log_data(self, data: Any) -> Any:
        """Remove sensitive information from logs"""
        if isinstance(data, dict):
            sanitized = {}
            sensitive_keys = ['password', 'token', 'secret', 'key', 'credential']
            
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_log_data(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_log_data(item) for item in data]
        return data
    
    def info(self, message: str, **kwargs):
        entry = self._create_log_entry("INFO", message, **kwargs)
        self.logger.info(json.dumps(entry))
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        entry = self._create_log_entry("ERROR", message, **kwargs)
        
        if exception:
            entry["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception)
            }
        
        self.logger.error(json.dumps(entry))
    
    def warning(self, message: str, **kwargs):
        entry = self._create_log_entry("WARNING", message, **kwargs)
        self.logger.warning(json.dumps(entry))

# Request ID middleware
class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Generate or extract request ID
            headers = dict(scope.get("headers", []))
            request_id = headers.get(b"x-request-id", str(uuid.uuid4()).encode()).decode()
            
            # Set in context
            request_id_var.set(request_id)
            
            # Add to response headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = message.get("headers", [])
                    headers.append([b"x-request-id", request_id.encode()])
                    message["headers"] = headers
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

def setup_logging():
    """Setup JSON structured logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',  # JSON will be the message
        handlers=[logging.StreamHandler()]
    )
    
    # Reduce noise from libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

```

### Day 11-14: Health Checks and API Endpoints

#### 1. Simple Health Check System (Week 2 Focus)
```python
# app/observability/health.py
from datetime import datetime
import asyncio

class SimpleHealthManager:
    def __init__(self):
        self.startup_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize health checks (minimal setup for Week 2)"""
        print("✅ Simple health checks initialized")
    
    async def basic_health(self) -> dict:
        """Basic health check - just return 200 OK"""
        return {
            "status": "healthy", 
            "timestamp": datetime.utcnow().isoformat(),
            "service": "pulseplan-api"
        }
    
    async def dependency_health(self) -> dict:
        """Check Redis + Database connectivity"""
        checks = {}
        overall_healthy = True
        
        # Check Redis
        try:
            from app.config.redis import redis_client
            await asyncio.wait_for(redis_client.client.ping(), timeout=3)
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {str(e)}"
            overall_healthy = False
        
        # Check Supabase  
        try:
            from app.config.supabase import supabase_client
            # Simple query to test Supabase connection
            result = supabase_client.table('oauth_tokens').select("count", count="exact").limit(1).execute()
            checks["supabase"] = "ok"
        except Exception as e:
            checks["supabase"] = f"error: {str(e)}"
            overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
            "checks": checks
        }
    
    async def readiness_check(self) -> bool:
        """Kubernetes readiness check - returns True/False"""
        try:
            result = await self.dependency_health()
            return result["status"] == "healthy"
        except Exception:
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        pass

# Global health manager (simplified for Week 2)
health_manager = SimpleHealthManager()

# Note: The robust HealthManager from the original design can be added in Phase 2+
# when you need detailed per-check timeouts, degraded states, and comprehensive monitoring
```

### Day 11-14: Middleware and Basic Endpoints

#### 1. Security Middleware
```python
# app/middleware/security.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
# Simple security middleware - no complex policy engine needed

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        
        return response
```

#### 2. Simple Health Check Endpoints 
```python
# app/api/v1/endpoints/health.py
from fastapi import APIRouter, HTTPException
from app.observability.health import health_manager

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check - always returns 200 OK"""
    return await health_manager.basic_health()

@router.get("/health/detailed") 
async def detailed_health_check():
    """Check Redis + Database connectivity"""
    return await health_manager.dependency_health()

@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness check"""
    is_ready = await health_manager.readiness_check()
    
    if not is_ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "ready"}
```

#### 3. Example API Endpoints with Supabase RLS
```python
# app/api/v1/endpoints/tokens.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth.simple_auth import get_current_user, CurrentUser
from app.config.supabase import get_supabase_client
from app.security.encryption import encryption_service

router = APIRouter()

@router.get("/tokens")
async def get_user_tokens(
    current_user: CurrentUser = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Get user's OAuth tokens - Supabase RLS automatically filters by user"""
    
    # RLS policy ensures user only sees their own tokens
    result = supabase.table('oauth_tokens').select('*').execute()
    
    # Decrypt tokens for response
    tokens = []
    for token_row in result.data:
        decrypted_token = encryption_service.decrypt_token(
            token_row['encrypted_access_token'], 
            current_user.user_id
        )
        
        tokens.append({
            'id': token_row['id'],
            'provider': token_row['provider'],
            'expires_at': token_row['expires_at'],
            'created_at': token_row['created_at']
            # Note: Never return actual tokens in API responses
        })
    
    return {"tokens": tokens}

@router.post("/tokens")
async def store_oauth_token(
    provider: str,
    access_token: str,
    refresh_token: str = None,
    expires_at: str = None,
    current_user: CurrentUser = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Store OAuth token - RLS ensures it's stored with correct user_id"""
    
    # Encrypt tokens
    encrypted_access = encryption_service.encrypt_token(access_token, current_user.user_id)
    encrypted_refresh = encryption_service.encrypt_token(refresh_token, current_user.user_id) if refresh_token else None
    
    # Insert with RLS - user_id automatically set by auth.uid()
    result = supabase.table('oauth_tokens').upsert({
        'user_id': current_user.user_id,  # RLS will verify this matches auth.uid()
        'provider': provider,
        'encrypted_access_token': encrypted_access,
        'encrypted_refresh_token': encrypted_refresh,
        'expires_at': expires_at
    }).execute()
    
    return {"message": "Token stored successfully", "id": result.data[0]['id']}

# Supabase RLS policies (set up in Supabase dashboard):
# 
# -- Users can only access their own tokens
# CREATE POLICY "Users own their tokens" ON oauth_tokens
# FOR ALL USING (auth.uid() = user_id);
# 
# -- Admins can access all tokens  
# CREATE POLICY "Admins access all tokens" ON oauth_tokens
# FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
```

## Phase 1 Deliverables and Success Criteria

### Deliverables (Simplified for MVP)
1. ✅ **FastAPI Application Structure** - Clean, organized project setup
2. ✅ **Supabase Integration** - Auth, RLS, and database via Supabase client
3. ✅ **Redis Configuration** - Simple connection for rate limiting and caching
4. ✅ **Encryption Service** - Local Fernet encryption for OAuth tokens
5. ✅ **Simple Auth System** - JWT token validation with Supabase RLS
6. ✅ **Rate Limiting** - Optional per-user rate limiting (60 req/min)
7. ✅ **Sentry Integration** - Error tracking (free tier: ~5k events/month)
8. ✅ **Structured Logging** - JSON logs with request IDs and user context
9. ✅ **Security Middleware** - Basic security headers and CORS
10. ✅ **Health Checks** - Simple Redis + Supabase connectivity checks

### Success Criteria (Simplified)
- [ ] Application starts successfully without errors
- [ ] Supabase client connects and can query tables
- [ ] Redis connectivity works for rate limiting
- [ ] Token encryption/decryption functions correctly
- [ ] Supabase JWT tokens are validated correctly
- [ ] RLS policies enforce user data access
- [ ] Rate limiting works (if enabled) - 60 req/min per user
- [ ] Sentry captures and filters errors appropriately
- [ ] Structured logs contain request IDs and user context
- [ ] Health checks return 200 for /health and /ready endpoints
- [ ] Security headers are present in responses

### Testing Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Set up Supabase tables (via Supabase dashboard or SQL editor)
# Note: Database schema is managed through Supabase dashboard, not code migrations

# Start application
uvicorn app.main:app --reload

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health/detailed

# Test Supabase connection
python -c "from app.config.supabase import supabase_client; print('✅ Supabase test:', supabase_client.table('oauth_tokens').select('count', count='exact').limit(1).execute())"

# Test encryption service (local only)
python -c "from app.security.encryption import encryption_service; print('✅ Encryption test:', encryption_service.health_check())"

# Quick smoke tests during development
pytest -q --disable-warnings --maxfail=1

# Run specific test modules
python -m pytest tests/test_auth.py
python -m pytest tests/test_rate_limiting.py

# Full test suite with coverage
pytest --cov=app --cov-report=term-missing
```

### Next Steps for Phase 2
1. **Token Refresh Service** - Implement centralized token management
2. **Rate Limiting System** - Add hierarchical rate limiting
3. **Basic Workflow Engine** - Set up LangGraph foundation
4. **Authentication Endpoints** - OAuth flow implementation
5. **Cache Service** - Multi-level caching with invalidation

This foundation provides the robust infrastructure needed for the remaining phases of the migration.