"""
Repository Layer
Error handling for database operations
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Database operation error"""
    def __init__(self, message: str, operation: str, table: str, details: Dict[str, Any] = None):
        self.message = message
        self.operation = operation
        self.table = table
        self.details = details or {}
        super().__init__(f"{operation} failed on {table}: {message}")