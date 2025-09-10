"""
Hyprctl client for retrieving window and workspace data
"""

import json
import subprocess
from typing import Optional, Any, List, Dict

from ..shared.debug import CommandDebugger


class HyprctlClient:
    def __init__(self, debug: bool = False) -> None:
        self.debugger = CommandDebugger("HyprctlClient", debug)

    def get_hyprctl_data(self, command: str) -> Optional[Any]:
        """Execute hyprctl command and return JSON data"""
        try:
            self.debugger.debug(f"Executing hyprctl {command}")
            result = subprocess.run(
                ["hyprctl", command, "-j"], 
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            self.debugger.debug(f"Successfully retrieved {command} data")
            return data
        except subprocess.CalledProcessError as e:
            self.debugger.debug(f"Hyprctl command failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.debugger.debug(f"Failed to parse JSON response: {e}")
            return None

    def get_workspace_clients(self, workspace_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get clients filtered to specific workspace"""
        try:
            # Validate input
            if not isinstance(workspace_id, int):
                self.debugger.debug(f"Invalid workspace_id type: {type(workspace_id)}")
                return None
            
            self.debugger.debug(f"Getting clients for workspace {workspace_id}")
            
            # Get all clients (this is the only way hyprctl provides the data)
            all_clients = self.get_hyprctl_data("clients")
            if not all_clients:
                self.debugger.debug("No clients data received from hyprctl")
                return None
            
            # Filter immediately and return only workspace clients
            workspace_clients = [
                client for client in all_clients 
                if client.get("workspace", {}).get("id") == workspace_id
            ]
            
            # Clear the all_clients reference to help with memory
            del all_clients
            
            self.debugger.debug(f"Found {len(workspace_clients)} clients in workspace {workspace_id}")
            return workspace_clients
            
        except Exception as e:
            self.debugger.debug(f"Unexpected error getting workspace {workspace_id} clients: {e}")
            return None