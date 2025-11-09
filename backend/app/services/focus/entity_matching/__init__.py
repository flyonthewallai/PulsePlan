"""
Entity Matching Package
Modular entity matching system for natural language input
"""
from .entity_matcher import EntityMatcher, get_entity_matcher
from .text_processor import TextProcessor
from .similarity_calculator import SimilarityCalculator
from .repository_manager import RepositoryManager
from .entity_resolver import EntityResolver

__all__ = [
    'EntityMatcher',
    'get_entity_matcher',
    'TextProcessor',
    'SimilarityCalculator',
    'RepositoryManager',
    'EntityResolver',
]
