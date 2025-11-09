"""
Data repository for scheduler persistence.

Thin wrapper around modular repository implementation.
For full implementation, see repositories/ subdirectory.
"""

# Import from modular implementation
from .repositories import Repository, get_repository

# Re-export for backward compatibility
__all__ = ['Repository', 'get_repository']
