import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from app.config.core.settings import settings
import logging

logger = logging.getLogger(__name__)

def setup_sentry():
    """Initialize Sentry error tracking (free tier compatible)"""
    if not settings.SENTRY_DSN:
        logger.warning("Sentry DSN not configured - error tracking disabled")
        return
    
    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            
            # Conservative sampling for free tier (5k events/month)
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            
            # Integrations
            integrations=[
                FastApiIntegration(auto_enabling_integrations=False),
                RedisIntegration(),
                HttpxIntegration(),
            ],
            
            # Data filtering
            before_send=filter_sensitive_data,
            send_default_pii=False,
            attach_stacktrace=True,
            
            # Performance monitoring (limited for free tier)
            enable_tracing=True,
            
            # Release tracking
            release=f"pulseplan-api@{settings.VERSION}",
        )
        
        logger.info("Sentry initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")

def filter_sensitive_data(event, hint):
    """Filter sensitive data from Sentry events"""
    try:
        # Filter request data
        if 'request' in event:
            request = event['request']
            
            # Filter headers
            if 'headers' in request:
                headers = request['headers']
                sensitive_headers = ['authorization', 'cookie', 'x-api-key']
                
                for header in sensitive_headers:
                    if header in headers:
                        headers[header] = '[Filtered]'
            
            # Filter query parameters
            if 'query_string' in request:
                # Don't log query strings that might contain tokens
                request['query_string'] = '[Filtered]'
            
            # Filter form data
            if 'data' in request and isinstance(request['data'], dict):
                data = request['data']
                sensitive_fields = ['password', 'token', 'secret', 'key', 'access_token', 'refresh_token']
                
                for field in sensitive_fields:
                    if field in data:
                        data[field] = '[Filtered]'
        
        # Filter extra data
        if 'extra' in event:
            extra = event['extra']
            if isinstance(extra, dict):
                sensitive_keys = ['token', 'password', 'secret', 'key', 'credential']
                for key in list(extra.keys()):
                    if any(sensitive in key.lower() for sensitive in sensitive_keys):
                        extra[key] = '[Filtered]'
        
        # Filter exception context
        if 'exception' in event and 'values' in event['exception']:
            for exception in event['exception']['values']:
                if 'stacktrace' in exception and 'frames' in exception['stacktrace']:
                    for frame in exception['stacktrace']['frames']:
                        if 'vars' in frame:
                            vars_dict = frame['vars']
                            sensitive_var_names = ['token', 'password', 'secret', 'key']
                            for var_name in list(vars_dict.keys()):
                                if any(sensitive in var_name.lower() for sensitive in sensitive_var_names):
                                    vars_dict[var_name] = '[Filtered]'
        
        return event
        
    except Exception as e:
        logger.error(f"Error filtering Sentry data: {e}")
        return event

def capture_exception(error: Exception, **kwargs):
    """Capture exception with additional context"""
    try:
        with sentry_sdk.push_scope() as scope:
            # Add custom context
            for key, value in kwargs.items():
                scope.set_context(key, value)
            
            sentry_sdk.capture_exception(error)
            
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")

def capture_message(message: str, level: str = "info", **kwargs):
    """Capture custom message with context"""
    try:
        with sentry_sdk.push_scope() as scope:
            # Add custom context
            for key, value in kwargs.items():
                scope.set_context(key, value)
            
            sentry_sdk.capture_message(message, level=level)
            
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")

def set_user_context(user_id: str, email: str = None):
    """Set user context for error tracking"""
    try:
        with sentry_sdk.configure_scope() as scope:
            scope.user = {
                "id": user_id,
                "email": email
            }
    except Exception as e:
        logger.error(f"Failed to set user context in Sentry: {e}")

def add_breadcrumb(message: str, category: str = "custom", level: str = "info", data: dict = None):
    """Add breadcrumb for debugging"""
    try:
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )
    except Exception as e:
        logger.error(f"Failed to add breadcrumb in Sentry: {e}")
