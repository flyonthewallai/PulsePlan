# PulsePlan FastAPI Backend

A modern, secure FastAPI backend for the PulsePlan productivity application, featuring intelligent scheduling, OAuth integrations, and comprehensive observability.

## Features

### Core Infrastructure
- **FastAPI Framework** - Modern, fast web framework with automatic API documentation
- **AES-256-GCM Encryption** - Enhanced token encryption with KMS-ready architecture
- **JWT Authentication** - Direct JWT verification using Supabase patterns
- **Redis Caching** - Upstash-compatible caching with connection pooling
- **Supabase Integration** - Row Level Security (RLS) enabled database operations

### Security & Observability
- **Structured Logging** - JSON logs with request correlation IDs
- **Sentry Integration** - Error tracking with sensitive data filtering
- **Rate Limiting** - Redis-based sliding window rate limiting
- **Security Headers** - Comprehensive HTTP security headers
- **Health Monitoring** - Kubernetes-ready health, readiness, and liveness probes

### OAuth Token Management
- **Multi-Provider Support** - Google, Microsoft, Canvas, Notion integrations
- **Automatic Token Refresh** - Background token refresh with validation
- **Encrypted Storage** - User-specific encryption keys with version management
- **Cache Integration** - Redis-based token caching for performance

## Quick Start

### Prerequisites
- Python 3.9+
- Redis (local or Upstash)
- Supabase project
- Environment variables configured

### Installation

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   # Development
   uvicorn app.main:app --reload --port 8000
   
   # Production
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

### Configuration

Key environment variables:

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret
TOKEN_ENCRYPTION_KEY=your-encryption-key
SECRET_KEY=your-secret-key

# OAuth Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# Optional
REDIS_URL=redis://localhost:6379
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
SENTRY_DSN=your-sentry-dsn
ENABLE_RATE_LIMITING=false
```

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

## Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /api/v1/health/health` - Detailed health with dependencies
- `GET /api/v1/health/ready` - Kubernetes readiness probe
- `GET /api/v1/health/live` - Kubernetes liveness probe

### OAuth Token Management
- `GET /api/v1/tokens/connections` - List user's OAuth connections
- `GET /api/v1/tokens/connections/status` - Connection status for all providers
- `GET /api/v1/tokens/tokens` - Get user tokens for agent use
- `POST /api/v1/tokens/connections/{provider}` - Store OAuth connection
- `DELETE /api/v1/tokens/connections/{provider}` - Remove OAuth connection

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_health.py

# Run with verbose output
pytest -v
```

## Database Schema

The backend uses the existing `calendar_connections` table with RLS policies:

```sql
-- Table structure (managed in Supabase)
calendar_connections:
- id (uuid, primary key)
- user_id (uuid, references auth.users)
- provider (text: 'google', 'microsoft', 'canvas', 'notion')
- access_token (text, encrypted)
- refresh_token (text, encrypted, nullable)
- expires_at (timestamptz, nullable)
- scopes (text[], default [])
- email (text, nullable)
- created_at (timestamptz, default now())
- updated_at (timestamptz, default now())

-- RLS Policies
CREATE POLICY "Users own their connections" ON calendar_connections
FOR ALL USING (auth.uid() = user_id);
```

## Architecture

### Encryption
- **Phase 1**: Local AES-256-GCM encryption with user-specific keys
- **Phase 2+**: AWS KMS integration (stubbed, ready for implementation)
- **Key Derivation**: PBKDF2 with 100,000 iterations (OWASP recommended)
- **Format**: `v{version}:{iv}:{auth_tag}:{encrypted_data}`

### Middleware Stack
1. **SecurityMiddleware** - HTTP security headers
2. **AuthMiddleware** - JWT authentication (optional)
3. **RequestLoggingMiddleware** - HTTP request/response logging
4. **RequestIDMiddleware** - Request correlation IDs
5. **RateLimitMiddleware** - Redis-based rate limiting (optional)

### Caching Strategy
- **Token Cache**: 5-minute TTL for user tokens
- **Connection Cache**: Automatic invalidation on updates
- **Rate Limiting**: Sliding window with Redis sorted sets

## Deployment

### Docker
```bash
# Build image
docker build -t pulseplan-api .

# Run container
docker run -p 8000:8000 --env-file .env pulseplan-api
```

### Kubernetes
The application includes health check endpoints for Kubernetes deployments:

```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health/live
    port: 8000
readinessProbe:
  httpGet:
    path: /api/v1/health/ready
    port: 8000
```

## Migration from Node.js

This FastAPI backend maintains API compatibility with the existing Node.js backend:

- **Same JWT verification** using `SUPABASE_JWT_SECRET`
- **Same database schema** with `calendar_connections` table
- **Same encryption patterns** (enhanced to AES-256-GCM)
- **Compatible OAuth flows** for all providers
- **Matching endpoint patterns** for seamless migration

## Development

### Project Structure
```
backend/
├── app/
│   ├── api/v1/endpoints/     # API endpoints
│   ├── config/               # Configuration modules
│   ├── core/                 # Core functionality (auth, etc.)
│   ├── middleware/           # Custom middleware
│   ├── models/               # Pydantic models
│   ├── observability/        # Logging, monitoring
│   ├── security/             # Encryption, security
│   └── services/             # Business logic
├── tests/                    # Test suite
└── requirements.txt          # Dependencies
```

### Code Quality
```bash
# Format code
black app/ tests/

# Lint code
ruff app/ tests/

# Type checking
mypy app/
```

## Contributing

1. Create virtual environment and install dependencies
2. Copy `.env.example` to `.env` and configure
3. Run tests to ensure everything works
4. Make changes and add tests
5. Run linting and formatting
6. Submit pull request

## License

MIT License - see existing project license.