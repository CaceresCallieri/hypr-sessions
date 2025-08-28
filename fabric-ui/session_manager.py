#!/usr/bin/env python3
"""
Hypr Sessions Manager - Fabric Layer Widget
"""

from pathlib import Path

import gi
from fabric import Application
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.wayland import WaylandWindow

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, Gtk, GtkLayerShell, GLib

from utils.path_setup import setup_fabric_ui_imports

from constants import (
    BROWSING_STATE,
    DELETE_CONFIRM_STATE,
    RESTORE_CONFIRM_STATE,
    DEBUG_MODE_ENABLED,
    DEBUG_VERBOSE_MODE,
    DEBUG_OUTPUT_TO_TERMINAL,
    DEBUG_OUTPUT_TO_FILE,
    DEBUG_LOG_FILE,
)

# Import our custom widgets and utilities
from widgets import BrowsePanelWidget, SavePanelWidget, ToggleSwitchWidget

from utils import (
    SessionUtils,
    initialize_debug_logger,
    get_debug_logger
)


class SessionManagerWidget(WaylandWindow):
    def __init__(self):
        self.app = None  # Will be set after Application creation
        
        # Initialize debug logging system
        self.debug_logger = initialize_debug_logger(
            DEBUG_LOG_FILE, DEBUG_MODE_ENABLED, DEBUG_VERBOSE_MODE,
            DEBUG_OUTPUT_TO_TERMINAL, DEBUG_OUTPUT_TO_FILE
        )
        self.debug_logger.debug_session_lifecycle("ui_startup", "session_manager", "initializing")
        super().__init__(
            title="session-manager",
            name="session-manager",
            layer="top",
            anchor="center",
            exclusivity="none",
            keyboard_mode="on-demand",
            visible=False,
            all_visible=False,
        )

        # Initialize session utilities
        self.session_utils = SessionUtils()

        # Create content
        title_label = Label(text="Hypr Sessions Manager", name="hello-label")
        title_label.set_markup(
            "<span size='large' weight='bold'>Hypr Sessions Manager</span>"
        )

        subtitle_label = Label(
            text="Manage your Hyprland sessions", name="subtitle-label"
        )
        subtitle_label.set_markup(
            "<span size='small'>Manage your Hyprland sessions</span>"
        )

        # Create toggle switch with callbacks
        self.toggle_switch = ToggleSwitchWidget(
            on_browse_clicked=self._on_browse_mode, on_save_clicked=self._on_save_mode
        )

        # Create panels with callbacks
        self.browse_panel = BrowsePanelWidget(
            session_utils=self.session_utils,
            on_session_clicked=self._on_session_clicked,
        )

        self.save_panel = SavePanelWidget(
            on_save_success=self._on_save_success, on_save_error=self._on_save_error
        )

        # Create dynamic content area
        self.content_area = Box(
            orientation="vertical",
            spacing=10,
            name="dynamic-content",
            children=[self.browse_panel],  # Start with browse panel
        )

        # Create layout
        content_box = Box(
            orientation="vertical",
            spacing=15,
            name="content-box",
            children=[
                title_label,
                subtitle_label,
                self.toggle_switch,
                self.content_area,
            ],
        )

        # Add to window and ensure visibility
        self.add(content_box)

        # Force size allocation
        self.set_size_request(400, 400)

        # Connect keyboard and scroll events
        self.connect("key-press-event", self.on_key_press)

        # Connect scroll events and enable event masks
        self.connect("scroll-event", self.on_scroll_event)

        # Enable scroll event masks so the window receives scroll events
        self.set_events(
            self.get_events()
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.SMOOTH_SCROLL_MASK
        )

        # Configure layer shell for exclusive keyboard focus to prevent focus loss
        self._configure_layer_shell_focus()

        # Show window after all content is added
        self.show_all()
        
        # Delay focus setting until after window is fully shown and widgets are realized
        GLib.timeout_add(100, self._delayed_focus_setup)

    def _configure_layer_shell_focus(self):
        """Configure layer shell properties for reliable keyboard focus management"""
        try:
            # Initialize layer shell for this window if not already done by Fabric
            if not GtkLayerShell.is_layer_window(self):
                GtkLayerShell.init_for_window(self)

            # Set exclusive keyboard mode to prevent focus loss
            # This ensures the layer surface always maintains keyboard focus when visible
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)

            self.debug_logger.debug_focus_operation(
                "layer_shell_setup", "window", True, 
                {"keyboard_mode": "exclusive"}
            )

        except Exception as e:
            self.debug_logger.debug_focus_operation(
                "layer_shell_setup", "window", False, 
                {"error": str(e), "fallback": "default_behavior"}
            )

    def _delayed_focus_setup(self):
        """Set up initial focus after window is fully realized"""
        try:
            # Start in browse mode and ensure search input gets focus
            if not self.toggle_switch.is_save_mode and self.browse_panel.search_input:
                self.browse_panel.search_input.grab_focus()
                self.debug_logger.debug_focus_operation(
                    "startup_focus", "search_input", True,
                    {"mode": "browse", "timing": "delayed_setup"}
                )
        except Exception as e:
            self.debug_logger.debug_focus_operation(
                "startup_focus", "search_input", False,
                {"error": str(e), "mode": "browse"}
            )
        
        return False  # Don't repeat this timeout

    def _focus_search_input(self):
        """Focus the search input with error handling"""
        try:
            if self.browse_panel.search_input and self.browse_panel.search_input.get_realized():
                self.browse_panel.search_input.grab_focus()
                self.debug_logger.debug_focus_operation(
                    "manual_focus", "search_input", True,
                    {"realized": True, "trigger": "browse_mode_switch"}
                )
        except Exception as e:
            self.debug_logger.debug_focus_operation(
                "manual_focus", "search_input", False,
                {"error": str(e), "trigger": "browse_mode_switch"}
            )
        
        return False  # Don't repeat this timeout

    def _on_browse_mode(self):
        """Handle switch to browse mode"""
        self.debug_logger.debug_state_transition(
            "session_manager", "save_mode", "browse_mode", "toggle_switch"
        )

        # Switch to browse panel
        self.content_area.children = [self.browse_panel]
        self.content_area.show_all()
        
        # Auto-focus the search input for immediate typing (permanent focus)
        # Use a small delay to ensure widget is fully realized
        GLib.timeout_add(50, self._focus_search_input)

    def _on_save_mode(self):
        """Handle switch to save mode"""
        self.debug_logger.debug_state_transition(
            "session_manager", "browse_mode", "save_mode", "toggle_switch"
        )

        # Switch to save panel
        self.content_area.children = [self.save_panel]
        self.content_area.show_all()

        # Auto-focus the input field
        self.save_panel.focus_input()

    def _on_session_clicked(self, session_name):
        """Handle session button click"""
        self.debug_logger.debug_navigation_operation(
            "session_click", None, session_name, "mouse_click"
        )
        # TODO: Add restore functionality later

    def _on_save_success(self, session_name, result):
        """Handle successful save operation"""
        self.debug_logger.debug_session_lifecycle(
            "save", session_name, "success", {"result": str(result)}
        )

        # Refresh browse panel to show new session
        self.browse_panel.refresh()

    def _on_save_error(self, session_name, error_message):
        """Handle save operation error"""
        self.debug_logger.debug_session_lifecycle(
            "save", session_name, "error", {"error": error_message}
        )

    def on_key_press(self, widget, event):
        """Handle key press events"""
        keycode = event.get_keycode()[1]
        keyval = event.keyval
        
        # Log high-level key processing
        self.debug_logger.debug_event_routing(
            "key_press", keyval, "session_manager", "top_level",
            {"keycode": keycode, "save_mode": self.toggle_switch.is_save_mode}
        )

        # Give save panel first chance to handle events when in save mode
        # (especially for Escape key during save operations)
        if self.toggle_switch.is_save_mode:
            if self.save_panel.handle_key_press_event(widget, event):
                return True

        # Give browse panel first chance to handle events when in browse mode
        # Use new GTK event-based handling for better character detection
        elif not self.toggle_switch.is_save_mode:
            if self.browse_panel.handle_key_press_event(widget, event):
                return True

        # Check for Escape or Q key (global quit) - only if panels didn't handle it
        if keyval == Gdk.KEY_Escape or keyval == Gdk.KEY_q:
            if self.app:
                self.app.quit()  # Properly quit the entire application
            else:
                self.close()  # Fallback to just closing window
            return True  # Event handled

        # Check for Tab key - panel switching only
        elif keyval == Gdk.KEY_Tab:
            # Toggle between panels - toggle switch handles everything automatically
            if self.toggle_switch.is_save_mode:
                self.toggle_switch.set_browse_mode()  # Automatically calls _on_browse_mode()
            else:
                self.toggle_switch.set_save_mode()  # Automatically calls _on_save_mode()

            return True  # Event handled

        elif keyval == Gdk.KEY_Right:
            if not self.toggle_switch.is_save_mode:  # If in browse mode, go to save
                self.toggle_switch.set_save_mode()
            return True

        elif keyval == Gdk.KEY_Left:
            if self.toggle_switch.is_save_mode:  # If in save mode, go to browse
                self.toggle_switch.set_browse_mode()
            return True

        # Browse mode actions (navigation now handled by browse panel directly)
        elif not self.toggle_switch.is_save_mode:  # Browse mode
            # Session actions (navigation handled by browse panel)
            if keyval in [Gdk.KEY_Return, Gdk.KEY_KP_Enter]:
                # Trigger restore confirmation instead of direct activation
                self._initiate_session_action("restore")
                return True
            # Note: Arrow keys handled by browse panel to prevent focus loss
            # Note: Delete functionality moved to browse panel GTK event handling

        return False  # Event not handled

    def on_scroll_event(self, widget, event):
        """Handle scroll events for session navigation"""
        # Determine scroll direction
        is_scroll_up = self._get_scroll_direction(event)
        if is_scroll_up is None:
            return False  # Unknown direction or no vertical movement

        # Only handle scroll in browse mode during browsing state
        if not self._can_handle_scroll():
            return True  # Consume event but don't navigate

        # Navigate with natural scroll behavior
        if is_scroll_up:
            self.browse_panel.select_next()  # Scroll up moves down in list
        else:
            self.browse_panel.select_previous()  # Scroll down moves up in list

        return True  # Consume scroll events

    def _get_scroll_direction(self, event):
        """
        Determine scroll direction from event.

        Returns:
            True if scrolling up, False if scrolling down, None if unknown/no movement
        """
        direction = event.direction

        if direction == Gdk.ScrollDirection.UP:
            return True
        elif direction == Gdk.ScrollDirection.DOWN:
            return False
        elif direction == Gdk.ScrollDirection.SMOOTH:
            # Handle smooth scrolling with deltas
            success, delta_x, delta_y = event.get_scroll_deltas()
            if delta_y < 0:
                return True  # Scroll up
            elif delta_y > 0:
                return False  # Scroll down
            else:
                return None  # No vertical movement
        else:
            return None  # Unknown scroll direction

    def _can_handle_scroll(self):
        """Check if scroll navigation is currently allowed"""
        return (
            not self.toggle_switch.is_save_mode
            and getattr(self.browse_panel, "state", BROWSING_STATE) == BROWSING_STATE
        )

    def _initiate_session_action(self, action_type):
        """Helper method to initiate session actions (restore/delete) with consistent logic"""
        selected_session = self.browse_panel.get_selected_session()
        if selected_session:
            print(f"DEBUG: Initiating {action_type} for session: {selected_session}")
            if action_type == "restore":
                self.browse_panel.restore_operation.selected_session = selected_session
                self.browse_panel.set_state(RESTORE_CONFIRM_STATE)
            elif action_type == "delete":
                self.browse_panel.delete_operation.selected_session = selected_session
                self.browse_panel.set_state(DELETE_CONFIRM_STATE)
        else:
            print(f"DEBUG: No session selected for {action_type}")


def main():
    """Create and run the session manager widget"""
    print("Starting Hypr Sessions Manager...")

    # Create widget first
    widget = SessionManagerWidget()

    # Create application with widget
    app = Application("hypr-sessions-manager", widget)

    # Store app reference in widget for proper shutdown
    widget.app = app

    # Load CSS from external file
    css_path = Path(__file__).parent / "session_manager.css"
    if css_path.exists():
        app.set_stylesheet_from_file(str(css_path))
        print(f"Loaded stylesheet: {css_path}")
    else:
        print("Warning: session_manager.css not found")

    print(
        "Session Manager started! Press Tab/←→ to switch panels, ↑↓ to navigate sessions, Enter to restore, Esc or Q to exit"
    )
    app.run()


if __name__ == "__main__":
    main()
