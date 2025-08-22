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
        
        # Create browse button (start as active)
        self.browse_button = Button(
            label="Browse Sessions",
            name="browse-button",
            on_clicked=self._handle_browse_clicked
        )
        
        # Create save button (start as inactive)
        self.save_button = Button(
            label="Save Session",
            name="save-button",
            on_clicked=self._handle_save_clicked
        )
        
        # Set initial state: browse active, save inactive
        self.browse_button.get_style_context().add_class("active")
        # save button starts without active class (inactive by default)
        
        # Add buttons to container
        self.children = [self.browse_button, self.save_button]
        
        # Ensure buttons expand equally
        self.set_homogeneous(True)
    
    def _handle_browse_clicked(self, *args):
        """Handle browse button click"""
        # set_browse_mode() now handles everything including callbacks
        self.set_browse_mode()
    
    def _handle_save_clicked(self, *args):
        """Handle save button click"""
        # set_save_mode() now handles everything including callbacks
        self.set_save_mode()
    
    def set_browse_mode(self):
        """Switch to browse mode - updates visual state and triggers callback"""
        if not self.is_save_mode:
            return  # Already in browse mode
            
        self.is_save_mode = False
        
        # Update CSS classes for state management
        self.browse_button.get_style_context().add_class("active")
        self.save_button.get_style_context().remove_class("active")
        
        # Automatically trigger callback for panel switching
        if self.on_browse_clicked:
            self.on_browse_clicked()
    
    def set_save_mode(self):
        """Switch to save mode - updates visual state and triggers callback"""
        if self.is_save_mode:
            return  # Already in save mode
            
        self.is_save_mode = True
        
        # Update CSS classes for state management
        self.browse_button.get_style_context().remove_class("active")
        self.save_button.get_style_context().add_class("active")
        
        # Automatically trigger callback for panel switching
        if self.on_save_clicked:
            self.on_save_clicked()