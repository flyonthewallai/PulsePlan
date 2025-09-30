"""
Authentication and security core module.

This module contains all authentication and security-related core functionality including:
- User authentication flows
- Authorization logic
- Security utilities and validations
- Token management utilities
"""

from .auth import (
    CurrentUser,
    verify_supabase_token,
    get_current_user,
    require_admin,
    check_user_access
)
from .security import (
    generate_secret_key,
    validate_email,
    sanitize_input,
    check_password_strength
)

__all__ = [
    "CurrentUser",
    "verify_supabase_token",
    "get_current_user",
    "require_admin",
    "check_user_access", 
    "generate_secret_key",
    "validate_email",
    "sanitize_input",
    "check_password_strength",
]
