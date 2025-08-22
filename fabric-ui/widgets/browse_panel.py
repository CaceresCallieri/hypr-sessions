"""
Browse Panel Widget for Hypr Sessions Manager
"""

import sys
from pathlib import Path

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.entry import Entry


# Add parent directory to path for clean imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import constants and backend client
from constants import (
    KEYCODE_ENTER, KEYCODE_ESCAPE, KEYCODE_Q, KEYCODE_TAB, KEYCODE_UP_ARROW, KEYCODE_DOWN_ARROW,
    BROWSING_STATE, DELETE_CONFIRM_STATE, DELETING_STATE, DELETE_SUCCESS_STATE, DELETE_ERROR_STATE,
    RESTORE_CONFIRM_STATE, RESTORING_STATE, RESTORE_SUCCESS_STATE, RESTORE_ERROR_STATE
)
from utils import BackendClient

# Import operation classes
from .operations import DeleteOperation, RestoreOperation


class BrowsePanelWidget(Box):
    """Panel widget for browsing and selecting sessions"""

    def __init__(self, session_utils, on_session_clicked=None):
        super().__init__(orientation="vertical", spacing=10, name="browse-panel")

        self.session_utils = session_utils
        self.on_session_clicked = on_session_clicked
        
        # Backend client for operations
        try:
            self.backend_client = BackendClient()
        except FileNotFoundError as e:
            print(f"Warning: Backend client unavailable: {e}")
            self.backend_client = None
            
        # Initialize operation handlers
        self.delete_operation = DeleteOperation(self, self.backend_client)
        self.restore_operation = RestoreOperation(self, self.backend_client)

        # Selection state management
        self.all_session_names = []  # Complete list of all sessions
        self.filtered_sessions = []  # Filtered session names based on search
        self.session_buttons = []  # List of currently visible session button widgets

        # Search functionality
        self.search_input = None  # GTK Entry widget for search
        self.search_query = ""  # Current search text

        # Scrollable window management
        self.VISIBLE_WINDOW_SIZE = (
            5  # Maximum sessions to display at once (configurable)
        )
        self.visible_start_index = 0  # First visible session index in global list
        self.selected_global_index = 0  # Selected session index in global list
        self.selected_local_index = 0  # Selected session index within visible window

        # Scroll indicator symbols (Nerd Font triangles)
        self.ARROW_UP = "\uf077"  # nf-fa-chevron_down
        self.ARROW_DOWN = "\uf078"  # nf-fa-chevron_up

        # Panel state management
        self.state = BROWSING_STATE  # Browse panel state management using constants

        # Create panel content
        self._create_content()

    def _is_printable_character(self, keycode):
        """Check if keycode represents a printable character"""
        # Navigation and special keys that should NOT be treated as text input
        navigation_keys = {
            KEYCODE_UP_ARROW, KEYCODE_DOWN_ARROW, KEYCODE_ENTER, KEYCODE_ESCAPE, 
            KEYCODE_TAB, KEYCODE_Q,
            # Additional special keys
            113, 114,  # Left/Right arrows (from constants)
            65307,     # Escape (alternative code)
            65293,     # Return/Enter (alternative code)
            65289,     # Tab (alternative code)
            65361, 65362, 65363, 65364,  # Arrow keys (alternative codes)
            65365, 65366,  # Page Up/Down
            65367, 65368,  # End/Home
            65535,     # Delete
            65288,     # Backspace
            65470, 65471, 65472, 65473, 65474, 65475, 65476, 65477, 65478, 65479, 65480, 65481,  # Function keys F1-F12
        }
        
        # If it's a known navigation key, it's not printable
        if keycode in navigation_keys:
            return False
            
        # Printable ASCII range and extended characters
        # Letters, numbers, symbols, space, punctuation
        return (32 <= keycode <= 126) or (160 <= keycode <= 255) or keycode in range(48, 58) or keycode in range(65, 91) or keycode in range(97, 123)

    def _create_content(self):
        """Create the browse panel content based on current state"""
        if self.state == BROWSING_STATE:
            self.children = self._create_browsing_ui()
        elif self.state == DELETE_CONFIRM_STATE:
            self.children = self.delete_operation.create_confirmation_ui()
        elif self.state == DELETING_STATE:
            self.children = self.delete_operation.create_progress_ui()
        elif self.state == DELETE_SUCCESS_STATE:
            self.children = self.delete_operation.create_success_ui()
        elif self.state == DELETE_ERROR_STATE:
            self.children = self.delete_operation.create_error_ui()
        elif self.state == RESTORE_CONFIRM_STATE:
            self.children = self.restore_operation.create_confirmation_ui()
        elif self.state == RESTORING_STATE:
            self.children = self.restore_operation.create_progress_ui()
        elif self.state == RESTORE_SUCCESS_STATE:
            self.children = self.restore_operation.create_success_ui()
        elif self.state == RESTORE_ERROR_STATE:
            self.children = self.restore_operation.create_error_ui()

    def _create_browsing_ui(self):
        """Create the normal browsing UI"""
        # Get and create session buttons first
        sessions_container = self._create_sessions_list()
        
        # Sessions list section header with filtered/total count
        total_sessions = len(self.all_session_names)
        filtered_count = len(self.filtered_sessions)
        if self.search_query:
            header_text = f"Available Sessions ({filtered_count}/{total_sessions}):"
        else:
            header_text = f"Available Sessions ({total_sessions}):"
        sessions_header = Label(text=header_text, name="sessions-header")
        sessions_header.set_markup(f"<span weight='bold'>{header_text}</span>")

        # Create search input widget
        search_input = self._create_search_input()

        return [sessions_header, search_input, sessions_container]

    def _create_search_input(self):
        """Create the search input widget with permanent focus"""
        if not self.search_input:
            self.search_input = Entry(
                text=self.search_query,
                placeholder_text="🔍 Search sessions...",
                name="session-search-input"
            )
            # Connect search input change event
            self.search_input.connect("changed", self._on_search_changed)
            
            # Ensure search input can receive focus and maintains it
            self.search_input.set_can_focus(True)
            
        # Focus will be set by delayed focus setup in main session manager
        return self.search_input

    def _on_search_changed(self, entry):
        """Handle search input text changes"""
        self.search_query = entry.get_text().strip()
        self._update_filtered_sessions()
        self.update_display()

    def _update_filtered_sessions(self):
        """Update filtered sessions based on current search query"""
        if not self.search_query:
            # No search query - show all sessions
            self.filtered_sessions = self.all_session_names.copy()
        else:
            # Filter sessions with case-insensitive substring matching
            query_lower = self.search_query.lower()
            self.filtered_sessions = [
                session for session in self.all_session_names
                if query_lower in session.lower()
            ]
        
        # Reset selection if current selection is not in filtered results
        if self.filtered_sessions:
            selected_session = self.get_selected_session()
            if selected_session not in self.filtered_sessions:
                # Reset to first filtered session
                self.selected_global_index = self.all_session_names.index(self.filtered_sessions[0])
        else:
            # No filtered results
            self.selected_global_index = -1

    def clear_search(self):
        """Clear the search input (maintains permanent focus)"""
        if self.search_input:
            self.search_input.set_text("")
            self.search_query = ""
            self._update_filtered_sessions()
            self.update_display()

    def _create_sessions_list(self):
        """Create the sessions list container with buttons for visible window"""
        all_sessions = self.session_utils.get_available_sessions()

        # Update global session state
        self.all_session_names = all_sessions
        self.session_buttons = []

        # Initialize filtered sessions on first load
        if not hasattr(self, 'filtered_sessions') or not self.filtered_sessions:
            self._update_filtered_sessions()

        if not self.filtered_sessions:
            # No sessions available (either none exist or none match search)
            self.selected_global_index = -1
            self.selected_local_index = -1
            
            if not all_sessions:
                message = "No sessions found"
            else:
                message = f"No sessions match '{self.search_query}'"
                
            no_sessions_label = Label(
                text=message, name="no-sessions-label"
            )
            no_sessions_label.set_markup(
                f"<span style='italic'>{message}</span>"
            )

            return Box(
                orientation="vertical",
                spacing=5,
                name="sessions-container",
                children=[no_sessions_label],
            )

        # Initialize selection state for first run
        if self.selected_global_index >= len(all_sessions) or self.selected_global_index == -1:
            if self.filtered_sessions:
                self.selected_global_index = self.all_session_names.index(self.filtered_sessions[0])

        # Get visible sessions for current window (from filtered results)
        visible_sessions = self.get_visible_sessions()

        # Create widget list with reserved space for scroll indicators
        widgets = []
        # FIX: Minimal shifting and window increase/decrease in size when the scroll indicators appear/disappear

        # Always reserve space for "more sessions above" indicator
        more_above = self._create_scroll_indicator(
            self.ARROW_UP, self.has_sessions_above()
        )
        widgets.append(more_above)

        # Create session buttons for visible sessions only
        for i, session_name in enumerate(visible_sessions):
            global_index = self.visible_start_index + i
            button = Button(
                label=f"• {session_name}",
                name="session-button",  # Base CSS class
                on_clicked=lambda *_, name=session_name: self._handle_session_clicked(
                    name
                ),
            )

            # Make button non-focusable to prevent focus stealing from search input
            button.set_can_focus(False)

            # Add selected class if this is the selected session
            if global_index == self.selected_global_index:
                button.get_style_context().add_class("selected")

            self.session_buttons.append(button)
            widgets.append(button)

        # Always reserve space for "more sessions below" indicator
        more_below = self._create_scroll_indicator(
            self.ARROW_DOWN, self.has_sessions_below()
        )
        widgets.append(more_below)

        return Box(
            orientation="vertical",
            spacing=5,
            name="sessions-container",
            children=widgets,
        )

    def _handle_session_clicked(self, session_name):
        """Handle session button click"""
        print(f"Session clicked: {session_name}")
        if self.on_session_clicked:
            self.on_session_clicked(session_name)

    def calculate_visible_window(self):
        """Calculate which sessions should be visible based on current selection and filtering"""
        total_filtered = len(self.filtered_sessions)

        if total_filtered <= self.VISIBLE_WINDOW_SIZE:
            # All filtered sessions fit in window
            self.visible_start_index = 0
            return list(range(total_filtered))

        # Convert global selection to filtered index
        selected_session = self.get_selected_session()
        if selected_session and selected_session in self.filtered_sessions:
            selected_filtered_index = self.filtered_sessions.index(selected_session)
        else:
            selected_filtered_index = 0

        # Calculate window position to keep selection visible
        window_end = self.visible_start_index + self.VISIBLE_WINDOW_SIZE

        # If selection is outside current window, adjust window
        if selected_filtered_index < self.visible_start_index:
            # Selection is above visible window
            self.visible_start_index = selected_filtered_index
        elif selected_filtered_index >= window_end:
            # Selection is below visible window
            self.visible_start_index = (
                selected_filtered_index - self.VISIBLE_WINDOW_SIZE + 1
            )

        # Ensure window doesn't go past end of filtered list
        self.visible_start_index = min(
            self.visible_start_index, total_filtered - self.VISIBLE_WINDOW_SIZE
        )
        self.visible_start_index = max(0, self.visible_start_index)

        # Calculate local selection index
        self.selected_local_index = (
            selected_filtered_index - self.visible_start_index
        )

        # Return indices of visible filtered sessions
        return list(
            range(
                self.visible_start_index,
                min(
                    self.visible_start_index + self.VISIBLE_WINDOW_SIZE, total_filtered
                ),
            )
        )

    def get_visible_sessions(self):
        """Get the list of sessions that should be currently visible"""
        visible_indices = self.calculate_visible_window()
        return [self.filtered_sessions[i] for i in visible_indices]

    def has_sessions_above(self):
        """Check if there are sessions above the visible window"""
        return self.visible_start_index > 0

    def has_sessions_below(self):
        """Check if there are sessions below the visible window"""
        total_filtered = len(self.filtered_sessions)
        return (self.visible_start_index + self.VISIBLE_WINDOW_SIZE) < total_filtered

    def _create_scroll_indicator(self, arrow_symbol, show_condition):
        """Create a scroll indicator with reserved space"""
        indicator = Label(text="", name="scroll-indicator")
        if show_condition:
            indicator.set_markup(arrow_symbol)
        else:
            indicator.set_markup("")  # Empty but reserves space
        return indicator

    def refresh(self):
        """Refresh the sessions list"""
        self._create_content()

    def select_next(self):
        """Select the next session with intelligent scrolling"""
        if not self.filtered_sessions:
            return

        # Get current position in filtered list
        selected_session = self.get_selected_session()
        if selected_session in self.filtered_sessions:
            current_filtered_index = self.filtered_sessions.index(selected_session)
        else:
            current_filtered_index = -1

        # Move to next session in filtered list (with wraparound)
        total_filtered = len(self.filtered_sessions)
        next_filtered_index = (current_filtered_index + 1) % total_filtered
        next_session = self.filtered_sessions[next_filtered_index]
        
        # Update global index to match the new selection
        self.selected_global_index = self.all_session_names.index(next_session)

        # Refresh display to show new selection and handle scrolling
        self.update_display()
        
        # Ensure search input maintains focus after navigation
        self._ensure_search_focus()

    def select_previous(self):
        """Select the previous session with intelligent scrolling"""
        if not self.filtered_sessions:
            return

        # Get current position in filtered list
        selected_session = self.get_selected_session()
        if selected_session in self.filtered_sessions:
            current_filtered_index = self.filtered_sessions.index(selected_session)
        else:
            current_filtered_index = 0

        # Move to previous session in filtered list (with wraparound)
        total_filtered = len(self.filtered_sessions)
        prev_filtered_index = (current_filtered_index - 1) % total_filtered
        prev_session = self.filtered_sessions[prev_filtered_index]
        
        # Update global index to match the new selection
        self.selected_global_index = self.all_session_names.index(prev_session)

        # Refresh display to show new selection and handle scrolling
        self.update_display()
        
        # Ensure search input maintains focus after navigation
        self._ensure_search_focus()

    def _ensure_search_focus(self):
        """Ensure search input maintains focus for continuous typing"""
        try:
            if self.search_input and not self.search_input.has_focus():
                self.search_input.grab_focus()
                print("DEBUG: Restored search input focus after navigation")
        except Exception as e:
            print(f"Warning: Failed to restore search input focus: {e}")

    def update_display(self):
        """Update the display to show current selection and scroll position"""
        # Recalculate visible window and refresh content
        self._create_content()

    def get_selected_session(self):
        """Get the name of the currently selected session"""
        if 0 <= self.selected_global_index < len(self.all_session_names):
            return self.all_session_names[self.selected_global_index]
        return None

    def activate_selected_session(self):
        """Activate (restore) the currently selected session"""
        selected_session = self.get_selected_session()
        if selected_session and self.on_session_clicked:
            self.on_session_clicked(selected_session)

    def set_state(self, new_state):
        """Change the browse panel state and refresh content"""
        if new_state != self.state:
            print(f"BrowsePanel: {self.state} → {new_state}")  # Debug logging
            self.state = new_state
            self._create_content()
            self.show_all()

    # Operation methods removed - now handled by operation classes
    # DeleteOperation and RestoreOperation handle all operation logic
    
    def handle_key_press(self, keycode):
        """Handle keyboard events using dual focus system"""        
        if self.state == DELETE_CONFIRM_STATE:
            if keycode == KEYCODE_ENTER:
                # Trigger the actual delete operation
                self.delete_operation.trigger_operation()
                return True
            elif keycode == KEYCODE_ESCAPE or keycode == KEYCODE_Q:
                # Cancel delete operation (ESC or Q key)
                print(f"DEBUG: Cancelled delete for session: {self.delete_operation.selected_session}")
                self.delete_operation.selected_session = None
                self.set_state(BROWSING_STATE)
                return True
        
        elif self.state == RESTORE_CONFIRM_STATE:
            if keycode == KEYCODE_ENTER:
                # Trigger the actual restore operation
                self.restore_operation.trigger_operation()
                return True
            elif keycode == KEYCODE_ESCAPE or keycode == KEYCODE_Q:
                # Cancel restore operation (ESC or Q key)
                print(f"DEBUG: Cancelled restore for session: {self.restore_operation.selected_session}")
                self.restore_operation.selected_session = None
                self.set_state(BROWSING_STATE)
                return True
        
        elif self.state == BROWSING_STATE:
            # Dual focus system: route keys by type, not focus state
            if self._is_printable_character(keycode):
                # Printable characters: let GTK route to search input (always focused)
                # Don't handle here - let it fall through to GTK's text input system
                return False
            
            elif keycode == KEYCODE_ESCAPE:
                # Clear search (search input maintains focus)
                self.clear_search()
                return True
                
            elif keycode == KEYCODE_ENTER:
                # Restore selected session (independent of input focus)
                return False  # Let main manager handle session activation
                
            elif keycode in [KEYCODE_UP_ARROW, KEYCODE_DOWN_ARROW]:
                # Navigation keys: handle directly to prevent focus loss
                if keycode == KEYCODE_UP_ARROW:
                    self.select_previous()
                elif keycode == KEYCODE_DOWN_ARROW:
                    self.select_next()
                return True  # Handled here, don't pass to main manager
        
        # Let main manager handle other keys
        return False

