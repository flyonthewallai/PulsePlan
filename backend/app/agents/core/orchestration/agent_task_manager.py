"""
Agent Task Manager
Manages agent task lifecycle with visual progress tracking and WebSocket updates
"""
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from app.config.database.supabase import get_supabase
from app.core import websocket_manager

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Agent task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Agent task types"""
    WORKFLOW = "workflow"
    CRUD_SUCCESS = "crud_success"
    CRUD_ERROR = "crud_error"
    SEARCH = "search"
    BRIEFING = "briefing"
    SCHEDULING = "scheduling"
    CONVERSATION = "conversation"


class ProgressStep(BaseModel):
    """Individual progress step"""
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    timestamp: Optional[datetime] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class AgentTaskCard(BaseModel):
    """Visual agent task card data"""
    id: str
    user_id: str
    conversation_id: Optional[str] = None
    task_type: TaskType
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: int = Field(default=0, ge=0, le=100)
    steps: List[ProgressStep] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    workflow_id: Optional[str] = None
    workflow_type: Optional[str] = None
    can_cancel: bool = True
    estimated_duration: Optional[int] = None  # seconds
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CRUDSuccessCard(BaseModel):
    """Success card for CRUD operations"""
    id: str
    user_id: str
    operation: str  # "created", "updated", "deleted"
    entity_type: str  # "task", "todo", "event"
    entity_title: str
    entity_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    acknowledgement_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentTaskManager:
    """
    Manages agent task lifecycle with visual progress tracking and WebSocket updates
    """

    def __init__(self):
        self.active_tasks: Dict[str, AgentTaskCard] = {}

    async def create_workflow_task(
        self,
        user_id: str,
        workflow_type: str,
        title: str,
        description: Optional[str] = None,
        conversation_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        steps: Optional[List[str]] = None,
        estimated_duration: Optional[int] = None
    ) -> AgentTaskCard:
        """
        Create a new workflow task with progress tracking
        """
        try:
            task_id = str(uuid.uuid4())

            # Create progress steps
            progress_steps = []
            if steps:
                for step_name in steps:
                    progress_steps.append(ProgressStep(
                        name=step_name,
                        description=f"Executing {step_name}..."
                    ))
            else:
                # Default steps for workflow
                progress_steps = [
                    ProgressStep(name="analyzing", description="Analyzing your request..."),
                    ProgressStep(name="processing", description="Processing workflow..."),
                    ProgressStep(name="completing", description="Finalizing results...")
                ]

            # Create task card
            task_card = AgentTaskCard(
                id=task_id,
                user_id=user_id,
                conversation_id=conversation_id,
                task_type=TaskType.WORKFLOW,
                title=title,
                description=description,
                steps=progress_steps,
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                estimated_duration=estimated_duration,
                started_at=datetime.utcnow()
            )

            # Store in memory and database
            self.active_tasks[task_id] = task_card
            await self._persist_task(task_card)

            # Emit to user via WebSocket
            await self._emit_task_update(task_card, "task_created")

            logger.info(f"Created workflow task {task_id} for user {user_id}: {title}")
            return task_card

        except Exception as e:
            logger.error(f"Failed to create workflow task: {e}")
            raise

    async def create_crud_success_card(
        self,
        user_id: str,
        operation: str,
        entity_type: str,
        entity_title: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        acknowledgement_message: Optional[str] = None
    ) -> CRUDSuccessCard:
        """
        Create a success card for CRUD operations (no progress tracking needed)
        """
        try:
            card_id = str(uuid.uuid4())

            success_card = CRUDSuccessCard(
                id=card_id,
                user_id=user_id,
                operation=operation,
                entity_type=entity_type,
                entity_title=entity_title,
                entity_id=entity_id,
                details=details or {},
                acknowledgement_message=acknowledgement_message
            )

            # Emit success card immediately
            # Convert datetime objects to ISO strings for JSON serialization
            card_data = success_card.dict()
            for key, value in card_data.items():
                if isinstance(value, datetime):
                    card_data[key] = value.isoformat()

            await websocket_manager.emit_to_user(user_id, "crud_success", {
                "card": card_data,
                "conversation_id": conversation_id
            })

            logger.info(f"Created CRUD success card for user {user_id}: {operation} {entity_type} '{entity_title}'")
            return success_card

        except Exception as e:
            logger.error(f"Failed to create CRUD success card: {e}")
            raise

    async def create_crud_failure_card(
        self,
        user_id: str,
        operation: str,
        entity_type: str,
        entity_title: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        acknowledgement_message: Optional[str] = None
    ) -> CRUDSuccessCard:
        """
        Create a failure card for CRUD operations (no progress tracking needed)
        """
        try:
            card_id = str(uuid.uuid4())

            failure_card = CRUDSuccessCard(
                id=card_id,
                user_id=user_id,
                operation=operation,
                entity_type=entity_type,
                entity_title=entity_title,
                entity_id=entity_id,
                details=details or {},
                acknowledgement_message=acknowledgement_message
            )

            # Emit failure card immediately
            # Convert datetime objects to ISO strings for JSON serialization
            card_data = failure_card.dict()
            for key, value in card_data.items():
                if isinstance(value, datetime):
                    card_data[key] = value.isoformat()

            await websocket_manager.emit_to_user(user_id, "crud_failure", {
                "card": card_data,
                "conversation_id": conversation_id
            })

            logger.info(f"Created CRUD failure card for user {user_id}: {operation} {entity_type} '{entity_title}'")
            return failure_card

        except Exception as e:
            logger.error(f"Failed to create CRUD failure card: {e}")
            raise

    async def update_task_progress(
        self,
        task_id: str,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        step_details: Optional[Dict[str, Any]] = None,
        status: Optional[TaskStatus] = None
    ) -> None:
        """
        Update task progress and emit WebSocket update
        """
        try:
            if task_id not in self.active_tasks:
                logger.warning(f"Task {task_id} not found for progress update")
                return

            task_card = self.active_tasks[task_id]
            updated = False

            # Update progress percentage
            if progress is not None:
                task_card.progress = max(0, min(100, progress))
                updated = True

            # Update current step
            if current_step:
                for step in task_card.steps:
                    if step.name == current_step:
                        step.status = TaskStatus.IN_PROGRESS
                        step.timestamp = datetime.utcnow()
                        if step_details:
                            step.details.update(step_details)
                        updated = True
                        break

            # Update overall status
            if status:
                task_card.status = status
                if status == TaskStatus.IN_PROGRESS and not task_card.started_at:
                    task_card.started_at = datetime.utcnow()
                updated = True

            if updated:
                task_card.updated_at = datetime.utcnow()
                await self._persist_task(task_card)
                await self._emit_task_update(task_card, "task_progress")

        except Exception as e:
            logger.error(f"Failed to update task progress: {e}")

    async def complete_task_step(
        self,
        task_id: str,
        step_name: str,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark a specific step as completed
        """
        try:
            if task_id not in self.active_tasks:
                return

            task_card = self.active_tasks[task_id]

            for step in task_card.steps:
                if step.name == step_name:
                    step.status = TaskStatus.COMPLETED
                    step.timestamp = datetime.utcnow()
                    if result:
                        step.details.update(result)
                    break

            # Calculate overall progress based on completed steps
            completed_steps = len([s for s in task_card.steps if s.status == TaskStatus.COMPLETED])
            task_card.progress = int((completed_steps / len(task_card.steps)) * 100) if task_card.steps else 100

            task_card.updated_at = datetime.utcnow()
            await self._persist_task(task_card)
            await self._emit_task_update(task_card, "step_completed")

        except Exception as e:
            logger.error(f"Failed to complete task step: {e}")

    async def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        success_message: Optional[str] = None
    ) -> None:
        """
        Mark task as completed
        """
        try:
            if task_id not in self.active_tasks:
                return

            task_card = self.active_tasks[task_id]
            task_card.status = TaskStatus.COMPLETED
            task_card.progress = 100
            task_card.completed_at = datetime.utcnow()

            if result:
                task_card.result = result

            # Mark all steps as completed
            for step in task_card.steps:
                if step.status != TaskStatus.COMPLETED:
                    step.status = TaskStatus.COMPLETED
                    step.timestamp = datetime.utcnow()

            task_card.updated_at = datetime.utcnow()
            await self._persist_task(task_card)
            await self._emit_task_update(task_card, "task_completed")

            # Remove from active tasks after a delay
            import asyncio
            asyncio.create_task(self._cleanup_task(task_id, delay=60))  # 1 minute delay

            logger.info(f"Completed task {task_id}: {task_card.title}")

        except Exception as e:
            logger.error(f"Failed to complete task: {e}")

    async def fail_task(
        self,
        task_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark task as failed
        """
        try:
            if task_id not in self.active_tasks:
                return

            task_card = self.active_tasks[task_id]
            task_card.status = TaskStatus.FAILED
            task_card.error_message = error_message
            task_card.completed_at = datetime.utcnow()

            if error_details:
                task_card.metadata.update(error_details)

            task_card.updated_at = datetime.utcnow()
            await self._persist_task(task_card)
            await self._emit_task_update(task_card, "task_failed")

            # Remove from active tasks after a delay
            import asyncio
            asyncio.create_task(self._cleanup_task(task_id, delay=120))  # 2 minute delay for errors

            logger.error(f"Failed task {task_id}: {error_message}")

        except Exception as e:
            logger.error(f"Failed to mark task as failed: {e}")

    async def cancel_task(
        self,
        task_id: str,
        reason: str = "Cancelled by user"
    ) -> bool:
        """
        Cancel a running task
        """
        try:
            if task_id not in self.active_tasks:
                return False

            task_card = self.active_tasks[task_id]

            if not task_card.can_cancel:
                logger.warning(f"Task {task_id} cannot be cancelled")
                return False

            task_card.status = TaskStatus.CANCELLED
            task_card.error_message = reason
            task_card.completed_at = datetime.utcnow()
            task_card.updated_at = datetime.utcnow()

            await self._persist_task(task_card)
            await self._emit_task_update(task_card, "task_cancelled")

            # Remove from active tasks immediately
            await self._cleanup_task(task_id, delay=0)

            logger.info(f"Cancelled task {task_id}: {reason}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return False

    async def get_user_tasks(
        self,
        user_id: str,
        status_filter: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[AgentTaskCard]:
        """
        Get tasks for a user
        """
        try:
            supabase = get_supabase()

            query = supabase.table("agent_tasks").select("*").eq("user_id", user_id)

            if status_filter:
                query = query.eq("status", status_filter.value)

            result = query.order("created_at", desc=True).limit(limit).execute()

            tasks = []
            for row in result.data or []:
                task_card = self._row_to_task_card(row)
                tasks.append(task_card)

            return tasks

        except Exception as e:
            logger.error(f"Failed to get user tasks: {e}")
            return []

    async def get_task(self, task_id: str) -> Optional[AgentTaskCard]:
        """
        Get specific task by ID
        """
        try:
            # Check active tasks first
            if task_id in self.active_tasks:
                return self.active_tasks[task_id]

            # Check database
            supabase = get_supabase()
            result = supabase.table("agent_tasks").select("*").eq("id", task_id).single().execute()

            if result.data:
                return self._row_to_task_card(result.data)

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")

        return None

    async def get_task_card(self, task_id: str) -> Optional[AgentTaskCard]:
        """
        Get task card by ID (alias for get_task for compatibility)
        """
        return await self.get_task(task_id)

    async def _persist_task(self, task_card: AgentTaskCard) -> None:
        """
        Persist task to database with retry logic for connectivity issues
        """
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                supabase = get_supabase()

                # Convert to database format
                task_data = {
                    "id": task_card.id,
                    "user_id": task_card.user_id,
                    "conversation_id": task_card.conversation_id,
                    "workflow_type": task_card.workflow_type,
                    "workflow_id": task_card.workflow_id,
                    "title": task_card.title,
                    "description": task_card.description,
                    "status": task_card.status.value,
                    "progress": task_card.progress,
                    "result": task_card.result,
                    "error_message": task_card.error_message,
                    "metadata": {
                        **task_card.metadata,
                        "task_type": task_card.task_type.value,
                        "steps": [self._serialize_step(step) for step in task_card.steps],
                        "can_cancel": task_card.can_cancel,
                        "estimated_duration": task_card.estimated_duration
                    },
                    "started_at": task_card.started_at.isoformat() if task_card.started_at else None,
                    "completed_at": task_card.completed_at.isoformat() if task_card.completed_at else None,
                    "created_at": task_card.created_at.isoformat(),
                    "updated_at": task_card.updated_at.isoformat()
                }

                supabase.table("agent_tasks").upsert(task_data).execute()
                logger.debug(f"Successfully persisted task {task_card.id}")
                return  # Success, exit retry loop

            except Exception as e:
                error_str = str(e)
                is_connectivity_issue = any(keyword in error_str.lower() for keyword in [
                    "502", "bad gateway", "cloudflare", "timeout", "connection", "network"
                ])
                
                if is_connectivity_issue and attempt < max_retries - 1:
                    logger.warning(f"Database connectivity issue for task {task_card.id} (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    if is_connectivity_issue:
                        logger.error(f"Database persistently unavailable for task {task_card.id} after {max_retries} attempts: {e}")
                        logger.info("Task will remain in memory and can be retried later")
                    else:
                        logger.error(f"Failed to persist task {task_card.id}: {e}")
                    break

    def _serialize_step(self, step) -> Dict[str, Any]:
        """Serialize a progress step, converting datetime objects to ISO strings"""
        step_data = step.dict()
        for key, value in step_data.items():
            if isinstance(value, datetime):
                step_data[key] = value.isoformat()
        return step_data

    async def _emit_task_update(self, task_card: AgentTaskCard, event_type: str) -> None:
        """
        Emit task update via WebSocket
        """
        try:
            # Convert datetime objects to ISO strings for JSON serialization
            task_data = task_card.dict()
            for key, value in task_data.items():
                if isinstance(value, datetime):
                    task_data[key] = value.isoformat()
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            for sub_key, sub_value in item.items():
                                if isinstance(sub_value, datetime):
                                    task_data[key][i][sub_key] = sub_value.isoformat()
            
            await websocket_manager.emit_to_user(task_card.user_id, event_type, {
                "task": task_data,
                "conversation_id": task_card.conversation_id
            })

        except Exception as e:
            logger.error(f"Failed to emit task update: {e}")

    async def _cleanup_task(self, task_id: str, delay: int = 0) -> None:
        """
        Remove task from active tasks after delay
        """
        try:
            if delay > 0:
                import asyncio
                await asyncio.sleep(delay)

            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                logger.debug(f"Cleaned up task {task_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup task {task_id}: {e}")

    def _row_to_task_card(self, row: Dict[str, Any]) -> AgentTaskCard:
        """
        Convert database row to AgentTaskCard
        """
        metadata = row.get("metadata", {})

        # Parse steps from metadata
        steps = []
        for step_data in metadata.get("steps", []):
            steps.append(ProgressStep(**step_data))

        return AgentTaskCard(
            id=row["id"],
            user_id=row["user_id"],
            conversation_id=row.get("conversation_id"),
            task_type=TaskType(metadata.get("task_type", "workflow")),
            title=row["title"],
            description=row.get("description"),
            status=TaskStatus(row["status"]),
            progress=row.get("progress", 0),
            steps=steps,
            result=row.get("result"),
            error_message=row.get("error_message"),
            metadata=metadata,
            workflow_id=row.get("workflow_id"),
            workflow_type=row.get("workflow_type"),
            can_cancel=metadata.get("can_cancel", True),
            estimated_duration=metadata.get("estimated_duration"),
            started_at=datetime.fromisoformat(row["started_at"]) if row.get("started_at") else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )


# Global service instance
_agent_task_manager = None

def get_agent_task_manager() -> AgentTaskManager:
    """Get global AgentTaskManager instance"""
    global _agent_task_manager
    if _agent_task_manager is None:
        _agent_task_manager = AgentTaskManager()
    return _agent_task_manager