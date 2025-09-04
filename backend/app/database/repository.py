"""
Repository Layer
ORM-like interface for Supabase operations with error handling and validation
"""
from typing import Dict, List, Optional, Any, Union, Type, Tuple
from datetime import datetime
import logging
from abc import ABC, abstractmethod

from .models import BaseDBModel, MODEL_REGISTRY
from ..config.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Database operation error"""
    def __init__(self, message: str, operation: str, table: str, details: Dict[str, Any] = None):
        self.message = message
        self.operation = operation
        self.table = table
        self.details = details or {}
        super().__init__(f"{operation} failed on {table}: {message}")


class BaseRepository(ABC):
    """Base repository interface"""
    
    def __init__(self, table_name: str, model_class: Type[BaseDBModel]):
        self.table_name = table_name
        self.model_class = model_class
        self.supabase = get_supabase_client()
    
    async def create(self, data: Union[Dict[str, Any], BaseDBModel]) -> BaseDBModel:
        """Create a new record"""
        try:
            # Convert to model if needed
            if isinstance(data, dict):
                model = self.model_class(**data)
            else:
                model = data
            
            # Prepare data for insertion
            insert_data = model.to_supabase_insert()
            
            # Execute insert
            response = await self.supabase.table(self.table_name).insert(insert_data).execute()
            
            if not response.data:
                raise DatabaseError(
                    "No data returned from insert operation",
                    "create",
                    self.table_name
                )
            
            # Return model instance
            return self.model_class(**response.data[0])
            
        except Exception as e:
            logger.error(f"Create operation failed on {self.table_name}: {str(e)}")
            raise DatabaseError(
                str(e),
                "create",
                self.table_name,
                {"input_data": insert_data if 'insert_data' in locals() else data}
            )
    
    async def get_by_id(self, record_id: str) -> Optional[BaseDBModel]:
        """Get record by ID"""
        try:
            response = await self.supabase.table(self.table_name).select("*").eq("id", record_id).execute()
            
            if not response.data:
                return None
            
            return self.model_class(**response.data[0])
            
        except Exception as e:
            logger.error(f"Get by ID failed on {self.table_name}: {str(e)}")
            raise DatabaseError(
                str(e),
                "get_by_id",
                self.table_name,
                {"record_id": record_id}
            )
    
    async def update(self, record_id: str, data: Union[Dict[str, Any], BaseDBModel]) -> Optional[BaseDBModel]:
        """Update a record"""
        try:
            # Convert to update format
            if isinstance(data, BaseDBModel):
                update_data = data.to_supabase_update()
            else:
                update_data = data.copy()
                update_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Execute update
            response = await self.supabase.table(self.table_name).update(update_data).eq("id", record_id).execute()
            
            if not response.data:
                return None
            
            return self.model_class(**response.data[0])
            
        except Exception as e:
            logger.error(f"Update operation failed on {self.table_name}: {str(e)}")
            raise DatabaseError(
                str(e),
                "update",
                self.table_name,
                {"record_id": record_id, "update_data": update_data if 'update_data' in locals() else data}
            )
    
    async def delete(self, record_id: str) -> bool:
        """Delete a record"""
        try:
            response = await self.supabase.table(self.table_name).delete().eq("id", record_id).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Delete operation failed on {self.table_name}: {str(e)}")
            raise DatabaseError(
                str(e),
                "delete",
                self.table_name,
                {"record_id": record_id}
            )
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[BaseDBModel]:
        """List all records with pagination"""
        try:
            response = await self.supabase.table(self.table_name).select("*").range(offset, offset + limit - 1).execute()
            
            return [self.model_class(**item) for item in response.data]
            
        except Exception as e:
            logger.error(f"List operation failed on {self.table_name}: {str(e)}")
            raise DatabaseError(
                str(e),
                "list_all",
                self.table_name,
                {"limit": limit, "offset": offset}
            )
    
    async def find_by(self, filters: Dict[str, Any], limit: int = 100) -> List[BaseDBModel]:
        """Find records by filters"""
        try:
            query = self.supabase.table(self.table_name).select("*")
            
            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = await query.limit(limit).execute()
            
            return [self.model_class(**item) for item in response.data]
            
        except Exception as e:
            logger.error(f"Find by filters failed on {self.table_name}: {str(e)}")
            raise DatabaseError(
                str(e),
                "find_by",
                self.table_name,
                {"filters": filters, "limit": limit}
            )
    
    async def find_one_by(self, filters: Dict[str, Any]) -> Optional[BaseDBModel]:
        """Find single record by filters"""
        try:
            query = self.supabase.table(self.table_name).select("*")
            
            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = await query.limit(1).execute()
            
            if not response.data:
                return None
            
            return self.model_class(**response.data[0])
            
        except Exception as e:
            logger.error(f"Find one by filters failed on {self.table_name}: {str(e)}")
            raise DatabaseError(
                str(e),
                "find_one_by",
                self.table_name,
                {"filters": filters}
            )
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters"""
        try:
            query = self.supabase.table(self.table_name).select("id", count="exact")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = await query.execute()
            
            return response.count if response.count is not None else 0
            
        except Exception as e:
            logger.error(f"Count operation failed on {self.table_name}: {str(e)}")
            raise DatabaseError(
                str(e),
                "count",
                self.table_name,
                {"filters": filters}
            )
    
    async def exists(self, record_id: str) -> bool:
        """Check if record exists"""
        try:
            response = await self.supabase.table(self.table_name).select("id").eq("id", record_id).limit(1).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Exists check failed on {self.table_name}: {str(e)}")
            return False


class UserRepository(BaseRepository):
    """User-specific repository methods"""
    
    def __init__(self):
        from .models import UserModel
        super().__init__("users", UserModel)
    
    async def get_by_email(self, email: str) -> Optional[BaseDBModel]:
        """Get user by email"""
        return await self.find_one_by({"email": email})
    
    async def update_subscription(self, user_id: str, subscription_data: Dict[str, Any]) -> Optional[BaseDBModel]:
        """Update user subscription"""
        subscription_data['subscription_updated_at'] = datetime.utcnow().isoformat()
        return await self.update(user_id, subscription_data)


class OAuthTokenRepository(BaseRepository):
    """OAuth token-specific repository methods"""
    
    def __init__(self):
        from .models import OAuthTokenModel
        super().__init__("oauth_tokens", OAuthTokenModel)
    
    async def get_by_user_and_provider(self, user_id: str, provider: str) -> Optional[BaseDBModel]:
        """Get token by user and provider"""
        return await self.find_one_by({"user_id": user_id, "provider": provider})
    
    async def get_active_tokens(self, user_id: str) -> List[BaseDBModel]:
        """Get all active tokens for user"""
        return await self.find_by({"user_id": user_id, "status": "active"})
    
    async def mark_expired(self, token_id: str) -> Optional[BaseDBModel]:
        """Mark token as expired"""
        return await self.update(token_id, {"status": "expired"})


class TaskRepository(BaseRepository):
    """Task-specific repository methods"""
    
    def __init__(self):
        from .models import TaskModel
        super().__init__("tasks", TaskModel)
    
    async def get_user_tasks(self, user_id: str, status: Optional[str] = None) -> List[BaseDBModel]:
        """Get tasks for user with optional status filter"""
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        return await self.find_by(filters)
    
    async def mark_completed(self, task_id: str) -> Optional[BaseDBModel]:
        """Mark task as completed"""
        return await self.update(task_id, {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        })
    
    async def get_overdue_tasks(self, user_id: str) -> List[BaseDBModel]:
        """Get overdue tasks for user"""
        try:
            current_time = datetime.utcnow().isoformat()
            response = await self.supabase.table(self.table_name).select("*").eq("user_id", user_id).lt("due_date", current_time).neq("status", "completed").execute()
            
            return [self.model_class(**item) for item in response.data]
            
        except Exception as e:
            logger.error(f"Get overdue tasks failed: {str(e)}")
            raise DatabaseError(str(e), "get_overdue_tasks", self.table_name, {"user_id": user_id})


class TodoRepository(BaseRepository):
    """Todo-specific repository methods"""
    
    def __init__(self):
        from .models import TodoModel
        super().__init__("todos", TodoModel)
    
    async def get_user_todos(self, user_id: str, status: Optional[str] = None) -> List[BaseDBModel]:
        """Get todos for user with optional status filter"""
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        return await self.find_by(filters)
    
    async def mark_completed(self, todo_id: str) -> Optional[BaseDBModel]:
        """Mark todo as completed"""
        return await self.update(todo_id, {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        })


class CalendarEventRepository(BaseRepository):
    """Calendar event-specific repository methods"""
    
    def __init__(self):
        from .models import CalendarEventModel
        super().__init__("calendar_events", CalendarEventModel)
    
    async def get_user_events(self, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[BaseDBModel]:
        """Get calendar events for user within date range"""
        try:
            query = self.supabase.table(self.table_name).select("*").eq("user_id", user_id)
            
            if start_date:
                query = query.gte("start_time", start_date.isoformat())
            if end_date:
                query = query.lte("start_time", end_date.isoformat())
            
            response = await query.execute()
            
            return [self.model_class(**item) for item in response.data]
            
        except Exception as e:
            logger.error(f"Get user events failed: {str(e)}")
            raise DatabaseError(str(e), "get_user_events", self.table_name, {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date
            })
    
    async def get_by_external_id(self, user_id: str, provider: str, external_id: str) -> Optional[BaseDBModel]:
        """Get event by external ID"""
        return await self.find_one_by({
            "user_id": user_id,
            "provider": provider,
            "external_id": external_id
        })


class MemoryRepository(BaseRepository):
    """Memory-specific repository methods"""
    
    def __init__(self):
        from .models import MemoryModel
        super().__init__("memories", MemoryModel)
    
    async def get_user_memories(self, user_id: str, memory_type: Optional[str] = None) -> List[BaseDBModel]:
        """Get memories for user with optional type filter"""
        filters = {"user_id": user_id}
        if memory_type:
            filters["memory_type"] = memory_type
        return await self.find_by(filters)
    
    async def search_by_content(self, user_id: str, search_term: str, limit: int = 10) -> List[BaseDBModel]:
        """Search memories by content"""
        try:
            response = await self.supabase.table(self.table_name).select("*").eq("user_id", user_id).ilike("content", f"%{search_term}%").limit(limit).execute()
            
            return [self.model_class(**item) for item in response.data]
            
        except Exception as e:
            logger.error(f"Search memories failed: {str(e)}")
            raise DatabaseError(str(e), "search_by_content", self.table_name, {
                "user_id": user_id,
                "search_term": search_term
            })


class WorkflowExecutionRepository(BaseRepository):
    """Workflow execution tracking repository"""
    
    def __init__(self):
        from .models import WorkflowExecutionModel
        super().__init__("workflow_executions", WorkflowExecutionModel)
    
    async def get_user_executions(self, user_id: str, workflow_type: Optional[str] = None, limit: int = 50) -> List[BaseDBModel]:
        """Get workflow executions for user"""
        filters = {"user_id": user_id}
        if workflow_type:
            filters["workflow_type"] = workflow_type
        return await self.find_by(filters, limit=limit)
    
    async def get_by_trace_id(self, trace_id: str) -> Optional[BaseDBModel]:
        """Get execution by trace ID"""
        return await self.find_one_by({"trace_id": trace_id})
    
    async def mark_completed(self, execution_id: str, output_data: Dict[str, Any], execution_time: float) -> Optional[BaseDBModel]:
        """Mark execution as completed"""
        return await self.update(execution_id, {
            "status": "completed",
            "output_data": output_data,
            "completed_at": datetime.utcnow().isoformat(),
            "execution_time": execution_time
        })
    
    async def mark_failed(self, execution_id: str, error: str, error_details: Optional[Dict[str, Any]] = None) -> Optional[BaseDBModel]:
        """Mark execution as failed"""
        return await self.update(execution_id, {
            "status": "failed",
            "error": error,
            "error_details": error_details,
            "completed_at": datetime.utcnow().isoformat()
        })


# Repository registry for dynamic access
REPOSITORY_REGISTRY = {
    'users': UserRepository,
    'oauth_tokens': OAuthTokenRepository,
    'tasks': TaskRepository,
    'todos': TodoRepository,
    'calendar_events': CalendarEventRepository,
    'memories': MemoryRepository,
    'workflow_executions': WorkflowExecutionRepository
}


def get_repository(table_name: str) -> BaseRepository:
    """Get repository instance by table name"""
    repo_class = REPOSITORY_REGISTRY.get(table_name)
    if not repo_class:
        # Fall back to generic repository
        model_class = MODEL_REGISTRY.get(table_name)
        if not model_class:
            raise ValueError(f"Unknown table: {table_name}")
        return BaseRepository(table_name, model_class)
    
    return repo_class()


class DatabaseManager:
    """Database manager for coordinated operations"""
    
    def __init__(self):
        self.users = UserRepository()
        self.oauth_tokens = OAuthTokenRepository()
        self.tasks = TaskRepository()
        self.todos = TodoRepository()
        self.calendar_events = CalendarEventRepository()
        self.memories = MemoryRepository()
        self.workflow_executions = WorkflowExecutionRepository()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            # Test basic connectivity
            response = await self.users.supabase.table("users").select("id").limit(1).execute()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "connection": "ok"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def get_repository(self, table_name: str) -> BaseRepository:
        """Get repository by name"""
        return get_repository(table_name)


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_manager() -> DatabaseManager:
    """FastAPI dependency to get database manager"""
    return db_manager