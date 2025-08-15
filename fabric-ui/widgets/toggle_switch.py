"""
Toggle Switch Widget for Hypr Sessions Manager
"""

from fabric.widgets.box import Box
from fabric.widgets.button import Button


class ToggleSwitchWidget(Box):
    """Segmented toggle switch widget for switching between Browse and Save modes"""
    
    def __init__(self, on_browse_clicked=None, on_save_clicked=None):
        super().__init__(
            orientation="horizontal",
            spacing=0,  # No spacing for seamless appearance
            name="segmented-toggle"
        )
        
        # State tracking
        self.is_save_mode = False
        
        # Store callbacks
        self.on_browse_clicked = on_browse_clicked
        self.on_save_clicked = on_save_clicked
        
        # Create left button (Browse Sessions)
        self.browse_button = Button(
            label="Browse Sessions",
            name="toggle-left-active",  # Start as active
            on_clicked=self._handle_browse_clicked
        )
        
        # Create right button (Save Session)
        self.save_button = Button(
            label="Save Session",
            name="toggle-right-inactive",  # Start as inactive
            on_clicked=self._handle_save_clicked
        )
        
        # Add buttons to container
        self.children = [self.browse_button, self.save_button]
        
        # Ensure buttons expand equally
        self.set_homogeneous(True)
    
    def _handle_browse_clicked(self, *args):
        """Handle browse button click"""
        if not self.is_save_mode:
            return  # Already in browse mode
            
        self.set_browse_mode()
        if self.on_browse_clicked:
            self.on_browse_clicked()
    
    def _handle_save_clicked(self, *args):
        """Handle save button click"""
        if self.is_save_mode:
            return  # Already in save mode
            
        self.set_save_mode()
        if self.on_save_clicked:
            self.on_save_clicked()
    
    def set_browse_mode(self):
        """Switch to browse mode visual state"""
        self.is_save_mode = False
        self.browse_button.set_name("toggle-left-active")
        self.save_button.set_name("toggle-right-inactive")
    
    def set_save_mode(self):
        """Switch to save mode visual state"""
        self.is_save_mode = True
        self.browse_button.set_name("toggle-left-inactive")
        self.save_button.set_name("toggle-right-active")