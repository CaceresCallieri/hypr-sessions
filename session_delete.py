"""
Session delete functionality
"""

import shutil
from config import get_config, SessionConfig
from utils import Utils


class SessionDelete(Utils):
    def __init__(self, debug: bool = False) -> None:
        super().__init__()
        self.debug: bool = debug
        self.config: SessionConfig = get_config()
    
    def debug_print(self, message: str) -> None:
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG SessionDelete] {message}")
    
    def delete_session(self, session_name: str) -> bool:
        """Delete a saved session directory and all its contents"""
        self.debug_print(f"Attempting to delete session: {session_name}")
        session_dir = self.config.get_session_directory(session_name)
        self.debug_print(f"Session directory path: {session_dir}")

        if not session_dir.exists():
            self.debug_print(f"Session directory does not exist: {session_dir}")
            print(f"Session not found: {session_name}")
            return False

        self.debug_print(f"Session directory exists, proceeding with deletion")
        try:
            # Count files before deletion for user feedback
            files_in_session = list(session_dir.iterdir())
            file_count = len(files_in_session)
            
            # Remove entire session directory
            shutil.rmtree(session_dir)
            self.debug_print(f"Successfully deleted session directory: {session_dir}")
            print(f"Session deleted: {session_name} ({file_count} files removed)")
            return True
        except Exception as e:
            self.debug_print(f"Error deleting session directory {session_dir}: {e}")
            print(f"Error deleting session: {e}")
            return False
