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
        self.all_session_names = []     # Complete list of all sessions
        self.session_buttons = []       # List of currently visible session button widgets
        
        # Scrollable window management
        self.VISIBLE_WINDOW_SIZE = 5    # Maximum sessions to display at once (configurable)
        self.visible_start_index = 0    # First visible session index in global list
        self.selected_global_index = 0  # Selected session index in global list
        self.selected_local_index = 0   # Selected session index within visible window
        
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
        
        # Initialize selection state for first run
        if self.selected_global_index >= len(all_sessions):
            self.selected_global_index = 0
        
        # Get visible sessions for current window
        visible_sessions = self.get_visible_sessions()
        
        # Create session buttons for visible sessions only
        widgets = []
        for i, session_name in enumerate(visible_sessions):
            global_index = self.visible_start_index + i
            button = Button(
                label=f"• {session_name}",
                name="session-button",  # Base CSS class
                on_clicked=lambda *_, name=session_name: self._handle_session_clicked(name)
            )
            
            # Add selected class if this is the selected session
            if global_index == self.selected_global_index:
                button.get_style_context().add_class("selected")
            
            self.session_buttons.append(button)
            widgets.append(button)
        
        return Box(
            orientation="vertical",
            spacing=5,
            name="sessions-container",
            children=widgets
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
            self.visible_start_index = self.selected_global_index - self.VISIBLE_WINDOW_SIZE + 1
        
        # Ensure window doesn't go past end of list
        self.visible_start_index = min(
            self.visible_start_index,
            total_sessions - self.VISIBLE_WINDOW_SIZE
        )
        self.visible_start_index = max(0, self.visible_start_index)
        
        # Calculate local selection index
        self.selected_local_index = self.selected_global_index - self.visible_start_index
        
        # Return indices of visible sessions
        return list(range(
            self.visible_start_index,
            min(self.visible_start_index + self.VISIBLE_WINDOW_SIZE, total_sessions)
        ))
    
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