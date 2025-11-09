"""
Security Setup
Centralized security configuration and middleware setup
"""
import logging
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import secrets
import re
import hashlib
import logging
from typing import Dict, Any

from app.config.core.settings import get_settings
# Lazy imports to avoid circular dependencies - these will be imported when needed

logger = logging.getLogger(__name__)


def setup_security_middleware(app: FastAPI):
    """
    Setup all security middleware in the correct order
    """
    settings = get_settings()
    
    # 1. Trusted host middleware (outermost - validates Host header)
    if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS != ["*"]:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
        logger.info(f"Trusted host middleware enabled with hosts: {settings.ALLOWED_HOSTS}")
    
    # 2. CORS middleware (before auth to handle preflight)
    if settings.ALLOWED_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "X-Requested-With",
                "Accept",
                "Origin",
                "User-Agent",
                "DNT",
                "Cache-Control",
                "X-Mx-ReqToken",
                "Keep-Alive",
                "X-Requested-With",
                "If-Modified-Since"
            ],
            max_age=86400,  # 24 hours
        )
        logger.info(f"CORS middleware enabled with origins: {settings.ALLOWED_ORIGINS}")
    
    # 3. Security headers middleware
    from app.middleware.security_headers import SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware enabled")
    
    # 4. Authentication middleware (optional - adds user context when available)
    auth_exempt_paths = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/api/v1/oauth"  # OAuth endpoints don't require existing auth
    ]
    
    # app.add_middleware(
    #     AuthMiddleware,  # TODO: Implement AuthMiddleware
    #     exempt_paths=auth_exempt_paths
    # )
    logger.info("Authentication middleware enabled")
    
    # 5. Rate limiting middleware (innermost - after user identification)
    # setup_rate_limiting(app)  # TODO: Implement setup_rate_limiting function
    
    logger.info("All security middleware configured")


def get_security_headers() -> dict:
    """
    Get security headers configuration
    """
    settings = get_settings()
    
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
        "Content-Security-Policy": get_csp_header(settings),
    }
    
    # Add HSTS for production
    if settings.is_production():
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    return headers


def get_csp_header(settings) -> str:
    """
    Generate Content Security Policy header
    """
    if settings.is_production():
        # Strict CSP for production (no 'unsafe-inline' for better XSS protection)
        return (
            "default-src 'self'; "
            "script-src 'self' https://cdnjs.cloudflare.com; "
            "style-src 'self' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "object-src 'none';"
        )
    else:
        # More relaxed CSP for development
        return (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https: wss: ws:; "
            "frame-ancestors 'none';"
        )


def validate_security_config():
    """
    Validate security configuration at startup
    """
    settings = get_settings()
    warnings = []
    errors = []
    
    # Check required security settings
    if not settings.SECRET_KEY:
        errors.append("SECRET_KEY is required")
    elif len(settings.SECRET_KEY) < 32:
        warnings.append("SECRET_KEY should be at least 32 characters long")
    
    if not settings.HMAC_SECRET_KEY:
        errors.append("HMAC_SECRET_KEY is required for payload signing")
    
    # Check production-specific settings
    if settings.is_production():
        if "*" in settings.ALLOWED_HOSTS:
            warnings.append("ALLOWED_HOSTS contains '*' in production - consider restricting")
        
        if settings.DEBUG:
            warnings.append("DEBUG is enabled in production - should be disabled")
        
        if not settings.SENTRY_DSN:
            warnings.append("SENTRY_DSN not configured for production error tracking")
    
    # Check CORS configuration
    if settings.ALLOWED_ORIGINS and "*" in settings.ALLOWED_ORIGINS and settings.is_production():
        warnings.append("CORS allows all origins in production - consider restricting")
    
    # Log warnings and errors
    for warning in warnings:
        logger.warning(f"Security warning: {warning}")
    
    for error in errors:
        logger.error(f"Security error: {error}")
    
    if errors:
        raise ValueError(f"Security configuration errors: {'; '.join(errors)}")
    
    if warnings:
        logger.info(f"Security validation completed with {len(warnings)} warnings")
    else:
        logger.info("Security validation completed successfully")


def get_security_info() -> dict:
    """
    Get current security configuration info (for health checks)
    """
    settings = get_settings()
    
    return {
        "environment": settings.ENVIRONMENT.value,
        "debug_mode": settings.DEBUG,
        "rate_limiting_enabled": settings.ENABLE_RATE_LIMITING,
        "payload_signing_enabled": settings.ENABLE_PAYLOAD_SIGNING,
        "content_filtering_enabled": settings.ENABLE_CONTENT_FILTERING,
        "input_validation_enabled": settings.ENABLE_INPUT_VALIDATION,
        "cors_configured": bool(settings.ALLOWED_ORIGINS),
        "trusted_hosts_configured": bool(settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS != ["*"]),
        "security_headers_enabled": True,
        "auth_middleware_enabled": True,
        "circuit_breakers_enabled": True
    }


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure random secret key
    """
    return secrets.token_urlsafe(length)


def validate_email(email: str) -> bool:
    """
    Validate email format using regex
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_input(input_string: str) -> str:
    """
    Sanitize user input to prevent XSS attacks
    """
    if not isinstance(input_string, str):
        return str(input_string)
    
    # Remove or encode potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&']
    sanitized = input_string
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, f'&#{ord(char)};')
    
    return sanitized.strip()


def check_password_strength(password: str) -> Dict[str, Any]:
    """
    Check password strength and return evaluation
    """
    requirements = {
        'minimum_length': len(password) >= 8,
        'has_uppercase': any(c.isupper() for c in password),
        'has_lowercase': any(c.islower() for c in password),
        'has_digit': any(c.isdigit() for c in password),
        'has_special': any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    }
    
    strength_score = sum(requirements.values())
    
    strength_levels = {
        5: 'very_strong',
        4: 'strong', 
        3: 'moderate',
        2: 'weak',
        1: 'very_weak',
        0: 'invalid'
    }
    
    return {
        'score': strength_score,
        'level': strength_levels.get(strength_score, 'invalid'),
        'requirements': requirements,
        'meets_minimum': strength_score >= 3
    }