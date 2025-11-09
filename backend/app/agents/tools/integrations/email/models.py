"""
Email Models and Enums
Data models for email operations
"""
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum


class EmailDraft(BaseModel):
    """Email draft for user verification"""
    to: List[str]
    subject: str
    body: str
    sender_email: str
    provider: str
    draft_id: str
    needs_approval: bool = True


class ContactSuggestion(BaseModel):
    """Suggestion to add email recipients to contacts"""
    email: str
    name: Optional[str] = None
    suggested_action: str = "add_to_contacts"  # add_to_contacts, ignore, auto_add


class EmailResult(BaseModel):
    """Enhanced email result with contact suggestions"""
    success: bool
    message_id: Optional[str] = None
    provider: str
    contact_suggestions: List[ContactSuggestion] = []
    message: str


class EmailVerificationRequired(Exception):
    """Exception raised when email needs user approval"""
    def __init__(self, draft: EmailDraft, message: str = "Email requires user verification before sending"):
        self.draft = draft
        self.message = message
        super().__init__(message)


class EmailSender(str, Enum):
    """Who is sending the email"""
    USER = "user"  # User sending from their own account
    AGENT = "agent"  # Agent sending to user from system email


class EmailProvider(str, Enum):
    """Email provider types"""
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    SYSTEM = "system"  # Agent system email
