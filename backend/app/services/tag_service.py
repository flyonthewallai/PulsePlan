"""
Tag Service
Business logic layer for tag operations
"""
import logging
from typing import Dict, Any, List, Optional
from collections import Counter

from app.database.repositories.task_repositories import (
    PredefinedTagRepository,
    UserTagRepository,
    TodoTagRepository,
    get_predefined_tag_repository,
    get_user_tag_repository,
    get_todo_tag_repository
)
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class TagService:
    """
    Tag management service

    Handles business logic for predefined and user custom tags.
    Implements RULES.md Section 6.1 - Service layer pattern.
    """

    def __init__(
        self,
        predefined_repo: Optional[PredefinedTagRepository] = None,
        user_repo: Optional[UserTagRepository] = None,
        todo_tag_repo: Optional[TodoTagRepository] = None
    ):
        """
        Initialize tag service with repositories

        Args:
            predefined_repo: Repository for predefined tags (injected)
            user_repo: Repository for user tags (injected)
            todo_tag_repo: Repository for todo tags junction table (injected)
        """
        self.predefined_repo = predefined_repo or get_predefined_tag_repository()
        self.user_repo = user_repo or get_user_tag_repository()
        self.todo_tag_repo = todo_tag_repo or get_todo_tag_repository()

    async def get_predefined_tags(self) -> List[Dict[str, Any]]:
        """
        Get all predefined system tags

        Returns:
            List of predefined tag dictionaries
        """
        try:
            tags = await self.predefined_repo.get_all_predefined()
            logger.info(f"Retrieved {len(tags)} predefined tags")
            return tags

        except Exception as e:
            logger.error(f"Error fetching predefined tags: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to retrieve predefined tags",
                operation="get_predefined_tags"
            )

    async def get_user_tags(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all custom tags for a user

        Args:
            user_id: User ID

        Returns:
            List of user tag dictionaries
        """
        try:
            tags = await self.user_repo.get_by_user(user_id)
            logger.info(f"Retrieved {len(tags)} user tags for user {user_id}")
            return tags

        except Exception as e:
            logger.error(f"Error fetching user tags: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to retrieve user tags",
                operation="get_user_tags",
                details={"user_id": user_id}
            )

    async def get_all_available_tags(self, user_id: str) -> Dict[str, Any]:
        """
        Get all available tags (predefined + user custom)

        Args:
            user_id: User ID

        Returns:
            Dictionary with predefined, user, and combined tags
        """
        try:
            # Fetch both predefined and user tags in parallel
            predefined_tags = await self.predefined_repo.get_all_predefined()
            user_tags = await self.user_repo.get_by_user(user_id)

            # Format predefined tags
            predefined_formatted = [
                {
                    "name": tag["name"],
                    "category": tag.get("category", "general"),
                    "type": "predefined"
                }
                for tag in predefined_tags
            ]

            # Format user tags
            user_formatted = [
                {
                    "name": tag["name"],
                    "category": "custom",
                    "type": "user"
                }
                for tag in user_tags
            ]

            all_tags = predefined_formatted + user_formatted

            logger.info(
                f"Retrieved {len(predefined_formatted)} predefined and "
                f"{len(user_formatted)} user tags for user {user_id}"
            )

            return {
                "predefined": predefined_formatted,
                "user": user_formatted,
                "all": all_tags,
                "predefined_count": len(predefined_formatted),
                "user_count": len(user_formatted),
                "total": len(all_tags)
            }

        except Exception as e:
            logger.error(f"Error fetching all available tags: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to retrieve available tags",
                operation="get_all_available_tags",
                details={"user_id": user_id}
            )

    async def create_user_tag(self, user_id: str, name: str) -> Dict[str, Any]:
        """
        Create a new user custom tag

        Args:
            user_id: User ID
            name: Tag name

        Returns:
            Created tag dictionary

        Raises:
            ServiceError: If tag already exists or creation fails
        """
        try:
            # Check if tag already exists for this user
            existing = await self.user_repo.get_by_name(user_id, name)

            if existing:
                raise ServiceError(
                    message="Tag already exists",
                    operation="create_user_tag",
                    details={"user_id": user_id, "name": name}
                )

            # Create the tag
            tag = await self.user_repo.create_user_tag(user_id, name)
            logger.info(f"Created user tag '{name}' for user {user_id}")

            return tag

        except ServiceError:
            # Re-raise service errors
            raise

        except Exception as e:
            logger.error(f"Error creating user tag: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to create user tag",
                operation="create_user_tag",
                details={"user_id": user_id, "name": name}
            )

    async def delete_user_tag(self, user_id: str, tag_id: str) -> bool:
        """
        Delete a user custom tag

        Args:
            user_id: User ID
            tag_id: Tag ID

        Returns:
            True if deleted, False if not found

        Raises:
            ServiceError: If deletion fails
        """
        try:
            deleted = await self.user_repo.delete_user_tag(user_id, tag_id)

            if deleted:
                logger.info(f"Deleted user tag {tag_id} for user {user_id}")
            else:
                logger.warning(f"Tag {tag_id} not found for user {user_id}")

            return deleted

        except Exception as e:
            logger.error(f"Error deleting user tag: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to delete user tag",
                operation="delete_user_tag",
                details={"user_id": user_id, "tag_id": tag_id}
            )

    async def get_tag_suggestions(self, user_id: str, text: str) -> List[str]:
        """
        Get tag suggestions based on text analysis

        Args:
            user_id: User ID
            text: Text to analyze

        Returns:
            List of suggested tag names
        """
        try:
            # Get all available tags
            all_tags_data = await self.get_all_available_tags(user_id)
            all_tag_names = {tag["name"].lower() for tag in all_tags_data["all"]}

            # Simple keyword-based suggestions
            text_lower = text.lower()
            suggestions = []

            tag_patterns = {
                "fitness": ["gym", "workout", "exercise", "fitness", "run", "walk", "jog", "bike"],
                "errand": ["store", "shop", "buy", "pick up", "get", "purchase", "grocery", "mall"],
                "work": ["work", "job", "office", "project", "deadline", "meeting", "client"],
                "personal": ["personal", "self", "me", "my"],
                "health": ["doctor", "dentist", "checkup", "appointment", "health", "medicine"],
                "family": ["family", "mom", "dad", "parent", "sibling", "kids", "children"],
                "club": ["club", "organization", "society", "group", "team"]
            }

            for tag, keywords in tag_patterns.items():
                if tag in all_tag_names and any(keyword in text_lower for keyword in keywords):
                    suggestions.append(tag)

            logger.info(f"Generated {len(suggestions)} tag suggestions for text")
            return suggestions[:3]  # Limit to 3 suggestions

        except Exception as e:
            logger.error(f"Error generating tag suggestions: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to generate tag suggestions",
                operation="get_tag_suggestions",
                details={"user_id": user_id, "text": text}
            )

    async def get_tag_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get tag usage analytics for a user

        Args:
            user_id: User ID

        Returns:
            Dictionary with tag analytics data
        """
        try:
            # Get tag usage from junction table
            tag_usage_records = await self.todo_tag_repo.get_tag_usage_for_user(user_id)

            # Count tag usage
            tag_names = [record["tag_name"] for record in tag_usage_records]
            tag_counts = Counter(tag_names)

            # Format analytics data
            analytics_data = [
                {"tag_name": tag, "usage_count": count}
                for tag, count in tag_counts.items()
            ]

            # Sort by usage count
            analytics_data.sort(key=lambda x: x["usage_count"], reverse=True)

            logger.info(f"Generated tag analytics for user {user_id}: {len(analytics_data)} unique tags")

            return {
                "tag_analytics": analytics_data,
                "total_unique_tags": len(analytics_data),
                "most_used_tag": analytics_data[0] if analytics_data else None
            }

        except Exception as e:
            logger.error(f"Error generating tag analytics: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to generate tag analytics",
                operation="get_tag_analytics",
                details={"user_id": user_id}
            )

    async def get_todo_tags(self, todo_id: str) -> List[str]:
        """
        Get tags for a todo from junction table

        Args:
            todo_id: Todo ID

        Returns:
            List of tag names
        """
        try:
            tag_records = await self.todo_tag_repo.get_tags_for_todo(todo_id)
            tag_names = [record["tag_name"] for record in tag_records]

            logger.info(f"Retrieved {len(tag_names)} tags for todo {todo_id}")
            return tag_names

        except Exception as e:
            logger.error(f"Error fetching todo tags: {e}", exc_info=True)
            # Don't raise error, return empty list as fallback
            return []

    async def update_todo_tags(self, todo_id: str, tag_names: List[str]) -> bool:
        """
        Update tags for a todo (replaces existing tags)

        Args:
            todo_id: Todo ID
            tag_names: List of tag names to set

        Returns:
            True if successful

        Raises:
            ServiceError: If update fails
        """
        try:
            # Delete existing tags
            await self.todo_tag_repo.delete_by_filters({"todo_id": todo_id})

            # Insert new tags
            if tag_names:
                tag_records = [
                    {"todo_id": todo_id, "tag_name": tag}
                    for tag in tag_names
                ]
                for record in tag_records:
                    await self.todo_tag_repo.create(record)

            logger.info(f"Updated tags for todo {todo_id}: {tag_names}")
            return True

        except Exception as e:
            logger.error(f"Error updating todo tags: {e}", exc_info=True)
            raise ServiceError(
                message="Failed to update todo tags",
                operation="update_todo_tags",
                details={"todo_id": todo_id, "tag_names": tag_names}
            )

    async def process_tags_for_todo(
        self,
        provided_tags: List[str],
        title: str,
        user_id: str
    ) -> List[str]:
        """
        Process tags with intelligent selection from predefined and user custom tags

        Args:
            provided_tags: Tags explicitly provided
            title: Todo title for auto-suggestion
            user_id: User ID

        Returns:
            List of processed tag names (max 3)
        """
        try:
            # Get all available tags
            all_tags_data = await self.get_all_available_tags(user_id)
            predefined_names = {tag["name"].lower() for tag in all_tags_data["predefined"]}
            user_names = {tag["name"].lower() for tag in all_tags_data["user"]}
            all_available = predefined_names | user_names

            processed_tags = []
            title_lower = title.lower()

            # Validate explicitly provided tags
            for tag in provided_tags:
                tag_lower = tag.lower()
                if tag_lower in all_available:
                    processed_tags.append(tag_lower)

            # Auto-suggest tags based on title
            if not provided_tags or len(processed_tags) < len(provided_tags):
                auto_tags = []

                # Academic keywords
                if any(word in title_lower for word in ["homework", "assignment", "study", "exam", "test", "quiz", "project", "research", "paper", "essay", "lab", "class", "lecture", "course"]):
                    auto_tags.extend(["academic", "study"])

                # Work keywords
                if any(word in title_lower for word in ["meeting", "call", "interview", "presentation", "report", "deadline", "client", "email", "work", "job", "office"]):
                    auto_tags.extend(["work", "professional"])

                # Personal/Life keywords
                if any(word in title_lower for word in ["shopping", "shop", "buy", "pick up", "get", "purchase", "store", "groceries"]):
                    auto_tags.extend(["personal", "shopping"])
                if any(word in title_lower for word in ["clean", "cleaning", "organize", "tidy", "laundry", "dishes", "vacuum"]):
                    auto_tags.extend(["personal", "cleaning"])
                if any(word in title_lower for word in ["gym", "workout", "exercise", "fitness", "run", "walk", "yoga", "sport"]):
                    auto_tags.extend(["personal", "fitness"])
                if any(word in title_lower for word in ["doctor", "dentist", "checkup", "appointment", "health", "medical", "therapy"]):
                    auto_tags.extend(["personal", "health"])
                if any(word in title_lower for word in ["family", "mom", "dad", "parent", "sibling", "kids", "children", "friends"]):
                    auto_tags.extend(["personal", "family"])

                # Creative keywords
                if any(word in title_lower for word in ["write", "writing", "blog", "article", "creative", "design", "art", "music"]):
                    auto_tags.extend(["personal", "creative"])

                # Urgency keywords
                if any(word in title_lower for word in ["urgent", "asap", "important", "critical", "priority", "emergency", "immediately"]):
                    auto_tags.append("urgent")

                # Time-based keywords
                if any(word in title_lower for word in ["daily", "weekly", "routine", "habit"]):
                    auto_tags.append("routine")

                # Add auto-suggested tags that exist in available tags
                for auto_tag in auto_tags:
                    if auto_tag not in processed_tags and auto_tag in all_available:
                        processed_tags.append(auto_tag)

                # Create custom tags for provided tags not in system
                for tag in provided_tags:
                    tag_lower = tag.lower()
                    if tag_lower not in processed_tags and tag_lower not in all_available:
                        try:
                            await self.create_user_tag(user_id, tag_lower)
                            processed_tags.append(tag_lower)
                        except ServiceError as e:
                            # Tag might already exist, try to add it anyway
                            if "already exists" in str(e).lower():
                                processed_tags.append(tag_lower)

            logger.info(f"Processed {len(processed_tags)} tags for todo: {processed_tags}")
            return processed_tags[:3]  # Limit to 3 tags max

        except Exception as e:
            logger.error(f"Error processing tags: {e}", exc_info=True)
            # Fallback to provided tags or empty list
            return provided_tags[:3] if provided_tags else []


def get_tag_service() -> TagService:
    """
    Factory function for TagService

    Used for dependency injection in FastAPI endpoints.
    """
    return TagService()
