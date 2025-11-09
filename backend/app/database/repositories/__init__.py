"""
Repository Layer - Domain-Organized Data Access

All repositories are organized by domain for easier navigation and maintenance.
"""

# Task repositories
from .task_repositories import (
    PredefinedTagRepository,
    UserTagRepository,
    TodoTagRepository,
    TaskRepository,
    TodoRepository,
    get_predefined_tag_repository,
    get_user_tag_repository,
    get_todo_tag_repository,
)

# User repositories
from .user_repositories import (
    UserRepository,
    CourseRepository,
    HobbiesRepository,
    get_user_repository,
    get_course_repository,
    get_hobbies_repository,
)

# Calendar repositories
from .calendar_repositories import (
    CalendarLinkRepository,
    CalendarCalendarRepository,
    CalendarEventRepository,
    TimeblocksRepository,
    get_calendar_link_repository,
    get_calendar_calendar_repository,
    get_calendar_event_repository,
    get_timeblocks_repository,
)

# Integration repositories
from .integration_repositories import (
    NLURepository,
    UsageRepository,
    BriefingsRepository,
    create_nlu_repository,
    get_usage_repository,
    get_briefings_repository,
)

__all__ = [
    # Task domain
    "PredefinedTagRepository",
    "UserTagRepository",
    "TodoTagRepository",
    "TaskRepository",
    "TodoRepository",
    "get_predefined_tag_repository",
    "get_user_tag_repository",
    "get_todo_tag_repository",
    # User domain
    "UserRepository",
    "CourseRepository",
    "HobbiesRepository",
    "get_user_repository",
    "get_course_repository",
    "get_hobbies_repository",
    # Calendar domain
    "CalendarLinkRepository",
    "CalendarCalendarRepository",
    "CalendarEventRepository",
    "TimeblocksRepository",
    "get_calendar_link_repository",
    "get_calendar_calendar_repository",
    "get_calendar_event_repository",
    "get_timeblocks_repository",
    # Integration domain
    "NLURepository",
    "UsageRepository",
    "BriefingsRepository",
    "create_nlu_repository",
    "get_usage_repository",
    "get_briefings_repository",
]
