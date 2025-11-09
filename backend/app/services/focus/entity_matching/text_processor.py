"""
Text Processing Module
Handles parsing, normalization, and entity name extraction from natural language input
"""
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Processes and normalizes text for entity matching

    Handles:
    - Input parsing (extracting keywords, type hints, course hints)
    - Text normalization (lowercasing, whitespace handling)
    - Entity name extraction from action queries
    """

    def __init__(self):
        # Common subject keywords for course detection
        self.common_subjects = [
            'biology', 'bio', 'chemistry', 'chem', 'physics', 'math',
            'history', 'english', 'literature', 'computer science', 'cs',
            'economics', 'econ', 'psychology', 'psych', 'sociology'
        ]

        # Action words to filter out when extracting entity names
        self.action_words = [
            'move', 'reschedule', 'shift', 'change', 'update', 'edit',
            'to', 'for', 'at', 'on', 'in', 'from'
        ]

        # Time references to filter out
        self.time_references = [
            'tomorrow', 'today', 'yesterday',
            'monday', 'tuesday', 'wednesday', 'thursday',
            'friday', 'saturday', 'sunday'
        ]

    def parse_input(self, input_text: str) -> Dict[str, Any]:
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
        entity_type = self._detect_entity_type(text_lower)

        # Extract duration
        duration = self._extract_duration(text_lower)

        # Extract potential course name
        course = self._extract_course(text_lower)

        # Clean name (remove duration and filler words)
        name = self._clean_name(input_text, duration)

        return {
            'name': name,
            'type': entity_type,
            'course': course,
            'keywords': keywords,
            'duration': duration
        }

    def _detect_entity_type(self, text_lower: str) -> str:
        """Detect entity type from text"""
        if any(word in text_lower for word in ['exam', 'test', 'midterm', 'final']):
            return 'exam'
        elif any(word in text_lower for word in ['assignment', 'homework', 'hw', 'essay', 'paper']):
            return 'assignment'
        elif any(word in text_lower for word in ['todo', 'task', 'do']):
            return 'todo'
        elif any(word in text_lower for word in ['study', 'review', 'prep', 'prepare']):
            return 'task'
        return None

    def _extract_duration(self, text_lower: str) -> int:
        """Extract duration in minutes from text"""
        duration_match = re.search(r'(\d+)\s*(min|minute|hour|hr)', text_lower)
        if duration_match:
            value = int(duration_match.group(1))
            unit = duration_match.group(2)
            return value if 'min' in unit else value * 60
        return None

    def _extract_course(self, text_lower: str) -> str:
        """Extract course/subject name from text"""
        for subject in self.common_subjects:
            if subject in text_lower:
                return subject.title()
        return None

    def _clean_name(self, input_text: str, duration_match_result: int) -> str:
        """Clean entity name by removing duration and filler words"""
        name = input_text

        # Find and remove duration text
        duration_match = re.search(r'(\d+)\s*(min|minute|hour|hr)', input_text.lower())
        if duration_match:
            name = name[:duration_match.start()].strip()

        # Remove filler words
        name = re.sub(r'\bfor\s+(my|the|a)\b', '', name, flags=re.IGNORECASE).strip()

        return name

    def normalize_text(self, text: str) -> str:
        """
        Normalize text: trim, lowercase, collapse whitespace

        Args:
            text: Input text to normalize

        Returns:
            Normalized text (lowercase, single spaces)
        """
        if not text:
            return ""
        # Collapse multiple spaces/tabs/newlines to single space
        normalized = re.sub(r'\s+', ' ', text.strip())
        return normalized.lower()

    def extract_entity_name(self, text: str) -> str:
        """
        Extract the core entity name from action queries

        Example: 'move bio study block to tomorrow' -> 'bio study block'

        Args:
            text: Input query text

        Returns:
            Extracted entity name
        """
        words = text.lower().split()
        filtered = []
        skip_next = False

        for i, word in enumerate(words):
            if skip_next:
                skip_next = False
                continue

            # Skip action verbs
            if word in self.action_words:
                # If we see 'to', 'for', 'at', 'on' - likely the entity name ended
                if word in ['to', 'for', 'at', 'on', 'in']:
                    break
                continue

            # Skip time references (tomorrow, today, monday, etc.)
            if word in self.time_references:
                break

            # Skip numbers that might be times
            if word.isdigit() and i < len(words) - 1 and words[i+1] in ['am', 'pm', 'hour', 'hours']:
                break

            filtered.append(word)

        return ' '.join(filtered).strip()
