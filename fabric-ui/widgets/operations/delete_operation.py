"""
Delete operation implementation for browse panel
"""

from typing import Dict, Any
from .base_operation import BaseOperation

# Centralized path setup for imports
from utils.path_setup import setup_fabric_ui_imports

from constants import DELETING_STATE


class DeleteOperation(BaseOperation):
    """Delete operation implementation"""
    
    def execute_backend_operation(self, session_name: str) -> Dict[str, Any]:
        """Execute the delete operation via backend"""
        return self.backend_client.delete_session(session_name)
    
    def get_operation_config(self) -> Dict[str, str]:
        """Get delete-specific configuration"""
        return {
            "color": "#f38ba8",  # Red theme for destructive action
            "action_verb": "Delete",
            "description": "Are you sure you wish to delete '{session_name}' session files?\nThis action cannot be undone.",
            "button_prefix": "delete",
            "success_description": "deleted successfully",
            "progress_state": DELETING_STATE,
            "operation_timeout": 10  # Delete is fast - shorter timeout
        }
    
    def cleanup_after_success(self):
        """Refresh session list to remove deleted session"""
        self.panel.refresh()