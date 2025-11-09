"""
Similarity Calculator Module
Calculates similarity scores between text strings for entity matching
"""
import logging
import re
from typing import List
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SimilarityCalculator:
    """
    Calculates similarity between text strings

    Uses multiple algorithms:
    - Exact matching
    - Substring matching (contains/starts-with)
    - Sequence matching (Levenshtein-like)
    - Keyword overlap
    - Word overlap
    """

    def __init__(self, text_processor):
        """
        Initialize similarity calculator

        Args:
            text_processor: TextProcessor instance for text normalization
        """
        self.text_processor = text_processor

    def calculate_similarity(
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
        - Contains match
        - Sequence matching (difflib)
        - Keyword overlap
        - Word overlap

        Args:
            text1: First text (usually user input)
            text2: Second text (usually entity name)
            keywords: Keywords extracted from text1

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Extract core entity name from text1 (in case it's an action query)
        text1_entity = self.text_processor.extract_entity_name(text1)

        # Use original text1 if extraction didn't help much
        if len(text1_entity) < len(text1) * 0.5:
            text1_entity = text1

        # Normalize both texts
        text1_norm = self.text_processor.normalize_text(text1_entity)
        text2_norm = self.text_processor.normalize_text(text2)

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
        sequence_score = self._calculate_sequence_score(text1_norm, text2_norm)

        # 5. Keyword overlap with normalization
        keyword_score = self._calculate_keyword_score(text1_norm, text2_norm, keywords)

        # 6. Word overlap (both directions) - more weight for significant overlap
        word_overlap = self._calculate_word_overlap(text1_norm, text2_norm)

        # 7. Weighted combination
        final_score = (sequence_score * 0.4) + (keyword_score * 0.3) + (word_overlap * 0.3)

        return min(final_score, 1.0)

    def _calculate_sequence_score(self, text1: str, text2: str) -> float:
        """Calculate sequence similarity using SequenceMatcher"""
        return SequenceMatcher(None, text1, text2).ratio()

    def _calculate_keyword_score(
        self,
        text1: str,
        text2: str,
        keywords: List[str]
    ) -> float:
        """Calculate keyword overlap score"""
        text2_words = set(re.findall(r'\b\w+\b', text2))
        keyword_matches = sum(1 for kw in keywords if kw in text2_words)
        return keyword_matches / max(len(keywords), 1) if keywords else 0

    def _calculate_word_overlap(self, text1: str, text2: str) -> float:
        """Calculate word overlap score"""
        text1_words = set(re.findall(r'\b\w+\b', text1))
        text2_words = set(re.findall(r'\b\w+\b', text2))
        return len(text1_words & text2_words) / max(len(text1_words | text2_words), 1)
