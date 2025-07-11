"""
Session save functionality
"""

import json
import shlex
import subprocess
from datetime import datetime
from pathlib import Path

from utils import Utils


class SessionSave(Utils):

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
        working_dir = window_data.get("working_directory")

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

        base_command = command_map.get(class_name, class_name)

        # For terminal applications, add working directory flag
        if self.is_terminal_app(class_name) and working_dir:
            # Properly escape the path for shell safety
            escaped_dir = shlex.quote(working_dir)

            if class_name == "alacritty":
                return f"{base_command} --working-directory={escaped_dir}"
            elif class_name == "kitty":
                return f"{base_command} --directory={escaped_dir}"
            elif class_name == "foot":
                return f"{base_command} --working-directory={escaped_dir}"
            elif class_name == "com.mitchellh.ghostty":
                return f"{base_command} --working-directory={escaped_dir}"
            elif class_name == "wezterm":
                return f"{base_command} --cwd={escaped_dir}"
            else:
                # Generic fallback - many terminals support --directory
                return f"{base_command} --directory={escaped_dir}"

        return base_command

    def get_working_directory(self, pid):
        """Get the working directory of a terminal process by finding its shell child"""
        try:
            # First try the process itself
            cwd_path = Path(f"/proc/{pid}/cwd")
            if cwd_path.exists():
                terminal_cwd = str(cwd_path.resolve())
                # If it's not the home directory, use it
                if terminal_cwd != str(Path.home()):
                    return terminal_cwd

            # If terminal CWD is home, look for shell children
            children = self.get_child_processes(pid)
            for child_pid in children:
                try:
                    child_cwd_path = Path(f"/proc/{child_pid}/cwd")
                    if child_cwd_path.exists():
                        child_cwd = str(child_cwd_path.resolve())
                        # Use child's working directory if it's different from home
                        if child_cwd != str(Path.home()):
                            return child_cwd
                except (OSError, PermissionError):
                    continue

            # Fallback to terminal's directory even if it's home
            return terminal_cwd if "terminal_cwd" in locals() else None

        except (OSError, PermissionError):
            pass
        return None

    def get_child_processes(self, parent_pid):
        """Get list of child process PIDs"""
        children = []
        try:
            # Read /proc/*/stat to find children
            proc_dirs = Path("/proc").glob("[0-9]*")
            for proc_dir in proc_dirs:
                try:
                    stat_file = proc_dir / "stat"
                    if stat_file.exists():
                        with open(stat_file, "r") as f:
                            stat_data = f.read().split()
                            if len(stat_data) >= 4:
                                ppid = int(stat_data[3])  # Parent PID is 4th field
                                if ppid == parent_pid:
                                    children.append(int(proc_dir.name))
                except (ValueError, OSError, PermissionError):
                    continue
        except (OSError, PermissionError):
            pass
        return children

    def is_terminal_app(self, class_name):
        """Check if the application is a terminal emulator"""
        terminal_apps = {
            "alacritty",
            "kitty",
            "foot",
            "com.mitchellh.ghostty",
            "wezterm",
            "gnome-terminal",
            "konsole",
            "xfce4-terminal",
            "terminator",
            "st",
            "urxvt",
            "rxvt-unicode",
        }
        return class_name.lower() in terminal_apps

    def save_session(self, session_name):
        """Save current workspace state including groups"""
        print(f"Saving session: {session_name}")

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

            # For terminal applications, capture working directory
            if self.is_terminal_app(window_data["class"]):
                pid = window_data.get("pid")
                if pid:
                    working_dir = self.get_working_directory(pid)
                    if working_dir:
                        window_data["working_directory"] = working_dir
                        print(f"  Captured working directory: {working_dir}")

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
            print(f"Saved {len(session_data['windows'])} windows")
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
