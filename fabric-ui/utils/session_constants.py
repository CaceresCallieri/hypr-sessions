"""
Session UI Constants

UI configuration constants specific to session management widgets.
Extracted from browse_panel.py for reusability across components.
"""

from typing import Final

# Session Display Configuration
VISIBLE_WINDOW_SIZE: Final[int] = 5  # Number of sessions visible at once
ARROW_UP: Final[str] = "\uf077"  # Nerd Font chevron up
ARROW_DOWN: Final[str] = "\uf078"  # Nerd Font chevron down

# Widget Pool Performance Configuration
WIDGET_POOL_MAINTENANCE_THRESHOLD: Final[int] = 20  # Trigger optimization when pool gets large
WIDGET_POOL_MAX_SIZE: Final[int] = 15  # Maximum widgets to keep in pool

# Search Performance Configuration
SEARCH_DEBOUNCE_MS: Final[int] = 300  # Milliseconds to wait before processing search