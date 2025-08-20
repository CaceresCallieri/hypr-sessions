"""
Main session saving orchestration
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from utils import Utils
from config import get_config
from session_types import SessionData, WindowInfo
from validation import SessionValidator, SessionAlreadyExistsError, SessionValidationError
from operation_result import OperationResult
from .hyprctl_client import HyprctlClient
from .launch_commands import LaunchCommandGenerator
from .terminal_handler import TerminalHandler
from .neovide_handler import NeovideHandler
from .browser_handler import BrowserHandler


class SessionSaver(Utils):
    def __init__(self, debug: bool = False) -> None:
        super().__init__()
        self.debug: bool = debug
        self.config = get_config()
        self.current_session_name: Optional[str] = None
        self.hyprctl_client: HyprctlClient = HyprctlClient(debug=debug)
        self.launch_command_generator: LaunchCommandGenerator = LaunchCommandGenerator(debug=debug)
        self.terminal_handler: TerminalHandler = TerminalHandler()
        self.neovide_handler: NeovideHandler = NeovideHandler(debug=debug)
        self.browser_handler: BrowserHandler = BrowserHandler(debug=debug)
    
    def debug_print(self, message: str) -> None:
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG SessionSaver] {message}")

    def save_session(self, session_name: str) -> OperationResult:
        """Save current workspace state including groups"""
        result = OperationResult(operation_name=f"Save session '{session_name}'")
        
        try:
            # Validate session name (already done in CLI, but adding here for direct usage)
            SessionValidator.validate_session_name(session_name)
            result.add_success("Session name validated")
            
            # Validate sessions directory is writable
            SessionValidator.validate_directory_writable(self.config.sessions_dir)
            result.add_success("Sessions directory accessible")
            
            # Check if session already exists
            session_path = self.config.get_session_directory(session_name)
            if session_path.exists():
                session_file = session_path / "session.json"
                if session_file.exists():
                    raise SessionAlreadyExistsError(
                        f"Session '{session_name}' already exists. "
                        f"Delete it first or use a different name."
                    )
            
            # Store session name for use in other methods
            self.current_session_name = session_name
            self.debug_print(f"Starting session save for: {session_name}")
            
        except (SessionValidationError, SessionAlreadyExistsError) as e:
            self.debug_print(f"Validation error: {e}")
            result.add_error(str(e))
            return result

        # Get current workspace clients only (never loads other workspace data)
        try:
            # Get current workspace ID first
            current_workspace_data = self.hyprctl_client.get_hyprctl_data("activeworkspace")
            current_workspace_id = (
                current_workspace_data.get("id") if current_workspace_data else None
            )
            
            if current_workspace_id is None:
                result.add_error("Could not determine current workspace")
                return result
                
            self.debug_print(f"Current workspace ID: {current_workspace_id}")

            # Get clients filtered to current workspace only using jq
            workspace_clients = self.hyprctl_client.get_workspace_clients(current_workspace_id)
            if workspace_clients is None:
                result.add_error("Failed to get workspace clients")
                return result

            self.debug_print(f"Found {len(workspace_clients)} clients in current workspace")

            if not workspace_clients:
                result.add_error(f"No windows found in current workspace ({current_workspace_id})")
                return result
            
            result.add_success(f"Found {len(workspace_clients)} windows in current workspace")
            
        except Exception as e:
            result.add_error(f"Failed to get window information: {e}")
            return result

        # Process groups - build group mapping
        groups: Dict[str, List[str]] = {}  # group_id -> list of window addresses
        address_to_group: Dict[str, str] = {}  # window address -> group_id

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
        
        captured_windows = 0
        failed_windows = 0

        for client in workspace_clients:
            address = client.get("address", "")
            client_class = client.get("class", "unknown")
            client_pid = client.get("pid")

            self.debug_print(f"Processing client: {client_class} (PID: {client_pid})")
            
            try:
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
                    "swallowing": client.get("swallowing", "0x0"),  # Capture swallowing property
                }

                # For terminal applications, capture working directory and running program
                if self.terminal_handler.is_terminal_app(window_data["class"]):
                    pid = window_data.get("pid")
                    if pid:
                        try:
                            working_dir = self.terminal_handler.get_working_directory(pid)
                            if working_dir:
                                window_data["working_directory"] = working_dir
                                result.add_success(f"Captured working directory for {client_class}")
                            else:
                                result.add_warning(f"Could not capture working directory for {client_class} (PID: {pid})")
                        except Exception as e:
                            result.add_warning(f"Failed to get working directory for {client_class}: {e}")
                        
                        # Detect running program in the terminal
                        try:
                            self.debug_print(f"Detecting running program for terminal PID {pid}")
                            running_program = self.terminal_handler.get_running_program(pid, debug=self.debug)
                            if running_program:
                                window_data["running_program"] = running_program
                                self.debug_print(f"Running program details: {running_program}")
                                result.add_success(f"Captured running program '{running_program['name']}' for {client_class}")
                            else:
                                self.debug_print("No running program detected (likely just shell)")
                        except Exception as e:
                            result.add_warning(f"Failed to detect running program for {client_class}: {e}")

                # For Neovide windows, capture session information
                if self.neovide_handler.is_neovide_window(window_data):
                    pid = window_data.get("pid")
                    self.debug_print(f"Detected Neovide window with class '{client_class}' and PID {pid}")
                    try:
                        neovide_session_info = self.neovide_handler.get_neovide_session_info(pid)
                        self.debug_print(f"Neovide session info: {neovide_session_info}")
                        if neovide_session_info:
                            window_data["neovide_session"] = neovide_session_info
                            # Try to create/capture session file in session directory
                            session_dir = str(self.config.get_session_directory(self.current_session_name))
                            session_file = self.neovide_handler.create_session_file(pid, session_dir)
                            self.debug_print(f"Created session file: {session_file}")
                            if session_file:
                                window_data["neovide_session"]["session_file"] = session_file
                                result.add_success(f"Captured Neovide session file for {client_class}")
                            else:
                                result.add_warning(f"Could not capture Neovide session for {client_class}, using working directory fallback")
                        else:
                            self.debug_print(f"Failed to get Neovide session info for PID {pid}")
                            result.add_warning(f"Could not get Neovide session info for {client_class}")
                    except Exception as e:
                        result.add_warning(f"Failed to capture Neovide session for {client_class}: {e}")

                # For browser windows, capture tab information
                if self.browser_handler.is_browser_window(window_data):
                    pid = window_data.get("pid")
                    browser_type = self.browser_handler.get_browser_type(window_data)
                    self.debug_print(f"Detected browser window with class '{client_class}' and PID {pid}")
                    try:
                        browser_session_info = self.browser_handler.get_enhanced_browser_session_info(window_data, session_name)
                        self.debug_print(f"Browser session info: {browser_session_info}")
                        if browser_session_info:
                            window_data["browser_session"] = browser_session_info
                            capture_method = browser_session_info.get("capture_method", "basic")
                            result.add_success(f"Captured {browser_type} browser session using {capture_method} method")
                        else:
                            self.debug_print(f"Failed to get browser session info for PID {pid}")
                            result.add_warning(f"Could not capture browser session for {browser_type}")
                    except Exception as e:
                        result.add_warning(f"Failed to capture browser session for {browser_type}: {e}")

                # Try to determine launch command based on class
                try:
                    launch_command = self.launch_command_generator.guess_launch_command(window_data)
                    window_data["launch_command"] = launch_command
                    self.debug_print(f"Generated launch command: {launch_command}")
                    result.add_success(f"Generated launch command for {client_class}")
                except Exception as e:
                    result.add_warning(f"Failed to generate launch command for {client_class}: {e}")
                    window_data["launch_command"] = client_class  # Fallback to class name

                session_data["windows"].append(window_data)
                captured_windows += 1
                
            except Exception as e:
                self.debug_print(f"Failed to process window {client_class} (PID: {client_pid}): {e}")
                result.add_error(f"Failed to process window {client_class}: {e}")
                failed_windows += 1

        # Add summary information
        result.add_success(f"Processed {captured_windows} windows successfully")
        if failed_windows > 0:
            result.add_warning(f"Failed to process {failed_windows} windows")

        # Debug: Print group information
        if groups:
            self.debug_print(f"Found {len(groups)} groups:")
            for group_id, addresses in groups.items():
                self.debug_print(f"  Group {group_id[:8]}... has {len(addresses)} windows")
            result.add_success(f"Detected {len(groups)} window groups")

        # Save session to file in new folder structure
        session_file = self.config.get_session_file_path(session_name)
        try:
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)
            result.add_success(f"Session saved to {session_file}")
            result.data = {
                "session_file": str(session_file),
                "windows_saved": len(session_data['windows']),
                "groups_detected": len(groups),
                "captured_windows": captured_windows,
                "failed_windows": failed_windows
            }
            return result
        except Exception as e:
            self.debug_print(f"Error saving session file: {e}")
            result.add_error(f"Failed to save session file: {e}")
            return result