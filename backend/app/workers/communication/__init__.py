"""
Communication workers for messaging and notifications.

This module contains all communication-related worker functionality including:
- Email service for sending briefings and notifications
- Email delivery and notification management using Resend
- Communication workflow orchestration
"""

from .email_service import (
    EmailService,
    get_email_service
)

__all__ = [
    "EmailService",
    "get_email_service",
]


