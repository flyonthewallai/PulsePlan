"""
Compatibility module for app.core.config.settings

This module redirects imports from the old app.core.config.settings location
to the new app.config.core.settings location for backward compatibility.
"""

# Import everything from the new location and re-export
from app.config.core.settings import *