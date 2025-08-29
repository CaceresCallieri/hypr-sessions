"""
Neovide-specific functionality for session capture and restoration
Supports enhanced session management via Neovim remote API
"""

import glob
import os
import shlex
import subprocess
import time
from pathlib import Path


class NeovideHandler:
    def __init__(self, debug=False):
        self.debug = debug
    
    def debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG NeovideHandler] {message}")
    
    def _ensure_session_directory(self, session_dir):
        """Ensure session directory exists"""
        session_dir_path = Path(session_dir)
        session_dir_path.mkdir(parents=True, exist_ok=True)
        self.debug_print(f"Ensured session directory exists: {session_dir_path}")
        return session_dir_path
    
    def _get_working_directory(self, pid):
        """Get working directory for a process PID"""
        cwd_path = Path(f"/proc/{pid}/cwd")
        if cwd_path.exists():
            working_dir = str(cwd_path.resolve())
            self.debug_print(f"Working directory for PID {pid}: {working_dir}")
            return working_dir
        else:
            self.debug_print(f"Working directory path does not exist: {cwd_path}")
            return None
    
    def is_neovide_window(self, window_data):
        """Check if a window is running Neovide"""
        class_name = window_data.get("class", "").lower()
        is_neovide = class_name == "neovide"
        self.debug_print(f"Checking window class '{class_name}' -> is_neovide: {is_neovide}")
        return is_neovide

    def find_nvim_socket_for_pid(self, pid):
        """Find the Neovim server socket associated with a PID"""
        self.debug_print(f"Looking for Neovim socket for PID {pid}")
        
        # Common socket locations
        socket_patterns = [
            f"/run/user/{os.getuid()}/nvim.{pid}.*",
            f"/tmp/nvim{os.getuid()}/*/nvim.{pid}.*",
            f"/tmp/nvim.{pid}.*"
        ]
        
        for pattern in socket_patterns:
            sockets = glob.glob(pattern)
            if sockets:
                socket_path = sockets[0]  # Take first match
                self.debug_print(f"Found Neovim socket: {socket_path}")
                return socket_path
        
        # Try to find any socket for the process tree
        try:
            # Get all child processes of the PID
            result = subprocess.run(
                ["pgrep", "-P", str(pid)], 
                capture_output=True, text=True, timeout=5
            )
            child_pids = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            for child_pid in child_pids:
                if child_pid:
                    for pattern in socket_patterns:
                        child_pattern = pattern.replace(str(pid), child_pid)
                        sockets = glob.glob(child_pattern)
                        if sockets:
                            socket_path = sockets[0]
                            self.debug_print(f"Found Neovim socket via child PID {child_pid}: {socket_path}")
                            return socket_path
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            self.debug_print(f"Error finding child processes: {e}")
        
        self.debug_print(f"No Neovim socket found for PID {pid}")
        return None

    def capture_neovim_session(self, pid, session_dir):
        """Capture Neovim session from running instance via remote API"""
        self.debug_print(f"Capturing Neovim session for PID {pid}")
        
        # Find the Neovim socket
        socket_path = self.find_nvim_socket_for_pid(pid)
        if not socket_path:
            self.debug_print(f"Cannot capture session - no Neovim socket found for PID {pid}")
            return None
        
        try:
            # Ensure session directory exists
            session_dir_path = self._ensure_session_directory(session_dir)
            
            # Create session filename
            session_filename = f"neovide-session-{pid}.vim"
            session_file = session_dir_path / session_filename
            self.debug_print(f"Creating session file: {session_file}")
            
            # Execute :mksession command via remote API
            # Note: Use backslash escaping for spaces, not shell quoting for Neovim commands
            escaped_path = str(session_file).replace(' ', '\\ ')
            mksession_cmd = f":mksession! {escaped_path}"
            result = subprocess.run([
                "nvim", "--server", socket_path, "--remote-send", mksession_cmd + "<CR>"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.debug_print(f"Failed to execute mksession command: {result.stderr}")
                return None
            
            # Wait for session file to be created
            max_wait = 3  # seconds
            wait_time = 0.1
            while not session_file.exists() and max_wait > 0:
                time.sleep(wait_time)
                max_wait -= wait_time
            
            if session_file.exists():
                self.debug_print(f"Successfully captured session: {session_file}")
                return str(session_file)
            else:
                self.debug_print(f"Session file was not created: {session_file}")
                return None
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            self.debug_print(f"Error capturing session for PID {pid}: {e}")
            return None

    def get_neovide_session_info(self, pid):
        """Extract session information from a running Neovide instance"""
        self.debug_print(f"Getting session info for Neovide PID {pid}")
        try:
            # Get the working directory from Neovide process
            working_dir = self._get_working_directory(pid)
            
            session_data = {
                "working_directory": working_dir,
                "session_file": None,
                "has_session": False,
                "nvim_socket": None
            }
            
            # Try to find Neovim socket
            socket_path = self.find_nvim_socket_for_pid(pid)
            if socket_path:
                session_data["nvim_socket"] = socket_path
                self.debug_print(f"Found Neovim socket: {socket_path}")
            
            return session_data
            
        except (OSError, PermissionError) as e:
            self.debug_print(f"Error getting session info for PID {pid}: {e}")
            pass
        return None

    def create_session_file(self, pid, session_dir):
        """Create a session file for a running Neovide instance"""
        self.debug_print(f"Creating session file for Neovide PID {pid}")
        
        # First try to capture live session via Neovim remote API
        session_file = self.capture_neovim_session(pid, session_dir)
        if session_file:
            return session_file
        
        # Fallback to basic session file with working directory
        self.debug_print(f"Falling back to basic session file for PID {pid}")
        try:
            # Get working directory
            working_dir = self._get_working_directory(pid)
            if not working_dir:
                return None
            
            # Ensure session directory exists
            session_dir_path = self._ensure_session_directory(session_dir)
            
            # Create session filename based on PID to avoid conflicts
            session_filename = f"hypr-session-neovide-{pid}.vim"
            session_file = session_dir_path / session_filename
            self.debug_print(f"Creating basic session file: {session_file}")
            
            # Create a basic session file that restores working directory
            basic_session = f'''\" Session file created by hypr-sessions for Neovide
\" Fallback session - Neovim remote API not available
cd {shlex.quote(working_dir)}
'''
            with open(session_file, "w") as f:
                f.write(basic_session)
                
            self.debug_print(f"Successfully created basic session file: {session_file}")
            return str(session_file)
            
        except Exception as e:
            self.debug_print(f"Error creating session file for PID {pid}: {e}")
            pass
        return None


    def get_restore_command(self, window_data, session_file=None):
        """Generate restore command for Neovide with session"""
        working_dir = window_data.get("working_directory")
        
        if session_file and Path(session_file).exists():
            # Launch Neovide with session file using -- to pass args to nvim
            escaped_session = shlex.quote(session_file)
            self.debug_print(f"Restoring Neovide with session file: {session_file}")
            return f"neovide -- -S {escaped_session}"
        elif working_dir:
            # Launch Neovide and change to working directory via nvim command
            escaped_dir = shlex.quote(working_dir)
            self.debug_print(f"Restoring Neovide with working directory: {working_dir}")
            return f"neovide -- -c {shlex.quote(f'cd {working_dir}')}"
        else:
            # Basic Neovide launch
            self.debug_print("Restoring Neovide with default settings")
            return "neovide"
