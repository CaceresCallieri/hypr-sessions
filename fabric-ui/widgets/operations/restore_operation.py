"""
Restore operation implementation for browse panel
"""

from typing import Dict, Any
from .base_operation import BaseOperation

from utils.path_setup import setup_fabric_ui_imports

from constants import RESTORING_STATE


class RestoreOperation(BaseOperation):
    """Restore operation implementation (supports both active and archive modes)"""
    
    def __init__(self, panel, backend_client):
        """Initialize the restore operation with dynamic mode from panel"""
        super().__init__(panel, backend_client)
    
    @property
    def is_archive_mode(self) -> bool:
        """Get current archive mode from panel (dynamic property)"""
        return getattr(self.panel, 'is_archive_mode', False)
    
    def execute_backend_operation(self, session_name: str) -> Dict[str, Any]:
        """Execute the restore or recovery operation via backend"""
        if self.is_archive_mode:
            return self.backend_client.recover_session(session_name)
        else:
            return self.backend_client.restore_session(session_name)
    
    def get_operation_config(self) -> Dict[str, str]:
        """Get mode-appropriate configuration (restore or recovery)"""
        if self.is_archive_mode:
            return {
                "color": "#a6e3a1",  # Green theme for positive action (same as restore)
                "action_verb": "Recover", 
                "description": "Recover '{session_name}' from archive?\n\nThis will restore the session to your active sessions list where it can be used normally. The session will be removed from the archive.",
                "button_prefix": "recovery",
                "success_description": "recovered successfully and is now available in active sessions",
                "progress_state": RESTORING_STATE,  # Unified state for both restore and recovery
                "operation_timeout": 45  # Recovery can involve file operations - moderate timeout
            }
        else:
            return {
                "color": "#a6e3a1",  # Green theme for positive action
                "action_verb": "Restore", 
                "description": "Restore '{session_name}' session to current workspace?\nThis will launch all saved applications and windows.",
                "button_prefix": "restore",
                "success_description": "restored successfully",
                "progress_state": RESTORING_STATE,
                "operation_timeout": 60  # Restore can be slow - longer timeout
            }
    
    def cleanup_after_success(self):
        """Handle post-operation cleanup based on mode"""
        if self.is_archive_mode:
            # After recovery, refresh to show updated session lists (archive → active)
            # The base class handles the actual panel refresh
            pass
        else:
            # No cleanup needed for restore - session list unchanged
            pass