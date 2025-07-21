"""
Session restore functionality
"""

import json
import subprocess
import time

from utils import Utils
from session_save.browser_handler import BrowserHandler


class SessionRestore(Utils):
    DELAY_BETWEEN_INSTRUCTIONS = 0.4
    
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug
        self.browser_handler = BrowserHandler(debug=debug)
    
    def debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG SessionRestore] {message}")

    def restore_session(self, session_name):
        """Restore a saved session with group support"""
        self.debug_print(f"Starting restoration of session: {session_name}")
        session_file = self.sessions_dir / f"{session_name}.json"
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
        self.debug_print(f"Session contains {len(windows)} windows and {len(groups)} groups")

        if groups:
            print(f"Found {len(groups)} groups to restore")

        # Step 1: Launch applications and create groups during launch
        if groups:
            print("Launching applications with groups...")
            self.debug_print(f"Using grouped launch method")
            self.launch_with_groups(session_data.get("windows", []), groups)
        else:
            print("Launching applications...")
            self.debug_print(f"Using simple launch method (no groups)")
            for window in session_data.get("windows", []):
                command = window.get("launch_command", "")
                if not command:
                    self.debug_print(f"Skipping window with no launch command")
                    continue

                print(f"Launching: {command}")
                self.debug_print(f"Executing command: {command}")
                try:
                    subprocess.Popen(
                        command.split(),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    time.sleep(self.DELAY_BETWEEN_INSTRUCTIONS)
                except Exception as e:
                    self.debug_print(f"Error launching command '{command}': {e}")
                    print(f"Error launching {command}: {e}")

        self.debug_print(f"Session restoration completed")
        print(f"Restored {len(session_data.get('windows', []))} applications")
        return True

    def launch_with_groups(self, windows, groups):
        """Launch applications and create groups during the process"""
        self.debug_print(f"Starting grouped launch with {len(windows)} windows")
        # Group windows by group_id
        windows_by_group = {}
        ungrouped_windows = []

        for window in windows:
            group_id = window.get("group_id")
            if group_id:
                if group_id not in windows_by_group:
                    windows_by_group[group_id] = []
                windows_by_group[group_id].append(window)
            else:
                ungrouped_windows.append(window)

        self.debug_print(f"Organized into {len(windows_by_group)} groups and {len(ungrouped_windows)} ungrouped windows")

        # Launch ungrouped windows first
        self.debug_print(f"Launching {len(ungrouped_windows)} ungrouped windows")
        for window in ungrouped_windows:
            command = window.get("launch_command", "")
            if not command:
                continue

            print(f"Launching: {command}")
            try:
                subprocess.Popen(
                    command.split(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(self.DELAY_BETWEEN_INSTRUCTIONS)
            except Exception as e:
                print(f"Error launching {command}: {e}")

        # Launch grouped windows
        self.debug_print(f"Launching {len(windows_by_group)} groups")
        for group_id, group_windows in windows_by_group.items():
            print(
                f"Launching group {group_id[:8]}... with {len(group_windows)} windows"
            )
            self.debug_print(f"Processing group {group_id} with {len(group_windows)} windows")

            if len(group_windows) < 2:
                # Single window, launch normally
                self.debug_print(f"Group {group_id} has only 1 window, launching normally")
                window = group_windows[0]
                command = window.get("launch_command", "")
                if command:
                    print(f"  Launching: {command}")
                    self.debug_print(f"Launching single window: {command}")
                    try:
                        subprocess.Popen(
                            command.split(),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        time.sleep(self.DELAY_BETWEEN_INSTRUCTIONS)
                    except Exception as e:
                        self.debug_print(f"Error launching single window '{command}': {e}")
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
                time.sleep(self.DELAY_BETWEEN_INSTRUCTIONS)  # Wait for window to appear

                # Make it a group
                cmd = ["hyprctl", "dispatch", "togglegroup"]
                subprocess.run(cmd, check=True, capture_output=True)
                time.sleep(self.DELAY_BETWEEN_INSTRUCTIONS)

                # Launch remaining windows (they will auto-join the group)
                for window in group_windows[1:]:
                    command = window.get("launch_command", "")
                    if not command:
                        continue

                    print(f"  Launching group member: {command}")
                    subprocess.Popen(
                        command.split(),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    time.sleep(self.DELAY_BETWEEN_INSTRUCTIONS)

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
