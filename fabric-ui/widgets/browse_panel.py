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
        
        if not sessions:
            # Show "no sessions" message
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
        session_buttons = []
        for session_name in sessions:
            button = Button(
                label=f"• {session_name}",
                name="session-button",
                on_clicked=lambda *_, name=session_name: self._handle_session_clicked(name)
            )
            session_buttons.append(button)
        
        return Box(
            orientation="vertical",
            spacing=5,
            name="sessions-container",
            children=session_buttons
        )
    
    def _handle_session_clicked(self, session_name):
        """Handle session button click"""
        print(f"Session clicked: {session_name}")
        if self.on_session_clicked:
            self.on_session_clicked(session_name)
    
    def refresh(self):
        """Refresh the sessions list"""
        self._create_content()