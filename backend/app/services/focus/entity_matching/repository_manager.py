"""
Repository Manager Module
Manages lazy-loading of database repositories for entity matching
"""
import logging
from typing import Optional

from app.database.repositories.task_repositories import (
    TaskRepository,
    get_task_repository,
    TodoRepository
)
from app.database.repositories.calendar_repositories import (
    TimeblocksRepository,
    get_timeblocks_repository
)

logger = logging.getLogger(__name__)


class RepositoryManager:
    """
    Manages database repository access with lazy loading

    Repositories:
    - TaskRepository: Access to tasks and exams
    - TodoRepository: Access to todos
    - TimeblocksRepository: Access to calendar timeblocks
    """

    def __init__(
        self,
        task_repository: Optional[TaskRepository] = None,
        todo_repository: Optional[TodoRepository] = None,
        timeblocks_repository: Optional[TimeblocksRepository] = None
    ):
        """
        Initialize repository manager

        Args:
            task_repository: Optional pre-initialized task repository
            todo_repository: Optional pre-initialized todo repository
            timeblocks_repository: Optional pre-initialized timeblocks repository
        """
        self._task_repository = task_repository
        self._todo_repository = todo_repository
        self._timeblocks_repository = timeblocks_repository

    @property
    def task_repository(self) -> TaskRepository:
        """
        Lazy-load task repository

        Returns:
            TaskRepository instance
        """
        if self._task_repository is None:
            self._task_repository = get_task_repository()
        return self._task_repository

    @property
    def todo_repository(self) -> TodoRepository:
        """
        Lazy-load todo repository

        Returns:
            TodoRepository instance
        """
        if self._todo_repository is None:
            self._todo_repository = TodoRepository()
        return self._todo_repository

    @property
    def timeblocks_repository(self) -> TimeblocksRepository:
        """
        Lazy-load timeblocks repository

        Returns:
            TimeblocksRepository instance
        """
        if self._timeblocks_repository is None:
            self._timeblocks_repository = get_timeblocks_repository()
        return self._timeblocks_repository
