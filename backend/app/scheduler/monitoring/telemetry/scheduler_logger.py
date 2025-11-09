"""
Structured logging for scheduler operations.

Provides consistent, searchable logging with context
and correlation IDs.
"""

import logging


class SchedulerLogger:
    """
    Structured logging for scheduler operations.

    Provides consistent, searchable logging with context
    and correlation IDs.
    """

    def __init__(self, logger_name: str = "scheduler"):
        """Initialize scheduler logger."""
        self.logger = logging.getLogger(logger_name)
        self._context_vars = {}

    def set_context(self, **kwargs):
        """Set logging context variables."""
        self._context_vars.update(kwargs)

    def clear_context(self):
        """Clear logging context."""
        self._context_vars.clear()

    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with context."""
        context = {**self._context_vars, **kwargs}

        if context:
            context_str = ' '.join(f"{k}={v}" for k, v in context.items())
            return f"{message} | {context_str}"

        return message

    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.logger.error(self._format_message(message, **kwargs))

    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(self._format_message(message, **kwargs))
