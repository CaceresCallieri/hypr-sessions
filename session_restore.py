"""
Session restore functionality
"""

import json
import subprocess
import time

from utils import Utils


class SessionRestore(Utils):
    def restore_session(self, session_name):
        """Restore a saved session with group support"""
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
        print(f"Timestamp: {session_data.get('timestamp')}")

        groups = session_data.get("groups", {})

        if groups:
            print(f"Found {len(groups)} groups to restore")

        # Step 1: Launch applications and create groups during launch
        if groups:
            print("Launching applications with groups...")
            self.launch_with_groups(session_data.get("windows", []), groups)
        else:
            print("Launching applications...")
            for window in session_data.get("windows", []):
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
                    time.sleep(1.0)
                except Exception as e:
                    print(f"Error launching {command}: {e}")

        print(f"Restored {len(session_data.get('windows', []))} applications")
        return True

    def launch_with_groups(self, windows, groups):
        """Launch applications and create groups during the process"""
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

        # Launch ungrouped windows first
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
                time.sleep(1.0)
            except Exception as e:
                print(f"Error launching {command}: {e}")

        # Launch grouped windows
        for group_id, group_windows in windows_by_group.items():
            print(
                f"Launching group {group_id[:8]}... with {len(group_windows)} windows"
            )

            if len(group_windows) < 2:
                # Single window, launch normally
                window = group_windows[0]
                command = window.get("launch_command", "")
                if command:
                    print(f"  Launching: {command}")
                    try:
                        subprocess.Popen(
                            command.split(),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        time.sleep(1.0)
                    except Exception as e:
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
                time.sleep(1.5)  # Wait for window to appear

                # Make it a group
                cmd = ["hyprctl", "dispatch", "togglegroup"]
                subprocess.run(cmd, check=True, capture_output=True)
                time.sleep(0.3)

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
                    time.sleep(1.0)

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
