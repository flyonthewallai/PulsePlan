"""
Email management tools for PulsePlan agents.
Handles Gmail, Outlook, and system email sending scenarios with smart routing.

This is a compatibility wrapper that imports from the modular email/ package.
For the implementation details, see the email/ subdirectory.
"""

# Import all classes from the email package for backward compatibility
from .email import (
    # Models and Enums
    EmailDraft,
    ContactSuggestion,
    EmailResult,
    EmailVerificationRequired,
    EmailSender,
    EmailProvider,

    # Router
    SmartEmailRouter,

    # Provider Tools
    GmailUserTool,
    GmailTool,
    OutlookUserTool,
    OutlookTool,
    SystemEmailTool,

    # Manager Tools
    EmailManagerTool,
    EmailIntegrationTool,
)

# Re-export all classes for backward compatibility
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
