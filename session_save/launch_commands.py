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

        # For Ghostty terminal, add working directory flag
        if class_name == "com.mitchellh.ghostty" and working_dir:
            # Properly escape the path for shell safety
            escaped_dir = shlex.quote(working_dir)
            return f"{base_command} --working-directory={escaped_dir}"
        
        # Future terminal support can be added here with similar patterns:
        # elif class_name == "alacritty" and working_dir:
        #     escaped_dir = shlex.quote(working_dir)
        #     return f"{base_command} --working-directory={escaped_dir}"
        # elif class_name == "kitty" and working_dir:
        #     escaped_dir = shlex.quote(working_dir)
        #     return f"{base_command} --directory={escaped_dir}"

        return base_command