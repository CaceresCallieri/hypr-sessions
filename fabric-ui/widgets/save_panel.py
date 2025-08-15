"""
Save Panel Widget for Hypr Sessions Manager
"""

# Import for backend integration
import sys
from pathlib import Path

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.label import Label

sys.path.append(str(Path(__file__).parent.parent))
from utils import BackendClient, BackendError


class SavePanelWidget(Box):
    """Panel widget for saving new sessions"""

    def __init__(self, on_save_success=None, on_save_error=None):
        super().__init__(orientation="vertical", spacing=15, name="save-panel")

        # Updated callback system
        self.on_save_success = on_save_success
        self.on_save_error = on_save_error

        # Backend client
        try:
            self.backend_client = BackendClient()
        except FileNotFoundError as e:
            print(f"Warning: Backend client unavailable: {e}")
            self.backend_client = None

        # Status message label (initially hidden)
        self.status_label = Label(text="", name="save-status-label")

        # Create panel content
        self._create_content()

    def _create_content(self):
        """Create the save panel content"""
        # Save session header
        save_header = Label(text="Save New Session:", name="save-header")
        save_header.set_markup("<span weight='bold'>Save New Session:</span>")

        # Session name input
        self.session_name_entry = Entry(
            placeholder_text="Enter session name...", name="session-name-input"
        )

        # Save button
        save_button = Button(
            label="Save Current Session",
            name="save-session-button",
            on_clicked=self._handle_save_clicked,
        )

        # Add to panel (include status label)
        self.children = [
            save_header,
            self.session_name_entry,
            save_button,
            self.status_label,
        ]

    def _handle_save_clicked(self, button):
        """Handle save button click with backend integration"""
        session_name = self.session_name_entry.get_text().strip()

        # Clear previous status
        self._clear_status()

        if not session_name:
            self._show_error("Please enter a session name")
            return

        if not self.backend_client:
            self._show_error("Backend client unavailable")
            return

        # Disable button during save
        button.set_sensitive(False)
        self._show_status("Saving session...", "info")

        try:
            # Call backend to save session
            result = self.backend_client.save_session(session_name)

            if result.get("success", False):
                # Success - break into multiple lines to prevent width expansion
                windows_saved = result.get("data", {}).get("windows_saved", 0)
                success_message = f"✅ Session '{session_name}'\nSaved successfully\n{windows_saved} windows"
                self._show_success(success_message)
                self.clear_input()

                # Notify parent component
                if self.on_save_success:
                    self.on_save_success(session_name, result)
            else:
                # Backend returned error
                error_msg = result.get("messages", [{}])[0].get(
                    "message", "Unknown error"
                )
                self._show_error(f"❌ Save failed: {error_msg}")

                if self.on_save_error:
                    self.on_save_error(session_name, error_msg)

        except BackendError as e:
            # Backend communication error
            self._show_error(f"❌ Backend error: {str(e)}")
            if self.on_save_error:
                self.on_save_error(session_name, str(e))

        except Exception as e:
            # Unexpected error
            self._show_error(f"❌ Unexpected error: {str(e)}")
            if self.on_save_error:
                self.on_save_error(session_name, str(e))

        finally:
            # Re-enable button
            button.set_sensitive(True)

    def focus_input(self):
        """Focus the session name input field"""
        self.session_name_entry.grab_focus()

    def clear_input(self):
        """Clear the session name input field"""
        self.session_name_entry.set_text("")

    def get_session_name(self):
        """Get the current session name from input"""
        return self.session_name_entry.get_text().strip()

    def _show_status(self, message: str, status_type: str = "info"):
        """Show a status message"""
        if status_type == "success":
            self.status_label.set_name("save-status-success")
        elif status_type == "error":
            self.status_label.set_name("save-status-error")
        else:
            self.status_label.set_name("save-status-info")

        self.status_label.set_text(message)
        self.status_label.show()

    def _show_success(self, message: str):
        """Show a success message"""
        self._show_status(message, "success")

    def _show_error(self, message: str):
        """Show an error message"""
        self._show_status(message, "error")

    def _clear_status(self):
        """Clear the status message"""
        self.status_label.set_text("")
        self.status_label.hide()

