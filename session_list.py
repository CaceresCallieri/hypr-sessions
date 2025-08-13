"""
Session list functionality
"""

import json

from config import get_config, SessionConfig
from operation_result import OperationResult
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
    
    def list_sessions(self) -> OperationResult:
        """List all saved sessions in folder format"""
        result = OperationResult(operation_name="List sessions")
        
        self.debug_print(f"Searching for session directories in: {self.config.sessions_dir}")
        
        try:
            # Find session directories (exclude hidden dirs and zen-browser-backups)
            session_dirs = [d for d in self.config.sessions_dir.iterdir() 
                           if d.is_dir() and not d.name.startswith('.') and d.name != 'zen-browser-backups']
        except Exception as e:
            result.add_error(f"Failed to scan sessions directory: {e}")
            return result
        
        self.debug_print(f"Found {len(session_dirs)} session directories")
        result.add_success(f"Found {len(session_dirs)} session directories")

        if not session_dirs:
            print("No saved sessions found")
            result.data = {"sessions": [], "session_count": 0}
            return result

        print("Saved sessions:")
        print("-" * 40)

        sessions_data = []
        valid_sessions = 0
        invalid_sessions = 0

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
                    
                    sessions_data.append({
                        "name": session_name,
                        "windows": window_count,
                        "files": file_count,
                        "timestamp": timestamp,
                        "valid": True
                    })
                    valid_sessions += 1
                    result.add_success(f"Processed session '{session_name}': {window_count} windows")

                except Exception as e:
                    self.debug_print(f"Error reading session file {session_file}: {e}")
                    print(f"  {session_name} (Error reading: {e})")
                    print()
                    
                    sessions_data.append({
                        "name": session_name,
                        "valid": False,
                        "error": str(e)
                    })
                    invalid_sessions += 1
                    result.add_warning(f"Failed to read session '{session_name}': {e}")
            else:
                self.debug_print(f"Session directory {session_dir} missing session.json")
                print(f"  {session_name} (Incomplete - missing session.json)")
                print()
                
                sessions_data.append({
                    "name": session_name,
                    "valid": False,
                    "error": "Missing session.json"
                })
                invalid_sessions += 1
                result.add_warning(f"Session '{session_name}' is incomplete: missing session.json")
        
        result.data = {
            "sessions": sessions_data,
            "session_count": len(session_dirs),
            "valid_sessions": valid_sessions,
            "invalid_sessions": invalid_sessions
        }
        
        if invalid_sessions > 0:
            result.add_warning(f"Found {invalid_sessions} invalid/incomplete sessions")
        
        return result
