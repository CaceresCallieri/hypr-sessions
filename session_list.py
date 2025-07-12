"""
Session list functionality
"""

import json

from utils import Utils


class SessionList(Utils):
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug
    
    def debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG SessionList] {message}")
    
    def list_sessions(self):
        """List all saved sessions"""
        self.debug_print(f"Searching for session files in: {self.sessions_dir}")
        session_files = list(self.sessions_dir.glob("*.json"))
        self.debug_print(f"Found {len(session_files)} session files")

        if not session_files:
            print("No saved sessions found")
            return

        print("Saved sessions:")
        print("-" * 40)

        for session_file in sorted(session_files):
            self.debug_print(f"Processing session file: {session_file}")
            try:
                with open(session_file, "r") as f:
                    session_data = json.load(f)

                name = session_data.get("session_name", session_file.stem)
                timestamp = session_data.get("timestamp", "Unknown")
                window_count = len(session_data.get("windows", []))
                
                self.debug_print(f"Session '{name}': {window_count} windows, saved {timestamp}")

                print(f"  {name}")
                print(f"    Windows: {window_count}")
                print(f"    Saved: {timestamp}")
                print()

            except Exception as e:
                self.debug_print(f"Error reading session file {session_file}: {e}")
                print(f"  {session_file.stem} (Error reading: {e})")
