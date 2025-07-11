"""
Session list functionality
"""

import json

from utils import Utils


class SessionList(Utils):
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

                print(f"  {name}")
                print(f"    Windows: {window_count}")
                print(f"    Saved: {timestamp}")
                print()

            except Exception as e:
                print(f"  {session_file.stem} (Error reading: {e})")
