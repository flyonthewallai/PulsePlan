"""
Entity Matcher Service
Intelligently matches natural language input to existing tasks, exams, todos, and timeblocks
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

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
        self._task_repository = task_repository
        self._todo_repository = todo_repository
        self._timeblocks_repository = timeblocks_repository
        self.min_match_confidence = 0.55  # Lowered threshold for better matching
    
    @property
    def task_repository(self) -> TaskRepository:
        """Lazy-load task repository"""
        if self._task_repository is None:
            self._task_repository = get_task_repository()
        return self._task_repository
    
    @property
    def todo_repository(self) -> TodoRepository:
        """Lazy-load todo repository"""
        if self._todo_repository is None:
            self._todo_repository = TodoRepository()
        return self._todo_repository
    
    @property
    def timeblocks_repository(self) -> TimeblocksRepository:
        """Lazy-load timeblocks repository"""
        if self._timeblocks_repository is None:
            self._timeblocks_repository = get_timeblocks_repository()
        return self._timeblocks_repository
    
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
                parsed_data = self._parse_input(input_text)
            
            # Extract key info
            keywords = parsed_data.get('keywords', [])
            entity_type_hint = parsed_data.get('type')  # 'exam', 'assignment', etc.
            course_hint = parsed_data.get('course')
            
            # Try matching in priority order
            match = None
            
            # 1. Try exact/fuzzy match with tasks
            match = await self._match_tasks(
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
                exam_match = await self._match_upcoming_exams(
                    user_id,
                    input_text,
                    keywords,
                    course_hint
                )
                if exam_match and exam_match['confidence'] > (match['confidence'] if match else 0):
                    match = exam_match
            
            # 3. Try matching todos
            if not match or match['confidence'] < 0.7:
                todo_match = await self._match_todos(
                    user_id,
                    input_text,
                    keywords
                )
                if todo_match and todo_match['confidence'] > (match['confidence'] if match else 0):
                    match = todo_match
            
            # 4. Try matching recent timeblocks
            if not match or match['confidence'] < 0.6:
                timeblock_match = await self._match_timeblocks(
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
                    all_candidates = await self._collect_all_candidates(
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
                match = await self._create_new_entity(
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
                return await self._create_new_entity(
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
    
    def _parse_input(self, input_text: str) -> Dict[str, Any]:
        """
        Parse natural language input into structured data
        
        Example: "Study for my biology exam for 45 minutes"
        Returns: {
            'name': 'Study for biology exam',
            'type': 'exam',
            'course': 'biology',
            'keywords': ['study', 'biology', 'exam'],
            'duration': 45
        }
        """
        text_lower = input_text.lower()
        
        # Extract keywords
        keywords = [
            word for word in re.findall(r'\b\w+\b', text_lower)
            if len(word) > 2  # Skip short words
        ]
        
        # Detect type
        entity_type = None
        if any(word in text_lower for word in ['exam', 'test', 'midterm', 'final']):
            entity_type = 'exam'
        elif any(word in text_lower for word in ['assignment', 'homework', 'hw', 'essay', 'paper']):
            entity_type = 'assignment'
        elif any(word in text_lower for word in ['todo', 'task', 'do']):
            entity_type = 'todo'
        elif any(word in text_lower for word in ['study', 'review', 'prep', 'prepare']):
            entity_type = 'task'
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*(min|minute|hour|hr)', text_lower)
        duration = None
        if duration_match:
            value = int(duration_match.group(1))
            unit = duration_match.group(2)
            duration = value if 'min' in unit else value * 60
        
        # Extract potential course name
        course = None
        common_subjects = [
            'biology', 'bio', 'chemistry', 'chem', 'physics', 'math', 
            'history', 'english', 'literature', 'computer science', 'cs',
            'economics', 'econ', 'psychology', 'psych', 'sociology'
        ]
        for subject in common_subjects:
            if subject in text_lower:
                course = subject.title()
                break
        
        # Clean name (remove duration and filler words)
        name = input_text
        if duration_match:
            name = name[:duration_match.start()].strip()
        name = re.sub(r'\bfor\s+(my|the|a)\b', '', name, flags=re.IGNORECASE).strip()
        
        return {
            'name': name,
            'type': entity_type,
            'course': course,
            'keywords': keywords,
            'duration': duration
        }
    
    async def _match_tasks(
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
            
            # Filter by course if hinted (course_hint used in post-filtering)
            # Note: Repository doesn't support ILIKE, so we filter in-memory
            
            # Query tasks using repository
            tasks = await self.task_repository.get_by_user(
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
                score = self._calculate_similarity(
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
    
    async def _match_upcoming_exams(
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
            tasks = await self.task_repository.get_by_user(
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
                score = self._calculate_similarity(
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
    
    async def _match_todos(
        self,
        user_id: str,
        input_text: str,
        keywords: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Match against todos"""
        try:
            # Query todos using repository
            todos = await self.todo_repository.get_by_user(
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
                score = self._calculate_similarity(
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
    
    async def _match_timeblocks(
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
            timeblocks = await self.timeblocks_repository.fetch_timeblocks(
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
                score = self._calculate_similarity(
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
    
    async def _create_new_entity(
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
                
                new_todo = await self.todo_repository.create(todo_data)
                
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
            
            new_task = await self.task_repository.create(task_data)
            
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
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: trim, lowercase, collapse whitespace"""
        if not text:
            return ""
        # Collapse multiple spaces/tabs/newlines to single space
        normalized = re.sub(r'\s+', ' ', text.strip())
        return normalized.lower()
    
    def _extract_entity_name(self, text: str) -> str:
        """Extract the core entity name from action queries like 'move bio study block to tomorrow' -> 'bio study block'"""
        # Remove common action verbs and prepositions
        action_words = ['move', 'reschedule', 'shift', 'change', 'update', 'edit', 'to', 'for', 'at', 'on', 'in', 'from']
        words = text.lower().split()
        # Filter out action words and time references
        filtered = []
        skip_next = False
        for i, word in enumerate(words):
            if skip_next:
                skip_next = False
                continue
            # Skip action verbs
            if word in action_words:
                # If we see 'to', 'for', 'at', 'on' - likely the entity name ended
                if word in ['to', 'for', 'at', 'on', 'in']:
                    break
                continue
            # Skip time references (tomorrow, today, monday, etc.)
            if word in ['tomorrow', 'today', 'yesterday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                break
            # Skip numbers that might be times
            if word.isdigit() and i < len(words) - 1 and words[i+1] in ['am', 'pm', 'hour', 'hours']:
                break
            filtered.append(word)
        return ' '.join(filtered).strip()
    
    def _calculate_similarity(
        self,
        text1: str,
        text2: str,
        keywords: List[str]
    ) -> float:
        """
        Calculate similarity between two texts with enhanced matching
        
        Returns score 0.0-1.0 based on:
        - Exact match (case-insensitive)
        - Starts-with match
        - Sequence matching (difflib)
        - Keyword overlap
        """
        # Extract core entity name from text1 (in case it's an action query)
        text1_entity = self._extract_entity_name(text1)
        # Use original text1 if extraction didn't help much
        if len(text1_entity) < len(text1) * 0.5:
            text1_entity = text1
        
        # Normalize both texts
        text1_norm = self._normalize_text(text1_entity)
        text2_norm = self._normalize_text(text2)
        
        # 1. Exact match boost (highest priority)
        if text1_norm == text2_norm:
            return 1.0
        
        # 2. Contains match boost (high priority for entity names)
        if text1_norm in text2_norm or text2_norm in text1_norm:
            base_score = 0.85
            # Boost if significant portion matches
            overlap_ratio = min(len(text1_norm), len(text2_norm)) / max(len(text1_norm), len(text2_norm), 1)
            return base_score + (overlap_ratio * 0.15)
        
        # 3. Starts-with boost (high priority)
        if text2_norm.startswith(text1_norm) or text1_norm.startswith(text2_norm):
            base_score = 0.9
            # Boost if significant portion matches
            overlap_ratio = min(len(text1_norm), len(text2_norm)) / max(len(text1_norm), len(text2_norm), 1)
            return base_score + (overlap_ratio * 0.1)
        
        # 4. Sequence matcher (Levenshtein-like)
        sequence_score = SequenceMatcher(None, text1_norm, text2_norm).ratio()
        
        # 5. Keyword overlap with normalization
        text1_words = set(re.findall(r'\b\w+\b', text1_norm))
        text2_words = set(re.findall(r'\b\w+\b', text2_norm))
        keyword_matches = sum(1 for kw in keywords if kw in text2_words)
        keyword_score = keyword_matches / max(len(keywords), 1) if keywords else 0
        
        # 6. Word overlap (both directions) - more weight for significant overlap
        word_overlap = len(text1_words & text2_words) / max(len(text1_words | text2_words), 1)
        
        # 7. Weighted combination
        final_score = (sequence_score * 0.4) + (keyword_score * 0.3) + (word_overlap * 0.3)
        
        return min(final_score, 1.0)
    
    async def _collect_all_candidates(
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
            tasks = await self.task_repository.get_by_user(
                user_id=user_id,
                filters={"order_by": "updated_at", "order_desc": True},
                limit=30
            )
            for task in tasks:
                if task.get("status") == "completed":
                    continue
                score = self._calculate_similarity(input_text, task['title'], keywords)
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
            todos = await self.todo_repository.get_by_user(
                user_id=user_id,
                filters={"completed": False}
            )
            # Limit to 20 most recent
            todos = todos[:20]
            for todo in todos:
                score = self._calculate_similarity(input_text, todo['title'], keywords)
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
            timeblocks = await self.timeblocks_repository.fetch_timeblocks(
                user_id=user_id,
                dt_from=window_start,
                dt_to=window_end
            )
            # Sort and limit to 100
            timeblocks = sorted(timeblocks, key=lambda x: x.get("start_at", ""), reverse=True)[:100]
            for block in timeblocks:
                score = self._calculate_similarity(input_text, block.get('title', ''), keywords)
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


# Singleton
_entity_matcher: Optional[EntityMatcher] = None


def get_entity_matcher() -> EntityMatcher:
    """Get or create EntityMatcher singleton"""
    global _entity_matcher
    if _entity_matcher is None:
        _entity_matcher = EntityMatcher()
    return _entity_matcher



