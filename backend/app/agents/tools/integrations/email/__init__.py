"""
Email Tools Package
Modular email management for PulsePlan agents
"""

# Models and Enums
from .models import (
    EmailDraft,
    ContactSuggestion,
    EmailResult,
    EmailVerificationRequired,
    EmailSender,
    EmailProvider
)

# Router
from .router import SmartEmailRouter

# Provider Tools
from .gmail_provider import GmailUserTool, GmailTool
from .outlook_provider import OutlookUserTool, OutlookTool
from .system_provider import SystemEmailTool

# Manager and Integration Tools
from .manager import EmailManagerTool, EmailIntegrationTool

__all__ = [
    # Models
    "EmailDraft",
    "ContactSuggestion",
    "EmailResult",
    "EmailVerificationRequired",
    "EmailSender",
    "EmailProvider",

    # Router
    "SmartEmailRouter",

    # Provider Tools
    "GmailUserTool",
    "GmailTool",
    "OutlookUserTool",
    "OutlookTool",
    "SystemEmailTool",

    # Manager Tools
    "EmailManagerTool",
    "EmailIntegrationTool",
]
