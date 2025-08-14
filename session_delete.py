"""
Session delete functionality
"""

import shutil
from config import get_config, SessionConfig
from operation_result import OperationResult
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
    
    def delete_session(self, session_name: str) -> OperationResult:
        """Delete a saved session directory and all its contents"""
        result = OperationResult(operation_name=f"Delete session '{session_name}'")
        
        try:
            # Validate session name (already done in CLI, but adding here for direct usage)
            SessionValidator.validate_session_name(session_name)
            result.add_success("Session name validated")
            
            self.debug_print(f"Attempting to delete session: {session_name}")
            
            # Check if session exists BEFORE calling get_session_directory (which creates directory)
            session_dir = self.config.sessions_dir / session_name
            SessionValidator.validate_session_exists(session_dir, session_name)
            result.add_success("Session exists and is accessible")
            
            # Now get the session directory (it won't create since it exists)
            session_dir = self.config.get_session_directory(session_name)
            self.debug_print(f"Session directory path: {session_dir}")
            
        except (SessionValidationError, SessionNotFoundError) as e:
            self.debug_print(f"Validation error: {e}")
            result.add_error(str(e))
            return result

        self.debug_print(f"Session directory exists, proceeding with deletion")
        try:
            # Count files before deletion for user feedback
            files_in_session = list(session_dir.iterdir())
            file_count = len(files_in_session)
            
            # Log each file being deleted for debugging
            if self.debug:
                for file_path in files_in_session:
                    self.debug_print(f"Deleting file: {file_path}")
            
            # Remove entire session directory
            shutil.rmtree(session_dir)
            self.debug_print(f"Successfully deleted session directory: {session_dir}")
            result.add_success(f"Deleted session directory and {file_count} files")
            result.data = {
                "session_name": session_name,
                "files_deleted": file_count,
                "session_dir": str(session_dir)
            }
            return result
        except Exception as e:
            self.debug_print(f"Error deleting session directory {session_dir}: {e}")
            result.add_error(f"Failed to delete session directory: {e}")
            return result
