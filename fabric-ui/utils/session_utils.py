"""
Session utilities for Hypr Sessions Manager
"""

from pathlib import Path


class SessionUtils:
    """Utility class for session directory operations"""
    
    @staticmethod
    def get_sessions_directory():
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
    def get_available_sessions():
        """Get list of available session names"""
        sessions_dir = SessionUtils.get_sessions_directory()
        if not sessions_dir.exists():
            return []
        
        sessions = []
        for item in sessions_dir.iterdir():
            if item.is_dir():
                session_file = item / "session.json"
                if session_file.exists():
                    sessions.append(item.name)
        
        return sorted(sessions)
    
    @staticmethod
    def session_exists(session_name):
        """Check if a session exists"""
        sessions_dir = SessionUtils.get_sessions_directory()
        session_dir = sessions_dir / session_name
        session_file = session_dir / "session.json"
        return session_dir.exists() and session_file.exists()
    
    @staticmethod
    def get_session_path(session_name):
        """Get the full path to a session directory"""
        sessions_dir = SessionUtils.get_sessions_directory()
        return sessions_dir / session_name
    
    @staticmethod
    def get_session_file_path(session_name):
        """Get the full path to a session.json file"""
        session_dir = SessionUtils.get_session_path(session_name)
        return session_dir / "session.json"