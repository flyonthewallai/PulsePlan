"""
Entity Matcher Service
Thin wrapper for backward compatibility - imports from modular entity_matching package
"""
from app.services.focus.entity_matching import (
    EntityMatcher,
    get_entity_matcher
)

__all__ = [
    'EntityMatcher',
    'get_entity_matcher'
]
