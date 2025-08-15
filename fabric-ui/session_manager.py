#!/usr/bin/env python3
"""
Hypr Sessions Manager - Fabric Layer Widget
"""

import os
import sys
from pathlib import Path

# Import GTK for the switch widget
import gi
from fabric import Application
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.wayland import WaylandWindow

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# Add parent directory to path to import session utilities
sys.path.append(str(Path(__file__).parent.parent))

# Import our custom widgets and utilities
from widgets import ToggleSwitchWidget, BrowsePanelWidget, SavePanelWidget
from utils import SessionUtils


class SessionManagerWidget(WaylandWindow):
    def __init__(self):
        super().__init__(
            title="session-manager",
            name="session-manager",
            layer="top",
            anchor="center",
            exclusivity="none",
            keyboard_mode="on-demand",
            visible=True,
            all_visible=True,
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
            on_browse_clicked=self._on_browse_mode,
            on_save_clicked=self._on_save_mode
        )

        # Create panels with callbacks
        self.browse_panel = BrowsePanelWidget(
            session_utils=self.session_utils,
            on_session_clicked=self._on_session_clicked
        )
        
        self.save_panel = SavePanelWidget(
            on_save_clicked=self._on_save_session
        )

        # Create dynamic content area
        self.content_area = Box(
            orientation="vertical",
            spacing=10,
            name="dynamic-content",
            children=[self.browse_panel]  # Start with browse panel
        )

        # Create layout
        content_box = Box(
            orientation="vertical",
            spacing=15,
            name="content-box",
            children=[title_label, subtitle_label, self.toggle_switch, self.content_area],
        )

        # Add to window and ensure visibility
        self.add(content_box)

        # Force size allocation
        self.set_size_request(400, 300)

        # Connect keyboard events
        self.connect("key-press-event", self.on_key_press)

        # Show everything
        content_box.show_all()
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

    def _on_save_session(self, session_name):
        """Handle save session request"""
        print(f"Saving session: {session_name}")
        # TODO: Connect to actual save functionality
        
        # Refresh browse panel in case we switch back
        self.browse_panel.refresh()

    def on_key_press(self, widget, event):
        """Handle key press events"""
        # Check for Escape key (keycode 9)
        if event.get_keycode()[1] == 9:  # Esc key
            self.close()
            return True  # Event handled
        return False  # Event not handled


def main():
    """Create and run the session manager widget"""
    print("Starting Hypr Sessions Manager...")

    # Create widget
    widget = SessionManagerWidget()

    # Create application
    app = Application("hypr-sessions-manager", widget)

    # Load CSS from external file
    css_path = Path(__file__).parent / "session_manager.css"
    if css_path.exists():
        app.set_stylesheet_from_file(str(css_path))
        print(f"Loaded stylesheet: {css_path}")
    else:
        print("Warning: session_manager.css not found")

    print("Session Manager started! Press Ctrl+C or click Close to exit")
    app.run()


if __name__ == "__main__":
    main()