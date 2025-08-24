"""
Browse Panel Widget for Hypr Sessions Manager
"""

import sys
from pathlib import Path

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.entry import Entry

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk


# Add parent directory to path for clean imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import constants and backend client
from constants import (
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


    def _is_ui_navigation_key(self, keyval):
        """Check if keyval represents a UI navigation key using GTK constants"""
        ui_navigation = {
            # Session navigation
            Gdk.KEY_Up, Gdk.KEY_Down,
            
            # Actions
            Gdk.KEY_Return, Gdk.KEY_KP_Enter,  # Restore session
            Gdk.KEY_Escape,                    # Clear search
            
            # Panel switching
            Gdk.KEY_Tab, Gdk.KEY_Left, Gdk.KEY_Right,
        }
        
        return keyval in ui_navigation

    def should_route_to_search(self, event):
        """Determine if event should route to search input using GTK event properties"""
        keyval = event.keyval
        
        # UI navigation keys go to navigation handlers
        if self._is_ui_navigation_key(keyval):
            return False
        
        # Handle modifier combinations (Ctrl+key, Alt+key, etc.)
        if event.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK):
            return False  # Don't route modifier combinations to search
        
        # Everything else goes to search input for filtering/editing
        # This includes: letters, numbers, symbols, backspace, delete, etc.
        return True

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
        self._update_session_list_only()

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
            self._update_session_list_only()

    def _create_sessions_list(self):
        """Create the sessions list container using shared widget creation logic"""
        # Update global session state
        all_sessions = self.session_utils.get_available_sessions()
        self.all_session_names = all_sessions
        self.session_buttons = []

        # Initialize filtered sessions on first load
        if not hasattr(self, 'filtered_sessions') or not self.filtered_sessions:
            self._update_filtered_sessions()

        # Use shared widget creation logic
        session_widgets = self._create_sessions_widget_list()

        return Box(
            orientation="vertical",
            spacing=5,
            name="sessions-container",
            children=session_widgets,
        )

    def _create_session_button(self, session_name, is_selected=False):
        """Pure factory method for creating session buttons with consistent logic"""
        button = Button(
            label=f"• {session_name}",
            name="session-button",  # Base CSS class
            on_clicked=lambda *_: self._handle_session_clicked(session_name),
        )
        
        # Make button non-focusable to prevent focus stealing from search input
        button.set_can_focus(False)
        
        # Add selected class if this is the selected session
        if is_selected:
            button.get_style_context().add_class("selected")
        
        return button

    def _create_sessions_widget_list(self):
        """Create complete widget list: scroll indicators + session buttons"""
        # Handle empty sessions case  
        if not self.filtered_sessions:
            self.selected_global_index = -1
            self.selected_local_index = -1
            
            if not self.all_session_names:
                message = "No sessions found"
            else:
                message = f"No sessions match '{self.search_query}'"
                
            no_sessions_label = Label(
                text=message, name="no-sessions-label"
            )
            no_sessions_label.set_markup(
                f"<span style='italic'>{message}</span>"
            )
            return [no_sessions_label]

        # Initialize selection state for first run
        if self.selected_global_index >= len(self.all_session_names) or self.selected_global_index == -1:
            if self.filtered_sessions:
                self.selected_global_index = self.all_session_names.index(self.filtered_sessions[0])

        # Get visible sessions and selected session for current window
        visible_sessions = self.get_visible_sessions()
        selected_session_name = self.get_selected_session()

        # Create complete widget list
        widgets = []

        # Always reserve space for "more sessions above" indicator
        more_above = self._create_scroll_indicator(
            self.ARROW_UP, self.has_sessions_above()
        )
        widgets.append(more_above)

        # Create session buttons for visible sessions using factory method
        for session_name in visible_sessions:
            is_selected = (session_name == selected_session_name)
            button = self._create_session_button(session_name, is_selected)
            self.session_buttons.append(button)
            widgets.append(button)

        # Always reserve space for "more sessions below" indicator
        more_below = self._create_scroll_indicator(
            self.ARROW_DOWN, self.has_sessions_below()
        )
        widgets.append(more_below)

        return widgets

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
        self._update_session_list_only()
        
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
        self._update_session_list_only()
        
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
    
    def _update_session_list_only(self):
        """Update only the session list while preserving persistent widgets like search input"""
        if self.state != BROWSING_STATE:
            # Only apply selective updates in browsing state
            self.update_display()
            return
            
        # Find the sessions container widget to update its contents
        sessions_container = None
        
        for child in self.children:
            if hasattr(child, 'get_name') and child.get_name() == 'sessions-container':
                sessions_container = child
                break
        
        if sessions_container is not None:
            # Update the sessions header with new count
            total_sessions = len(self.all_session_names)
            filtered_count = len(self.filtered_sessions)
            if self.search_query:
                header_text = f"Available Sessions ({filtered_count}/{total_sessions}):"
            else:
                header_text = f"Available Sessions ({total_sessions}):"
            
            # Find and update sessions header
            for child in self.children:
                if hasattr(child, 'get_name') and child.get_name() == 'sessions-header':
                    child.set_markup(f"<span weight='bold'>{header_text}</span>")
                    break
            
            # Create new session widgets using shared logic
            new_session_widgets = self._create_sessions_widget_list()
            
            # Update only the sessions container contents, not the container itself
            sessions_container.children = new_session_widgets
        else:
            # Fallback to full update if we can't find sessions container
            self.update_display()
    

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
    
    def handle_key_press_event(self, widget, event):
        """Handle keyboard events using full GTK event context"""
        if self.state == DELETE_CONFIRM_STATE:
            return self._handle_confirmation_state_event(event, self.delete_operation, DELETE_CONFIRM_STATE)
        
        elif self.state == RESTORE_CONFIRM_STATE:
            return self._handle_confirmation_state_event(event, self.restore_operation, RESTORE_CONFIRM_STATE)
        
        elif self.state == BROWSING_STATE:
            # Use new GTK event-based routing
            if self.should_route_to_search(event):
                # Let GTK route to search input (don't handle here)
                return False
            else:
                # Handle UI navigation keys
                return self._handle_navigation_event(event)
        
        # Let main manager handle other keys
        return False

    def _handle_confirmation_state_event(self, event, operation, state):
        """Handle confirmation state with GTK event"""
        keyval = event.keyval
        
        if keyval in [Gdk.KEY_Return, Gdk.KEY_KP_Enter]:
            # Trigger the operation
            operation.trigger_operation()
            return True
        elif keyval == Gdk.KEY_Escape:
            # Cancel operation
            print(f"DEBUG: Cancelled {operation.get_operation_config()['action_verb'].lower()} for session: {operation.selected_session}")
            operation.selected_session = None
            self.set_state(BROWSING_STATE)
            return True
        
        return False

    def _handle_navigation_event(self, event):
        """Handle navigation events in browsing state"""
        keyval = event.keyval
        
        if keyval == Gdk.KEY_Escape:
            # Clear search
            self.clear_search()
            return True
        elif keyval in [Gdk.KEY_Up, Gdk.KEY_Down]:
            # Handle session navigation directly
            if keyval == Gdk.KEY_Up:
                self.select_previous()
            else:
                self.select_next()
            return True
        elif keyval in [Gdk.KEY_Return, Gdk.KEY_KP_Enter]:
            # Let main manager handle session activation
            return False
        elif keyval == Gdk.KEY_Tab:
            # Let main manager handle panel switching
            return False
        elif keyval in [Gdk.KEY_Left, Gdk.KEY_Right]:
            # Let main manager handle panel switching
            return False
        
        return False


