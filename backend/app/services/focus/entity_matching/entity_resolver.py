"""
Entity Resolver Module
Core entity matching logic for tasks, exams, todos, and timeblocks
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class EntityResolver:
    """
    Resolves natural language input to existing entities

    Matching Priority:
    1. Tasks (especially with type='exam' or 'assignment')
    2. Upcoming exams/assignments (due soon)
    3. Todos (small action items)
    4. Recent timeblocks (by context)
    """

    def __init__(self, repository_manager, similarity_calculator, min_match_confidence: float = 0.55):
        """
        Initialize entity resolver

        Args:
            repository_manager: RepositoryManager instance
            similarity_calculator: SimilarityCalculator instance
            min_match_confidence: Minimum confidence threshold for matches
        """
        self.repo_manager = repository_manager
        self.similarity_calculator = similarity_calculator
        self.min_match_confidence = min_match_confidence

    async def match_tasks(
        self,
        user_id: str,
        input_text: str,
        keywords: List[str],
        type_hint: Optional[str],
        course_hint: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Match against existing tasks"""
        try:
            # Build filters for repository query
            filters = {
                "order_by": "updated_at",
                "order_desc": True
            }

            # Filter by type if hinted
            if type_hint in ['exam', 'assignment']:
                filters["task_type"] = type_hint

            # Query tasks using repository
            tasks = await self.repo_manager.task_repository.get_by_user(
                user_id=user_id,
                filters=filters,
                limit=50
            )

            # Filter out completed tasks and apply course hint in-memory
            filtered_tasks = []
            for task in tasks:
                if task.get("status") == "completed":
                    continue
                if course_hint and task.get("course"):
                    if course_hint.lower() not in task.get("course", "").lower():
                        continue
                filtered_tasks.append(task)

            if not filtered_tasks:
                return None

            # Find best match and collect top candidates for logging
            best_match = None
            best_score = 0
            candidates_with_scores = []

            for task in filtered_tasks:
                score = self.similarity_calculator.calculate_similarity(
                    input_text,
                    task['title'],
                    keywords
                )

                # Boost score if types match
                if type_hint and task.get('task_type') == type_hint:
                    score *= 1.2

                # Boost score if course matches
                if course_hint and task.get('course'):
                    if course_hint.lower() in task['course'].lower():
                        score *= 1.3

                # Boost score if due soon (within 7 days)
                if task.get('due_date'):
                    try:
                        due_date = datetime.fromisoformat(task['due_date'].replace('Z', '+00:00'))
                        days_until = (due_date - datetime.utcnow()).days
                        if 0 <= days_until <= 7:
                            score *= 1.1
                    except:
                        pass

                candidates_with_scores.append((task, score))

                if score > best_score:
                    best_score = score
                    best_match = task

            # Log top 3 candidates
            top_candidates = sorted(candidates_with_scores, key=lambda x: x[1], reverse=True)[:3]
            if top_candidates:
                logger.info(f"Task matching - top 3 candidates: {[(c[0]['title'], f'{c[1]:.3f}') for c in top_candidates]}")

            if best_match and best_score >= self.min_match_confidence:
                return {
                    'entity_type': 'task',
                    'entity_id': best_match['id'],
                    'entity': best_match,
                    'confidence': min(best_score, 1.0),
                    'auto_created': False,
                    'match_reason': 'fuzzy_match' if best_score < 0.9 else 'exact_match'
                }

            return None

        except Exception as e:
            logger.error(f"Error matching tasks: {e}")
            return None

    async def match_upcoming_exams(
        self,
        user_id: str,
        input_text: str,
        keywords: List[str],
        course_hint: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Match against upcoming exams/assignments"""
        try:
            # Query upcoming exams/assignments within 30 days
            future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

            # Build filters for repository
            filters = {
                "due_before": future_date,
                "order_by": "due_date",
                "order_desc": False
            }

            # Query tasks using repository
            tasks = await self.repo_manager.task_repository.get_by_user(
                user_id=user_id,
                filters=filters,
                limit=20
            )

            # Filter to only exam/quiz/assignment types and not completed
            filtered_tasks = []
            for task in tasks:
                if task.get("task_type") in ["exam", "quiz", "assignment"] and task.get("status") != "completed":
                    filtered_tasks.append(task)

            if not filtered_tasks:
                return None

            # Find best match (prioritize by due date proximity)
            best_match = None
            best_score = 0
            candidates_with_scores = []

            for task in filtered_tasks:
                score = self.similarity_calculator.calculate_similarity(
                    input_text,
                    task['title'],
                    keywords
                )

                # Strong boost for course match
                if course_hint and task.get('course'):
                    if course_hint.lower() in task['course'].lower():
                        score *= 1.5

                # Boost for sooner due dates
                if task.get('due_date'):
                    try:
                        due_date = datetime.fromisoformat(task['due_date'].replace('Z', '+00:00'))
                        days_until = (due_date - datetime.utcnow()).days
                        if 0 <= days_until <= 3:
                            score *= 1.3  # Due very soon
                        elif days_until <= 7:
                            score *= 1.1  # Due this week
                    except:
                        pass

                candidates_with_scores.append((task, score))

                if score > best_score:
                    best_score = score
                    best_match = task

            # Log top 3 candidates
            top_candidates = sorted(candidates_with_scores, key=lambda x: x[1], reverse=True)[:3]
            if top_candidates:
                logger.info(f"Exam matching - top 3 candidates: {[(c[0]['title'], f'{c[1]:.3f}') for c in top_candidates]}")

            if best_match and best_score >= self.min_match_confidence:
                return {
                    'entity_type': 'exam' if best_match.get('task_type') == 'exam' else 'task',
                    'entity_id': best_match['id'],
                    'entity': best_match,
                    'confidence': min(best_score, 1.0),
                    'auto_created': False,
                    'match_reason': 'upcoming_exam'
                }

            return None

        except Exception as e:
            logger.error(f"Error matching exams: {e}")
            return None

    async def match_todos(
        self,
        user_id: str,
        input_text: str,
        keywords: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Match against todos"""
        try:
            # Query todos using repository
            todos = await self.repo_manager.todo_repository.get_by_user(
                user_id=user_id,
                filters={"completed": False}
            )

            # Limit to 30 most recent
            todos = todos[:30] if len(todos) > 30 else todos

            if not todos:
                return None

            best_match = None
            best_score = 0
            candidates_with_scores = []

            for todo in todos:
                score = self.similarity_calculator.calculate_similarity(
                    input_text,
                    todo['title'],
                    keywords
                )

                candidates_with_scores.append((todo, score))

                if score > best_score:
                    best_score = score
                    best_match = todo

            # Log top 3 candidates
            top_candidates = sorted(candidates_with_scores, key=lambda x: x[1], reverse=True)[:3]
            if top_candidates:
                logger.info(f"Todo matching - top 3 candidates: {[(c[0]['title'], f'{c[1]:.3f}') for c in top_candidates]}")

            if best_match and best_score >= self.min_match_confidence:
                return {
                    'entity_type': 'todo',
                    'entity_id': best_match['id'],
                    'entity': best_match,
                    'confidence': min(best_score, 1.0),
                    'auto_created': False,
                    'match_reason': 'todo_match'
                }

            return None

        except Exception as e:
            logger.error(f"Error matching todos: {e}")
            return None

    async def match_timeblocks(
        self,
        user_id: str,
        input_text: str,
        keywords: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Match against unified timeblocks (Pulse + external) via v_timeblocks"""
        try:
            # Query broader rolling window on unified view using repository
            window_start = datetime.now(timezone.utc) - timedelta(days=14)
            window_end = datetime.now(timezone.utc) + timedelta(days=30)

            # Use timeblocks repository
            timeblocks = await self.repo_manager.timeblocks_repository.fetch_timeblocks(
                user_id=user_id,
                dt_from=window_start,
                dt_to=window_end
            )

            # Sort and limit to 200 most recent
            timeblocks = sorted(timeblocks, key=lambda x: x.get("start_at", ""), reverse=True)[:200]

            if not timeblocks:
                return None

            best_match = None
            best_score = 0
            candidates_with_scores = []

            for block in timeblocks:
                score = self.similarity_calculator.calculate_similarity(
                    input_text,
                    block.get('title', ''),
                    keywords
                )
                # Boost upcoming blocks slightly
                try:
                    start_iso = block.get('start_at')
                    if start_iso:
                        start_dt = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
                        if start_dt >= datetime.utcnow():
                            score *= 1.1
                except Exception:
                    pass

                candidates_with_scores.append((block, score))

                if score > best_score:
                    best_score = score
                    best_match = block

            # Log top 3 candidates
            top_candidates = sorted(candidates_with_scores, key=lambda x: x[1], reverse=True)[:3]
            if top_candidates:
                logger.info(f"Timeblock matching - top 3 candidates: {[(c[0].get('title', 'Untitled'), f'{c[1]:.3f}') for c in top_candidates]}")

            if best_match and best_score >= self.min_match_confidence:
                result = {
                    'entity_type': 'timeblock',
                    'entity_id': best_match['id'],
                    'entity': best_match,
                    'confidence': min(best_score, 1.0),
                    'auto_created': False,
                    'match_reason': 'timeblock_match'
                }
                # Preserve provider fields so downstream can route calendar edits
                if 'provider' in best_match:
                    result['provider'] = best_match.get('provider')
                    result['provider_event_id'] = best_match.get('provider_event_id')
                    result['provider_calendar_id'] = best_match.get('provider_calendar_id')
                    result['source'] = best_match.get('source')
                return result

            return None

        except Exception as e:
            logger.error(f"Error matching timeblocks: {e}")
            return None

    async def collect_all_candidates(
        self,
        user_id: str,
        input_text: str,
        keywords: List[str],
        entity_type_hint: Optional[str],
        course_hint: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Collect all candidates from all sources for clarification"""
        candidates = []

        # Collect from tasks using repository
        try:
            tasks = await self.repo_manager.task_repository.get_by_user(
                user_id=user_id,
                filters={"order_by": "updated_at", "order_desc": True},
                limit=30
            )
            for task in tasks:
                if task.get("status") == "completed":
                    continue
                score = self.similarity_calculator.calculate_similarity(input_text, task['title'], keywords)
                if entity_type_hint and task.get('task_type') == entity_type_hint:
                    score *= 1.2
                if course_hint and task.get('course') and course_hint.lower() in task['course'].lower():
                    score *= 1.3
                candidates.append({
                    'entity_type': 'task',
                    'entity_id': task['id'],
                    'title': task['title'],
                    'confidence': min(score, 1.0),
                    'entity': task
                })
        except Exception as e:
            logger.warning(f"Error collecting task candidates: {e}")

        # Collect from todos using repository
        try:
            todos = await self.repo_manager.todo_repository.get_by_user(
                user_id=user_id,
                filters={"completed": False}
            )
            # Limit to 20 most recent
            todos = todos[:20]
            for todo in todos:
                score = self.similarity_calculator.calculate_similarity(input_text, todo['title'], keywords)
                candidates.append({
                    'entity_type': 'todo',
                    'entity_id': todo['id'],
                    'title': todo['title'],
                    'confidence': min(score, 1.0),
                    'entity': todo
                })
        except Exception as e:
            logger.warning(f"Error collecting todo candidates: {e}")

        # Collect from timeblocks using repository
        try:
            window_start = datetime.now(timezone.utc) - timedelta(days=14)
            window_end = datetime.now(timezone.utc) + timedelta(days=30)
            timeblocks = await self.repo_manager.timeblocks_repository.fetch_timeblocks(
                user_id=user_id,
                dt_from=window_start,
                dt_to=window_end
            )
            # Sort and limit to 100
            timeblocks = sorted(timeblocks, key=lambda x: x.get("start_at", ""), reverse=True)[:100]
            for block in timeblocks:
                score = self.similarity_calculator.calculate_similarity(input_text, block.get('title', ''), keywords)
                # Boost upcoming blocks
                try:
                    start_iso = block.get('start_at')
                    if start_iso:
                        start_dt = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
                        if start_dt >= datetime.utcnow():
                            score *= 1.1
                except Exception:
                    pass
                candidates.append({
                    'entity_type': 'timeblock',
                    'entity_id': block['id'],
                    'title': block.get('title', 'Untitled'),
                    'confidence': min(score, 1.0),
                    'entity': block
                })
        except Exception as e:
            logger.warning(f"Error collecting timeblock candidates: {e}")

        return candidates

    async def create_new_entity(
        self,
        user_id: str,
        input_text: str,
        parsed_data: Dict[str, Any],
        duration_minutes: Optional[int]
    ) -> Dict[str, Any]:
        """Create a new task/todo based on input"""
        try:
            name = parsed_data.get('name', input_text)
            entity_type = parsed_data.get('type', 'task')
            course = parsed_data.get('course')

            # Decide whether to create task or todo
            # Todo if: very short (< 15 min), simple action verbs, or has "todo" keyword
            is_todo = (
                (duration_minutes and duration_minutes < 15) or
                any(word in input_text.lower() for word in ['email', 'call', 'message', 'send', 'check'])
            )

            if is_todo:
                # Create todo using repository
                todo_data = {
                    'user_id': user_id,
                    'title': name,
                    'estimated_minutes': duration_minutes
                }

                new_todo = await self.repo_manager.todo_repository.create(todo_data)

                if new_todo:
                    logger.info(f"Created new todo: {new_todo['id']}")
                    return {
                        'entity_type': 'todo',
                        'entity_id': new_todo['id'],
                        'entity': new_todo,
                        'confidence': 1.0,
                        'auto_created': True,
                        'match_reason': 'created'
                    }

            # Create task using repository
            task_data = {
                'user_id': user_id,
                'title': name,
                'task_type': entity_type if entity_type in ['exam', 'assignment', 'quiz'] else 'task',
                'estimated_minutes': duration_minutes,
                'course': course,
                'status': 'pending'
            }

            new_task = await self.repo_manager.task_repository.create(task_data)

            if new_task:
                logger.info(f"Created new task: {new_task['id']}")
                return {
                    'entity_type': 'task',
                    'entity_id': new_task['id'],
                    'entity': new_task,
                    'confidence': 1.0,
                    'auto_created': True,
                    'match_reason': 'created'
                }

            # Fallback: return None (will use context only)
            raise Exception("Failed to create entity")

        except Exception as e:
            logger.error(f"Error creating new entity: {e}", exc_info=True)
            # Return a match result without entity (will rely on context field)
            return {
                'entity_type': 'task',
                'entity_id': None,
                'entity': None,
                'confidence': 0.5,
                'auto_created': False,
                'match_reason': 'no_entity'
            }
