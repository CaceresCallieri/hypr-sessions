"""
UI Constants for Hypr Sessions Manager

This module contains all shared constants used across the UI components,
including GTK keycodes and other configuration values.
"""

from typing import Final

# GTK Keycodes
# These are the specific keycodes used by GTK for keyboard event handling
KEYCODE_ESCAPE: Final[int] = 9
KEYCODE_TAB: Final[int] = 23
KEYCODE_ENTER: Final[int] = 36
KEYCODE_LEFT_ARROW: Final[int] = 113
KEYCODE_RIGHT_ARROW: Final[int] = 114
KEYCODE_UP_ARROW: Final[int] = 111
KEYCODE_DOWN_ARROW: Final[int] = 116
KEYCODE_D: Final[int] = 40

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

# Future expansion possibilities:
# UI_COLORS = {...}
# UI_TIMEOUTS = {...}
# UI_DIMENSIONS = {...}
# SCROLL_INDICATORS = {...}