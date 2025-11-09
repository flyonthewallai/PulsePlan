"""Task Domain Repositories"""

from .tag_repository import (
    PredefinedTagRepository,
    UserTagRepository,
    TodoTagRepository,
    get_predefined_tag_repository,
    get_user_tag_repository,
    get_todo_tag_repository,
)

from .task_repository import (
    TaskRepository,
    get_task_repository,
)

from .todo_repository import (
    TodoRepository,
)

__all__ = [
    # Tag repositories
    "PredefinedTagRepository",
    "UserTagRepository",
    "TodoTagRepository",
    "get_predefined_tag_repository",
    "get_user_tag_repository",
    "get_todo_tag_repository",
    # Task repository
    "TaskRepository",
    "get_task_repository",
    # Todo repository
    "TodoRepository",
]
