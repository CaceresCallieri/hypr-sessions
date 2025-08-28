"""
Utilities package for Hypr Sessions Manager
"""

# Centralized path setup - must be imported first
from .path_setup import setup_fabric_ui_imports

from .session_utils import SessionUtils
from .backend_client import BackendClient, BackendError
from .debug_logger import initialize_debug_logger, get_debug_logger

# Session UI utilities
from .session_constants import (
    VISIBLE_WINDOW_SIZE, 
    ARROW_UP, 
    ARROW_DOWN,
    WIDGET_POOL_MAINTENANCE_THRESHOLD,
    WIDGET_POOL_MAX_SIZE,
    SEARCH_DEBOUNCE_MS
)
from .widget_helpers import (
    create_scroll_indicator,
    create_session_button, 
    apply_selection_styling,
    update_button_label_efficiently,
    prepare_widget_for_reuse
)

__all__ = [
    "SessionUtils", 
    "BackendClient", 
    "BackendError",
    "initialize_debug_logger",
    "get_debug_logger",
    "VISIBLE_WINDOW_SIZE",
    "ARROW_UP", 
    "ARROW_DOWN",
    "WIDGET_POOL_MAINTENANCE_THRESHOLD",
    "WIDGET_POOL_MAX_SIZE", 
    "SEARCH_DEBOUNCE_MS",
    "create_scroll_indicator",
    "create_session_button",
    "apply_selection_styling", 
    "update_button_label_efficiently",
    "prepare_widget_for_reuse"
]