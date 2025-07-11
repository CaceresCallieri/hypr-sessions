"""
Session capture functionality
"""

import json
import subprocess
from datetime import datetime

from utils import Utils


class SessionCapture(Utils):

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

    def capture_session(self, session_name):
        """Capture current workspace state including groups"""
        print(f"Capturing session: {session_name}")

        # Get all clients (windows) from current workspace
        clients = self.get_hyprctl_data("clients")
        if not clients:
            print("No clients found")
            return False

        # Get current workspace to filter clients
        current_workspace_data = self.get_hyprctl_data("activeworkspace")
        current_workspace_id = (
            current_workspace_data.get("id") if current_workspace_data else None
        )

        # Filter clients for current workspace only
        workspace_clients = [
            client
            for client in clients
            if client.get("workspace", {}).get("id") == current_workspace_id
        ]

        if not workspace_clients:
            print(f"No clients found in current workspace")
            return False

        # Process groups - build group mapping
        groups = {}  # group_id -> list of window addresses
        address_to_group = {}  # window address -> group_id

        for client in workspace_clients:
            address = client.get("address", "")
            group_info = client.get("grouped", [])

            if group_info:  # This window is in a group
                # Use the first address in the group as the group ID
                group_addresses = [addr for addr in group_info if addr]
                if group_addresses:
                    group_id = group_addresses[
                        0
                    ]  # Use first address as group identifier
                    if group_id not in groups:
                        groups[group_id] = []
                    groups[group_id] = group_addresses
                    address_to_group[address] = group_id

        # Process each client
        session_data = {
            "session_name": session_name,
            "timestamp": datetime.now().isoformat(),
            "windows": [],
            "groups": groups,  # Store group information
        }

        for client in workspace_clients:
            address = client.get("address", "")

            window_data = {
                "address": address,
                "class": client.get("class", "unknown"),
                "title": client.get("title", ""),
                "pid": client.get("pid"),
                "at": client.get("at", [0, 0]),  # [x, y] position
                "size": client.get("size", [800, 600]),  # [width, height]
                "floating": client.get("floating", False),
                "fullscreen": client.get("fullscreen", False),
                "initialClass": client.get("initialClass", ""),
                "initialTitle": client.get("initialTitle", ""),
                "grouped": client.get("grouped", []),
                "group_id": address_to_group.get(address, None),
            }

            # Try to determine launch command based on class
            launch_command = self.guess_launch_command(window_data)
            window_data["launch_command"] = launch_command

            session_data["windows"].append(window_data)

        # Debug: Print group information
        if groups:
            print(f"Found {len(groups)} groups:")
            for group_id, addresses in groups.items():
                print(f"  Group {group_id[:8]}... has {len(addresses)} windows")

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
