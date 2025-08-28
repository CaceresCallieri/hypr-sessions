"""
Restore operation implementation for browse panel
"""

from typing import Dict, Any
from .base_operation import BaseOperation

from utils.path_setup import setup_fabric_ui_imports

from constants import RESTORING_STATE


class RestoreOperation(BaseOperation):
    """Restore operation implementation"""
    
    def execute_backend_operation(self, session_name: str) -> Dict[str, Any]:
        """Execute the restore operation via backend"""
        return self.backend_client.restore_session(session_name)
    
    def get_operation_config(self) -> Dict[str, str]:
        """Get restore-specific configuration"""
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
        """No cleanup needed for restore - session list unchanged"""
        pass