"""
Browse Panel Widget for Hypr Sessions Manager
"""

import sys
from pathlib import Path

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label

# Add parent directory to path for clean imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import constants for key handling
from constants import KEYCODE_ENTER, KEYCODE_ESCAPE


class BrowsePanelWidget(Box):
    """Panel widget for browsing and selecting sessions"""

    def __init__(self, session_utils, on_session_clicked=None):
        super().__init__(orientation="vertical", spacing=10, name="browse-panel")

        self.session_utils = session_utils
        self.on_session_clicked = on_session_clicked

        # Selection state management
        self.all_session_names = []  # Complete list of all sessions
        self.session_buttons = []  # List of currently visible session button widgets

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

        # Delete state management
        self.state = "browsing"  # States: "browsing", "delete_confirm"
        self.selected_session_for_delete = None

        # Create panel content
        self._create_content()

    def _create_content(self):
        """Create the browse panel content based on current state"""
        if self.state == "browsing":
            self.children = self._create_browsing_ui()
        elif self.state == "delete_confirm":
            self.children = self._create_delete_confirmation_ui()

    def _create_browsing_ui(self):
        """Create the normal browsing UI"""
        # Get and create session buttons first
        sessions_container = self._create_sessions_list()
        
        # Sessions list section header with total count (now that we have the actual count)
        total_sessions = len(self.all_session_names)
        header_text = f"Available Sessions ({total_sessions}):"
        sessions_header = Label(text=header_text, name="sessions-header")
        sessions_header.set_markup(f"<span weight='bold'>{header_text}</span>")

        return [sessions_header, sessions_container]

    def _create_delete_confirmation_ui(self):
        """Create the delete confirmation UI"""
        # For now, just a simple placeholder - we'll enhance this next
        session_name = self.selected_session_for_delete or "Unknown"
        
        # Main warning message
        warning_message = Label(
            text=f"Delete Session: {session_name}",
            name="delete-title"
        )
        warning_message.set_markup(f"<span weight='bold' color='#f38ba8'>Delete Session: {session_name}</span>")
        
        # Simple confirmation text for now
        confirm_text = f"Are you sure you wish to delete '{session_name}' session files?\nThis action cannot be undone."
        confirm_message = Label(text=confirm_text, name="delete-confirmation")
        
        # Instructions
        instructions = Label(
            text="Press Enter to DELETE • Esc to Cancel",
            name="delete-instructions"  
        )
        instructions.set_markup("<span size='small' style='italic'>Press Enter to DELETE • Esc to Cancel</span>")
        
        return [warning_message, confirm_message, instructions]

    def _create_sessions_list(self):
        """Create the sessions list container with buttons for visible window"""
        all_sessions = self.session_utils.get_available_sessions()

        # Update global session state
        self.all_session_names = all_sessions
        self.session_buttons = []

        if not all_sessions:
            # No sessions available
            self.selected_global_index = -1
            self.selected_local_index = -1
            no_sessions_label = Label(
                text="No sessions found", name="no-sessions-label"
            )
            no_sessions_label.set_markup(
                "<span style='italic'>No sessions found</span>"
            )

            return Box(
                orientation="vertical",
                spacing=5,
                name="sessions-container",
                children=[no_sessions_label],
            )

        # Initialize selection state for first run
        if self.selected_global_index >= len(all_sessions):
            self.selected_global_index = 0

        # Get visible sessions for current window
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
        """Calculate which sessions should be visible based on current selection"""
        total_sessions = len(self.all_session_names)

        if total_sessions <= self.VISIBLE_WINDOW_SIZE:
            # All sessions fit in window
            self.visible_start_index = 0
            return list(range(total_sessions))

        # Calculate window position to keep selection visible
        window_end = self.visible_start_index + self.VISIBLE_WINDOW_SIZE

        # If selection is outside current window, adjust window
        if self.selected_global_index < self.visible_start_index:
            # Selection is above visible window
            self.visible_start_index = self.selected_global_index
        elif self.selected_global_index >= window_end:
            # Selection is below visible window
            self.visible_start_index = (
                self.selected_global_index - self.VISIBLE_WINDOW_SIZE + 1
            )

        # Ensure window doesn't go past end of list
        self.visible_start_index = min(
            self.visible_start_index, total_sessions - self.VISIBLE_WINDOW_SIZE
        )
        self.visible_start_index = max(0, self.visible_start_index)

        # Calculate local selection index
        self.selected_local_index = (
            self.selected_global_index - self.visible_start_index
        )

        # Return indices of visible sessions
        return list(
            range(
                self.visible_start_index,
                min(
                    self.visible_start_index + self.VISIBLE_WINDOW_SIZE, total_sessions
                ),
            )
        )

    def get_visible_sessions(self):
        """Get the list of sessions that should be currently visible"""
        visible_indices = self.calculate_visible_window()
        return [self.all_session_names[i] for i in visible_indices]

    def has_sessions_above(self):
        """Check if there are sessions above the visible window"""
        return self.visible_start_index > 0

    def has_sessions_below(self):
        """Check if there are sessions below the visible window"""
        total_sessions = len(self.all_session_names)
        return (self.visible_start_index + self.VISIBLE_WINDOW_SIZE) < total_sessions

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
        if not self.all_session_names:
            return

        # Move to next session in global list (with wraparound)
        total_sessions = len(self.all_session_names)
        self.selected_global_index = (self.selected_global_index + 1) % total_sessions

        # Refresh display to show new selection and handle scrolling
        self.update_display()

    def select_previous(self):
        """Select the previous session with intelligent scrolling"""
        if not self.all_session_names:
            return

        # Move to previous session in global list (with wraparound)
        total_sessions = len(self.all_session_names)
        self.selected_global_index = (self.selected_global_index - 1) % total_sessions

        # Refresh display to show new selection and handle scrolling
        self.update_display()

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

    def handle_key_press(self, keycode):
        """Handle keyboard events for different browse panel states"""        
        if self.state == "delete_confirm":
            if keycode == KEYCODE_ENTER:
                # Perform delete operation
                print(f"DEBUG: Confirmed delete for session: {self.selected_session_for_delete}")
                # TODO: Add actual delete operation here
                self.set_state("browsing")  # Return to browsing for now
                return True
            elif keycode == KEYCODE_ESCAPE:
                # Cancel delete operation
                print(f"DEBUG: Cancelled delete for session: {self.selected_session_for_delete}")
                self.selected_session_for_delete = None
                self.set_state("browsing")
                return True
        
        # Let main manager handle other keys in browsing state
        return False

