"""
Centralized path setup for fabric-ui imports

This module handles the sys.path configuration needed for fabric-ui components
to import from the parent hypr-sessions directory. Eliminates duplicate path
setup code across multiple files.
"""

import sys
from pathlib import Path


def setup_fabric_ui_imports():
    """Add parent directory to sys.path for fabric-ui imports
    
    This allows fabric-ui components to import from the main hypr-sessions
    directory (constants, utils, etc.) without duplicating path setup code.
    """
    # Get the hypr-sessions directory (parent of fabric-ui)
    parent_dir = str(Path(__file__).parent.parent.parent)
    
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)


# Auto-setup when this module is imported
setup_fabric_ui_imports()