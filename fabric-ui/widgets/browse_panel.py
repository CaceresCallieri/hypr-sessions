"""
Browse Panel Widget for Hypr Sessions Manager
"""

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label


class BrowsePanelWidget(Box):
    """Panel widget for browsing and selecting sessions"""
    
    def __init__(self, session_utils, on_session_clicked=None):
        super().__init__(
            orientation="vertical",
            spacing=10,
            name="browse-panel"
        )
        
        self.session_utils = session_utils
        self.on_session_clicked = on_session_clicked
        
        # Selection state management
        self.selected_index = 0    # Start with first session selected
        self.session_buttons = []  # List of session button widgets
        self.session_names = []    # List of session names (parallel to buttons)
        
        # Create panel content
        self._create_content()
    
    def _create_content(self):
        """Create the browse panel content"""
        # Sessions list section header
        sessions_header = Label(text="Available Sessions:", name="sessions-header")
        sessions_header.set_markup("<span weight='bold'>Available Sessions:</span>")
        
        # Get and create session buttons
        sessions_container = self._create_sessions_list()
        
        # Add to panel
        self.children = [sessions_header, sessions_container]
    
    def _create_sessions_list(self):
        """Create the sessions list container with buttons"""
        sessions = self.session_utils.get_available_sessions()
        
        # Reset state
        self.session_buttons = []
        self.session_names = sessions
        
        if not sessions:
            # No sessions available
            self.selected_index = -1  # No selection possible
            no_sessions_label = Label(
                text="No sessions found", 
                name="no-sessions-label"
            )
            no_sessions_label.set_markup(
                "<span style='italic'>No sessions found</span>"
            )
            
            return Box(
                orientation="vertical",
                spacing=5,
                name="sessions-container",
                children=[no_sessions_label]
            )
        
        # Create session buttons
        for i, session_name in enumerate(sessions):
            button = Button(
                label=f"• {session_name}",
                name="session-button",  # Base CSS class
                on_clicked=lambda *_, name=session_name: self._handle_session_clicked(name)
            )
            
            # Add selected class to first button
            if i == 0:
                button.get_style_context().add_class("selected")
            
            self.session_buttons.append(button)
        
        # Set first session as selected
        self.selected_index = 0 if sessions else -1
        
        return Box(
            orientation="vertical",
            spacing=5,
            name="sessions-container",
            children=self.session_buttons
        )
    
    def _handle_session_clicked(self, session_name):
        """Handle session button click"""
        print(f"Session clicked: {session_name}")
        if self.on_session_clicked:
            self.on_session_clicked(session_name)
    
    def refresh(self):
        """Refresh the sessions list"""
        self._create_content()
    
    def select_next(self):
        """Select the next session in the list (with wraparound)"""
        if not self.session_buttons:
            return
        
        # Remove selected class from current button
        if self.selected_index >= 0:
            self.session_buttons[self.selected_index].get_style_context().remove_class("selected")
        
        # Move to next (with wraparound)
        self.selected_index = (self.selected_index + 1) % len(self.session_buttons)
        
        # Add selected class to new button
        self.session_buttons[self.selected_index].get_style_context().add_class("selected")
    
    def select_previous(self):
        """Select the previous session in the list (with wraparound)"""
        if not self.session_buttons:
            return
        
        # Remove selected class from current button
        if self.selected_index >= 0:
            self.session_buttons[self.selected_index].get_style_context().remove_class("selected")
        
        # Move to previous (with wraparound)
        self.selected_index = (self.selected_index - 1) % len(self.session_buttons)
        
        # Add selected class to new button
        self.session_buttons[self.selected_index].get_style_context().add_class("selected")
    
    def get_selected_session(self):
        """Get the name of the currently selected session"""
        if 0 <= self.selected_index < len(self.session_names):
            return self.session_names[self.selected_index]
        return None
    
    def activate_selected_session(self):
        """Activate (restore) the currently selected session"""
        selected_session = self.get_selected_session()
        if selected_session and self.on_session_clicked:
            self.on_session_clicked(selected_session)