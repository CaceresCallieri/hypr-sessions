"""
Session list functionality
"""

import json

from config import get_config, SessionConfig
from utils import Utils


class SessionList(Utils):
    def __init__(self, debug: bool = False) -> None:
        super().__init__()
        self.debug: bool = debug
        self.config: SessionConfig = get_config()
    
    def debug_print(self, message: str) -> None:
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG SessionList] {message}")
    
    def list_sessions(self) -> None:
        """List all saved sessions in folder format"""
        self.debug_print(f"Searching for session directories in: {self.config.sessions_dir}")
        
        # Find session directories (exclude hidden dirs and zen-browser-backups)
        session_dirs = [d for d in self.config.sessions_dir.iterdir() 
                       if d.is_dir() and not d.name.startswith('.') and d.name != 'zen-browser-backups']
        
        self.debug_print(f"Found {len(session_dirs)} session directories")

        if not session_dirs:
            print("No saved sessions found")
            return

        print("Saved sessions:")
        print("-" * 40)

        for session_dir in sorted(session_dirs):
            session_name = session_dir.name
            session_file = session_dir / "session.json"
            
            self.debug_print(f"Processing session directory: {session_dir}")
            
            if session_file.exists():
                try:
                    with open(session_file, "r") as f:
                        session_data = json.load(f)

                    timestamp = session_data.get("timestamp", "Unknown")
                    window_count = len(session_data.get("windows", []))
                    
                    # Count all files in session directory
                    all_files = list(session_dir.iterdir())
                    file_count = len(all_files)
                    
                    self.debug_print(f"Session '{session_name}': {window_count} windows, {file_count} files, saved {timestamp}")

                    print(f"  {session_name}")
                    print(f"    Windows: {window_count}")
                    print(f"    Files: {file_count}")
                    print(f"    Saved: {timestamp}")
                    print()

                except Exception as e:
                    self.debug_print(f"Error reading session file {session_file}: {e}")
                    print(f"  {session_name} (Error reading: {e})")
                    print()
            else:
                self.debug_print(f"Session directory {session_dir} missing session.json")
                print(f"  {session_name} (Incomplete - missing session.json)")
                print()
