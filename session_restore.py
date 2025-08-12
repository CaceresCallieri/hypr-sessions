"""
Session restore functionality
"""

import json
import shlex
import subprocess
import time
from typing import Dict, List, Any

from config import get_config, SessionConfig
from session_save.browser_handler import BrowserHandler
from session_save.hyprctl_client import HyprctlClient
from session_types import SessionData, WindowInfo, GroupMapping
from utils import Utils


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

    def detect_swallowing_relationships(self, windows: List[WindowInfo]) -> Dict[str, Dict[str, WindowInfo]]:
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
                    self.debug_print(f"Found swallowing relationship: {window.get('class')} ({window_address[:10]}...) swallowing {swallowed_window.get('class')} ({swallowing_address[:10]}...)")
                    
                    swallowing_relationships[window_address] = {
                        'swallowing': window,
                        'swallowed': swallowed_window
                    }
                else:
                    self.debug_print(f"Warning: Window {window_address[:10]}... claims to swallow {swallowing_address[:10]}... but swallowed window not found in session")
        
        self.debug_print(f"Detected {len(swallowing_relationships)} swallowing relationships from session data")
        return swallowing_relationships

    def create_swallowing_command(self, swallowing_window: WindowInfo, swallowed_window: WindowInfo) -> str:
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
            self.debug_print(f"Unsupported terminal class: {terminal_class}, falling back to separate launches")
            return None
        
        # Extract GUI command from the launch_command
        # This might be something like "neovide -- -S /path/to/session.vim"
        gui_executable_and_args = gui_command
        
        # For Neovide specifically, we might want to remove certain arguments that don't make sense
        # in the terminal launch context, but for now let's use the full command
        
        # Build the combined command with shell persistence
        if terminal_working_dir:
            combined_command = f"ghostty --working-directory={shlex.quote(terminal_working_dir)} -e sh -c {shlex.quote(f'{gui_executable_and_args}; exec $SHELL')}"
        else:
            combined_command = f"ghostty -e sh -c {shlex.quote(f'{gui_executable_and_args}; exec $SHELL')}"
        
        self.debug_print(f"Created combined swallowing command: {combined_command}")
        return combined_command

    def get_swallowing_delay(self) -> float:
        """Get the delay to use after launching swallowing commands"""
        # Swallowing commands might take longer to complete, so use a longer delay
        return self.config.delay_between_instructions * 2.0

    def restore_session(self, session_name: str) -> bool:
        """Restore a saved session with group support"""
        self.debug_print(f"Starting restoration of session: {session_name}")
        session_file = self.config.get_session_file_path(session_name)
        self.debug_print(f"Session file path: {session_file}")

        if not session_file.exists():
            self.debug_print(f"Session file does not exist: {session_file}")
            print(f"Session file not found: {session_file}")
            return False

        try:
            with open(session_file, "r") as f:
                session_data = json.load(f)
            self.debug_print(f"Successfully loaded session data")
        except Exception as e:
            self.debug_print(f"Error loading session data: {e}")
            print(f"Error loading session: {e}")
            return False

        print(f"Restoring session: {session_name}")
        print(f"Timestamp: {session_data.get('timestamp')}")

        windows = session_data.get("windows", [])
        groups = session_data.get("groups", {})
        self.debug_print(
            f"Session contains {len(windows)} windows and {len(groups)} groups"
        )

        # Detect swallowing relationships
        swallowing_relationships = self.detect_swallowing_relationships(windows)
        if swallowing_relationships:
            print(f"Found {len(swallowing_relationships)} swallowing relationships to restore")

        if groups:
            print(f"Found {len(groups)} groups to restore")

        # Step 1: Launch applications and create groups during launch
        if groups:
            print("Launching applications with groups...")
            self.debug_print(f"Using grouped launch method")
            self.launch_with_groups(session_data.get("windows", []), groups, swallowing_relationships)
        else:
            print("Launching applications...")
            self.debug_print(f"Using simple launch method (no groups)")
            self.launch_windows_simple(session_data.get("windows", []), swallowing_relationships)

        self.debug_print(f"Session restoration completed")
        print(f"Restored {len(session_data.get('windows', []))} applications")
        return True

    def launch_windows_simple(self, windows: List[WindowInfo], swallowing_relationships: Dict[str, Dict[str, WindowInfo]]) -> None:
        """Launch windows without groups, handling swallowing relationships"""
        self.debug_print(f"Starting simple launch for {len(windows)} windows")
        
        # Keep track of which windows we've already launched via swallowing
        launched_addresses = set()
        
        # Build a set of addresses that are being swallowed (should not be launched separately)
        swallowed_addresses = set()
        for relationship in swallowing_relationships.values():
            swallowed_addresses.add(relationship['swallowed'].get("address", ""))
        
        self.debug_print(f"Found {len(swallowed_addresses)} windows that are swallowed and should not be launched separately")
        
        for window in windows:
            window_address = window.get("address", "")
            
            # Skip if this window was already launched as part of a swallowing relationship
            if window_address in launched_addresses:
                self.debug_print(f"Skipping {window.get('class')} - already launched via swallowing")
                continue
            
            # Skip if this window is being swallowed by another window
            if window_address in swallowed_addresses:
                self.debug_print(f"Skipping {window.get('class')} - will be launched as part of swallowing relationship")
                continue
            
            # Check if this window is swallowing another window
            if window_address in swallowing_relationships:
                # This window is swallowing another - create combined command
                relationship = swallowing_relationships[window_address]
                swallowing_window = relationship['swallowing']
                swallowed_window = relationship['swallowed']
                
                combined_command = self.create_swallowing_command(swallowing_window, swallowed_window)
                if combined_command:
                    print(f"Launching swallowing pair: {swallowing_window.get('class')} + {swallowed_window.get('class')}")
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
                        self.debug_print(f"Error launching swallowing command '{combined_command}': {e}")
                        print(f"Error launching swallowing pair: {e}")
                        # Fall back to separate launches
                        self._launch_single_window(swallowing_window)
                        self._launch_single_window(swallowed_window)
                        launched_addresses.add(swallowing_window.get("address", ""))
                        launched_addresses.add(swallowed_window.get("address", ""))
                else:
                    # Fall back to separate launches
                    self.debug_print(f"Could not create swallowing command, launching separately")
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

        print(f"Launching: {command}")
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
            print(f"Error launching {command}: {e}")

    def launch_with_groups(self, windows: List[WindowInfo], groups: GroupMapping, swallowing_relationships: Dict[str, Dict[str, WindowInfo]]) -> None:
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

        # Launch grouped windows
        self.debug_print(f"Launching {len(windows_by_group)} groups")
        for group_id, group_windows in windows_by_group.items():
            print(
                f"Launching group {group_id[:8]}... with {len(group_windows)} windows"
            )
            self.debug_print(
                f"Processing group {group_id} with {len(group_windows)} windows"
            )

            if len(group_windows) < 2:
                # Single window, launch normally
                self.debug_print(
                    f"Group {group_id} has only 1 window, launching normally"
                )
                window = group_windows[0]
                command = window.get("launch_command", "")
                if command:
                    print(f"  Launching: {command}")
                    self.debug_print(f"Launching single window: {command}")
                    try:
                        subprocess.Popen(
                            shlex.split(command),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        time.sleep(self.config.delay_between_instructions)
                    except Exception as e:
                        self.debug_print(
                            f"Error launching single window '{command}': {e}"
                        )
                        print(f"  Error launching {command}: {e}")
                continue

            # Launch first window of the group
            first_window = group_windows[0]
            command = first_window.get("launch_command", "")
            if not command:
                continue

            print(f"  Launching group leader: {command}")
            try:
                subprocess.Popen(
                    command.split(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(self.config.delay_between_instructions)  # Wait for window to appear

                # Make it a group
                cmd = ["hyprctl", "dispatch", "togglegroup"]
                subprocess.run(cmd, check=True, capture_output=True)
                time.sleep(self.config.delay_between_instructions)

                # Launch remaining windows (they will auto-join the group)
                for window in group_windows[1:]:
                    command = window.get("launch_command", "")
                    if not command:
                        continue

                    print(f"  Launching group member: {command}")
                    subprocess.Popen(
                        shlex.split(command),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    time.sleep(self.config.delay_between_instructions)

                # After opening all clients in the group, lock the group to prevent other windows from joining
                cmd = ["hyprctl", "dispatch", "lockactivegroup", "lock"]
                subprocess.run(cmd, check=True, capture_output=True)
                print(
                    f"  Successfully created and locked group with {len(group_windows)} windows"
                )

            except subprocess.CalledProcessError as e:
                print(f"  Error creating group: {e}")
            except Exception as e:
                print(f"  Unexpected error during group creation: {e}")
