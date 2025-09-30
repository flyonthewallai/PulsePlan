"""
Compatibility package for app.core.config

This package redirects imports from the old app.core.config location
to the new app.config.core.settings location for backward compatibility.
"""

# Import everything from the new location
from app.config.core.settings import *
from app.config.core.settings import get_settings

# Provide backward compatibility aliases
settings = get_settings()

# Re-export commonly used items
__all__ = [
    "Settings",
    "settings",
    "get_settings",
    "Environment"
]