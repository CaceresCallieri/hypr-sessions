"""
Session utilities for Hypr Sessions Manager
"""

from pathlib import Path
from typing import List


class SessionUtils:
    """Utility class for session directory operations"""
    
    @staticmethod
    def _get_sessions_from_directory(directory: Path, apply_security_validation: bool = True) -> List[str]:
        """Helper method to extract valid sessions from any directory
        
        Args:
            directory: Directory to scan for sessions
            apply_security_validation: Whether to apply comprehensive security validation
                                     (should be True for archived sessions, can be False for active sessions)
                                     
        Returns:
            List of valid session names (directory names) sorted alphabetically
        """
        try:
            if not directory.exists():
                return []
            
            sessions = []
            for item in directory.iterdir():
                # Basic validation - must be directory with session.json
                if not item.is_dir():
                    continue
                    
                # Apply security validation if requested (for archived sessions)
                if apply_security_validation:
                    # Security validation - prevent path traversal attacks
                    if (not item.name.startswith('.') and 
                        not '..' in item.name and
                        not item.name.startswith('/') and
                        not item.name.startswith('\\') and
                        # Additional security: prevent absolute paths and UNC paths
                        not item.name.startswith('~') and
                        not '\\' in item.name and
                        # Prevent null bytes and other control characters
                        not any(ord(c) < 32 for c in item.name)):
                        # Directory passes security validation
                        pass
                    else:
                        continue  # Skip directories that fail security validation
                
                # Check for session.json file
                try:
                    session_file = item / "session.json"
                    if session_file.exists():
                        sessions.append(item.name)
                except (PermissionError, OSError):
                    continue  # Skip inaccessible sessions gracefully
            
            return sorted(sessions)
        except (PermissionError, OSError):
            return []  # Graceful degradation on filesystem errors
    
    @staticmethod
    def get_sessions_directory() -> Path:
        """Get the active sessions directory path (new structure)"""
        home = Path.home()
        sessions_root = home / ".config" / "hypr-sessions"
        
        # Check if new structure exists
        active_dir = sessions_root / "sessions"
        if active_dir.exists():
            return active_dir
        
        # Fallback to old structure for compatibility
        return sessions_root
    
    @staticmethod
    def get_available_sessions() -> List[str]:
        """Get list of available session names"""
        return SessionUtils._get_sessions_from_directory(
            SessionUtils.get_sessions_directory(), 
            apply_security_validation=False  # Active sessions don't need path traversal protection
        )
    
    @staticmethod
    def session_exists(session_name: str) -> bool:
        """Check if a session exists"""
        sessions_dir = SessionUtils.get_sessions_directory()
        session_dir = sessions_dir / session_name
        session_file = session_dir / "session.json"
        return session_dir.exists() and session_file.exists()
    
    @staticmethod
    def get_session_path(session_name: str) -> Path:
        """Get the full path to a session directory"""
        sessions_dir = SessionUtils.get_sessions_directory()
        return sessions_dir / session_name
    
    @staticmethod
    def get_session_file_path(session_name: str) -> Path:
        """Get the full path to a session.json file"""
        session_dir = SessionUtils.get_session_path(session_name)
        return session_dir / "session.json"
    
    @staticmethod
    def get_archived_sessions_directory() -> Path:
        """Get the archived sessions directory path"""
        home = Path.home()
        sessions_root = home / ".config" / "hypr-sessions"
        archived_dir = sessions_root / "archived"
        return archived_dir
    
    @staticmethod
    def get_archived_sessions() -> List[str]:
        """Get list of archived session names with timestamps"""
        return SessionUtils._get_sessions_from_directory(
            SessionUtils.get_archived_sessions_directory(), 
            apply_security_validation=True  # Archived sessions require full security validation
        )