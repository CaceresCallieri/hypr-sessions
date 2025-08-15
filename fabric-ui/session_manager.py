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
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.label import Label
from fabric.widgets.wayland import WaylandWindow

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# Add parent directory to path to import session utilities
sys.path.append(str(Path(__file__).parent.parent))


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

        # Toggle switch section
        toggle_container = self.create_toggle_switch()

        # Create panels
        self.browse_panel = self.create_browse_panel()
        self.save_panel = self.create_save_panel()

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
            children=[title_label, subtitle_label, toggle_container, self.content_area],
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

    def create_toggle_switch(self):
        """Create a segmented toggle switch like Hotels/Apartments example"""
        # State tracking
        self.is_save_mode = False

        # Create left button (Browse Sessions)
        self.browse_button = Button(
            label="Browse Sessions",
            name="toggle-left-active",  # Start as active
            on_clicked=lambda *_: self.set_browse_mode(),
        )

        # Create right button (Save Session)
        self.save_button = Button(
            label="Save Session",
            name="toggle-right-inactive",  # Start as inactive
            on_clicked=lambda *_: self.set_save_mode(),
        )

        # Create container that looks like a single segmented control
        toggle_box = Box(
            orientation="horizontal",
            spacing=0,  # No spacing for seamless appearance
            name="segmented-toggle",
            children=[self.browse_button, self.save_button],
        )

        # Ensure buttons expand equally
        toggle_box.set_homogeneous(True)

        return toggle_box

    def create_browse_panel(self):
        """Create the browse sessions panel"""
        # Sessions list section header
        sessions_header = Label(text="Available Sessions:", name="sessions-header")
        sessions_header.set_markup("<span weight='bold'>Available Sessions:</span>")

        # Get and create session buttons
        sessions_container = self.create_sessions_list()

        # Create browse panel container
        browse_panel = Box(
            orientation="vertical",
            spacing=10,
            name="browse-panel",
            children=[sessions_header, sessions_container],
        )

        return browse_panel

    def create_save_panel(self):
        """Create the save session panel"""
        # Save session header
        save_header = Label(text="Save New Session:", name="save-header")
        save_header.set_markup("<span weight='bold'>Save New Session:</span>")

        # Session name input
        self.session_name_entry = Entry(
            placeholder_text="Enter session name...", name="session-name-input"
        )

        # Save button
        save_button = Button(
            label="💾 Save Current Session",
            name="save-session-button",
            on_clicked=self.on_save_session_clicked,
        )

        # Create save panel container
        save_panel = Box(
            orientation="vertical",
            spacing=15,
            name="save-panel",
            children=[save_header, self.session_name_entry, save_button],
        )

        return save_panel

    def on_save_session_clicked(self, button):
        """Handle save session button click"""
        session_name = self.session_name_entry.get_text()
        if session_name.strip():
            print(f"Saving session: {session_name}")
            # TODO: Connect to actual save functionality
            self.session_name_entry.set_text("")  # Clear input
        else:
            print("Please enter a session name")

    def set_browse_mode(self):
        """Switch to browse sessions mode"""
        if not self.is_save_mode:
            return  # Already in browse mode

        self.is_save_mode = False
        print("Switched to Browse Sessions mode")

        # Update button styles
        self.browse_button.set_name("toggle-left-active")
        self.save_button.set_name("toggle-right-inactive")

        # Switch to browse panel
        self.content_area.children = [self.browse_panel]
        self.content_area.show_all()

    def set_save_mode(self):
        """Switch to save session mode"""
        if self.is_save_mode:
            return  # Already in save mode

        self.is_save_mode = True
        print("Switched to Save Session mode")

        # Update button styles
        self.browse_button.set_name("toggle-left-inactive")
        self.save_button.set_name("toggle-right-active")

        # Switch to save panel
        self.content_area.children = [self.save_panel]
        self.content_area.show_all()

        # Auto-focus the input field
        self.session_name_entry.grab_focus()

    def get_sessions_directory(self):
        """Get the sessions directory path"""
        home = Path.home()
        return home / ".config" / "hypr-sessions"

    def get_available_sessions(self):
        """Get list of available session names"""
        sessions_dir = self.get_sessions_directory()
        if not sessions_dir.exists():
            return []

        sessions = []
        for item in sessions_dir.iterdir():
            if item.is_dir():
                session_file = item / "session.json"
                if session_file.exists():
                    sessions.append(item.name)

        return sorted(sessions)

    def create_sessions_list(self):
        """Create the sessions list container with buttons"""
        sessions = self.get_available_sessions()

        if not sessions:
            # Show "no sessions" message
            no_sessions_label = Label(
                text="No sessions found", name="no-sessions-label"
            )
            no_sessions_label.set_markup(
                "<span style='italic'>No sessions found</span>"
            )

            return Box(
                orientation="vertical",
                spacing=5,
                name="sessions-container",
                children=[no_sessions_label],
            )

        # Create session buttons
        session_buttons = []
        for session_name in sessions:
            button = Button(
                label=f"• {session_name}",
                name="session-button",
                on_clicked=lambda *_, name=session_name: self.on_session_clicked(name),
            )
            session_buttons.append(button)

        return Box(
            orientation="vertical",
            spacing=5,
            name="sessions-container",
            children=session_buttons,
        )

    def on_session_clicked(self, session_name):
        """Handle session button click (placeholder for now)"""
        print(f"Session clicked: {session_name}")
        # TODO: Add restore functionality later

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
