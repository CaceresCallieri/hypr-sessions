"""
Browser-specific functionality for session capture and restoration
Supports Zen Browser tab management via keyboard shortcut extension
"""

import json
import os
import subprocess
import time
from config import get_config


class BrowserHandler:
    def __init__(self, debug=False):
        self.debug = debug
        self.config = get_config()
        self.supported_browsers = self.config.supported_browsers

    def debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG BrowserHandler] {message}")

    def is_browser_window(self, window_data):
        """Check if a window is running a supported browser"""
        class_name = window_data.get("class", "").lower()
        is_browser = class_name in self.supported_browsers
        self.debug_print(
            f"Checking window class '{class_name}' -> is_browser: {is_browser}"
        )
        return is_browser

    def is_zen_browser_window(self, window_data):
        """Check if a window is specifically running Zen Browser"""
        class_name = window_data.get("class", "").lower()
        zen_browsers = {"zen-alpha", "zen"}
        is_zen = class_name in zen_browsers
        self.debug_print(f"Checking window class '{class_name}' -> is_zen: {is_zen}")
        return is_zen

    def get_browser_type(self, window_data):
        """Determine the specific browser type from window data"""
        class_name = window_data.get("class", "").lower()

        zen_browsers = {"zen-alpha", "zen"}
        if class_name in zen_browsers:
            return "zen"
        elif class_name == "firefox":
            return "firefox"
        else:
            return "unknown"

    def get_browser_session_info(self, window_data):
        """Extract basic session information from a browser window"""
        self.debug_print(
            f"Getting session info for browser window: {window_data.get('class')}"
        )

        try:
            browser_type = self.get_browser_type(window_data)
            pid = window_data.get("pid")
            title = window_data.get("title", "")

            session_data = {
                "browser_type": browser_type,
                "window_title": title,
                "pid": pid,
                "tabs": [],  # Will be populated later via native messaging
                "has_extension": False,  # Will be determined during tab capture
                "capture_method": "basic",  # Will be upgraded to "extension" if available
            }

            self.debug_print(f"Browser session info: {session_data}")
            return session_data

        except Exception as e:
            self.debug_print(f"Error getting browser session info: {e}")
            return None

    def create_basic_session_data(self, window_data):
        """Create basic session data for browser without extension support"""
        self.debug_print("Creating basic session data (no extension)")

        browser_type = self.get_browser_type(window_data)
        title = window_data.get("title", "")

        return {
            "browser_type": browser_type,
            "tabs": [],  # No tab data available without extension
            "capture_method": "fallback",
            "has_extension": False,
            "note": "Extension required for tab capture",
        }

    def wait_for_keyboard_shortcut_file(self, timeout=None):
        """Wait for keyboard shortcut extension to create hypr-session-tabs file"""
        import glob
        import time

        if timeout is None:
            timeout = self.config.browser_tab_file_timeout
        
        downloads_dir = str(self.config.downloads_dir)
        self.debug_print(f"Monitoring {downloads_dir} for keyboard shortcut tab files")

        # Get initial file list to detect new files
        initial_files = set()
        try:
            pattern = os.path.join(downloads_dir, "hypr-session-tabs-*.json")
            initial_files = set(glob.glob(pattern))
            self.debug_print(f"Initial tab files: {len(initial_files)}")
        except Exception as e:
            self.debug_print(f"Error getting initial file list: {e}")

        # Wait for new file to appear  
        poll_interval = self.config.browser_tab_file_poll_interval
        max_attempts = int(timeout / poll_interval)
        for attempt in range(max_attempts):
            try:
                pattern = os.path.join(downloads_dir, "hypr-session-tabs-*.json")
                current_files = set(glob.glob(pattern))
                new_files = current_files - initial_files

                if new_files:
                    # Get the most recent file
                    newest_file = max(new_files, key=os.path.getctime)
                    self.debug_print(
                        f"Found new keyboard shortcut tab file: {newest_file}"
                    )

                    # Validate file has content
                    try:
                        with open(newest_file, "r") as f:
                            content = f.read().strip()
                            if content:
                                self.debug_print(
                                    f"File has content ({len(content)} chars)"
                                )
                                return newest_file
                    except Exception as e:
                        self.debug_print(f"Error reading file: {e}")

            except Exception as e:
                self.debug_print(f"Error checking for new files: {e}")

            time.sleep(poll_interval)

        self.debug_print(
            f"No keyboard shortcut tab file appeared after {timeout} seconds"
        )
        return None

    def load_keyboard_shortcut_tab_data(self, tab_file_path):
        """Load tab data from keyboard shortcut extension file"""
        try:
            with open(tab_file_path, "r") as f:
                tab_data = json.load(f)

            tabs = tab_data.get("tabs", [])
            self.debug_print(f"Loaded {len(tabs)} tabs from keyboard shortcut file")
            self.debug_print(
                f"Tab capture method: {tab_data.get('captureMethod', 'unknown')}"
            )
            self.debug_print(f"Window ID: {tab_data.get('windowId', 'unknown')}")

            return {
                "tabs": tabs,
                "capture_method": "keyboard_shortcut",
                "keyboard_shortcut": tab_data.get("keyboardShortcut", self.config.browser_keyboard_shortcut),
                "window_id": tab_data.get("windowId"),
                "timestamp": tab_data.get("timestamp"),
                "tab_count": len(tabs),
            }

        except Exception as e:
            self.debug_print(f"Error loading keyboard shortcut tab file: {e}")
            return None

    def capture_tabs_via_keyboard_shortcut(self, window_data):
        """Capture tabs by sending keyboard shortcut directly to browser window"""
        try:
            window_address = window_data.get("address")
            if not window_address:
                self.debug_print("No window address available for sendshortcut")
                return None

            # Send keyboard shortcut using hyprctl sendshortcut (no focus needed)
            shortcut = self.config.browser_keyboard_shortcut
            self.debug_print(
                f"Sending {shortcut} keyboard shortcut to capture tabs via sendshortcut"
            )
            # Convert shortcut format (Alt+U -> ALT,u)
            shortcut_parts = shortcut.lower().replace('+', ',')
            hyprctl_shortcut = f"{shortcut_parts},address:{window_address}"
            
            shortcut_result = subprocess.run(
                [
                    "hyprctl",
                    "dispatch",
                    "sendshortcut",
                    hyprctl_shortcut,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if shortcut_result.returncode != 0:
                self.debug_print(
                    f"Failed to send keyboard shortcut: {shortcut_result.stderr}"
                )
                # NOTE: For window manager agnostic support, could fallback to tools like:
                # - wtype (Wayland): wtype -M alt u
                # - xdotool (X11): xdotool key alt+u
                return None

            # Wait for extension to create tab file
            tab_file = self.wait_for_keyboard_shortcut_file()
            if tab_file:
                # Load tab data from file
                tab_data = self.load_keyboard_shortcut_tab_data(tab_file)
                if tab_data:
                    self.debug_print(
                        f"Successfully captured {tab_data['tab_count']} tabs via keyboard shortcut"
                    )
                    # Clean up the tab file
                    try:
                        os.remove(tab_file)
                        self.debug_print(f"Cleaned up tab file: {tab_file}")
                    except:
                        pass
                    return tab_data

            return None

        except Exception as e:
            self.debug_print(f"Error in keyboard shortcut tab capture: {e}")
            return None

    def get_enhanced_browser_session_info(self, window_data, session_name):
        """Get enhanced session info with tab data via keyboard shortcut extension"""
        self.debug_print(
            f"Getting enhanced session info for: {window_data.get('class')}"
        )

        # Start with basic session info
        session_info = self.get_browser_session_info(window_data)
        if not session_info:
            return None

        # Try to capture tabs via keyboard shortcut
        tab_data = self.capture_tabs_via_keyboard_shortcut(window_data)
        if tab_data:
            session_info.update(
                {
                    "tabs": tab_data["tabs"],
                    "has_extension": True,
                    "capture_method": tab_data["capture_method"],
                    "keyboard_shortcut": tab_data.get("keyboard_shortcut"),
                    "window_id": tab_data.get("window_id"),
                    "tab_count": tab_data["tab_count"],
                }
            )
            self.debug_print(
                f"Successfully captured {tab_data['tab_count']} tabs via keyboard shortcut"
            )
        else:
            # Fallback to basic session data
            fallback_data = self.create_basic_session_data(window_data)
            session_info.update(fallback_data)
            self.debug_print(
                "Falling back to basic session data - keyboard shortcut capture failed"
            )

        return session_info

    def get_restore_command(self, browser_data, browser_type="zen"):
        """Generate restore command for browser with tab URLs"""
        self.debug_print(f"Generating restore command for browser type: {browser_type}")

        # Get command from config
        zen_command = self.config.application_commands.get("zen", "zen-browser") 
        firefox_command = self.config.application_commands.get("firefox", "firefox")
        
        if browser_type == "zen":
            base_command = zen_command
        elif browser_type == "firefox":
            base_command = firefox_command
        else:
            self.debug_print(f"Unknown browser type: {browser_type}, using zen as default")
            base_command = zen_command

        # Add tab URLs as arguments if available
        tabs = browser_data.get("tabs", [])
        if tabs and len(tabs) > 0:
            # Extract URLs from tab data
            urls = []
            for tab in tabs:
                url = tab.get("url", "")
                if (
                    url
                    and not url.startswith("about:")
                    and not url.startswith("moz-extension:")
                ):
                    urls.append(url)

            if urls:
                self.debug_print(f"Adding {len(urls)} URLs to browser command")
                # Return command with URLs as arguments
                return f"{base_command} {' '.join(f'"{url}"' for url in urls)}"

        # Fallback to basic browser command
        return base_command
