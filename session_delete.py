"""
Session delete functionality
"""

from utils import Utils


class SessionDelete(Utils):
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug
    
    def debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG SessionDelete] {message}")
    
    def delete_session(self, session_name):
        """Delete a saved session"""
        self.debug_print(f"Attempting to delete session: {session_name}")
        session_file = self.sessions_dir / f"{session_name}.json"
        self.debug_print(f"Session file path: {session_file}")

        if not session_file.exists():
            self.debug_print(f"Session file does not exist: {session_file}")
            print(f"Session not found: {session_name}")
            return False

        self.debug_print(f"Session file exists, proceeding with deletion")
        try:
            session_file.unlink()
            self.debug_print(f"Successfully deleted session file: {session_file}")
            print(f"Session deleted: {session_name}")
            return True
        except Exception as e:
            self.debug_print(f"Error deleting session file {session_file}: {e}")
            print(f"Error deleting session: {e}")
            return False
