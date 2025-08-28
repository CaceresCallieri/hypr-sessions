"""
UI Constants for Hypr Sessions Manager

This module contains all shared constants used across the UI components,
including GTK keycodes and other configuration values.
"""

from typing import Final


# Browse Panel States
# These constants define the possible states of the browse panel for better maintainability
# and to prevent typos when referencing states throughout the codebase
BROWSING_STATE: Final[str] = "browsing"
DELETE_CONFIRM_STATE: Final[str] = "delete_confirm"
DELETING_STATE: Final[str] = "deleting"
DELETE_SUCCESS_STATE: Final[str] = "delete_success"
DELETE_ERROR_STATE: Final[str] = "delete_error"
RESTORE_CONFIRM_STATE: Final[str] = "restore_confirm"
RESTORING_STATE: Final[str] = "restoring"
RESTORE_SUCCESS_STATE: Final[str] = "restore_success"
RESTORE_ERROR_STATE: Final[str] = "restore_error"

# Debug Configuration
# Controls comprehensive UI debug logging system
DEBUG_MODE_ENABLED: Final[bool] = True  # Set to True for streamlined debug output
DEBUG_VERBOSE_MODE: Final[bool] = (
    False  # Set to True for detailed widget/performance logging
)
DEBUG_OUTPUT_TO_TERMINAL: Final[bool] = True  # Output debug logs to terminal (default)
DEBUG_OUTPUT_TO_FILE: Final[bool] = True  # Also save debug logs to file (optional)
DEBUG_LOG_FILE: Final[str] = "/tmp/hypr-sessions-ui-debug.log"

# Future expansion possibilities:
# UI_COLORS = {...}
# UI_TIMEOUTS = {...}
# UI_DIMENSIONS = {...}
# SCROLL_INDICATORS = {...}
