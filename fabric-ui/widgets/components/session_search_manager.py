"""
Session Search Manager Component

Manages session search functionality including filtering and focus management.
Extracted from BrowsePanelWidget for better separation of concerns.
"""

import time
from typing import List, Optional, Callable

from fabric.widgets.entry import Entry


class SessionSearchManager:
    """Manages session search functionality and state"""

    def __init__(self, debug_logger=None):
        """Initialize the search manager
        
        Args:
            debug_logger: Optional debug logger for search operations
        """
        self.debug_logger = debug_logger
        
        # Search state
        self.search_query = ""
        self.search_cursor_position = 0
        self.search_input = None  # Current GTK Entry widget

    def create_search_input(self, on_search_changed_callback: Optional[Callable] = None) -> Entry:
        """Create search input widget with preserved state
        
        Args:
            on_search_changed_callback: Callback for search text changes
            
        Returns:
            Entry widget configured for search
        """
        self.search_input = Entry(
            text=self.search_query,
            placeholder_text="🔍 Search sessions...",
            name="session-search-input"
        )
        
        if on_search_changed_callback:
            self.search_input.connect("changed", on_search_changed_callback)
        
        self.search_input.set_can_focus(True)
        return self.search_input

    def update_filtered_sessions(self, all_session_names: List[str]) -> tuple[List[str], Optional[str]]:
        """Update filtered sessions based on current search query
        
        Args:
            all_session_names: Complete list of all available sessions
            
        Returns:
            Tuple of (filtered_sessions, suggested_selected_session)
        """
        start_time = time.time()
        
        if not self.search_query:
            # No search query - show all sessions
            filtered_sessions = all_session_names.copy()
            filter_type = "show_all"
        else:
            # Filter sessions with case-insensitive substring matching
            query_lower = self.search_query.lower()
            filtered_sessions = [
                session
                for session in all_session_names
                if query_lower in session.lower()
            ]
            filter_type = "substring_match"
        
        # Log filtering performance
        timing_ms = (time.time() - start_time) * 1000
        if self.debug_logger:
            self.debug_logger.debug_search_operation(
                "filtering", self.search_query, len(filtered_sessions), timing_ms,
                {"filter_type": filter_type, "total_sessions": len(all_session_names)}
            )

        # Suggest new selection if needed
        suggested_selection = None
        if filtered_sessions:
            suggested_selection = filtered_sessions[0]  # Default to first result
        
        return filtered_sessions, suggested_selection

    def handle_search_changed(self, entry: Entry) -> str:
        """Handle search input text changes
        
        Args:
            entry: GTK Entry widget with new search text
            
        Returns:
            New search query text
        """
        start_time = time.time()
        
        new_text = entry.get_text().strip()
        self.search_query = new_text
        
        # Log search operation performance
        timing_ms = (time.time() - start_time) * 1000
        if self.debug_logger:
            self.debug_logger.debug_search_operation(
                "input_change", self.search_query, 0, timing_ms,
                {"trigger": "user_typing"}
            )
        
        return self.search_query

    def clear_search(self) -> str:
        """Clear the search query and reset cursor position
        
        Returns:
            Empty search query
        """
        self.search_query = ""
        self.search_cursor_position = 0
        
        if self.debug_logger:
            self.debug_logger.debug_search_operation(
                "clear", "", 0, 0,
                {"trigger": "ctrl_l_shortcut"}
            )
        
        return self.search_query

    def preserve_search_state(self):
        """Preserve search input state before widget recreation"""
        if hasattr(self, 'search_input') and self.search_input:
            self.search_cursor_position = self.search_input.get_position()

    def restore_search_state(self):
        """Restore search input focus and cursor position after widget recreation"""
        if self.search_input:
            self.search_input.grab_focus()
            self.search_input.set_position(self.search_cursor_position)

    def ensure_search_focus(self):
        """Ensure search input maintains focus for continuous typing"""
        try:
            if self.search_input and not self.search_input.has_focus():
                self.search_input.grab_focus()
                if self.debug_logger:
                    self.debug_logger.debug_focus_recovery(
                        "navigation", "search_input", True, {"trigger": "ensure_search_focus"}
                    )
        except Exception as e:
            if self.debug_logger:
                self.debug_logger.debug_focus_recovery(
                    "navigation", "search_input", False, 
                    {"trigger": "ensure_search_focus", "error": str(e)}
                )

    def has_search_query(self) -> bool:
        """Check if there's an active search query
        
        Returns:
            True if search query is not empty
        """
        return bool(self.search_query.strip())

    def get_search_query(self) -> str:
        """Get current search query
        
        Returns:
            Current search query string
        """
        return self.search_query