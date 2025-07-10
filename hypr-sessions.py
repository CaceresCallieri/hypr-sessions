#!/usr/bin/env python3

"""
Hyprland Session Manager - Basic Prototype
Captures and restores workspace sessions in Hyprland
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class HyprlandSessionManager:
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

    def get_current_workspace(self):
        """Get the currently active workspace"""
        workspaces = self.get_hyprctl_data("activeworkspace")
        if workspaces:
            return workspaces.get("id", 1)
        return 1

    def capture_session(self, session_name):
        """Capture current workspace state"""
        print(f"Capturing session: {session_name}")

        # Get current workspace
        current_workspace = self.get_current_workspace()

        # Get all clients (windows)
        clients = self.get_hyprctl_data("clients")
        if not clients:
            print("No clients found")
            return False

        # Filter clients for current workspace
        workspace_clients = [
            client
            for client in clients
            if client.get("workspace", {}).get("id") == current_workspace
        ]

        if not workspace_clients:
            print(f"No clients found in workspace {current_workspace}")
            return False

        # Process each client
        session_data = {
            "session_name": session_name,
            "workspace": current_workspace,
            "timestamp": datetime.now().isoformat(),
            "windows": [],
        }

        for client in workspace_clients:
            window_data = {
                "class": client.get("class", "unknown"),
                "title": client.get("title", ""),
                "pid": client.get("pid"),
                "workspace": client.get("workspace", {}).get("id"),
                "at": client.get("at", [0, 0]),  # [x, y] position
                "size": client.get("size", [800, 600]),  # [width, height]
                "floating": client.get("floating", False),
                "fullscreen": client.get("fullscreen", False),
                "initialClass": client.get("initialClass", ""),
                "initialTitle": client.get("initialTitle", ""),
            }

            # Try to determine launch command based on class
            launch_command = self.guess_launch_command(window_data)
            window_data["launch_command"] = launch_command

            session_data["windows"].append(window_data)

        # Save session to file
        session_file = self.sessions_dir / f"{session_name}.json"
        try:
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)
            print(f"Session saved to: {session_file}")
            print(f"Captured {len(session_data['windows'])} windows")
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def guess_launch_command(self, window_data):
        """Guess the launch command based on window class"""
        class_name = window_data.get("class", "").lower()

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

    def restore_session(self, session_name):
        """Restore a saved session"""
        session_file = self.sessions_dir / f"{session_name}.json"

        if not session_file.exists():
            print(f"Session file not found: {session_file}")
            return False

        try:
            with open(session_file, "r") as f:
                session_data = json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
            return False

        print(f"Restoring session: {session_name}")
        print(f"Original workspace: {session_data.get('workspace')}")
        print(f"Timestamp: {session_data.get('timestamp')}")

        # Get current workspace
        current_workspace = self.get_current_workspace()

        # Launch each application
        for window in session_data.get("windows", []):
            command = window.get("launch_command", "")
            if not command:
                continue

            print(f"Launching: {command}")

            try:
                # Launch application in background
                subprocess.Popen(
                    command.split(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                # Small delay between launches
                import time

                time.sleep(0.5)

            except Exception as e:
                print(f"Error launching {command}: {e}")

        print(f"Restored {len(session_data.get('windows', []))} applications")
        print("Note: Window positioning will be handled by Hyprland's layout")
        return True

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
                workspace = session_data.get("workspace", "Unknown")

                print(f"  {name}")
                print(f"    Workspace: {workspace}")
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


def main():
    parser = argparse.ArgumentParser(description="Hyprland Session Manager")
    parser.add_argument(
        "action",
        choices=["save", "restore", "list", "delete"],
        help="Action to perform",
    )
    parser.add_argument(
        "session_name",
        nargs="?",
        help="Name of the session (required for save/restore/delete)",
    )

    args = parser.parse_args()

    manager = HyprlandSessionManager()

    if args.action == "save":
        if not args.session_name:
            print("Session name is required for save action")
            sys.exit(1)
        manager.capture_session(args.session_name)

    elif args.action == "restore":
        if not args.session_name:
            print("Session name is required for restore action")
            sys.exit(1)
        manager.restore_session(args.session_name)

    elif args.action == "list":
        manager.list_sessions()

    elif args.action == "delete":
        if not args.session_name:
            print("Session name is required for delete action")
            sys.exit(1)
        manager.delete_session(args.session_name)


if __name__ == "__main__":
    main()
