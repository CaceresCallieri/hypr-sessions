"""
Launch command generation for different applications
"""

import shlex
from .terminal_handler import TerminalHandler
from .neovide_handler import NeovideHandler


class LaunchCommandGenerator:
    def __init__(self, debug=False):
        self.terminal_handler = TerminalHandler()
        self.neovide_handler = NeovideHandler(debug=debug)

    def guess_launch_command(self, window_data):
        """Guess the launch command based on window class"""
        class_name = window_data.get("class", "").lower()
        title = window_data.get("title", "")
        working_dir = window_data.get("working_directory")
        running_program = window_data.get("running_program")

        # Common application mappings
        command_map = {
            "zen": "zen-browser",
            "com.mitchellh.ghostty": "ghostty",
            "firefox": "firefox",
            "chromium": "chromium",
            "google-chrome": "google-chrome",
            "neovim": "nvim",
            "neovide": "neovide",
            "code": "code",
            "code-oss": "code-oss",
            "thunar": "thunar",
            "nautilus": "nautilus",
            "dolphin": "dolphin",
            # Future terminal support can be added here:
            # "alacritty": "alacritty",
            # "kitty": "kitty",
            # "foot": "foot",
            # "wezterm": "wezterm",
        }

        base_command = command_map.get(class_name, class_name)

        # Check for Neovide session data first
        neovide_session = window_data.get("neovide_session")
        if neovide_session:
            return self.neovide_handler.get_restore_command(window_data, 
                                                         neovide_session.get("session_file"))

        # For Ghostty terminal, add working directory and program execution
        if class_name == "com.mitchellh.ghostty":
            command_parts = [base_command]
            
            # Add working directory if available
            if working_dir:
                command_parts.append(f"--working-directory={working_dir}")
            
            # Add program execution if available
            if running_program:
                command_parts.append("-e")
                
                # Handle shell commands vs direct programs with shell persistence
                if running_program.get("shell_command"):
                    # For shell commands like "npm run dev", use trap to handle signals properly
                    shell_command = running_program["shell_command"]
                    wrapper_command = f"trap 'echo Program interrupted' INT; {shell_command}; exec $SHELL"
                    command_parts.extend(["sh", "-c", f'"{wrapper_command}"'])
                else:
                    # For direct programs like "yazi", execute with shell persistence  
                    program_name = running_program["name"]
                    args = running_program.get("args", [])
                    if args:
                        full_program = f"{program_name} {' '.join(args)}"
                    else:
                        full_program = program_name
                    wrapper_command = f"{full_program}; exec $SHELL"
                    command_parts.extend(["sh", "-c", wrapper_command])
            
            return " ".join(command_parts)
        
        # Future terminal support can be added here with similar patterns:
        # elif class_name == "alacritty" and working_dir:
        #     escaped_dir = shlex.quote(working_dir)
        #     return f"{base_command} --working-directory={escaped_dir}"
        # elif class_name == "kitty" and working_dir:
        #     escaped_dir = shlex.quote(working_dir)
        #     return f"{base_command} --directory={escaped_dir}"

        return base_command