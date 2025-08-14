#!/usr/bin/env python3
"""
Hypr Sessions Manager - Fabric Layer Widget
"""

import sys
import os
from pathlib import Path
from fabric import Application
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.wayland import WaylandWindow

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
        title_label = Label(
            text="Hypr Sessions Manager",
            name="hello-label"
        )
        title_label.set_markup("<span size='large' weight='bold'>Hypr Sessions Manager</span>")

        subtitle_label = Label(
            text="Manage your Hyprland sessions",
            name="subtitle-label"
        )
        subtitle_label.set_markup("<span size='small'>Manage your Hyprland sessions</span>")

        # Sessions list section
        sessions_header = Label(
            text="Available Sessions:",
            name="sessions-header"
        )
        sessions_header.set_markup("<span weight='bold'>Available Sessions:</span>")

        # Get and create session buttons
        sessions_container = self.create_sessions_list()

        # Create layout
        content_box = Box(
            orientation="vertical",
            spacing=15,
            name="content-box",
            children=[title_label, subtitle_label, sessions_header, sessions_container],
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
                text="No sessions found",
                name="no-sessions-label"
            )
            no_sessions_label.set_markup("<span style='italic'>No sessions found</span>")
            
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
                on_clicked=lambda *_, name=session_name: self.on_session_clicked(name)
            )
            session_buttons.append(button)
        
        return Box(
            orientation="vertical",
            spacing=5,
            name="sessions-container",
            children=session_buttons
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

