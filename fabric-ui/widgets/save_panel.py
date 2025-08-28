"""
Save Panel Widget for Hypr Sessions Manager
"""

# Import for backend integration
import threading
import time

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.label import Label

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib

from utils.path_setup import setup_fabric_ui_imports

from utils import (
    BackendClient,
    BackendError
)


class SavePanelWidget(Box):
    """Panel widget for saving new sessions"""

    # Configuration constants
    OPERATION_TIMEOUT = 35  # seconds (longer than backend timeout)
    MIN_DISPLAY_TIME = 0.5  # seconds (minimum saving state visibility)
    SUCCESS_AUTO_RETURN_DELAY = 2  # seconds (auto-return from success)

    def __init__(self, on_save_success=None, on_save_error=None, debug_logger=None):
        super().__init__(orientation="vertical", spacing=15, name="save-panel")

        # Updated callback system
        self.on_save_success = on_save_success
        self.on_save_error = on_save_error
        self.debug_logger = debug_logger

        # Backend client
        try:
            self.backend_client = BackendClient()
        except FileNotFoundError as e:
            print(f"Warning: Backend client unavailable: {e}")
            self.backend_client = None

        # State management
        self.state = "input"  # States: "input", "saving", "success", "error"
        self.saving_session_name = None
        self.last_session_name = ""  # For error recovery
        self.save_in_progress = False  # Prevent multiple concurrent saves
        
        # Widget references (created in _create_content)
        self.session_name_entry = None
        self.save_button = None

        # Create panel content
        self._create_content()

    def _create_content(self):
        """Create the save panel content based on current state"""
        if self.state == "input":
            self.children = self._create_input_ui()
        elif self.state == "saving":
            self.children = self._create_saving_ui()
        elif self.state == "success":
            self.children = self._create_success_ui()
        elif self.state == "error":
            self.children = self._create_error_ui()

    def _create_input_ui(self):
        """Create the normal input UI"""
        # Save session header
        save_header = Label(text="Save New Session:", name="save-header")
        save_header.set_markup("<span weight='bold'>Save New Session:</span>")

        # Session name input
        self.session_name_entry = Entry(
            placeholder_text="Enter session name...", name="session-name-input"
        )
        
        # Restore previous session name if available (for error recovery)
        if self.last_session_name:
            self.session_name_entry.set_text(self.last_session_name)

        # Save button
        self.save_button = Button(
            label="Save Current Session",
            name="save-session-button",
            on_clicked=self._handle_save_clicked,
        )

        return [save_header, self.session_name_entry, self.save_button]

    def _create_saving_ui(self):
        """Create the saving state UI"""
        # Center-aligned saving message
        saving_message = Label(
            text=f"Saving session '{self.saving_session_name}'...",
            name="save-status-info"
        )
        saving_message.set_markup(
            f"<span size='large'>Saving session</span>\n"
            f"<span weight='bold'>'{self.saving_session_name}'</span>\n"
            f"<span size='small' style='italic'>Please wait...</span>"
        )
        
        return [saving_message]

    def _create_success_ui(self):
        """Create the success state UI"""
        success_message = Label(
            text=f"Session '{self.saving_session_name}' saved successfully!",
            name="save-status-success"
        )
        success_message.set_markup(
            f"<span size='large'>Success!</span>\n"
            f"<span weight='bold'>Session '{self.saving_session_name}'</span>\n"
            f"<span>saved successfully</span>"
        )
        
        # Auto-return to input state after configured delay
        GLib.timeout_add_seconds(self.SUCCESS_AUTO_RETURN_DELAY, self._return_to_input)
        
        return [success_message]

    def _create_error_ui(self):
        """Create the error state UI with retry option"""
        error_message = Label(
            text="Failed to save session",
            name="save-status-error"
        )
        error_message.set_markup(
            f"<span size='large'>Save Failed</span>\n"
            f"<span size='small'>Session '{self.saving_session_name}'</span>\n"
            f"<span size='small' style='italic'>Check the error and try again</span>"
        )
        
        # Retry button
        retry_button = Button(
            label="Try Again",
            name="save-session-button",
            on_clicked=self._handle_retry_clicked,
        )
        
        # Back button
        back_button = Button(
            label="Back to Input",
            name="save-session-button",
            on_clicked=self._handle_back_clicked,
        )
        
        return [error_message, retry_button, back_button]

    def _handle_save_clicked(self, button):
        """Handle save button click with state-based UI"""
        self._trigger_save_operation()

    def _trigger_save_operation(self):
        """Common save logic used by both button click and Enter key"""
        # Prevent multiple concurrent saves
        if self.save_in_progress:
            print("Save already in progress, ignoring request")
            return
            
        session_name = self.session_name_entry.get_text().strip()

        # Validate input
        if not session_name:
            # Could add validation error state, but for now just return
            return

        if not self.backend_client:
            # Could add backend error state
            return

        # Mark save as in progress
        self.save_in_progress = True
        
        # Store session name and transition to saving state
        self.saving_session_name = session_name
        self.last_session_name = session_name  # For error recovery
        self.set_state("saving")

        # Start save operation with timeout protection
        self._start_save_operation(session_name)

    def _start_save_operation(self, session_name):
        """Start the actual save operation asynchronously"""
        # Set a timeout for the save operation
        self.timeout_id = GLib.timeout_add_seconds(self.OPERATION_TIMEOUT, self._handle_save_timeout)
        
        def run_save_operation():
            """Run the save operation in a separate thread"""
            try:
                # Ensure saving state is visible for at least 500ms for better UX
                start_time = time.time()
                
                # Call backend to save session
                result = self.backend_client.save_session(session_name)
                
                # Calculate minimum delay to show saving state
                elapsed = time.time() - start_time
                if elapsed < self.MIN_DISPLAY_TIME:
                    time.sleep(self.MIN_DISPLAY_TIME - elapsed)
                
                # Schedule UI update on main thread
                GLib.idle_add(self._handle_save_success, session_name, result)
                
            except BackendError as e:
                # Schedule error handling on main thread
                GLib.idle_add(self._handle_save_error_async, session_name, str(e))
                
            except Exception as e:
                # Schedule error handling on main thread
                GLib.idle_add(self._handle_save_error_async, session_name, str(e))
        
        # Start the save operation in a background thread
        save_thread = threading.Thread(target=run_save_operation, daemon=True)
        save_thread.start()

    def _cleanup_operation(self):
        """Clean up the current save operation"""
        if hasattr(self, 'timeout_id'):
            GLib.source_remove(self.timeout_id)
            delattr(self, 'timeout_id')
        self.save_in_progress = False

    def _handle_save_success(self, session_name, result):
        """Handle successful save operation on main thread"""
        self._cleanup_operation()
        
        if result.get("success", False):
            # Success - transition to success state
            self.set_state("success")
            
            # Notify parent component
            if self.on_save_success:
                self.on_save_success(session_name, result)
        else:
            # Backend returned error - transition to error state
            error_msg = result.get("messages", [{}])[0].get(
                "message", "Unknown error"
            )
            self.set_state("error")
            
            if self.on_save_error:
                self.on_save_error(session_name, error_msg)
        
        return False  # Don't repeat this idle callback

    def _handle_save_error_async(self, session_name, error_message):
        """Handle save operation error on main thread"""
        self._cleanup_operation()
            
        # Backend communication error
        self.set_state("error")
        if self.on_save_error:
            self.on_save_error(session_name, error_message)
        
        return False  # Don't repeat this idle callback

    def set_state(self, new_state):
        """Change the UI state and refresh content"""
        if new_state != self.state:
            print(f"SavePanel: {self.state} → {new_state}")  # Debug logging
            self.state = new_state
            self._create_content()
            self.show_all()

    def _handle_save_timeout(self):
        """Handle save operation timeout"""
        print("Save operation timed out")
        self._cleanup_operation()
        self.set_state("error")
        if self.on_save_error:
            self.on_save_error(self.saving_session_name, "Save operation timed out")
        return False  # Don't repeat timeout

    def _return_to_input(self):
        """Return to input state after success"""
        self.set_state("input")
        self.clear_input()  # Clear the input field for next use
        return False  # Don't repeat timeout

    def _handle_retry_clicked(self, button):
        """Handle retry button click"""
        # Prevent multiple concurrent saves
        if self.save_in_progress:
            return
            
        # Mark save as in progress and transition back to saving state
        self.save_in_progress = True
        self.set_state("saving")
        self._start_save_operation(self.saving_session_name)

    def _handle_back_clicked(self, button):
        """Handle back to input button click"""
        self.set_state("input")

    def focus_input(self):
        """Focus the session name input field"""
        if self.session_name_entry:
            self.session_name_entry.grab_focus()

    def clear_input(self):
        """Clear the session name input field"""
        if self.session_name_entry:
            self.session_name_entry.set_text("")
        self.last_session_name = ""  # Clear recovery name too

    def get_session_name(self):
        """Get the current session name from input"""
        if self.session_name_entry:
            return self.session_name_entry.get_text().strip()
        return ""

    def handle_key_press_event(self, widget, event):
        """Handle keyboard events using GTK event-based handling
        
        Args:
            widget: Widget that received the event
            event: GTK key press event
            
        Returns:
            True if event was handled, False to continue propagation
        """
        keyval = event.keyval
        modifiers = event.state
        
        # Enhanced debug logging with human-readable keys
        if self.debug_logger:
            key_name = self.debug_logger.get_human_readable_key(keyval, modifiers)
            self.debug_logger.debug_event_flow(
                key_name, "SavePanelWidget", "handle_key_press_event", "save_panel_key_handling",
                {"state": self.state, "keyval": keyval}
            )
        
        # Enter key handling - trigger save when in input state
        if keyval in [Gdk.KEY_Return, Gdk.KEY_KP_Enter]:
            if self.state == "input":
                if self.debug_logger:
                    key_name = self.debug_logger.get_human_readable_key(keyval, modifiers)
                    session_name = self.get_session_name()
                    self.debug_logger.debug_action_outcome(
                        key_name, "save_operation_triggered", 
                        {"session": session_name, "state": f"{self.state}→saving"}
                    )
                    self.debug_logger.debug_event_flow(
                        key_name, "SavePanelWidget", "_trigger_save_operation", 
                        f"saving_session_{session_name}"
                    )
                
                # Trigger the same save logic as button click
                self._trigger_save_operation()
                return True
        
        # Escape or Q key handling based on current state
        elif keyval == Gdk.KEY_Escape or keyval == Gdk.KEY_q:
            if self.debug_logger:
                key_name = self.debug_logger.get_human_readable_key(keyval, modifiers)
                
            if self.state == "saving":
                # Cancel save operation
                if self.debug_logger:
                    self.debug_logger.debug_action_outcome(
                        key_name, "save_operation_cancelled", 
                        {"state": f"{self.state}→input", "session": self.saving_session_name}
                    )
                    self.debug_logger.debug_event_flow(
                        key_name, "SavePanelWidget", "handle_key_press_event", 
                        "cancel_save_operation"
                    )
                
                print("Cancelling save operation...")
                self.save_in_progress = False
                self.set_state("input")
                return True
            elif self.state == "error":
                # Return to input from error state
                if self.debug_logger:
                    self.debug_logger.debug_action_outcome(
                        key_name, "error_state_dismissed", 
                        {"state": f"{self.state}→input", "session": self.saving_session_name}
                    )
                
                self.set_state("input")
                return True
            elif self.state == "success":
                # Skip auto-return timer and go directly to input
                if self.debug_logger:
                    self.debug_logger.debug_action_outcome(
                        key_name, "success_state_dismissed", 
                        {"state": f"{self.state}→input", "session": self.saving_session_name}
                    )
                
                self.set_state("input")
                self.clear_input()
                return True
        
        return False  # Let other handlers process the key

    def cancel_save_operation(self):
        """Manually cancel an ongoing save operation"""
        if self.state == "saving" and self.save_in_progress:
            print("Manually cancelling save operation")
            self.save_in_progress = False
            self.set_state("input")

