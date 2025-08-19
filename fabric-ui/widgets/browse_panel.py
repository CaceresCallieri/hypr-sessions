"""
Browse Panel Widget for Hypr Sessions Manager
"""

import sys
import threading
import time
from pathlib import Path

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib

# Add parent directory to path for clean imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import constants and backend client
from constants import KEYCODE_ENTER, KEYCODE_ESCAPE
from utils import BackendClient, BackendError


class BrowsePanelWidget(Box):
    """Panel widget for browsing and selecting sessions"""
    
    # Configuration constants
    OPERATION_TIMEOUT = 35  # seconds (longer than backend timeout)
    MIN_DISPLAY_TIME = 0.5  # seconds (minimum deleting state visibility)
    SUCCESS_AUTO_RETURN_DELAY = 2  # seconds (auto-return from success)

    def __init__(self, session_utils, on_session_clicked=None):
        super().__init__(orientation="vertical", spacing=10, name="browse-panel")

        self.session_utils = session_utils
        self.on_session_clicked = on_session_clicked
        
        # Backend client for delete operations
        try:
            self.backend_client = BackendClient()
        except FileNotFoundError as e:
            print(f"Warning: Backend client unavailable: {e}")
            self.backend_client = None

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
        self.state = "browsing"  # States: "browsing", "delete_confirm", "deleting", "delete_success", "delete_error", "restore_confirm", "restoring", "restore_success", "restore_error"
        self.selected_session_for_delete = None
        self.delete_in_progress = False  # Prevent multiple concurrent deletes
        
        # Restore state management
        self.selected_session_for_restore = None
        self.restore_in_progress = False  # Prevent multiple concurrent restores

        # Create panel content
        self._create_content()

    def _create_content(self):
        """Create the browse panel content based on current state"""
        if self.state == "browsing":
            self.children = self._create_browsing_ui()
        elif self.state == "delete_confirm":
            self.children = self._create_delete_confirmation_ui()
        elif self.state == "deleting":
            self.children = self._create_deleting_ui()
        elif self.state == "delete_success":
            self.children = self._create_delete_success_ui()
        elif self.state == "delete_error":
            self.children = self._create_delete_error_ui()
        elif self.state == "restore_confirm":
            self.children = self._create_restore_confirmation_ui()
        elif self.state == "restoring":
            self.children = self._create_restoring_ui()
        elif self.state == "restore_success":
            self.children = self._create_restore_success_ui()
        elif self.state == "restore_error":
            self.children = self._create_restore_error_ui()

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

    def _create_deleting_ui(self):
        """Create the deleting state UI"""
        session_name = self.selected_session_for_delete or "Unknown"
        
        # Center-aligned deleting message
        deleting_message = Label(
            text=f"Deleting session '{session_name}'...",
            name="delete-status-info"
        )
        deleting_message.set_markup(
            f"<span size='large'>Deleting session</span>\n"
            f"<span weight='bold'>'{session_name}'</span>\n"
            f"<span size='small' style='italic'>Please wait...</span>"
        )
        
        return [deleting_message]

    def _create_delete_success_ui(self):
        """Create the delete success state UI"""
        session_name = self.selected_session_for_delete or "Unknown"
        
        success_message = Label(
            text=f"Session '{session_name}' deleted successfully!",
            name="delete-status-success"
        )
        success_message.set_markup(
            f"<span size='large'>Success!</span>\n"
            f"<span weight='bold'>Session '{session_name}'</span>\n"
            f"<span>deleted successfully</span>"
        )
        
        # Auto-return to browsing state after configured delay
        GLib.timeout_add_seconds(self.SUCCESS_AUTO_RETURN_DELAY, self._return_to_browsing)
        
        return [success_message]

    def _create_delete_error_ui(self):
        """Create the delete error state UI with retry option"""
        session_name = self.selected_session_for_delete or "Unknown"
        
        error_message = Label(
            text="Failed to delete session",
            name="delete-status-error"
        )
        error_message.set_markup(
            f"<span size='large'>Delete Failed</span>\n"
            f"<span size='small'>Session '{session_name}'</span>\n"
            f"<span size='small' style='italic'>Check the error and try again</span>"
        )
        
        # Retry button
        retry_button = Button(
            label="Try Again",
            name="delete-retry-button",
            on_clicked=self._handle_retry_delete_clicked,
        )
        
        # Back button
        back_button = Button(
            label="Back to Sessions",
            name="delete-back-button",
            on_clicked=self._handle_back_to_browsing_clicked,
        )
        
        return [error_message, retry_button, back_button]

    def _create_restore_confirmation_ui(self):
        """Create the restore confirmation UI"""
        session_name = self.selected_session_for_restore or "Unknown"
        
        # Main confirmation message (green theme for restore vs red for delete)
        warning_message = Label(
            text=f"Restore Session: {session_name}",
            name="restore-title"
        )
        warning_message.set_markup(f"<span weight='bold' color='#a6e3a1'>Restore Session: {session_name}</span>")
        
        # Confirmation text
        confirm_text = f"Restore '{session_name}' session to current workspace?\nThis will launch all saved applications and windows."
        confirm_message = Label(text=confirm_text, name="restore-confirmation")
        
        # Instructions
        instructions = Label(
            text="Press Enter to RESTORE • Esc to Cancel",
            name="restore-instructions"  
        )
        instructions.set_markup("<span size='small' style='italic'>Press Enter to RESTORE • Esc to Cancel</span>")
        
        return [warning_message, confirm_message, instructions]

    def _create_restoring_ui(self):
        """Create the restoring state UI"""
        session_name = self.selected_session_for_restore or "Unknown"
        
        # Center-aligned restoring message
        restoring_message = Label(
            text=f"Restoring session '{session_name}'...",
            name="restore-status-info"
        )
        restoring_message.set_markup(
            f"<span size='large'>Restoring session</span>\n"
            f"<span weight='bold'>'{session_name}'</span>\n"
            f"<span size='small' style='italic'>Please wait...</span>"
        )
        
        return [restoring_message]

    def _create_restore_success_ui(self):
        """Create the restore success state UI"""
        session_name = self.selected_session_for_restore or "Unknown"
        
        success_message = Label(
            text=f"Session '{session_name}' restored successfully!",
            name="restore-status-success"
        )
        success_message.set_markup(
            f"<span size='large'>Success!</span>\n"
            f"<span weight='bold'>Session '{session_name}'</span>\n"
            f"<span>restored successfully</span>"
        )
        
        # Auto-return to browsing state after configured delay
        GLib.timeout_add_seconds(self.SUCCESS_AUTO_RETURN_DELAY, self._return_to_browsing_from_restore)
        
        return [success_message]

    def _create_restore_error_ui(self):
        """Create the restore error state UI with retry option"""
        session_name = self.selected_session_for_restore or "Unknown"
        
        error_message = Label(
            text="Failed to restore session",
            name="restore-status-error"
        )
        error_message.set_markup(
            f"<span size='large'>Restore Failed</span>\n"
            f"<span size='small'>Session '{session_name}'</span>\n"
            f"<span size='small' style='italic'>Check the error and try again</span>"
        )
        
        # Retry button
        retry_button = Button(
            label="Try Again",
            name="restore-retry-button",
            on_clicked=self._handle_retry_restore_clicked,
        )
        
        # Back button
        back_button = Button(
            label="Back to Sessions",
            name="restore-back-button",
            on_clicked=self._handle_back_to_browsing_from_restore_clicked,
        )
        
        return [error_message, retry_button, back_button]

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

    def _trigger_delete_operation(self):
        """Trigger the delete operation for the selected session"""
        # Prevent multiple concurrent deletes
        if self.delete_in_progress:
            print("Delete already in progress, ignoring request")
            return
            
        if not self.selected_session_for_delete:
            print("No session selected for deletion")
            return
            
        if not self.backend_client:
            print("Backend client unavailable")
            return

        # Mark delete as in progress
        self.delete_in_progress = True
        
        # Transition to deleting state
        self.set_state("deleting")

        # Start delete operation with timeout protection
        self._start_delete_operation(self.selected_session_for_delete)

    def _start_delete_operation(self, session_name):
        """Start the actual delete operation asynchronously"""
        # Set a timeout for the delete operation
        self.timeout_id = GLib.timeout_add_seconds(self.OPERATION_TIMEOUT, self._handle_delete_timeout)
        
        def run_delete_operation():
            """Run the delete operation in a separate thread"""
            try:
                # Ensure deleting state is visible for at least 500ms for better UX
                start_time = time.time()
                
                # Call backend to delete session
                result = self.backend_client.delete_session(session_name)
                
                # Calculate minimum delay to show deleting state
                elapsed = time.time() - start_time
                if elapsed < self.MIN_DISPLAY_TIME:
                    time.sleep(self.MIN_DISPLAY_TIME - elapsed)
                
                # Schedule UI update on main thread
                GLib.idle_add(self._handle_delete_success, session_name, result)
                
            except BackendError as e:
                # Schedule error handling on main thread
                GLib.idle_add(self._handle_delete_error_async, session_name, str(e))
                
            except Exception as e:
                # Schedule error handling on main thread
                GLib.idle_add(self._handle_delete_error_async, session_name, str(e))
        
        # Start the delete operation in a background thread
        delete_thread = threading.Thread(target=run_delete_operation, daemon=True)
        delete_thread.start()

    def _cleanup_delete_operation(self):
        """Clean up the current delete operation"""
        if hasattr(self, 'timeout_id'):
            GLib.source_remove(self.timeout_id)
            delattr(self, 'timeout_id')
        self.delete_in_progress = False

    def _handle_delete_success(self, session_name, result):
        """Handle successful delete operation on main thread"""
        self._cleanup_delete_operation()
        
        if result.get("success", False):
            # Success - transition to success state
            self.set_state("delete_success")
        else:
            # Backend returned error - transition to error state
            error_msg = result.get("messages", [{}])[0].get(
                "message", "Unknown error"
            )
            self.set_state("delete_error")
        
        return False  # Don't repeat this idle callback

    def _handle_delete_error_async(self, session_name, error_message):
        """Handle delete operation error on main thread"""
        self._cleanup_delete_operation()
            
        # Backend communication error
        self.set_state("delete_error")
        
        return False  # Don't repeat this idle callback

    def _handle_delete_timeout(self):
        """Handle delete operation timeout"""
        print("Delete operation timed out")
        self._cleanup_delete_operation()
        self.set_state("delete_error")
        return False  # Don't repeat timeout

    def _return_to_browsing(self):
        """Return to browsing state after success"""
        self.selected_session_for_delete = None
        self.set_state("browsing")
        # Refresh session list to remove deleted session
        self.refresh()
        return False  # Don't repeat timeout

    def _handle_retry_delete_clicked(self, button):
        """Handle retry button click in error state"""
        # Prevent multiple concurrent deletes
        if self.delete_in_progress:
            return
            
        # Mark delete as in progress and transition back to deleting state
        self.delete_in_progress = True
        self.set_state("deleting")
        self._start_delete_operation(self.selected_session_for_delete)

    def _handle_back_to_browsing_clicked(self, button):
        """Handle back to browsing button click in error state"""
        self.selected_session_for_delete = None
        self.set_state("browsing")

    def handle_key_press(self, keycode):
        """Handle keyboard events for different browse panel states"""        
        if self.state == "delete_confirm":
            if keycode == KEYCODE_ENTER:
                # Trigger the actual delete operation
                self._trigger_delete_operation()
                return True
            elif keycode == KEYCODE_ESCAPE:
                # Cancel delete operation
                print(f"DEBUG: Cancelled delete for session: {self.selected_session_for_delete}")
                self.selected_session_for_delete = None
                self.set_state("browsing")
                return True
        
        elif self.state == "restore_confirm":
            if keycode == KEYCODE_ENTER:
                # Trigger the actual restore operation
                self._trigger_restore_operation()
                return True
            elif keycode == KEYCODE_ESCAPE:
                # Cancel restore operation
                print(f"DEBUG: Cancelled restore for session: {self.selected_session_for_restore}")
                self.selected_session_for_restore = None
                self.set_state("browsing")
                return True
        
        # Let main manager handle other keys in browsing state
        return False

    def _trigger_restore_operation(self):
        """Trigger the restore operation for the selected session"""
        # Prevent multiple concurrent restores
        if self.restore_in_progress:
            print("Restore already in progress, ignoring request")
            return
            
        if not self.selected_session_for_restore:
            print("No session selected for restoration")
            return
            
        if not self.backend_client:
            print("Backend client unavailable")
            return

        # Mark restore as in progress
        self.restore_in_progress = True
        
        # Transition to restoring state
        self.set_state("restoring")

        # For now, simulate the restore operation since we're not connecting to backend yet
        self._simulate_restore_operation(self.selected_session_for_restore)

    def _simulate_restore_operation(self, session_name):
        """Simulate the restore operation for frontend testing"""
        # Add timeout protection for consistency with real operations
        self.timeout_id = GLib.timeout_add_seconds(self.OPERATION_TIMEOUT, self._handle_restore_timeout)
        
        def run_simulate_restore():
            try:
                # Ensure restoring state is visible for at least 500ms for better UX
                start_time = time.time()
                
                # Simulate restore operation (2 seconds)
                time.sleep(2.0)
                
                # Calculate minimum delay to show restoring state
                elapsed = time.time() - start_time
                if elapsed < self.MIN_DISPLAY_TIME:
                    time.sleep(self.MIN_DISPLAY_TIME - elapsed)
                
                # Simulate success (for now - later we'll handle real backend responses)
                GLib.idle_add(self._handle_restore_success_simulation, session_name)
                
            except Exception as e:
                # Schedule error handling on main thread
                GLib.idle_add(self._handle_restore_error_simulation, session_name, str(e))
        
        # Start the simulate operation in a background thread
        restore_thread = threading.Thread(target=run_simulate_restore, daemon=True)
        restore_thread.start()

    def _handle_restore_success_simulation(self, session_name):
        """Handle simulated successful restore operation on main thread"""
        self._cleanup_restore_operation()
        
        # Success - transition to success state
        self.set_state("restore_success")
        
        return False  # Don't repeat this idle callback

    def _handle_restore_error_simulation(self, session_name, error_message):
        """Handle simulated restore operation error on main thread"""
        self._cleanup_restore_operation()
            
        # Simulation error
        self.set_state("restore_error")
        
        return False  # Don't repeat this idle callback

    def _cleanup_restore_operation(self):
        """Clean up the current restore operation"""
        if hasattr(self, 'timeout_id'):
            GLib.source_remove(self.timeout_id)
            delattr(self, 'timeout_id')
        self.restore_in_progress = False

    def _handle_restore_timeout(self):
        """Handle restore operation timeout"""
        print("Restore operation timed out")
        self._cleanup_restore_operation()
        self.set_state("restore_error")
        return False  # Don't repeat timeout

    def _return_to_browsing_from_restore(self):
        """Return to browsing state after restore success"""
        self.selected_session_for_restore = None
        self.set_state("browsing")
        # No need to refresh since restore doesn't change session list
        return False  # Don't repeat timeout

    def _handle_retry_restore_clicked(self, button):
        """Handle retry button click in restore error state"""
        # Prevent multiple concurrent restores
        if self.restore_in_progress:
            return
            
        # Mark restore as in progress and transition back to restoring state
        self.restore_in_progress = True
        self.set_state("restoring")
        self._simulate_restore_operation(self.selected_session_for_restore)

    def _handle_back_to_browsing_from_restore_clicked(self, button):
        """Handle back to browsing button click in restore error state"""
        self.selected_session_for_restore = None
        self.set_state("browsing")

