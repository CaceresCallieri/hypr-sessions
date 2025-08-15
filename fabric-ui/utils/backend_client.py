"""
Backend Client for Hypr Sessions Manager
Handles communication with the CLI backend using subprocess calls
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


class BackendClient:
    """Client for communicating with the hypr-sessions CLI backend"""
    
    def __init__(self):
        # Path to the CLI script (one directory up from fabric-ui)
        self.cli_path = Path(__file__).parent.parent.parent / "hypr-sessions.py"
        if not self.cli_path.exists():
            raise FileNotFoundError(f"CLI script not found at {self.cli_path}")
    
    def _run_command(self, command_args: list) -> Dict[str, Any]:
        """
        Run a CLI command and return parsed JSON result
        
        Args:
            command_args: List of command arguments (e.g., ['save', 'session-name'])
            
        Returns:
            Dict containing the JSON response from CLI
            
        Raises:
            BackendError: If the command fails or returns invalid JSON
        """
        # Build full command with --json flag
        full_command = [str(self.cli_path)] + command_args + ["--json"]
        
        try:
            # Run the command
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            # Parse JSON output
            try:
                response = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise BackendError(f"Invalid JSON response: {e}\nOutput: {result.stdout}")
            
            # Check if command succeeded
            if result.returncode != 0:
                error_msg = response.get('messages', [{}])[0].get('message', 'Unknown error')
                raise BackendError(f"Command failed: {error_msg}")
            
            return response
            
        except subprocess.TimeoutExpired:
            raise BackendError("Command timed out after 30 seconds")
        except subprocess.SubprocessError as e:
            raise BackendError(f"Failed to execute command: {e}")
    
    def save_session(self, session_name: str) -> Dict[str, Any]:
        """
        Save the current session
        
        Args:
            session_name: Name for the new session
            
        Returns:
            Dict containing save result with success status and details
            
        Raises:
            BackendError: If save operation fails
        """
        return self._run_command(['save', session_name])
    
    def restore_session(self, session_name: str) -> Dict[str, Any]:
        """
        Restore a saved session
        
        Args:
            session_name: Name of session to restore
            
        Returns:
            Dict containing restore result with success status and details
            
        Raises:
            BackendError: If restore operation fails
        """
        return self._run_command(['restore', session_name])
    
    def list_sessions(self) -> Dict[str, Any]:
        """
        List all available sessions
        
        Returns:
            Dict containing list of sessions and metadata
            
        Raises:
            BackendError: If list operation fails
        """
        return self._run_command(['list'])
    
    def delete_session(self, session_name: str) -> Dict[str, Any]:
        """
        Delete a saved session
        
        Args:
            session_name: Name of session to delete
            
        Returns:
            Dict containing deletion result with success status and details
            
        Raises:
            BackendError: If delete operation fails
        """
        return self._run_command(['delete', session_name])


class BackendError(Exception):
    """Exception raised for backend communication errors"""
    pass


# Example usage and response format documentation:
"""
Example save_session response:
{
    "success": true,
    "operation": "Save session 'work-session'",
    "data": {
        "session_file": "/path/to/session.json",
        "windows_saved": 5,
        "groups_detected": 1
    },
    "messages": [
        {
            "status": "success",
            "message": "Session saved successfully",
            "context": null
        }
    ],
    "summary": {
        "success_count": 15,
        "warning_count": 2,
        "error_count": 0
    }
}

Example error response:
{
    "success": false,
    "operation": "Save session 'invalid/name'",
    "data": null,
    "messages": [
        {
            "status": "error",
            "message": "Session name contains invalid characters: '/'",
            "context": "Invalid characters: <>:\"/\\|?*"
        }
    ],
    "summary": {
        "success_count": 0,
        "warning_count": 0,
        "error_count": 1
    }
}
"""