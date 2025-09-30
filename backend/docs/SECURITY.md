# PulsePlan Security Documentation

## Overview

PulsePlan implements enterprise-grade security measures to protect user data, authentication tokens, and system integrity. This document outlines our comprehensive security architecture and implementation details.

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Data Encryption](#data-encryption)
3. [Token Management](#token-management)
4. [Rate Limiting](#rate-limiting)
5. [Audit Logging](#audit-logging)
6. [Cache Security](#cache-security)
7. [API Security](#api-security)
8. [Database Security](#database-security)
9. [Security Monitoring](#security-monitoring)
10. [Deployment Security](#deployment-security)
11. [Security Best Practices](#security-best-practices)
12. [Incident Response](#incident-response)

---

## Authentication & Authorization

### JWT Token-Based Authentication

PulsePlan uses JSON Web Tokens (JWT) for stateless authentication:

```python
# Location: app/core/auth.py
- Secure token generation with configurable expiration
- Token refresh mechanism with rotation
- Automatic token validation on protected endpoints
- User context extraction from validated tokens
```

**Security Features:**
- **Algorithm**: RS256 (RSA with SHA-256)
- **Token Expiration**: Configurable (default: 24 hours)
- **Refresh Tokens**: Secure rotation with revocation
- **Claims Validation**: Issuer, audience, and expiration checks

### OAuth Integration Security

Secure OAuth 2.0 implementation for third-party services:

```python
# Location: app/services/token_service.py
- Encrypted OAuth token storage
- Automatic token refresh with error handling
- Scope validation and permission checks
- Provider-specific security configurations
```

**Supported Providers:**
- **Google**: Gmail, Calendar, Drive integration
- **Microsoft**: Outlook, Calendar, Graph API access
- **Custom OIDC**: Extensible for enterprise SSO

---

## Data Encryption

### AWS KMS Integration

Enterprise-grade encryption using AWS Key Management Service:

```python
# Location: app/security/encryption.py
class EncryptionService:
    def _encrypt_with_kms(self, plaintext_token: str, user_id: str) -> str:
        """Encrypt using AWS KMS with encryption context"""
        
    def _decrypt_with_kms(self, encrypted_token: str, user_id: str) -> str:
        """Decrypt with context validation and error handling"""
```

**KMS Security Features:**
- **Customer-Managed Keys**: Full control over encryption keys
- **Encryption Context**: User-specific context for additional security
- **Audit Trail**: All KMS operations logged in CloudTrail
- **Key Rotation**: Automatic yearly key rotation support
- **Regional Isolation**: Keys restricted to specific AWS regions

### Fallback Encryption (Fernet)

Symmetric encryption fallback when KMS is unavailable:

```python
# Fernet encryption with secure key derivation
- 256-bit AES encryption in CBC mode
- HMAC authentication for integrity
- Secure random key generation
- Key versioning for rotation support
```

### Configuration

```bash
# Environment Variables
USE_KMS=true                              # Enable KMS encryption
KMS_KEY_ID=alias/pulseplan-encryption     # KMS key identifier
ENCRYPTION_FALLBACK_TO_FERNET=true        # Allow fallback
FERNET_KEY_VERSION=1                      # Key rotation support
```

---

## Token Management

### OAuth Token Security

Comprehensive OAuth token lifecycle management:

```python
# Location: app/services/token_service.py
class TokenService:
    async def store_tokens(self, user_id: str, provider: str, tokens: OAuthTokens):
        """Securely store encrypted OAuth tokens"""
        
    async def refresh_token_if_needed(self, user_id: str, provider: str):
        """Automatic token refresh with error handling"""
```

**Security Measures:**
- **Encryption at Rest**: All tokens encrypted before storage
- **Automatic Refresh**: Proactive token renewal before expiration
- **Secure Deletion**: Proper token cleanup on user logout
- **Access Logging**: All token operations audited
- **Rate Limiting**: Protection against token abuse

### Token Storage Schema

```sql
-- Secure token storage in Supabase
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    provider TEXT NOT NULL,
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    scopes TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row Level Security enabled
ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;
```

---

## Rate Limiting

### Redis-Based Rate Limiting

Sophisticated rate limiting using sliding window algorithm:

```python
# Location: app/config/redis_client.py
async def check_rate_limit(
    identifier: str, 
    limit: int, 
    window_seconds: int,
    increment: int = 1
) -> Dict[str, Any]:
    """Sliding window rate limiting with sorted sets"""
```

**Rate Limiting Tiers:**
- **API Endpoints**: 1000 requests/hour per user
- **OAuth Operations**: 60 requests/hour per user
- **Email Sending**: 100 emails/day per user
- **Webhook Processing**: 500 webhooks/hour per user

### Implementation Details

```python
# Rate limiting configuration
RATE_LIMITS = {
    "api_general": {"limit": 1000, "window": 3600},
    "oauth_operations": {"limit": 60, "window": 3600}, 
    "email_send": {"limit": 100, "window": 86400},
    "webhook_process": {"limit": 500, "window": 3600}
}
```

---

## Audit Logging

### Comprehensive Audit Trail

Complete audit logging for compliance and security monitoring:

```python
# Location: app/agents/graphs/database_graph.py
async def _create_audit_log(self, state: WorkflowState, entity_type: str, operation: str):
    """Create comprehensive audit log entry"""
    
    audit_entry = {
        "id": str(uuid.uuid4()),
        "user_id": state["user_id"],
        "entity_type": entity_type,
        "operation": operation,
        "success": state["output_data"].get("success", False),
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": state.get("user_context", {}).get("ip_address"),
        "user_agent": state.get("user_context", {}).get("user_agent"),
        "request_id": state.get("request_id"),
        "workflow_id": state.get("workflow_id"),
        "affected_records": state["output_data"].get("affected_records", 0),
        "error_message": state["output_data"].get("error"),
        "input_data_hash": hash(json.dumps(state["input_data"], sort_keys=True)),
        "metadata": {
            "node_execution_time": state.get("metrics", {}).get("execution_time_ms"),
            "cache_keys_invalidated": state.get("metrics", {}).get("cache_management", {}).get("keys_invalidated", []),
            "database_queries": state.get("metrics", {}).get("database_queries", 0),
            "validation_result": state.get("metrics", {}).get("validation", {}).get("passed", True)
        }
    }
```

**Audit Coverage:**
- All CRUD operations on user data
- Authentication and authorization events
- OAuth token operations
- Email sending and webhook processing
- Cache invalidation operations
- Error events and security violations

---

## Cache Security

### Redis Security Implementation

Secure caching with automatic invalidation:

```python
# Location: app/agents/graphs/database_graph.py
async def _invalidate_cache(self, state: WorkflowState, entity_type: str, operation: str):
    """Smart cache invalidation by entity type and operation"""
    
    # User-specific cache patterns
    if entity_type == "tasks":
        keys_to_invalidate = [
            f"user_tasks:{user_id}",
            f"user_tasks:{user_id}:*",
            f"task_counts:{user_id}",
            f"user_data:{user_id}",
            f"workflow_cache:{user_id}:task_*"
        ]
```

**Cache Security Features:**
- **User Isolation**: All cache keys include user_id
- **Automatic Invalidation**: Smart invalidation on data changes
- **TTL Management**: Configurable expiration for all cached data
- **Encryption**: Sensitive data encrypted in cache
- **Access Controls**: Redis AUTH and connection encryption

### Cache Configuration

```python
# Redis security settings
REDIS_SSL_CERT_REQS = "required"
REDIS_SSL_CHECK_HOSTNAME = True
REDIS_PASSWORD = "secure-redis-password"
REDIS_MAX_CONNECTIONS = 20
REDIS_TIMEOUT = 30
```

---

## API Security

### Request Security

Comprehensive API security measures:

```python
# Security middleware and validation
- CORS configuration with allowed origins
- Request size limits (10MB default)
- Input validation and sanitization
- SQL injection prevention
- XSS protection headers
- CSRF protection for web clients
```

### Security Headers

```python
# Automatically applied security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
```

### API Rate Limiting

```python
# Endpoint-specific rate limiting
@rate_limit("api_general")
async def process_query():
    """General API endpoints"""

@rate_limit("oauth_operations")  
async def oauth_callback():
    """OAuth operations"""

@rate_limit("email_send")
async def send_email():
    """Email sending endpoints"""
```

---

## Database Security

### Supabase Security Configuration

Row-level security and access controls:

```sql
-- Row Level Security policies
CREATE POLICY "Users can only access their own data" ON tasks
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only access their own tokens" ON oauth_tokens
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only access their own audit logs" ON audit_logs
    FOR SELECT USING (auth.uid() = user_id::uuid);
```

### Database Connection Security

```python
# Secure database connections
- SSL/TLS encryption in transit
- Connection pooling with limits
- Prepared statements to prevent SQL injection
- Database credentials via environment variables
- Connection timeout and retry logic
```

---

## Security Monitoring

### Real-Time Monitoring

Comprehensive security event monitoring:

```python
# Security event detection
- Failed authentication attempts
- Unusual API usage patterns
- Rate limit violations
- Token refresh failures
- Encryption/decryption errors
- Suspicious workflow patterns
```

### Alerting Configuration

```python
# Security alerts
SECURITY_ALERTS = {
    "failed_auth_threshold": 5,           # Alert after 5 failed attempts
    "rate_limit_violations": 10,          # Alert after 10 violations/hour
    "token_refresh_failures": 3,          # Alert after 3 consecutive failures
    "encryption_errors": 1,               # Alert immediately on encryption errors
    "audit_log_failures": 1               # Alert on audit logging failures
}
```

---

## Deployment Security

### Environment Security

Secure deployment configuration:

```bash
# Production environment variables
NODE_ENV=production
DEBUG=false
LOG_LEVEL=warn

# Security-specific settings
USE_KMS=true
REQUIRE_HTTPS=true
SESSION_SECURE=true
CSRF_PROTECTION=true

# Database and cache security
DATABASE_SSL=require
REDIS_TLS=true
REDIS_AUTH_ENABLED=true
```

### Infrastructure Security

```yaml
# Docker security configuration
security_opt:
  - no-new-privileges:true
  - apparmor:docker-default

# Network security
networks:
  - pulseplan-network

# Volume security (read-only where possible)
volumes:
  - type: bind
    source: ./config
    target: /app/config
    read_only: true
```

---

## Security Best Practices

### Development Guidelines

1. **Secrets Management**
   - Never commit secrets to version control
   - Use environment variables or secret management systems
   - Rotate secrets regularly

2. **Input Validation**
   - Validate all inputs at API boundaries
   - Use Pydantic models for automatic validation
   - Sanitize data before database operations

3. **Error Handling** 
   - Don't expose internal system details in errors
   - Log security events for monitoring
   - Implement graceful degradation

4. **Dependencies**
   - Regularly update dependencies for security patches
   - Use dependency vulnerability scanning
   - Pin dependency versions in production

### Code Review Security Checklist

- [ ] Secrets and credentials properly handled
- [ ] Input validation implemented
- [ ] Error handling doesn't expose sensitive info
- [ ] Audit logging included for sensitive operations
- [ ] Rate limiting applied where appropriate
- [ ] User authorization checked
- [ ] Data encryption used for sensitive data
- [ ] SQL injection prevention verified

---

## Incident Response

### Security Incident Procedures

1. **Detection**
   - Monitor security alerts and logs
   - User reports of suspicious activity
   - Automated threat detection systems

2. **Assessment**
   - Determine scope and impact
   - Identify affected users and data
   - Classify incident severity

3. **Containment**
   - Isolate affected systems
   - Revoke compromised tokens
   - Block malicious IP addresses

4. **Recovery**
   - Restore from secure backups
   - Update security measures
   - Re-encrypt compromised data

5. **Post-Incident**
   - Document lessons learned
   - Update security procedures
   - Notify affected users if required

### Emergency Contacts

```bash
# Security team contacts
SECURITY_EMAIL=security@pulseplan.com
INCIDENT_PHONE=+1-XXX-XXX-XXXX
ON_CALL_ROTATION=pagerduty://pulseplan-security
```

---

## Security Compliance

### Standards Compliance

PulsePlan security implementation supports compliance with:

- **SOC 2 Type II**: Comprehensive audit logging and access controls
- **GDPR**: Data encryption, user consent, and right to deletion
- **HIPAA**: Enhanced encryption and audit capabilities (if handling health data)
- **ISO 27001**: Information security management standards

### Regular Security Reviews

- **Quarterly**: Security configuration review
- **Bi-annually**: Penetration testing
- **Annually**: Full security audit and compliance assessment
- **As needed**: Incident response and threat assessment

---

## Configuration Reference

### Complete Security Environment Variables

```bash
# Authentication
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Encryption
USE_KMS=true
KMS_KEY_ID=alias/pulseplan-encryption
AWS_REGION=us-east-1
ENCRYPTION_FALLBACK_TO_FERNET=true

# Database Security
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
DATABASE_SSL=require
DATABASE_POOL_SIZE=20

# Redis Security
REDIS_URL=rediss://user:pass@host:6379/0
REDIS_SSL_CERT_REQS=required
REDIS_SSL_CHECK_HOSTNAME=true

# API Security
CORS_ORIGINS=https://app.pulseplan.com
MAX_REQUEST_SIZE=10485760
RATE_LIMITING_ENABLED=true

# Monitoring
LOG_LEVEL=info
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years
SECURITY_ALERTS_ENABLED=true
```

---

## Support and Contact

For security-related questions or to report vulnerabilities:

- **Email**: security@pulseplan.com
- **Bug Bounty**: security@pulseplan.com (responsible disclosure)
- **Emergency**: Use incident response procedures above

**Security Team Response Time:**
- Critical vulnerabilities: 4 hours
- High severity issues: 24 hours  
- Medium/Low severity: 72 hours

---

*This document is regularly updated to reflect current security implementations and best practices. Last updated: January 2025*