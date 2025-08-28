"""
Session List Renderer Component

Handles creation and layout of session widgets for display.
Extracted from BrowsePanelWidget for better separation of concerns.
"""

from typing import List, Optional, Callable

from fabric.widgets.label import Label

from utils import ARROW_UP, ARROW_DOWN, create_scroll_indicator
from .session_widget_pool import SessionWidgetPool
from .session_window_calculator import SessionWindowCalculator


class SessionListRenderer:
    """Handles creation and layout of session widgets"""

    def __init__(self, widget_pool: SessionWidgetPool, window_calculator: SessionWindowCalculator, 
                 debug_logger=None):
        """Initialize the session list renderer
        
        Args:
            widget_pool: Widget pool for button management
            window_calculator: Window calculator for visibility
            debug_logger: Optional debug logger
        """
        self.widget_pool = widget_pool
        self.window_calculator = window_calculator
        self.debug_logger = debug_logger
        
        # Track active session buttons for pool management
        self.active_session_buttons = []

    def create_session_widget_list(self, all_session_names: List[str], 
                                 filtered_sessions: List[str], 
                                 selected_session: Optional[str],
                                 search_query: str = "",
                                 on_session_clicked: Optional[Callable] = None) -> List:
        """Create complete widget list: scroll indicators + session buttons
        
        Args:
            all_session_names: Complete list of all available sessions
            filtered_sessions: Filtered list based on search
            selected_session: Currently selected session name
            search_query: Current search query for empty state message
            on_session_clicked: Callback for session button clicks
            
        Returns:
            List of widgets ready for display
        """
        # Reset performance counters for this render cycle
        self.widget_pool.reset_performance_counters()
        
        # Handle empty sessions case
        empty_widget = self._create_empty_sessions_widget(
            all_session_names, filtered_sessions, search_query
        )
        if empty_widget:
            return [empty_widget]
        
        # Build the session widgets
        widgets = self._build_session_widgets(
            filtered_sessions, selected_session, on_session_clicked
        )
        
        # Perform periodic pool maintenance
        self.widget_pool.perform_maintenance_if_needed(set(all_session_names))
        
        return widgets

    def _create_empty_sessions_widget(self, all_session_names: List[str], 
                                    filtered_sessions: List[str], 
                                    search_query: str) -> Optional[Label]:
        """Create widget for empty sessions state, returns None if sessions exist
        
        Args:
            all_session_names: Complete list of all sessions
            filtered_sessions: Filtered list based on search
            search_query: Current search query
            
        Returns:
            Label widget for empty state, or None if sessions exist
        """
        if filtered_sessions:
            return None
            
        message = ("No sessions found" if not all_session_names 
                  else f"No sessions match '{search_query}'")
        
        no_sessions_label = Label(text=message, name="no-sessions-label")
        no_sessions_label.set_markup(f"<span style='italic'>{message}</span>")
        return no_sessions_label

    def _build_session_widgets(self, filtered_sessions: List[str], 
                             selected_session: Optional[str],
                             on_session_clicked: Optional[Callable]) -> List:
        """Build the core widget list with scroll indicators and session buttons
        
        Args:
            filtered_sessions: List of filtered session names
            selected_session: Currently selected session name
            on_session_clicked: Callback for session button clicks
            
        Returns:
            List of widgets with scroll indicators and session buttons
        """
        # Get visible sessions from window calculator
        visible_sessions = self.window_calculator.get_visible_sessions(
            filtered_sessions, selected_session
        )
        
        widgets = []
        
        # Top scroll indicator
        has_above = self.window_calculator.has_sessions_above()
        widgets.append(create_scroll_indicator(ARROW_UP, has_above))
        
        # Session buttons
        self.active_session_buttons = []
        for session_name in visible_sessions:
            is_selected = session_name == selected_session
            button = self.widget_pool.get_or_create_button(
                session_name, is_selected, on_session_clicked
            )
            self.active_session_buttons.append(button)
            widgets.append(button)
        
        # Bottom scroll indicator
        has_below = self.window_calculator.has_sessions_below(len(filtered_sessions))
        widgets.append(create_scroll_indicator(ARROW_DOWN, has_below))
        
        return widgets

    def create_sessions_header(self, all_session_count: int, filtered_count: int, 
                             has_search_query: bool) -> Label:
        """Create sessions header with count information
        
        Args:
            all_session_count: Total number of sessions
            filtered_count: Number of filtered sessions
            has_search_query: Whether search query is active
            
        Returns:
            Label widget with session count information
        """
        if has_search_query:
            header_text = f"Available Sessions ({filtered_count}/{all_session_count}):"
        else:
            header_text = f"Available Sessions ({all_session_count}):"
        
        sessions_header = Label(text=header_text, name="sessions-header")
        sessions_header.set_markup(f"<span weight='bold'>{header_text}</span>")
        return sessions_header

    def create_shortcuts_hint(self) -> Label:
        """Create keyboard shortcuts hint label
        
        Returns:
            Label widget with keyboard shortcuts
        """
        shortcuts_hint = Label(
            text="↑↓ Navigate • Enter Restore • Ctrl+D Delete",
            name="keyboard-shortcuts-hint"
        )
        shortcuts_hint.set_markup(
            "<span size='small' style='italic'>↑↓ Navigate • Enter Restore • Ctrl+D Delete</span>"
        )
        return shortcuts_hint

    def prepare_for_state_transition(self):
        """Prepare widgets for state transitions (e.g., from confirmation back to browse)"""
        self.widget_pool.prepare_for_reparenting()

    def get_performance_stats(self) -> dict:
        """Get performance statistics from the widget pool
        
        Returns:
            Dictionary with performance metrics
        """
        return self.widget_pool.get_performance_stats()

    def get_active_buttons(self) -> List:
        """Get list of currently active session buttons
        
        Returns:
            List of active button widgets
        """
        return self.active_session_buttons.copy()