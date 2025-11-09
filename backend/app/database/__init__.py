"""
Database Package
Provides ORM-like functionality for Supabase operations
"""
from .models import (
    BaseDBModel,
    UserModel,
    TaskModel,
    TodoModel,
    CalendarEventModel,
    MemoryModel,
    WorkflowExecutionModel,
    MODEL_REGISTRY,
    get_model_class,
    validate_model_data
)

from .repository import (
    DatabaseError
)

from .session import get_db, get_supabase_db

from .manager import (
    DatabaseManager,
    get_database_manager
)

__all__ = [
    # Models
    'BaseDBModel',
    'UserModel',
    'TaskModel',
    'TodoModel',
    'CalendarEventModel',
    'MemoryModel',
    'WorkflowExecutionModel',
    'MODEL_REGISTRY',
    'get_model_class',
    'validate_model_data',

    # Repository
    'DatabaseError',

    # Session
    'get_db',
    'get_supabase_db',

    # Manager
    'DatabaseManager',
    'get_database_manager'
]