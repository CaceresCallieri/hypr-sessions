"""
Main session saving orchestration
"""

import json
from datetime import datetime

from utils import Utils
from .hyprctl_client import HyprctlClient
from .launch_commands import LaunchCommandGenerator
from .terminal_handler import TerminalHandler
from .neovide_handler import NeovideHandler


class SessionSaver(Utils):
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug
        self.hyprctl_client = HyprctlClient()
        self.launch_command_generator = LaunchCommandGenerator(debug=debug)
        self.terminal_handler = TerminalHandler()
        self.neovide_handler = NeovideHandler(debug=debug)
    
    def debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG SessionSaver] {message}")

    def save_session(self, session_name):
        """Save current workspace state including groups"""
        print(f"Saving session: {session_name}")
        self.debug_print(f"Starting session save for: {session_name}")

        # Get all clients (windows) from current workspace
        clients = self.hyprctl_client.get_hyprctl_data("clients")
        if not clients:
            print("No clients found")
            return False
        
        self.debug_print(f"Found {len(clients)} total clients")

        # Get current workspace to filter clients
        current_workspace_data = self.hyprctl_client.get_hyprctl_data("activeworkspace")
        current_workspace_id = (
            current_workspace_data.get("id") if current_workspace_data else None
        )
        self.debug_print(f"Current workspace ID: {current_workspace_id}")

        # Filter clients for current workspace only
        workspace_clients = [
            client
            for client in clients
            if client.get("workspace", {}).get("id") == current_workspace_id
        ]
        
        self.debug_print(f"Filtered to {len(workspace_clients)} clients in current workspace")

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
            client_class = client.get("class", "unknown")
            client_pid = client.get("pid")

            self.debug_print(f"Processing client: {client_class} (PID: {client_pid})")

            window_data = {
                "address": address,
                "class": client_class,
                "title": client.get("title", ""),
                "pid": client_pid,
                "at": client.get("at", [0, 0]),  # [x, y] position
                "size": client.get("size", [800, 600]),  # [width, height]
                "floating": client.get("floating", False),
                "fullscreen": client.get("fullscreen", False),
                "initialClass": client.get("initialClass", ""),
                "initialTitle": client.get("initialTitle", ""),
                "grouped": client.get("grouped", []),
                "group_id": address_to_group.get(address, None),
            }

            # For terminal applications, capture working directory and running program
            if self.terminal_handler.is_terminal_app(window_data["class"]):
                pid = window_data.get("pid")
                if pid:
                    working_dir = self.terminal_handler.get_working_directory(pid)
                    if working_dir:
                        window_data["working_directory"] = working_dir
                        print(f"  Captured working directory: {working_dir}")
                    
                    # Detect running program in the terminal
                    self.debug_print(f"Detecting running program for terminal PID {pid}")
                    running_program = self.terminal_handler.get_running_program(pid, debug=self.debug)
                    if running_program:
                        window_data["running_program"] = running_program
                        print(f"  Captured running program: {running_program['name']}")
                        self.debug_print(f"Running program details: {running_program}")
                    else:
                        self.debug_print("No running program detected (likely just shell)")

            # For Neovide windows, capture session information
            if self.neovide_handler.is_neovide_window(window_data):
                pid = window_data.get("pid")
                print(f"  Found Neovide window (PID: {pid})")
                self.debug_print(f"Detected Neovide window with class '{client_class}' and PID {pid}")
                neovide_session_info = self.neovide_handler.get_neovide_session_info(pid)
                self.debug_print(f"Neovide session info: {neovide_session_info}")
                if neovide_session_info:
                    window_data["neovide_session"] = neovide_session_info
                    # Try to create/capture session file
                    session_file = self.neovide_handler.create_session_file(pid, str(self.sessions_dir))
                    self.debug_print(f"Created session file: {session_file}")
                    if session_file:
                        window_data["neovide_session"]["session_file"] = session_file
                        print(f"  Captured Neovide session: {session_file}")
                    else:
                        print(f"  Could not capture Neovide session, will restore with working directory")
                else:
                    self.debug_print(f"Failed to get Neovide session info for PID {pid}")

            # Try to determine launch command based on class
            launch_command = self.launch_command_generator.guess_launch_command(window_data)
            window_data["launch_command"] = launch_command
            self.debug_print(f"Generated launch command: {launch_command}")

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