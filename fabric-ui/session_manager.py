#!/usr/bin/env python3
"""
Hypr Sessions Manager - Fabric Layer Widget
"""

import sys
from pathlib import Path

import gi
from fabric import Application
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.wayland import WaylandWindow

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk

# Add parent directory to path to import session utilities
sys.path.append(str(Path(__file__).parent.parent))

# Import our custom widgets and utilities
from widgets import BrowsePanelWidget, SavePanelWidget, ToggleSwitchWidget
from utils import SessionUtils
from constants import (
    KEYCODE_ESCAPE,
    KEYCODE_TAB,
    KEYCODE_ENTER,
    KEYCODE_LEFT_ARROW,
    KEYCODE_RIGHT_ARROW,
    KEYCODE_UP_ARROW,
    KEYCODE_DOWN_ARROW,
    KEYCODE_D,
)


class SessionManagerWidget(WaylandWindow):
    def __init__(self):
        self.app = None  # Will be set after Application creation
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

        # Connect keyboard events
        self.connect("key-press-event", self.on_key_press)

        # Show window after all content is added
        self.show_all()

    def _on_browse_mode(self):
        """Handle switch to browse mode"""
        print("Switched to Browse Sessions mode")

        # Switch to browse panel
        self.content_area.children = [self.browse_panel]
        self.content_area.show_all()

    def _on_save_mode(self):
        """Handle switch to save mode"""
        print("Switched to Save Session mode")

        # Switch to save panel
        self.content_area.children = [self.save_panel]
        self.content_area.show_all()

        # Auto-focus the input field
        self.save_panel.focus_input()

    def _on_session_clicked(self, session_name):
        """Handle session button click"""
        print(f"Session clicked: {session_name}")
        # TODO: Add restore functionality later

    def _on_save_success(self, session_name, result):
        """Handle successful save operation"""
        print(f"Session '{session_name}' saved successfully!")

        # Refresh browse panel to show new session
        self.browse_panel.refresh()

    def _on_save_error(self, session_name, error_message):
        """Handle save operation error"""
        print(f"Failed to save session '{session_name}': {error_message}")

    def on_key_press(self, widget, event):
        """Handle key press events"""
        keycode = event.get_keycode()[1]
        state = event.get_state()

        # Give save panel first chance to handle events when in save mode
        # (especially for Escape key during save operations)
        if self.toggle_switch.is_save_mode:
            if self.save_panel.handle_key_press(keycode):
                return True

        # Give browse panel first chance to handle events when in browse mode
        # (especially for Escape key during delete confirmation)
        elif not self.toggle_switch.is_save_mode:
            if self.browse_panel.handle_key_press(keycode):
                return True

        # Check for Escape key (global quit) - only if panels didn't handle it
        if keycode == KEYCODE_ESCAPE:
            if self.app:
                self.app.quit()  # Properly quit the entire application
            else:
                self.close()  # Fallback to just closing window
            return True  # Event handled

        # Check for Tab key
        elif keycode == KEYCODE_TAB:
            # Toggle between panels - toggle switch handles everything automatically
            if self.toggle_switch.is_save_mode:
                self.toggle_switch.set_browse_mode()  # Automatically calls _on_browse_mode()
            else:
                self.toggle_switch.set_save_mode()  # Automatically calls _on_save_mode()

            return True  # Event handled

        elif keycode == KEYCODE_RIGHT_ARROW:
            if not self.toggle_switch.is_save_mode:  # If in browse mode, go to save
                self.toggle_switch.set_save_mode()
            return True

        elif keycode == KEYCODE_LEFT_ARROW:
            if self.toggle_switch.is_save_mode:  # If in save mode, go to browse
                self.toggle_switch.set_browse_mode()
            return True

        # Browse mode navigation (only for keys not handled by browse panel)
        elif not self.toggle_switch.is_save_mode:  # Browse mode
            # Standard navigation
            if keycode == KEYCODE_UP_ARROW:
                self.browse_panel.select_previous()
                return True
            elif keycode == KEYCODE_DOWN_ARROW:
                self.browse_panel.select_next()
                return True
            elif keycode == KEYCODE_ENTER:
                self.browse_panel.activate_selected_session()
                return True
            elif keycode == KEYCODE_D:
                # Check if a session is selected, then trigger delete confirmation
                selected_session = self.browse_panel.get_selected_session()
                if selected_session:
                    print(f"DEBUG: Initiating delete for session: {selected_session}")
                    self.browse_panel.selected_session_for_delete = selected_session
                    self.browse_panel.set_state("delete_confirm")
                else:
                    print("DEBUG: No session selected for deletion")
                return True

        return False  # Event not handled


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
        "Session Manager started! Press Tab/←→ to switch panels, ↑↓ to navigate sessions, Enter to restore, Esc to exit"
    )
    app.run()


if __name__ == "__main__":
    main()
