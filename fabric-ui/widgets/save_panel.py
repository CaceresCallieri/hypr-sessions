"""
Save Panel Widget for Hypr Sessions Manager
"""

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.label import Label


class SavePanelWidget(Box):
    """Panel widget for saving new sessions"""
    
    def __init__(self, on_save_clicked=None):
        super().__init__(
            orientation="vertical",
            spacing=15,
            name="save-panel"
        )
        
        self.on_save_clicked = on_save_clicked
        
        # Create panel content
        self._create_content()
    
    def _create_content(self):
        """Create the save panel content"""
        # Save session header
        save_header = Label(text="Save New Session:", name="save-header")
        save_header.set_markup("<span weight='bold'>Save New Session:</span>")
        
        # Session name input
        self.session_name_entry = Entry(
            placeholder_text="Enter session name...", 
            name="session-name-input"
        )
        
        # Save button
        save_button = Button(
            label="💾 Save Current Session",
            name="save-session-button",
            on_clicked=self._handle_save_clicked
        )
        
        # Add to panel
        self.children = [save_header, self.session_name_entry, save_button]
    
    def _handle_save_clicked(self, button):
        """Handle save button click"""
        session_name = self.session_name_entry.get_text()
        if session_name.strip():
            print(f"Saving session: {session_name}")
            if self.on_save_clicked:
                self.on_save_clicked(session_name)
            self.session_name_entry.set_text("")  # Clear input
        else:
            print("Please enter a session name")
    
    def focus_input(self):
        """Focus the session name input field"""
        self.session_name_entry.grab_focus()
    
    def clear_input(self):
        """Clear the session name input field"""
        self.session_name_entry.set_text("")
    
    def get_session_name(self):
        """Get the current session name from input"""
        return self.session_name_entry.get_text().strip()