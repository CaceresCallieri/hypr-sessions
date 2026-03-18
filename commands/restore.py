"""
Session restore functionality
"""

import json
import os
import shlex
import signal
import subprocess
import time
from typing import Any, Dict, List, Optional

from .shared.config import SessionConfig, get_config
from .shared.debug import CommandDebugger
from .shared.operation_result import OperationResult
from .save.browser_handler import BrowserHandler
from .save.hyprctl_client import HyprctlClient
from .shared.session_types import GroupMapping, SessionData, WindowInfo
from .shared.utils import Utils
from .shared.validation import SessionValidator, SessionNotFoundError, SessionValidationError


class SessionRestore(Utils):
    def __init__(self, debug: bool = False) -> None:
        super().__init__()
        self.debugger = CommandDebugger("SessionRestore", debug)
        self.config: SessionConfig = get_config()
        self.browser_handler: BrowserHandler = BrowserHandler(debug=debug)
        self.hyprctl_client: HyprctlClient = HyprctlClient()
    
    def _launch_window_command_with_timeout(self, command: str, timeout: int = 30) -> bool:
        """Launch window command with timeout protection and startup validation"""
        self.debugger.debug(f"Launching with timeout ({timeout}s): {command}")

        # Launch process in new process group for clean termination
        try:
            process = subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
        except FileNotFoundError as e:
            self.debugger.debug(f"Command not found: {command}, error: {e}")
            return False
        except PermissionError as e:
            self.debugger.debug(f"Permission denied launching command: {command}, error: {e}")
            return False
        except OSError as e:
            self.debugger.debug(f"OS error launching command: {command}, error: {e}")
            return False

        # Wait for process to start (brief check for immediate failures)
        try:
            return_code = process.wait(timeout=5)  # Quick startup validation
            if return_code != 0:
                # Process failed to start properly
                stderr = process.stderr.read().decode() if process.stderr else ""
                self.debugger.debug(f"Command failed to start: {command}, error: {stderr}")
                return False
        except subprocess.TimeoutExpired:
            # Process is still running after 5 seconds - this is expected for GUI applications
            # The process started successfully and is running
            self.debugger.debug(f"Process started successfully and is running: {command}")
            return True
        except Exception as e:
            self.debugger.debug(f"Unexpected error launching command: {command}, error: {e}")
            return False

        return True

    def detect_swallowing_relationships(
        self, windows: List[WindowInfo]
    ) -> Dict[str, Dict[str, WindowInfo]]:
        """
        Detect swallowing relationships from session data using the saved swallowing property.
        Returns dict mapping swallowing_address -> {'swallowing': window, 'swallowed': window}
        """
        self.debugger.debug("Detecting swallowing relationships from saved session data")

        swallowing_relationships = {}
        windows_by_address = {w.get("address"): w for w in windows if w.get("address")}

        for window in windows:
            swallowing_address = window.get("swallowing", "")
            window_address = window.get("address", "")

            # Check if this window is swallowing another (swallowing != "0x0")
            if swallowing_address and swallowing_address != "0x0":
                swallowed_window = windows_by_address.get(swallowing_address)

                if swallowed_window:
                    self.debugger.debug(
                        f"Found swallowing relationship: {window.get('class')} ({window_address[:10]}...) swallowing {swallowed_window.get('class')} ({swallowing_address[:10]}...)"
                    )

                    swallowing_relationships[window_address] = {
                        "swallowing": window,
                        "swallowed": swallowed_window,
                    }
                else:
                    self.debugger.debug(
                        f"Warning: Window {window_address[:10]}... claims to swallow {swallowing_address[:10]}... but swallowed window not found in session"
                    )

        self.debugger.debug(
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

        self.debugger.debug(f"Creating swallowing command:")
        self.debugger.debug(f"  Terminal: {terminal_class} -> {terminal_command}")
        self.debugger.debug(f"  GUI App: {gui_class} -> {gui_command}")

        # For now, only handle ghostty terminals
        if terminal_class != "com.mitchellh.ghostty":
            self.debugger.debug(
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

        self.debugger.debug(f"Created combined swallowing command: {combined_command}")
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
            
            self.debugger.debug(f"Starting restoration of session: {session_name}")
            
            # Check if session exists BEFORE calling get_active_session_file_path (which creates directory)
            session_dir = self.config.get_active_sessions_dir() / session_name
            SessionValidator.validate_session_exists(session_dir, session_name)
            result.add_success("Session exists and is accessible")
            
            session_file = self.config.get_active_session_file_path(session_name)
            self.debugger.debug(f"Session file path: {session_file}")
            
        except (SessionValidationError, SessionNotFoundError) as e:
            self.debugger.debug(f"Validation error: {e}")
            result.add_error(str(e))
            return result

        try:
            with open(session_file, "r") as f:
                session_data = json.load(f)
            self.debugger.debug(f"Successfully loaded session data")
            result.add_success("Session data loaded successfully")
        except (json.JSONDecodeError, FileNotFoundError, PermissionError, OSError) as e:
            self.debugger.debug(f"Error loading session data: {e}")
            result.add_json_error(e, f"load session '{session_name}'", str(session_file))
            return result
        except (OSError, PermissionError) as e:
            self.debugger.debug(f"File system error loading session data: {e}")
            result.add_error(f"File system error: Cannot load session '{session_name}': {e}")
            return result
        except Exception as e:
            self.debugger.debug(f"Unexpected error loading session data: {e}")
            result.add_error(f"Unexpected error: Failed to load session '{session_name}'. {str(e)}")
            return result

        self.debugger.debug(f"Restoring session: {session_name}")
        self.debugger.debug(f"Timestamp: {session_data.get('timestamp')}")

        windows = session_data.get("windows", [])
        groups = session_data.get("groups", {})
        self.debugger.debug(
            f"Session contains {len(windows)} windows and {len(groups)} groups"
        )
        result.add_success(f"Found {len(windows)} windows and {len(groups)} groups to restore")

        # Detect swallowing relationships
        swallowing_relationships = self.detect_swallowing_relationships(windows)
        if swallowing_relationships:
            self.debugger.debug(
                f"Found {len(swallowing_relationships)} swallowing relationships to restore"
            )
            result.add_success(f"Detected {len(swallowing_relationships)} swallowing relationships")

        if groups:
            self.debugger.debug(f"Found {len(groups)} groups to restore")

        # Step 1: Launch applications and create groups during launch
        launch_result = None
        try:
            if groups:
                self.debugger.debug("Launching applications with groups...")
                self.debugger.debug(f"Using grouped launch method")
                launch_result = self.launch_with_groups(
                    session_data.get("windows", []), groups, swallowing_relationships
                )
            else:
                self.debugger.debug("Launching applications...")
                self.debugger.debug(f"Using simple launch method (no groups)")
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
                
        except (OSError, PermissionError) as e:
            self.debugger.debug(f"System access error during launch: {e}")
            result.add_error(f"System access error: Cannot launch applications: {e}")
            return result
        except subprocess.TimeoutExpired as e:
            self.debugger.debug(f"Timeout during launch: {e}")
            result.add_error(f"Application launch timeout: {e}")
            return result
        except Exception as e:
            self.debugger.debug(f"Unexpected error during launch: {e}")
            result.add_error(f"Unexpected error launching applications: {e}")
            return result

        self.debugger.debug(f"Session restoration completed")
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
        self.debugger.debug(f"Starting simple launch for {len(windows)} windows")

        # Keep track of which windows we've already launched via swallowing
        launched_addresses = set()

        # Build a set of addresses that are being swallowed (should not be launched separately)
        swallowed_addresses = set()
        for relationship in swallowing_relationships.values():
            swallowed_addresses.add(relationship["swallowed"].get("address", ""))

        self.debugger.debug(
            f"Found {len(swallowed_addresses)} windows that are swallowed and should not be launched separately"
        )

        for window in windows:
            window_address = window.get("address", "")

            # Skip if this window was already launched as part of a swallowing relationship
            if window_address in launched_addresses:
                self.debugger.debug(
                    f"Skipping {window.get('class')} - already launched via swallowing"
                )
                continue

            # Skip if this window is being swallowed by another window
            if window_address in swallowed_addresses:
                self.debugger.debug(
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
                    self.debugger.debug(
                        f"Launching swallowing pair: {swallowing_window.get('class')} + {swallowed_window.get('class')}"
                    )
                    self.debugger.debug(f"Combined swallowing command: {combined_command}")

                    # Use timeout-protected launch
                    launch_success = self._launch_window_command_with_timeout(combined_command, timeout=30)
                    
                    if launch_success:
                        time.sleep(self.get_swallowing_delay())
                        # Mark both windows as launched
                        launched_addresses.add(swallowing_window.get("address", ""))
                        launched_addresses.add(swallowed_window.get("address", ""))
                    else:
                        self.debugger.debug(f"Swallowing command launch failed or timed out: {combined_command}")
                        # Fall back to separate launches
                        self._launch_single_window(swallowing_window)
                        self._launch_single_window(swallowed_window)
                        launched_addresses.add(swallowing_window.get("address", ""))
                        launched_addresses.add(swallowed_window.get("address", ""))
                else:
                    # Fall back to separate launches
                    self.debugger.debug(
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
            self.debugger.debug(f"Skipping window with no launch command")
            return

        self.debugger.debug(f"Launching: {command}")
        self.debugger.debug(f"Executing command: {command}")
        
        # Use timeout-protected launch
        launch_success = self._launch_window_command_with_timeout(command, timeout=30)
        
        if launch_success:
            time.sleep(self.config.delay_between_instructions)
        else:
            self.debugger.debug(f"Single window launch failed or timed out: {command}")

    def launch_group_with_swallowing(self, group_windows: List[WindowInfo], swallowing_relationships: Dict[str, Dict[str, WindowInfo]]) -> None:
        """Launch a group of windows with swallowing relationship support"""
        self.debugger.debug(f"Starting group launch with swallowing support for {len(group_windows)} windows")
        
        if len(group_windows) < 2:
            # Single window group, use simple launch logic
            self.debugger.debug("Single window group, using simple launch logic")
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
                self.debugger.debug(f"Excluding swallowed window {window.get('class')} from group membership")
        
        if len(effective_group_windows) < 2:
            # After filtering swallowed windows, we don't have enough for a group
            self.debugger.debug("After filtering swallowed windows, not enough windows for a group")
            self.launch_windows_simple(group_windows, swallowing_relationships)
            return
        
        self.debugger.debug(f"Launching group with {len(effective_group_windows)} effective windows (filtered from {len(group_windows)})")
        
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
                self.debugger.debug(f"Launching group leader (swallowing): {swallowing_window.get('class')} + {swallowed_window.get('class')}")
                self.debugger.debug(f"Group leader swallowing command: {combined_command}")
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
            self.debugger.debug("No command for group leader, skipping group creation")
            return
        
        # Launch group leader
        self.debugger.debug(f"Launching group leader: {command}")
        
        # Use timeout-protected launch for group leader
        launch_success = self._launch_window_command_with_timeout(command, timeout=30)
        
        if not launch_success:
            self.debugger.debug(f"Group leader launch failed or timed out: {command}")
            return
        
        # Use appropriate delay
        if use_swallowing_delay:
            time.sleep(self.get_swallowing_delay())
        else:
            time.sleep(self.config.delay_between_instructions)

        # Make it a group
        try:
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
                        self.debugger.debug(f"Launching group member (swallowing): {swallowing_window.get('class')} + {swallowed_window.get('class')}")
                        self.debugger.debug(f"Group member swallowing command: {combined_command}")
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
                    self.debugger.debug(f"No command for group member, skipping")
                    continue

                self.debugger.debug(f"Launching group member: {member_command}")
                
                # Use timeout-protected launch for group member
                member_launch_success = self._launch_window_command_with_timeout(member_command, timeout=30)
                
                if not member_launch_success:
                    self.debugger.debug(f"Group member launch failed or timed out: {member_command}")
                    continue  # Skip this member but continue with other group members
                
                # Use appropriate delay
                if use_member_swallowing_delay:
                    time.sleep(self.get_swallowing_delay())
                else:
                    time.sleep(self.config.delay_between_instructions)

            # Lock the group to prevent other windows from joining
            cmd = ["hyprctl", "dispatch", "lockactivegroup", "lock"]
            subprocess.run(cmd, check=True, capture_output=True)
            self.debugger.debug(f"Successfully created and locked group with {len(effective_group_windows)} windows")

        except (subprocess.CalledProcessError, FileNotFoundError, PermissionError) as e:
            self.debugger.debug(f"Process error creating group: {e}")
            # Note: We don't add errors to result here as this is a non-critical operation
            # Group creation failure doesn't prevent successful session restoration
        except subprocess.TimeoutExpired as e:
            self.debugger.debug(f"Timeout during group creation: {e}")
            # Note: We don't add errors to result here as this is a non-critical operation
        except Exception as e:
            self.debugger.debug(f"Unexpected error during group creation: {e}")
            # Note: We don't add errors to result here as this is a non-critical operation

    def launch_with_groups(
        self,
        windows: List[WindowInfo],
        groups: GroupMapping,
        swallowing_relationships: Dict[str, Dict[str, WindowInfo]],
    ) -> None:
        """Launch applications and create groups during the process"""
        self.debugger.debug(f"Starting grouped launch with {len(windows)} windows")
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

        self.debugger.debug(
            f"Organized into {len(windows_by_group)} groups and {len(ungrouped_windows)} ungrouped windows"
        )

        # Launch ungrouped windows first (with swallowing support)
        self.debugger.debug(f"Launching {len(ungrouped_windows)} ungrouped windows")
        if ungrouped_windows:
            self.launch_windows_simple(ungrouped_windows, swallowing_relationships)

        # Launch grouped windows with swallowing support
        self.debugger.debug(f"Launching {len(windows_by_group)} groups")
        for group_id, group_windows in windows_by_group.items():
            self.debugger.debug(
                f"Launching group {group_id[:8]}... with {len(group_windows)} windows"
            )
            self.debugger.debug(
                f"Processing group {group_id} with {len(group_windows)} windows"
            )
            
            # Launch this group with swallowing support
            self.launch_group_with_swallowing(group_windows, swallowing_relationships)
