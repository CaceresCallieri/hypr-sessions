"""
Core session management functionality
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path


class SessionManager:
    def __init__(self):
        self.sessions_dir = Path.home() / ".config" / "hypr-sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def get_hyprctl_data(self, command):
        """Execute hyprctl command and return JSON data"""
        try:
            result = subprocess.run(
                ["hyprctl", command, "-j"], capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Error executing hyprctl {command}: {e}")
            return None

    def guess_launch_command(self, window_data):
        """Guess the launch command based on window class"""
        class_name = window_data.get("class", "").lower()
        title = window_data.get("title", "")

        # Common application mappings
        command_map = {
            "zen": "zen-browser",
            "com.mitchellh.ghostty": "ghostty",
            "firefox": "firefox",
            "chromium": "chromium",
            "google-chrome": "google-chrome",
            "alacritty": "alacritty",
            "kitty": "kitty",
            "foot": "foot",
            "neovim": "nvim",
            "code": "code",
            "code-oss": "code-oss",
            "thunar": "thunar",
            "nautilus": "nautilus",
            "dolphin": "dolphin",
        }

        return command_map.get(class_name, class_name)

    def list_sessions(self):
        """List all saved sessions"""
        session_files = list(self.sessions_dir.glob("*.json"))

        if not session_files:
            print("No saved sessions found")
            return

        print("Saved sessions:")
        print("-" * 40)

        for session_file in sorted(session_files):
            try:
                with open(session_file, "r") as f:
                    session_data = json.load(f)

                name = session_data.get("session_name", session_file.stem)
                timestamp = session_data.get("timestamp", "Unknown")
                window_count = len(session_data.get("windows", []))

                print(f"  {name}")
                print(f"    Windows: {window_count}")
                print(f"    Saved: {timestamp}")
                print()

            except Exception as e:
                print(f"  {session_file.stem} (Error reading: {e})")

    def delete_session(self, session_name):
        """Delete a saved session"""
        session_file = self.sessions_dir / f"{session_name}.json"

        if not session_file.exists():
            print(f"Session not found: {session_name}")
            return False

        try:
            session_file.unlink()
            print(f"Session deleted: {session_name}")
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
