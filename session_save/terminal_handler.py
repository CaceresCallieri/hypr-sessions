"""
Terminal-specific functionality for working directory capture
"""

from pathlib import Path


class TerminalHandler:
    def is_terminal_app(self, class_name):
        """Check if the application is a terminal emulator (currently only Ghostty supported)"""
        # Currently only supporting Ghostty terminal
        # Future terminal support can be added to this set:
        terminal_apps = {
            "com.mitchellh.ghostty",
            # Future terminals can be added here:
            # "alacritty",
            # "kitty", 
            # "foot",
            # "wezterm",
            # "gnome-terminal",
        }
        return class_name.lower() in terminal_apps

    def get_working_directory(self, pid):
        """Get the working directory of a terminal process by finding its shell child"""
        try:
            # First try the process itself
            cwd_path = Path(f"/proc/{pid}/cwd")
            if cwd_path.exists():
                terminal_cwd = str(cwd_path.resolve())
                # If it's not the home directory, use it
                if terminal_cwd != str(Path.home()):
                    return terminal_cwd

            # If terminal CWD is home, look for shell children
            children = self.get_child_processes(pid)
            for child_pid in children:
                try:
                    child_cwd_path = Path(f"/proc/{child_pid}/cwd")
                    if child_cwd_path.exists():
                        child_cwd = str(child_cwd_path.resolve())
                        # Use child's working directory if it's different from home
                        if child_cwd != str(Path.home()):
                            return child_cwd
                except (OSError, PermissionError):
                    continue

            # Fallback to terminal's directory even if it's home
            return terminal_cwd if "terminal_cwd" in locals() else None

        except (OSError, PermissionError):
            pass
        return None

    def get_child_processes(self, parent_pid):
        """Get list of child process PIDs"""
        children = []
        try:
            # Read /proc/*/stat to find children
            proc_dirs = Path("/proc").glob("[0-9]*")
            for proc_dir in proc_dirs:
                try:
                    stat_file = proc_dir / "stat"
                    if stat_file.exists():
                        with open(stat_file, "r") as f:
                            stat_data = f.read().split()
                            if len(stat_data) >= 4:
                                ppid = int(stat_data[3])  # Parent PID is 4th field
                                if ppid == parent_pid:
                                    children.append(int(proc_dir.name))
                except (ValueError, OSError, PermissionError):
                    continue
        except (OSError, PermissionError):
            pass
        return children