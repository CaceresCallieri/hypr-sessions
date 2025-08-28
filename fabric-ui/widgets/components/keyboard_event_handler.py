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
        modifiers = event.state
        
        # Enhanced debug event routing with human-readable keys
        if self.debug_logger:
            key_name = self.debug_logger.get_human_readable_key(keyval, modifiers)
            
            # Event flow tracing for verbose mode
            self.debug_logger.debug_event_flow(
                key_name, widget.__class__.__name__, "handle_key_press_event", "routing_decision",
                {"state": self.browse_panel.state, "keyval": keyval}
            )
            
            # Standard event routing log  
            self.debug_logger.debug_event_routing(
                "key_press", keyval, "browse_panel", "handle_key_press_event",
                {"state": self.browse_panel.state, "widget": widget.__class__.__name__, "key": key_name}
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
        key_name = self.debug_logger.get_human_readable_key(keyval, event.state) if self.debug_logger else str(keyval)

        # UI navigation keys go to navigation handlers
        is_navigation = self._is_ui_navigation_key(keyval)
        if is_navigation:
            if self.debug_logger:
                self.debug_logger.debug_key_detection(
                    keyval, "navigation", False, False,
                    {"routing_decision": "navigation_handler", "key": key_name}
                )
                self.debug_logger.debug_action_outcome(
                    key_name, "routed_to_navigation", {"handler": "keyboard_event_handler"}
                )
            return False

        # Handle modifier combinations (Ctrl+key, Alt+key, etc.)
        has_modifiers = bool(event.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK))
        if has_modifiers:
            if self.debug_logger:
                self.debug_logger.debug_key_detection(
                    keyval, "modifier_combo", False, has_modifiers,
                    {"routing_decision": "blocked", "modifiers": event.state, "key": key_name}
                )
                self.debug_logger.debug_action_outcome(
                    key_name, "modifier_combo_blocked", {"modifiers": event.state}
                )
            return False  # Don't route modifier combinations to search

        # Everything else goes to search input for filtering/editing
        if self.debug_logger:
            self.debug_logger.debug_key_detection(
                keyval, "printable", True, has_modifiers,
                {"routing_decision": "search_input", "key": key_name}
            )
            self.debug_logger.debug_action_outcome(
                key_name, "routed_to_search", {"handler": "search_input"}
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
                # Enhanced action outcome logging
                self.debug_logger.debug_action_outcome(
                    "Ctrl+D", "delete_confirmation_displayed", 
                    {"session": selected_session, "state": f"{self.browse_panel.state}→{DELETE_CONFIRM_STATE}"}
                )
                self.debug_logger.debug_event_flow(
                    "Ctrl+D", "KeyboardEventHandler", "_handle_ctrl_d_delete", 
                    f"delete_confirmation_for_{selected_session}"
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
                self.debug_logger.debug_action_outcome(
                    "Ctrl+D", "delete_failed", {"reason": "no_session_selected"}
                )
            return True

    def _handle_ctrl_l_clear_search(self) -> bool:
        """Handle Ctrl+L clear search operation
        
        Returns:
            True if operation was handled
        """
        # Debug log the clear search trigger
        if self.debug_logger:
            old_query = self.browse_panel.search_query
            self.debug_logger.debug_navigation_operation(
                "clear_search_trigger", None, None, "ctrl_l_shortcut",
                {"search_query": old_query, "state": self.browse_panel.state}
            )
            self.debug_logger.debug_action_outcome(
                "Ctrl+L", "search_cleared", 
                {"from": old_query, "to": "", "focus": "search_input"}
            )
            self.debug_logger.debug_event_flow(
                "Ctrl+L", "KeyboardEventHandler", "_handle_ctrl_l_clear_search", 
                "search_input_cleared_and_focused"
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
            # Get current selection for outcome logging
            old_selection = self.browse_panel.get_selected_session()
            
            # Handle session navigation directly
            if keyval == Gdk.KEY_Up:
                self.browse_panel.select_previous()
                direction = "previous"
                key_name = "Up"
            else:
                self.browse_panel.select_next()
                direction = "next"
                key_name = "Down"
            
            # Log action outcome
            if self.debug_logger:
                new_selection = self.browse_panel.get_selected_session()
                if old_selection != new_selection:
                    self.debug_logger.debug_action_outcome(
                        key_name, "selection_changed", 
                        {"from": old_selection, "to": new_selection, "direction": direction}
                    )
                    self.debug_logger.debug_event_flow(
                        key_name, "KeyboardEventHandler", "_handle_navigation_keys", 
                        f"selected_{direction}_session_{new_selection}"
                    )
                else:
                    self.debug_logger.debug_action_outcome(
                        key_name, "selection_unchanged", 
                        {"session": old_selection, "reason": "boundary_reached", "direction": direction}
                    )
            
            return True
        elif keyval in [Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_Tab, Gdk.KEY_Left, Gdk.KEY_Right]:
            # Let main manager handle session activation and panel switching
            return False

        return False