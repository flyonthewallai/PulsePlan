"""
Smart Email Router
Routes email operations based on sender, recipient, and available accounts
"""
from typing import Dict, Any, Optional
from .models import EmailSender, EmailProvider
from app.agents.tools.core.base import ToolError


class SmartEmailRouter:
    """
    Routes email operations based on sender, recipient, and available accounts
    """

    @staticmethod
    def determine_best_provider(
        sender: EmailSender,
        connected_accounts: Dict[str, Any],
        user_preference: Optional[str] = None
    ) -> EmailProvider:
        """
        Determine best email provider based on context

        Args:
            sender: Who is sending (user vs agent)
            connected_accounts: User's connected email accounts
            user_preference: User's preferred email provider

        Returns:
            Best email provider to use
        """
        if sender == EmailSender.AGENT:
            # Agent always sends from system email
            return EmailProvider.SYSTEM

        # User is sending - check their connected accounts
        available_providers = []

        if "gmail" in connected_accounts or "google" in connected_accounts:
            available_providers.append(EmailProvider.GMAIL)

        if "microsoft" in connected_accounts or "outlook" in connected_accounts:
            available_providers.append(EmailProvider.OUTLOOK)

        if not available_providers:
            raise ToolError("No email accounts connected", "email_router")

        # Use user preference if available and valid
        if user_preference:
            preferred = EmailProvider(user_preference.lower())
            if preferred in available_providers:
                return preferred

        # Default priority: Gmail > Outlook
        if EmailProvider.GMAIL in available_providers:
            return EmailProvider.GMAIL

        return available_providers[0]
