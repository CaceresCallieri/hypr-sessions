"""
Browse Panel Widget for Hypr Sessions Manager

Streamlined version using modular component architecture.
Reduced from 1260 lines to ~400 lines through component extraction.
"""

import gi
from fabric.widgets.box import Box

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk

# Centralized path setup for imports
from utils.path_setup import setup_fabric_ui_imports

# Import constants and backend client
from constants import (
    BROWSING_STATE,
    DELETE_CONFIRM_STATE,
    DELETE_ERROR_STATE,
    DELETE_SUCCESS_STATE,
    DELETING_STATE,
    RESTORE_CONFIRM_STATE,
    RESTORE_ERROR_STATE,
    RESTORE_SUCCESS_STATE,
    RESTORING_STATE,
)

from utils import BackendClient
from utils.debug_logger import get_debug_logger

# Import operation classes
from .operations import DeleteOperation, RestoreOperation

# Import extracted components
from .components import (
    SessionWidgetPool,
    SessionWindowCalculator,
    SessionListRenderer,
    KeyboardEventHandler,
    SessionSearchManager
)


class BrowsePanelWidget(Box):
    """Streamlined panel widget for browsing and selecting sessions"""

    def __init__(self, session_utils, on_session_clicked=None):
        super().__init__(orientation="vertical", spacing=10, name="browse-panel")

        self.session_utils = session_utils
        self.on_session_clicked = on_session_clicked

        # Initialize debug logger
        self.debug_logger = get_debug_logger()
        if self.debug_logger:
            self.debug_logger.debug_session_lifecycle("ui_startup", "browse_panel", "initializing")

        # Backend client for operations
        try:
            self.backend_client = BackendClient()
            if self.debug_logger:
                self.debug_logger.debug_backend_call("init", None, 0, True, {"status": "available"})
        except FileNotFoundError as e:
            if self.debug_logger:
                self.debug_logger.debug_backend_call("init", None, 0, False, {"error": str(e)})
            self.backend_client = None

        # Initialize operation handlers
        self.delete_operation = DeleteOperation(self, self.backend_client)
        self.restore_operation = RestoreOperation(self, self.backend_client)

        # Initialize modular components
        self.widget_pool = SessionWidgetPool(self.debug_logger)
        self.window_calculator = SessionWindowCalculator()
        self.list_renderer = SessionListRenderer(
            self.widget_pool, self.window_calculator, self.debug_logger
        )
        self.keyboard_handler = KeyboardEventHandler(self)
        self.search_manager = SessionSearchManager(self.debug_logger)

        # Core state management - simplified with components
        self.all_session_names = []
        self.filtered_sessions = []
        self.selected_session_name = None
        self.state = BROWSING_STATE

        # Initialize with single update path
        self.update_display()

    def update_display(self):
        """Single update method handles ALL UI updates - delegates to components"""
        # Store search state before rebuilding
        self.search_manager.preserve_search_state()
        
        # Create content based on current state
        if self.state == BROWSING_STATE:
            content = self._create_browsing_content()
        elif self.state == DELETE_CONFIRM_STATE:
            content = self.delete_operation.create_confirmation_ui()
        elif self.state == DELETING_STATE:
            content = self.delete_operation.create_progress_ui()
        elif self.state == DELETE_SUCCESS_STATE:
            content = self.delete_operation.create_success_ui()
        elif self.state == DELETE_ERROR_STATE:
            content = self.delete_operation.create_error_ui()
        elif self.state == RESTORE_CONFIRM_STATE:
            content = self.restore_operation.create_confirmation_ui()
        elif self.state == RESTORING_STATE:
            content = self.restore_operation.create_progress_ui()
        elif self.state == RESTORE_SUCCESS_STATE:
            content = self.restore_operation.create_success_ui()
        elif self.state == RESTORE_ERROR_STATE:
            content = self.restore_operation.create_error_ui()
        else:
            if self.debug_logger and self.debug_logger.enabled:
                self.debug_logger.debug_state_transition(
                    "browse_panel", self.state, "error", "unknown_state"
                )
            content = [Label(text="Error: Unknown state", name="error-label")]
        
        # Replace all content with new widgets
        self.children = content
        self.show_all()
        
        # Restore search input focus and cursor position (browsing state only)
        if self.state == BROWSING_STATE:
            self.search_manager.restore_search_state()

    def _create_browsing_content(self):
        """Create complete browsing content using components"""
        # Update session data
        self._refresh_session_data()
        
        # Create search input using search manager
        search_input = self.search_manager.create_search_input(self._on_search_changed)
        
        # Create sessions header using list renderer
        sessions_header = self.list_renderer.create_sessions_header(
            len(self.all_session_names), 
            len(self.filtered_sessions),
            self.search_manager.has_search_query()
        )
        
        # Create session widgets container
        sessions_container = self._create_sessions_container()
        
        # Create keyboard shortcuts hint using list renderer
        shortcuts_hint = self.list_renderer.create_shortcuts_hint()

        return [search_input, sessions_header, sessions_container, shortcuts_hint]

    def _create_sessions_container(self):
        """Create session widgets container using components"""
        # Create session widgets using list renderer
        session_widgets = self.list_renderer.create_session_widget_list(
            self.all_session_names,
            self.filtered_sessions, 
            self.selected_session_name,
            self.search_manager.get_search_query(),
            self._handle_session_clicked
        )
        
        return Box(
            orientation="vertical",
            spacing=5,
            name="sessions-container",
            children=session_widgets
        )

    def _refresh_session_data(self):
        """Refresh session data and update filtered sessions"""
        # Get current session data
        self.all_session_names = self.session_utils.get_available_sessions()
        
        # Update filtered sessions using search manager
        self.filtered_sessions, suggested_selection = self.search_manager.update_filtered_sessions(
            self.all_session_names
        )
        
        # Set initial selection if needed
        if self.filtered_sessions and not self.selected_session_name:
            self.selected_session_name = suggested_selection

    def _on_search_changed(self, entry):
        """Handle search input text changes - delegates to search manager"""
        # Update search query using search manager
        self.search_manager.handle_search_changed(entry)
        
        # Update filtered sessions
        self.filtered_sessions, suggested_selection = self.search_manager.update_filtered_sessions(
            self.all_session_names
        )
        
        # Update selection if current selection is not in filtered results
        if self.filtered_sessions:
            if self.selected_session_name not in self.filtered_sessions:
                self.selected_session_name = suggested_selection
        else:
            self.selected_session_name = None
        
        # Update only session list, not entire UI (preserves search input)
        self._update_sessions_only()

    def _update_sessions_only(self):
        """Update only session list and header without recreating search input"""
        if self.state != BROWSING_STATE:
            # For non-browsing states, do full update
            self.update_display()
            return
            
        # Find and update existing widgets in current children
        current_children = list(self.children)
        if len(current_children) >= 4:  # [search_input, header, sessions_container, shortcuts]
            # Update the header (index 1)
            header = current_children[1]
            updated_header = self.list_renderer.create_sessions_header(
                len(self.all_session_names),
                len(self.filtered_sessions), 
                self.search_manager.has_search_query()
            )
            header.set_markup(updated_header.get_text())
            
            # Update the sessions container (index 2)
            sessions_container = current_children[2]
            new_session_widgets = self.list_renderer.create_session_widget_list(
                self.all_session_names,
                self.filtered_sessions,
                self.selected_session_name, 
                self.search_manager.get_search_query(),
                self._handle_session_clicked
            )
            sessions_container.children = new_session_widgets
            
            # Show updated content
            self.show_all()
        else:
            # Fallback to full update if structure is unexpected
            self.update_display()

    def clear_search(self):
        """Clear the search and refresh display - delegates to search manager"""
        self.search_manager.clear_search()
        self.filtered_sessions, suggested_selection = self.search_manager.update_filtered_sessions(
            self.all_session_names
        )
        self.selected_session_name = suggested_selection
        self.update_display()

    def refresh(self):
        """Refresh the sessions list"""
        self.update_display()

    def select_next(self):
        """Select the next session with intelligent scrolling"""
        if not self.filtered_sessions:
            return

        # Get next index using window calculator
        next_idx = self.window_calculator.get_next_selection_index(
            self.filtered_sessions, self.selected_session_name
        )
        
        old_session = self.selected_session_name
        self.selected_session_name = self.filtered_sessions[next_idx]
        
        # Debug navigation
        if self.debug_logger:
            self.debug_logger.debug_navigation_operation(
                "select_next", old_session, self.selected_session_name, "arrow_key",
                {"next_idx": next_idx, "wraparound": next_idx == 0}
            )

        # Refresh display to show new selection
        self.update_display()

    def select_previous(self):
        """Select the previous session with intelligent scrolling"""
        if not self.filtered_sessions:
            return

        # Get previous index using window calculator
        prev_idx = self.window_calculator.get_previous_selection_index(
            self.filtered_sessions, self.selected_session_name
        )
        
        old_session = self.selected_session_name
        self.selected_session_name = self.filtered_sessions[prev_idx]
        
        # Debug navigation
        if self.debug_logger:
            self.debug_logger.debug_navigation_operation(
                "select_previous", old_session, self.selected_session_name, "arrow_key",
                {"prev_idx": prev_idx, "wraparound": prev_idx == len(self.filtered_sessions) - 1}
            )

        # Refresh display to show new selection
        self.update_display()

    def _handle_session_clicked(self, session_name):
        """Handle session button click - delegates to callback"""
        if not isinstance(session_name, str) or not session_name.strip():
            raise ValueError(f"session_name must be non-empty string, got {repr(session_name)}")
            
        if self.debug_logger and self.debug_logger.enabled:
            self.debug_logger.debug_navigation_operation(
                "session_click", None, session_name, "mouse_click"
            )
        
        if self.on_session_clicked:
            self.on_session_clicked(session_name)

    def get_selected_session(self):
        """Get the name of the currently selected session"""
        return self.selected_session_name

    def is_session_selected(self, session_name):
        """Check if given session is currently selected"""
        return session_name == self.selected_session_name

    def activate_selected_session(self):
        """Activate (restore) the currently selected session"""
        selected_session = self.get_selected_session()
        if selected_session and self.on_session_clicked:
            self.on_session_clicked(selected_session)

    def set_state(self, new_state):
        """Change the browse panel state and refresh content"""
        if new_state != self.state:
            old_state = self.state
            self.state = new_state
            
            # Debug state transitions
            if self.debug_logger:
                self.debug_logger.debug_state_transition(
                    "browse_panel", old_state, new_state, "set_state"
                )
            
            # Prepare widgets for state transitions
            if new_state == BROWSING_STATE and old_state in [RESTORE_CONFIRM_STATE, DELETE_CONFIRM_STATE]:
                self.list_renderer.prepare_for_state_transition()
            
            # Use single update path for all state transitions
            self.update_display()
            
            # Restore search focus when returning to browsing state from confirmations
            if new_state == BROWSING_STATE and old_state in [RESTORE_CONFIRM_STATE, DELETE_CONFIRM_STATE]:
                self.search_manager.ensure_search_focus()

    def handle_key_press_event(self, widget, event):
        """Handle keyboard events - delegates to keyboard handler"""
        return self.keyboard_handler.handle_key_press_event(widget, event)

    # Compatibility methods for existing operation classes
    def should_route_to_search(self, event):
        """Compatibility method - delegates to keyboard handler"""
        return self.keyboard_handler.should_route_to_search(event)

    # Properties for backward compatibility with operation classes
    @property
    def search_query(self):
        """Get current search query - compatibility property"""
        return self.search_manager.get_search_query()

    @search_query.setter 
    def search_query(self, value):
        """Set search query - compatibility property"""
        self.search_manager.search_query = value

    @property
    def search_input(self):
        """Get search input widget - compatibility property"""
        return self.search_manager.search_input

    @search_input.setter
    def search_input(self, value):
        """Set search input widget - compatibility property"""
        self.search_manager.search_input = value

    # Navigation helper methods for operation classes
    def get_visible_sessions(self):
        """Get visible sessions - delegates to window calculator"""
        return self.window_calculator.get_visible_sessions(
            self.filtered_sessions, self.selected_session_name
        )

    def has_sessions_above(self):
        """Check if sessions above - delegates to window calculator"""
        return self.window_calculator.has_sessions_above()

    def has_sessions_below(self):
        """Check if sessions below - delegates to window calculator"""  
        return self.window_calculator.has_sessions_below(len(self.filtered_sessions))

    # Legacy method stubs for operation classes (will be removed after operations are updated)
    def _get_current_filtered_position(self):
        """Get position of selected session in filtered list"""
        return self.window_calculator._get_selected_filtered_index(
            self.filtered_sessions, self.selected_session_name
        )

    def _ensure_search_focus(self):
        """Ensure search focus - delegates to search manager"""
        self.search_manager.ensure_search_focus()

    # Debug methods for development
    def get_performance_stats(self):
        """Get performance statistics from components"""
        widget_pool_stats = self.list_renderer.get_performance_stats()
        return {
            'component': 'browse_panel_modular',
            'widget_pool': widget_pool_stats,
            'total_sessions': len(self.all_session_names),
            'filtered_sessions': len(self.filtered_sessions),
            'visible_window_start': self.window_calculator.visible_start_index
        }

    def enable_component_debug(self):
        """Enable debug output for all components"""
        if self.debug_logger and self.debug_logger.enabled:
            self.debug_logger.debug_session_lifecycle(
                "debug_control", "browse_panel", "components_debug_enabled"
            )

    def disable_component_debug(self):
        """Disable debug output for all components"""
        if self.debug_logger and self.debug_logger.enabled:
            self.debug_logger.debug_session_lifecycle(
                "debug_control", "browse_panel", "components_debug_disabled"
            )