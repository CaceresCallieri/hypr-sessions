"""
Recovery operation implementation for browse panel
"""

from typing import Dict, Any
from .base_operation import BaseOperation

from utils.path_setup import setup_fabric_ui_imports

from constants import RECOVERING_STATE


class RecoveryOperation(BaseOperation):
    """Recovery operation implementation for archived sessions"""
    
    def execute_backend_operation(self, session_name: str) -> Dict[str, Any]:
        """Execute the recovery operation via backend"""
        return self.backend_client.recover_session(session_name)
    
    def get_operation_config(self) -> Dict[str, str]:
        """Get recovery-specific configuration"""
        return {
            "color": "#a6e3a1",  # Green theme for positive action (same as restore)
            "action_verb": "Recover", 
            "description": "Recover '{session_name}' from archive?\nSession will be restored to active sessions and can be used normally.",
            "button_prefix": "recovery",
            "success_description": "recovered from archive successfully",
            "progress_state": RECOVERING_STATE,
            "operation_timeout": 45  # Recovery can involve file operations - moderate timeout
        }
    
    def cleanup_after_success(self):
        """Update session list after successful recovery - archived session now active"""
        # After recovery, refresh to show updated session lists (archive → active)
        # The base class handles the actual panel refresh
        pass