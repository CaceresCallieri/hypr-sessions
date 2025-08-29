"""
Hyprctl client for retrieving window and workspace data
"""

import json
import subprocess
from typing import Optional, Any, List, Dict


class HyprctlClient:
    def __init__(self, debug: bool = False) -> None:
        self.debug = debug
        
    def debug_print(self, message: str) -> None:
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG HyprctlClient] {message}")

    def get_hyprctl_data(self, command: str) -> Optional[Any]:
        """Execute hyprctl command and return JSON data"""
        try:
            self.debug_print(f"Executing hyprctl {command}")
            result = subprocess.run(
                ["hyprctl", command, "-j"], 
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            self.debug_print(f"Successfully retrieved {command} data")
            return data
        except subprocess.CalledProcessError as e:
            self.debug_print(f"Hyprctl command failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.debug_print(f"Failed to parse JSON response: {e}")
            return None

    def get_workspace_clients(self, workspace_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get clients filtered to specific workspace"""
        try:
            # Validate input
            if not isinstance(workspace_id, int):
                self.debug_print(f"Invalid workspace_id type: {type(workspace_id)}")
                return None
            
            self.debug_print(f"Getting clients for workspace {workspace_id}")
            
            # Get all clients (this is the only way hyprctl provides the data)
            all_clients = self.get_hyprctl_data("clients")
            if not all_clients:
                self.debug_print("No clients data received from hyprctl")
                return None
            
            # Filter immediately and return only workspace clients
            workspace_clients = [
                client for client in all_clients 
                if client.get("workspace", {}).get("id") == workspace_id
            ]
            
            # Clear the all_clients reference to help with memory
            del all_clients
            
            self.debug_print(f"Found {len(workspace_clients)} clients in workspace {workspace_id}")
            return workspace_clients
            
        except Exception as e:
            self.debug_print(f"Unexpected error getting workspace {workspace_id} clients: {e}")
            return None