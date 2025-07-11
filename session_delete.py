"""
Session delete functionality
"""

from utils import Utils


class SessionDelete(Utils):
    def delete_session(self, session_name):
        """Delete a saved session"""
        session_file = self.sessions_dir / f"{session_name}.json"

        if not session_file.exists():
            print(f"Session not found: {session_name}")
            return False

        try:
            session_file.unlink()
            print(f"Session deleted: {session_name}")
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
