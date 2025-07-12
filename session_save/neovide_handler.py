"""
Neovide-specific functionality for session capture and restoration
"""

import os
import shlex
import subprocess
import tempfile
from pathlib import Path


class NeovideHandler:
    def is_neovide_window(self, window_data):
        """Check if a window is running Neovide"""
        class_name = window_data.get("class", "").lower()
        return class_name == "neovide"

    def get_neovide_session_info(self, pid):
        """Extract session information from a running Neovide instance"""
        try:
            # Get the working directory from Neovide process
            cwd_path = Path(f"/proc/{pid}/cwd")
            working_dir = str(cwd_path.resolve()) if cwd_path.exists() else None
            
            session_data = {
                "working_directory": working_dir,
                "session_file": None,
                "has_session": False
            }
            
            # Check if there's an existing session file in the working directory
            if working_dir:
                session_file = Path(working_dir) / "Session.vim"
                if session_file.exists():
                    session_data["session_file"] = str(session_file)
                    session_data["has_session"] = True
                    
            return session_data
            
        except (OSError, PermissionError):
            pass
        return None

    def create_session_file(self, pid, session_dir):
        """Create a session file for a running Neovide instance"""
        try:
            # Get working directory
            cwd_path = Path(f"/proc/{pid}/cwd")
            if not cwd_path.exists():
                return None
                
            working_dir = str(cwd_path.resolve())
            
            # Create session filename based on PID to avoid conflicts
            session_filename = f"hypr-session-neovide-{pid}.vim"
            session_file = Path(session_dir) / session_filename
            
            # Create a basic session file that restores working directory
            # This is a minimal approach - in the future we could try to use
            # Neovim's remote API if Neovide supports it
            basic_session = f'''\" Session file created by hypr-sessions for Neovide
cd {shlex.quote(working_dir)}
'''
            with open(session_file, "w") as f:
                f.write(basic_session)
                
            return str(session_file)
            
        except Exception:
            pass
        return None


    def get_restore_command(self, window_data, session_file=None):
        """Generate restore command for Neovide with session"""
        working_dir = window_data.get("working_directory")
        
        if session_file and Path(session_file).exists():
            # Launch Neovide with session file using -- to pass args to nvim
            escaped_session = shlex.quote(session_file)
            return f"neovide -- -S {escaped_session}"
        elif working_dir:
            # Launch Neovide and change to working directory via nvim command
            escaped_dir = shlex.quote(working_dir)
            return f"neovide -- -c {shlex.quote(f'cd {working_dir}')}"
        else:
            # Basic Neovide launch
            return "neovide"
