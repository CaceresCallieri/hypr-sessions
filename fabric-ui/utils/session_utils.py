"""
Session utilities for Hypr Sessions Manager
"""

from pathlib import Path


class SessionUtils:
    """Utility class for session directory operations"""
    
    @staticmethod
    def get_sessions_directory():
        """Get the sessions directory path"""
        home = Path.home()
        return home / ".config" / "hypr-sessions"
    
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