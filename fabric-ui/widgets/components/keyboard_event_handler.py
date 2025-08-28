"""
Keyboard Event Handler Component

Handles keyboard events and routing for browse panel functionality.
Extracted from BrowsePanelWidget for better separation of concerns.
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk

from constants import (
    BROWSING_STATE,
    DELETE_CONFIRM_STATE,
    RESTORE_CONFIRM_STATE
)


class KeyboardEventHandler:
    """Handles keyboard events and routing for browse panel"""

    def __init__(self, browse_panel):
        """Initialize the keyboard event handler
        
        Args:
            browse_panel: Reference to the parent browse panel widget
        """
        self.browse_panel = browse_panel
        self.debug_logger = getattr(browse_panel, 'debug_logger', None)

    def handle_key_press_event(self, widget, event) -> bool:
        """Handle keyboard events using full GTK event context
        
        Args:
            widget: Widget that received the event
            event: GTK key press event
            
        Returns:
            True if event was handled, False to continue propagation
        """
        keyval = event.keyval
        
        # Debug event routing decisions
        if self.debug_logger:
            self.debug_logger.debug_event_routing(
                "key_press", keyval, "browse_panel", "handle_key_press_event",
                {"state": self.browse_panel.state, "widget": widget.__class__.__name__}
            )

        # Route based on current panel state
        if self.browse_panel.state == DELETE_CONFIRM_STATE:
            return self._handle_confirmation_state_event(
                event, self.browse_panel.delete_operation
            )
        elif self.browse_panel.state == RESTORE_CONFIRM_STATE:
            return self._handle_confirmation_state_event(
                event, self.browse_panel.restore_operation
            )
        elif self.browse_panel.state == BROWSING_STATE:
            # Use GTK event-based routing
            if self.should_route_to_search(event):
                # Let GTK route to search input (don't handle here)
                return False
            else:
                # Handle UI navigation keys
                return self._handle_navigation_event(event)

        # Let main manager handle other keys
        return False

    def should_route_to_search(self, event) -> bool:
        """Determine if event should route to search input using GTK event properties
        
        Args:
            event: GTK key press event
            
        Returns:
            True if event should go to search input, False for navigation
        """
        keyval = event.keyval

        # UI navigation keys go to navigation handlers
        is_navigation = self._is_ui_navigation_key(keyval)
        if is_navigation:
            if self.debug_logger:
                self.debug_logger.debug_key_detection(
                    keyval, "navigation", False, False,
                    {"routing_decision": "navigation_handler"}
                )
            return False

        # Handle modifier combinations (Ctrl+key, Alt+key, etc.)
        has_modifiers = bool(event.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK))
        if has_modifiers:
            if self.debug_logger:
                self.debug_logger.debug_key_detection(
                    keyval, "modifier_combo", False, has_modifiers,
                    {"routing_decision": "blocked", "modifiers": event.state}
                )
            return False  # Don't route modifier combinations to search

        # Everything else goes to search input for filtering/editing
        if self.debug_logger:
            self.debug_logger.debug_key_detection(
                keyval, "printable", True, has_modifiers,
                {"routing_decision": "search_input"}
            )
        return True

    def _is_ui_navigation_key(self, keyval) -> bool:
        """Check if keyval represents a UI navigation key using GTK constants
        
        Args:
            keyval: GTK key value
            
        Returns:
            True if key is for UI navigation, False otherwise
        """
        ui_navigation = {
            # Session navigation
            Gdk.KEY_Up,
            Gdk.KEY_Down,
            # Actions
            Gdk.KEY_Return,
            Gdk.KEY_KP_Enter,  # Restore session
            # Panel switching
            Gdk.KEY_Tab,
            Gdk.KEY_Left,
            Gdk.KEY_Right,
        }
        return keyval in ui_navigation

    def _handle_confirmation_state_event(self, event, operation) -> bool:
        """Handle confirmation state with GTK event
        
        Args:
            event: GTK key press event
            operation: Delete or restore operation instance
            
        Returns:
            True if event was handled
        """
        keyval = event.keyval

        if keyval in [Gdk.KEY_Return, Gdk.KEY_KP_Enter]:
            # Trigger the operation
            operation.trigger_operation()
            return True
        elif keyval == Gdk.KEY_Escape:
            # Cancel operation
            if self.debug_logger and self.debug_logger.enabled:
                operation_name = operation.get_operation_config()['action_verb'].lower()
                self.debug_logger.debug_operation_state(
                    operation_name, "cancelled", operation.selected_session
                )
            
            operation.selected_session = None
            self.browse_panel.set_state(BROWSING_STATE)
            return True

        return False

    def _handle_navigation_event(self, event) -> bool:
        """Handle navigation events in browsing state
        
        Args:
            event: GTK key press event
            
        Returns:
            True if event was handled
        """
        keyval = event.keyval
        has_ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)

        # Handle keyboard shortcuts with focused methods
        if has_ctrl:
            return self._handle_ctrl_shortcuts(event, keyval)
        
        return self._handle_navigation_keys(keyval)

    def _handle_ctrl_shortcuts(self, event, keyval) -> bool:
        """Handle Ctrl+key combinations
        
        Args:
            event: GTK key press event
            keyval: GTK key value
            
        Returns:
            True if shortcut was handled
        """
        if keyval == Gdk.KEY_d:
            return self._handle_ctrl_d_delete()
        elif keyval == Gdk.KEY_l:
            return self._handle_ctrl_l_clear_search()
        
        return False

    def _handle_ctrl_d_delete(self) -> bool:
        """Handle Ctrl+D delete operation trigger
        
        Returns:
            True if operation was initiated
        """
        selected_session = self.browse_panel.get_selected_session()
        if selected_session:
            # Debug log the delete trigger
            if self.debug_logger:
                self.debug_logger.debug_navigation_operation(
                    "delete_trigger", selected_session, None, "ctrl_d_shortcut",
                    {"state": self.browse_panel.state}
                )
            
            self.browse_panel.delete_operation.selected_session = selected_session
            self.browse_panel.set_state(DELETE_CONFIRM_STATE)
            return True
        else:
            if self.debug_logger and self.debug_logger.enabled:
                self.debug_logger.debug_navigation_operation(
                    "delete_trigger_failed", None, None, "ctrl_d_shortcut",
                    {"reason": "no_session_selected"}
                )
            return True

    def _handle_ctrl_l_clear_search(self) -> bool:
        """Handle Ctrl+L clear search operation
        
        Returns:
            True if operation was handled
        """
        # Debug log the clear search trigger
        if self.debug_logger:
            self.debug_logger.debug_navigation_operation(
                "clear_search_trigger", None, None, "ctrl_l_shortcut",
                {"search_query": self.browse_panel.search_query, "state": self.browse_panel.state}
            )
        
        self.browse_panel.clear_search()
        return True

    def _handle_navigation_keys(self, keyval) -> bool:
        """Handle navigation keys (arrows, enter, tab)
        
        Args:
            keyval: GTK key value
            
        Returns:
            True if key was handled
        """
        if keyval in [Gdk.KEY_Up, Gdk.KEY_Down]:
            # Handle session navigation directly
            if keyval == Gdk.KEY_Up:
                self.browse_panel.select_previous()
            else:
                self.browse_panel.select_next()
            return True
        elif keyval in [Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_Tab, Gdk.KEY_Left, Gdk.KEY_Right]:
            # Let main manager handle session activation and panel switching
            return False

        return False