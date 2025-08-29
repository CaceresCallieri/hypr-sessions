"""
Terminal-specific functionality for working directory capture
"""

from pathlib import Path
from typing import Set, List, Optional

from ..shared.session_types import RunningProgram


class TerminalHandler:
    def is_terminal_app(self, class_name: str) -> bool:
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

    def get_working_directory(self, pid: int) -> Optional[str]:
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
                            stat_line = f.read().strip()
                            # Handle process names with spaces by finding the last ')' 
                            # then splitting the remaining fields
                            last_paren = stat_line.rfind(')')
                            if last_paren != -1:
                                # Split only the fields after the process name
                                fields_after_name = stat_line[last_paren + 1:].split()
                                if len(fields_after_name) >= 2:
                                    ppid = int(fields_after_name[1])  # Parent PID is 2nd field after name
                                    if ppid == parent_pid:
                                        children.append(int(proc_dir.name))
                except (ValueError, OSError, PermissionError):
                    continue
        except (OSError, PermissionError):
            pass
        return children

    def get_running_program(self, terminal_pid, debug=False):
        """Detect running program in terminal by analyzing process tree"""
        try:
            children = self.get_child_processes(terminal_pid)
            if debug:
                print(f"[DEBUG TerminalHandler] Found {len(children)} child processes: {children}")
            
            for child_pid in children:
                program_info = self._analyze_process(child_pid, debug)
                if program_info:
                    if debug:
                        print(f"[DEBUG TerminalHandler] Detected running program: {program_info}")
                    return program_info
            
            if debug:
                print("[DEBUG TerminalHandler] No interesting programs detected")
            return None
            
        except (OSError, PermissionError) as e:
            if debug:
                print(f"[DEBUG TerminalHandler] Error detecting running program: {e}")
            return None

    def _analyze_process(self, pid, debug=False):
        """Analyze a single process to determine if it's an interesting program"""
        try:
            # Read command line
            cmdline_path = Path(f"/proc/{pid}/cmdline")
            if not cmdline_path.exists():
                return None
                
            with open(cmdline_path, "rb") as f:
                cmdline_data = f.read()
                
            if not cmdline_data:
                return None
                
            # Parse null-separated arguments
            args = cmdline_data.decode('utf-8', errors='ignore').split('\0')[:-1]
            if not args:
                return None
                
            # Filter out empty arguments
            args = [arg for arg in args if arg.strip()]
            if not args:
                return None
                
            program_name = Path(args[0]).name
            if debug:
                print(f"[DEBUG TerminalHandler] Process {pid}: {program_name} with args {args}")
            
            # Skip the hypr-sessions save command itself to avoid capturing it
            if (program_name == "python" and len(args) >= 2 and 
                "hypr-sessions.py" in args[1] and "save" in args):
                if debug:
                    print(f"[DEBUG TerminalHandler] Skipping hypr-sessions save command")
                return None
            
            # Skip neovide programs since they're handled by dedicated neovide session management
            if program_name == "neovide":
                if debug:
                    print(f"[DEBUG TerminalHandler] Skipping neovide program (handled separately)")
                return None
            
            # Skip embedded nvim processes (these are children of GUI editors like neovide)
            if program_name == "nvim" and "--embed" in args:
                if debug:
                    print(f"[DEBUG TerminalHandler] Skipping embedded nvim (child of GUI editor)")
                return None
            
            # Skip shell processes unless they're running specific commands
            shell_names = {"bash", "zsh", "fish", "sh", "dash"}
            if program_name in shell_names:
                # Check if shell is running a command with -c flag
                if len(args) >= 3 and args[1] == "-c":
                    shell_command = args[2]
                    return {
                        "name": shell_command.split()[0] if shell_command.split() else program_name,
                        "args": [],
                        "full_command": shell_command,
                        "shell_command": shell_command
                    }
                # For shells without -c, look at their children recursively
                children = self.get_child_processes(pid)
                if debug:
                    print(f"[DEBUG TerminalHandler] Shell {pid} has {len(children)} children: {children}")
                
                for child_pid in children:
                    child_result = self._analyze_process(child_pid, debug)
                    if child_result:
                        return child_result
                
                # If no direct children found interesting programs, look deeper
                # This handles cases like: shell -> npm -> node processes
                if debug:
                    print(f"[DEBUG TerminalHandler] Looking deeper into process tree...")
                for child_pid in children:
                    grandchildren = self.get_child_processes(child_pid)
                    if debug and grandchildren:
                        print(f"[DEBUG TerminalHandler] Child {child_pid} has grandchildren: {grandchildren}")
                    for grandchild_pid in grandchildren:
                        grandchild_result = self._analyze_process(grandchild_pid, debug)
                        if grandchild_result:
                            return grandchild_result
                return None
            
            # For non-shell programs, determine if it should be treated as shell command
            full_command = " ".join(args)
            
            # Check if this is a multi-word command that should be treated as shell command
            if (len(args) > 1 or 
                program_name in ["npm", "yarn", "pnpm", "bun"] or
                " " in args[0]):  # Handle cases where the whole command is in args[0]
                
                # Package manager and multi-word commands should be shell commands
                return {
                    "name": args[0],
                    "args": [],
                    "full_command": full_command,
                    "shell_command": full_command
                }
            else:
                # Direct program execution
                return {
                    "name": program_name,
                    "args": args[1:] if len(args) > 1 else [],
                    "full_command": full_command,
                    "shell_command": None
                }
            
        except (OSError, PermissionError, UnicodeDecodeError) as e:
            if debug:
                print(f"[DEBUG TerminalHandler] Error analyzing process {pid}: {e}")
            return None