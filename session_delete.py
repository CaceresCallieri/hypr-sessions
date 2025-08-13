"""
Session delete functionality
"""

import shutil
from config import get_config, SessionConfig
from utils import Utils
from validation import SessionValidator, SessionNotFoundError, SessionValidationError


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
        try:
            # Validate session name (already done in CLI, but adding here for direct usage)
            SessionValidator.validate_session_name(session_name)
            
            self.debug_print(f"Attempting to delete session: {session_name}")
            
            # Check if session exists BEFORE calling get_session_directory (which creates directory)
            session_dir = self.config.sessions_dir / session_name
            SessionValidator.validate_session_exists(session_dir, session_name)
            
            # Now get the session directory (it won't create since it exists)
            session_dir = self.config.get_session_directory(session_name)
            self.debug_print(f"Session directory path: {session_dir}")
            
        except (SessionValidationError, SessionNotFoundError) as e:
            self.debug_print(f"Validation error: {e}")
            print(f"Error: {e}")
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
