"""
Database Package
Provides ORM-like functionality for Supabase operations
"""
from .models import (
    BaseDBModel,
    UserModel,
    OAuthTokenModel,
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
    BaseRepository,
    UserRepository,
    OAuthTokenRepository,
    TaskRepository,
    TodoRepository,
    CalendarEventRepository,
    MemoryRepository,
    WorkflowExecutionRepository,
    DatabaseManager,
    DatabaseError,
    REPOSITORY_REGISTRY,
    get_repository,
    db_manager,
    get_db_manager
)

from .session import get_db, get_supabase_db

__all__ = [
    # Models
    'BaseDBModel',
    'UserModel',
    'OAuthTokenModel',
    'TaskModel',
    'TodoModel',
    'CalendarEventModel',
    'MemoryModel',
    'WorkflowExecutionModel',
    'MODEL_REGISTRY',
    'get_model_class',
    'validate_model_data',
    
    # Repositories
    'BaseRepository',
    'UserRepository',
    'OAuthTokenRepository',
    'TaskRepository',
    'TodoRepository',
    'CalendarEventRepository',
    'MemoryRepository',
    'WorkflowExecutionRepository',
    'DatabaseManager',
    'DatabaseError',
    'REPOSITORY_REGISTRY',
    'get_repository',
    'db_manager',
    'get_db_manager',
    
    # Session
    'get_db',
    'get_supabase_db'
]