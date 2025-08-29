"""
Session restore functionality
"""

import json
import shlex
import subprocess
import time
from typing import Any, Dict, List

from .shared.config import SessionConfig, get_config
from .shared.operation_result import OperationResult
from .save.browser_handler import BrowserHandler
from .save.hyprctl_client import HyprctlClient
from .shared.session_types import GroupMapping, SessionData, WindowInfo
from .shared.utils import Utils
from .shared.validation import SessionValidator, SessionNotFoundError, SessionValidationError


class SessionRestore(Utils):
    def __init__(self, debug: bool = False) -> None:
        super().__init__()
        self.debug: bool = debug
        self.config: SessionConfig = get_config()
        self.browser_handler: BrowserHandler = BrowserHandler(debug=debug)
        self.hyprctl_client: HyprctlClient = HyprctlClient()

    def debug_print(self, message: str) -> None:
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG SessionRestore] {message}")

    def detect_swallowing_relationships(
        self, windows: List[WindowInfo]
    ) -> Dict[str, Dict[str, WindowInfo]]:
        """
        Detect swallowing relationships from session data using the saved swallowing property.
        Returns dict mapping swallowing_address -> {'swallowing': window, 'swallowed': window}
        """
        self.debug_print("Detecting swallowing relationships from saved session data")

        swallowing_relationships = {}
        windows_by_address = {w.get("address"): w for w in windows if w.get("address")}

        for window in windows:
            swallowing_address = window.get("swallowing", "")
            window_address = window.get("address", "")

            # Check if this window is swallowing another (swallowing != "0x0")
            if swallowing_address and swallowing_address != "0x0":
                swallowed_window = windows_by_address.get(swallowing_address)

                if swallowed_window:
                    self.debug_print(
                        f"Found swallowing relationship: {window.get('class')} ({window_address[:10]}...) swallowing {swallowed_window.get('class')} ({swallowing_address[:10]}...)"
                    )

                    swallowing_relationships[window_address] = {
                        "swallowing": window,
                        "swallowed": swallowed_window,
                    }
                else:
                    self.debug_print(
                        f"Warning: Window {window_address[:10]}... claims to swallow {swallowing_address[:10]}... but swallowed window not found in session"
                    )

        self.debug_print(
            f"Detected {len(swallowing_relationships)} swallowing relationships from session data"
        )
        return swallowing_relationships

    def create_swallowing_command(
        self, swallowing_window: WindowInfo, swallowed_window: WindowInfo
    ) -> str:
        """
        Create a combined launch command for swallowing behavior.
        Takes the terminal (swallowed) and GUI app (swallowing) and combines them.
        """
        # Get the terminal command (should be ghostty with working directory)
        terminal_command = swallowed_window.get("launch_command", "")
        terminal_class = swallowed_window.get("class", "")
        terminal_working_dir = swallowed_window.get("working_directory", "")

        # Get the GUI app command
        gui_command = swallowing_window.get("launch_command", "")
        gui_class = swallowing_window.get("class", "")

        self.debug_print(f"Creating swallowing command:")
        self.debug_print(f"  Terminal: {terminal_class} -> {terminal_command}")
        self.debug_print(f"  GUI App: {gui_class} -> {gui_command}")

        # For now, only handle ghostty terminals
        if terminal_class != "com.mitchellh.ghostty":
            self.debug_print(
                f"Unsupported terminal class: {terminal_class}, falling back to separate launches"
            )
            return None

        # Extract GUI command from the launch_command
        # This might be something like "neovide -- -S /path/to/session.vim"
        gui_executable_and_args = gui_command

        # Build the combined command with shell persistence
        # Properly escape the GUI command to prevent shell interpretation issues
        escaped_gui_command = shlex.quote(gui_executable_and_args)
        shell_command = f"{escaped_gui_command}; exec $SHELL"
        
        if terminal_working_dir:
            combined_command = f"ghostty --working-directory={shlex.quote(terminal_working_dir)} -e sh -c {shlex.quote(shell_command)}"
        else:
            combined_command = f"ghostty -e sh -c {shlex.quote(shell_command)}"

        self.debug_print(f"Created combined swallowing command: {combined_command}")
        return combined_command

    def get_swallowing_delay(self) -> float:
        """Get the delay to use after launching swallowing commands"""
        # Swallowing commands might take longer to complete, so use a longer delay
        return self.config.delay_between_instructions * 2.0

    def restore_session(self, session_name: str) -> OperationResult:
        """Restore a saved session with group support"""
        result = OperationResult(operation_name=f"Restore session '{session_name}'")
        
        try:
            # Validate session name (already done in CLI, but adding here for direct usage)
            SessionValidator.validate_session_name(session_name)
            result.add_success("Session name validated")
            
            self.debug_print(f"Starting restoration of session: {session_name}")
            
            # Check if session exists BEFORE calling get_active_session_file_path (which creates directory)
            session_dir = self.config.get_active_sessions_dir() / session_name
            SessionValidator.validate_session_exists(session_dir, session_name)
            result.add_success("Session exists and is accessible")
            
            session_file = self.config.get_active_session_file_path(session_name)
            self.debug_print(f"Session file path: {session_file}")
            
        except (SessionValidationError, SessionNotFoundError) as e:
            self.debug_print(f"Validation error: {e}")
            result.add_error(str(e))
            return result

        try:
            with open(session_file, "r") as f:
                session_data = json.load(f)
            self.debug_print(f"Successfully loaded session data")
            result.add_success("Session data loaded successfully")
        except Exception as e:
            self.debug_print(f"Error loading session data: {e}")
            result.add_error(f"Failed to load session data: {e}")
            return result

        self.debug_print(f"Restoring session: {session_name}")
        self.debug_print(f"Timestamp: {session_data.get('timestamp')}")

        windows = session_data.get("windows", [])
        groups = session_data.get("groups", {})
        self.debug_print(
            f"Session contains {len(windows)} windows and {len(groups)} groups"
        )
        result.add_success(f"Found {len(windows)} windows and {len(groups)} groups to restore")

        # Detect swallowing relationships
        swallowing_relationships = self.detect_swallowing_relationships(windows)
        if swallowing_relationships:
            self.debug_print(
                f"Found {len(swallowing_relationships)} swallowing relationships to restore"
            )
            result.add_success(f"Detected {len(swallowing_relationships)} swallowing relationships")

        if groups:
            self.debug_print(f"Found {len(groups)} groups to restore")

        # Step 1: Launch applications and create groups during launch
        launch_result = None
        try:
            if groups:
                self.debug_print("Launching applications with groups...")
                self.debug_print(f"Using grouped launch method")
                launch_result = self.launch_with_groups(
                    session_data.get("windows", []), groups, swallowing_relationships
                )
            else:
                self.debug_print("Launching applications...")
                self.debug_print(f"Using simple launch method (no groups)")
                launch_result = self.launch_windows_simple(
                    session_data.get("windows", []), swallowing_relationships
                )
            
            # Merge launch results
            if launch_result:
                result.messages.extend(launch_result.messages)
                if not launch_result.success:
                    result.success = False
            else:
                result.add_success("Applications launched successfully")
                
        except Exception as e:
            self.debug_print(f"Error during launch: {e}")
            result.add_error(f"Failed to launch applications: {e}")
            return result

        self.debug_print(f"Session restoration completed")
        result.add_success(f"Restored {len(windows)} applications")
        
        result.data = {
            "windows_restored": len(windows),
            "groups_restored": len(groups),
            "swallowing_relationships": len(swallowing_relationships),
            "session_file": str(session_file)
        }
        
        return result

    def launch_windows_simple(
        self,
        windows: List[WindowInfo],
        swallowing_relationships: Dict[str, Dict[str, WindowInfo]],
    ) -> None:
        """Launch windows without groups, handling swallowing relationships"""
        self.debug_print(f"Starting simple launch for {len(windows)} windows")

        # Keep track of which windows we've already launched via swallowing
        launched_addresses = set()

        # Build a set of addresses that are being swallowed (should not be launched separately)
        swallowed_addresses = set()
        for relationship in swallowing_relationships.values():
            swallowed_addresses.add(relationship["swallowed"].get("address", ""))

        self.debug_print(
            f"Found {len(swallowed_addresses)} windows that are swallowed and should not be launched separately"
        )

        for window in windows:
            window_address = window.get("address", "")

            # Skip if this window was already launched as part of a swallowing relationship
            if window_address in launched_addresses:
                self.debug_print(
                    f"Skipping {window.get('class')} - already launched via swallowing"
                )
                continue

            # Skip if this window is being swallowed by another window
            if window_address in swallowed_addresses:
                self.debug_print(
                    f"Skipping {window.get('class')} - will be launched as part of swallowing relationship"
                )
                continue

            # Check if this window is swallowing another window
            if window_address in swallowing_relationships:
                # This window is swallowing another - create combined command
                relationship = swallowing_relationships[window_address]
                swallowing_window = relationship["swallowing"]
                swallowed_window = relationship["swallowed"]

                combined_command = self.create_swallowing_command(
                    swallowing_window, swallowed_window
                )
                if combined_command:
                    self.debug_print(
                        f"Launching swallowing pair: {swallowing_window.get('class')} + {swallowed_window.get('class')}"
                    )
                    self.debug_print(f"Combined swallowing command: {combined_command}")

                    try:
                        subprocess.Popen(
                            shlex.split(combined_command),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        time.sleep(self.get_swallowing_delay())

                        # Mark both windows as launched
                        launched_addresses.add(swallowing_window.get("address", ""))
                        launched_addresses.add(swallowed_window.get("address", ""))

                    except Exception as e:
                        self.debug_print(
                            f"Error launching swallowing command '{combined_command}': {e}"
                        )
                        self.debug_print(f"Error launching swallowing pair: {e}")
                        # Fall back to separate launches
                        self._launch_single_window(swallowing_window)
                        self._launch_single_window(swallowed_window)
                        launched_addresses.add(swallowing_window.get("address", ""))
                        launched_addresses.add(swallowed_window.get("address", ""))
                else:
                    # Fall back to separate launches
                    self.debug_print(
                        f"Could not create swallowing command, launching separately"
                    )
                    self._launch_single_window(swallowing_window)
                    self._launch_single_window(swallowed_window)
                    launched_addresses.add(swallowing_window.get("address", ""))
                    launched_addresses.add(swallowed_window.get("address", ""))
            else:
                # Regular window launch
                self._launch_single_window(window)
                launched_addresses.add(window_address)

    def _launch_single_window(self, window: WindowInfo) -> None:
        """Launch a single window with its normal command"""
        command = window.get("launch_command", "")
        if not command:
            self.debug_print(f"Skipping window with no launch command")
            return

        self.debug_print(f"Launching: {command}")
        self.debug_print(f"Executing command: {command}")
        try:
            subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(self.config.delay_between_instructions)
        except Exception as e:
            self.debug_print(f"Error launching command '{command}': {e}")

    def launch_group_with_swallowing(self, group_windows: List[WindowInfo], swallowing_relationships: Dict[str, Dict[str, WindowInfo]]) -> None:
        """Launch a group of windows with swallowing relationship support"""
        self.debug_print(f"Starting group launch with swallowing support for {len(group_windows)} windows")
        
        if len(group_windows) < 2:
            # Single window group, use simple launch logic
            self.debug_print("Single window group, using simple launch logic")
            self.launch_windows_simple(group_windows, swallowing_relationships)
            return
        
        # Build sets for swallowing detection
        swallowed_addresses = set()
        for relationship in swallowing_relationships.values():
            swallowed_addresses.add(relationship["swallowed"].get("address", ""))
        
        # Filter out swallowed windows from group membership since they'll be launched as part of swallowing pairs
        effective_group_windows = []
        for window in group_windows:
            window_address = window.get("address", "")
            if window_address not in swallowed_addresses:
                effective_group_windows.append(window)
            else:
                self.debug_print(f"Excluding swallowed window {window.get('class')} from group membership")
        
        if len(effective_group_windows) < 2:
            # After filtering swallowed windows, we don't have enough for a group
            self.debug_print("After filtering swallowed windows, not enough windows for a group")
            self.launch_windows_simple(group_windows, swallowing_relationships)
            return
        
        self.debug_print(f"Launching group with {len(effective_group_windows)} effective windows (filtered from {len(group_windows)})")
        
        # Launch first effective window (group leader)
        first_window = effective_group_windows[0]
        first_window_address = first_window.get("address", "")
        
        # Check if the first window is involved in swallowing
        if first_window_address in swallowing_relationships:
            # Group leader is swallowing another window
            relationship = swallowing_relationships[first_window_address]
            swallowing_window = relationship["swallowing"]
            swallowed_window = relationship["swallowed"]
            
            combined_command = self.create_swallowing_command(swallowing_window, swallowed_window)
            if combined_command:
                self.debug_print(f"Launching group leader (swallowing): {swallowing_window.get('class')} + {swallowed_window.get('class')}")
                self.debug_print(f"Group leader swallowing command: {combined_command}")
                command = combined_command
                use_swallowing_delay = True
            else:
                # Fall back to separate launch
                command = first_window.get("launch_command", "")
                use_swallowing_delay = False
        else:
            # Regular group leader
            command = first_window.get("launch_command", "")
            use_swallowing_delay = False
        
        if not command:
            self.debug_print("No command for group leader, skipping group creation")
            return
        
        # Launch group leader
        self.debug_print(f"Launching group leader: {command}")
        try:
            subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            
            # Use appropriate delay
            if use_swallowing_delay:
                time.sleep(self.get_swallowing_delay())
            else:
                time.sleep(self.config.delay_between_instructions)

            # Make it a group
            cmd = ["hyprctl", "dispatch", "togglegroup"]
            subprocess.run(cmd, check=True, capture_output=True)
            time.sleep(self.config.delay_between_instructions)

            # Launch remaining effective windows (they will auto-join the group)
            for window in effective_group_windows[1:]:
                window_address = window.get("address", "")
                
                # Check if this window is involved in swallowing
                if window_address in swallowing_relationships:
                    # This window is swallowing another
                    relationship = swallowing_relationships[window_address]
                    swallowing_window = relationship["swallowing"]
                    swallowed_window = relationship["swallowed"]
                    
                    combined_command = self.create_swallowing_command(swallowing_window, swallowed_window)
                    if combined_command:
                        self.debug_print(f"Launching group member (swallowing): {swallowing_window.get('class')} + {swallowed_window.get('class')}")
                        self.debug_print(f"Group member swallowing command: {combined_command}")
                        member_command = combined_command
                        use_member_swallowing_delay = True
                    else:
                        # Fall back to separate launch
                        member_command = window.get("launch_command", "")
                        use_member_swallowing_delay = False
                else:
                    # Regular group member
                    member_command = window.get("launch_command", "")
                    use_member_swallowing_delay = False
                
                if not member_command:
                    self.debug_print(f"No command for group member, skipping")
                    continue

                self.debug_print(f"Launching group member: {member_command}")
                subprocess.Popen(
                    shlex.split(member_command),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                
                # Use appropriate delay
                if use_member_swallowing_delay:
                    time.sleep(self.get_swallowing_delay())
                else:
                    time.sleep(self.config.delay_between_instructions)

            # Lock the group to prevent other windows from joining
            cmd = ["hyprctl", "dispatch", "lockactivegroup", "lock"]
            subprocess.run(cmd, check=True, capture_output=True)
            self.debug_print(f"Successfully created and locked group with {len(effective_group_windows)} windows")

        except subprocess.CalledProcessError as e:
            self.debug_print(f"Error creating group: {e}")
            self.debug_print(f"Error creating group: {e}")
        except Exception as e:
            self.debug_print(f"Unexpected error during group creation: {e}")
            self.debug_print(f"Unexpected error during group creation: {e}")

    def launch_with_groups(
        self,
        windows: List[WindowInfo],
        groups: GroupMapping,
        swallowing_relationships: Dict[str, Dict[str, WindowInfo]],
    ) -> None:
        """Launch applications and create groups during the process"""
        self.debug_print(f"Starting grouped launch with {len(windows)} windows")
        # Group windows by group_id
        windows_by_group: Dict[str, List[WindowInfo]] = {}
        ungrouped_windows: List[WindowInfo] = []

        for window in windows:
            group_id = window.get("group_id")
            if group_id:
                if group_id not in windows_by_group:
                    windows_by_group[group_id] = []
                windows_by_group[group_id].append(window)
            else:
                ungrouped_windows.append(window)

        self.debug_print(
            f"Organized into {len(windows_by_group)} groups and {len(ungrouped_windows)} ungrouped windows"
        )

        # Launch ungrouped windows first (with swallowing support)
        self.debug_print(f"Launching {len(ungrouped_windows)} ungrouped windows")
        if ungrouped_windows:
            self.launch_windows_simple(ungrouped_windows, swallowing_relationships)

        # Launch grouped windows with swallowing support
        self.debug_print(f"Launching {len(windows_by_group)} groups")
        for group_id, group_windows in windows_by_group.items():
            self.debug_print(
                f"Launching group {group_id[:8]}... with {len(group_windows)} windows"
            )
            self.debug_print(
                f"Processing group {group_id} with {len(group_windows)} windows"
            )
            
            # Launch this group with swallowing support
            self.launch_group_with_swallowing(group_windows, swallowing_relationships)
