"""
Entity Matcher Service
Main coordinating class for entity matching
"""
import logging
from typing import Dict, Any, Optional

from .text_processor import TextProcessor
from .similarity_calculator import SimilarityCalculator
from .repository_manager import RepositoryManager
from .entity_resolver import EntityResolver

from app.database.repositories.task_repositories import TaskRepository, TodoRepository
from app.database.repositories.calendar_repositories import TimeblocksRepository

logger = logging.getLogger(__name__)


class EntityMatcher:
    """
    Matches natural language focus session input to existing entities

    Matching Priority:
    1. Tasks (especially with type='exam' or 'assignment')
    2. Upcoming exams/assignments (due soon)
    3. Todos (small action items)
    4. Recent timeblocks (by context)
    5. Create new if no good match
    """

    def __init__(
        self,
        task_repository: Optional[TaskRepository] = None,
        todo_repository: Optional[TodoRepository] = None,
        timeblocks_repository: Optional[TimeblocksRepository] = None
    ):
        """
        Initialize entity matcher with optional repository injection

        Args:
            task_repository: Optional pre-initialized task repository
            todo_repository: Optional pre-initialized todo repository
            timeblocks_repository: Optional pre-initialized timeblocks repository
        """
        # Initialize components
        self.text_processor = TextProcessor()
        self.similarity_calculator = SimilarityCalculator(self.text_processor)
        self.repo_manager = RepositoryManager(
            task_repository=task_repository,
            todo_repository=todo_repository,
            timeblocks_repository=timeblocks_repository
        )
        self.entity_resolver = EntityResolver(
            repository_manager=self.repo_manager,
            similarity_calculator=self.similarity_calculator,
            min_match_confidence=0.55  # Lowered threshold for better matching
        )

        # Configuration
        self.min_match_confidence = 0.55

    async def match_entity(
        self,
        user_id: str,
        input_text: str,
        duration_minutes: Optional[int] = None,
        parsed_data: Optional[Dict[str, Any]] = None,
        allow_auto_create: bool = True,
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Match input text to existing entity or create new one

        Args:
            user_id: User UUID
            input_text: Natural language input ("Study for bio exam")
            duration_minutes: Optional duration in minutes
            parsed_data: Optional pre-parsed structured data
            allow_auto_create: If False, never auto-create entities (returns clarification candidates instead)
            intent: Intent name (e.g., 'reschedule', 'create_calendar_event') for context

        Returns:
            {
                'entity_type': 'task|timeblock|todo|exam',
                'entity_id': 'uuid',
                'entity': {...},  # Full entity data
                'confidence': 0.0-1.0,
                'auto_created': bool,
                'match_reason': 'exact_match|fuzzy_match|keyword|created|clarification_needed',
                'candidates': [...]  # Top candidates when clarification needed
            }
        """
        try:
            logger.info(f"Matching entity for user {user_id}: '{input_text}'")

            # Parse input if not already parsed
            if not parsed_data:
                parsed_data = self.text_processor.parse_input(input_text)

            # Extract key info
            keywords = parsed_data.get('keywords', [])
            entity_type_hint = parsed_data.get('type')  # 'exam', 'assignment', etc.
            course_hint = parsed_data.get('course')

            # Try matching in priority order
            match = None

            # 1. Try exact/fuzzy match with tasks
            match = await self.entity_resolver.match_tasks(
                user_id,
                input_text,
                keywords,
                entity_type_hint,
                course_hint
            )

            if match and match['confidence'] >= self.min_match_confidence:
                return match

            # 2. Try matching upcoming exams/assignments
            if not match or match['confidence'] < 0.8:
                exam_match = await self.entity_resolver.match_upcoming_exams(
                    user_id,
                    input_text,
                    keywords,
                    course_hint
                )
                if exam_match and exam_match['confidence'] > (match['confidence'] if match else 0):
                    match = exam_match

            # 3. Try matching todos
            if not match or match['confidence'] < 0.7:
                todo_match = await self.entity_resolver.match_todos(
                    user_id,
                    input_text,
                    keywords
                )
                if todo_match and todo_match['confidence'] > (match['confidence'] if match else 0):
                    match = todo_match

            # 4. Try matching recent timeblocks
            if not match or match['confidence'] < 0.6:
                timeblock_match = await self.entity_resolver.match_timeblocks(
                    user_id,
                    input_text,
                    keywords
                )
                if timeblock_match and timeblock_match['confidence'] > (match['confidence'] if match else 0):
                    match = timeblock_match

            # 5. Handle no good match
            if not match or match['confidence'] < self.min_match_confidence:
                # For reschedule/calendar intents, never auto-create - ask for clarification
                if not allow_auto_create or intent in ["reschedule", "create_calendar_event"]:
                    # Collect top candidates for clarification
                    all_candidates = await self.entity_resolver.collect_all_candidates(
                        user_id, input_text, keywords, entity_type_hint, course_hint
                    )
                    # Return top 3 candidates for clarification
                    top_candidates = sorted(all_candidates, key=lambda x: x['confidence'], reverse=True)[:3]
                    logger.info(f"Entity match failed - top candidates: {[(c['title'], c['confidence']) for c in top_candidates]}")
                    return {
                        'entity_type': None,
                        'entity_id': None,
                        'entity': None,
                        'confidence': top_candidates[0]['confidence'] if top_candidates else 0.0,
                        'auto_created': False,
                        'match_reason': 'clarification_needed',
                        'candidates': top_candidates
                    }

                # Otherwise, create new entity
                match = await self.entity_resolver.create_new_entity(
                    user_id,
                    input_text,
                    parsed_data,
                    duration_minutes
                )

            logger.info(
                f"Entity match result: {match['entity_type']} "
                f"(confidence: {match['confidence']:.2f}, "
                f"reason: {match['match_reason']})"
            )

            return match

        except Exception as e:
            logger.error(f"Error matching entity: {e}", exc_info=True)
            # Fallback: only create if allowed
            if allow_auto_create and intent not in ["reschedule", "create_calendar_event"]:
                return await self.entity_resolver.create_new_entity(
                    user_id,
                    input_text,
                    {'name': input_text},
                    duration_minutes
                )
            else:
                return {
                    'entity_type': None,
                    'entity_id': None,
                    'entity': None,
                    'confidence': 0.0,
                    'auto_created': False,
                    'match_reason': 'error',
                    'candidates': []
                }


# Singleton
_entity_matcher: Optional[EntityMatcher] = None


def get_entity_matcher() -> EntityMatcher:
    """Get or create EntityMatcher singleton"""
    global _entity_matcher
    if _entity_matcher is None:
        _entity_matcher = EntityMatcher()
    return _entity_matcher
