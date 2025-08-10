"""
Browser-specific functionality for session capture and restoration
Supports Zen Browser tab management via native messaging extension
"""

import json
import os
import struct
import subprocess
import time
from pathlib import Path


class BrowserHandler:
    def __init__(self, debug=False):
        self.debug = debug
        self.supported_browsers = [
            "zen-alpha",  # Zen Browser (alpha)
            "zen",  # Zen Browser (stable)
            "firefox",  # Firefox (future support)
        ]

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
        is_zen = class_name in ["zen-alpha", "zen"]
        self.debug_print(f"Checking window class '{class_name}' -> is_zen: {is_zen}")
        return is_zen

    def get_browser_type(self, window_data):
        """Determine the specific browser type from window data"""
        class_name = window_data.get("class", "").lower()

        if class_name in ["zen-alpha", "zen"]:
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

    def test_extension_availability(self):
        """Test if browser extension is available and responsive"""
        self.debug_print("Testing extension availability")

        try:
            # Get the path to the native host script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, "..")
            native_host_path = os.path.join(
                project_root, "browser_extension", "native_host.py"
            )

            if not os.path.exists(native_host_path):
                self.debug_print(f"Native host script not found at: {native_host_path}")
                return False

            # Test basic communication
            test_message = {"action": "ping"}
            message_json = json.dumps(test_message)
            message_bytes = message_json.encode("utf-8")
            message_length = len(message_bytes)
            binary_message = struct.pack("<I", message_length) + message_bytes

            process = subprocess.Popen(
                ["python3", native_host_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout, stderr = process.communicate(input=binary_message, timeout=3)

            if len(stdout) >= 4:
                response_length = struct.unpack("<I", stdout[:4])[0]
                response_data = stdout[4 : 4 + response_length]
                response = json.loads(response_data.decode("utf-8"))

                if response.get("status") == "pong":
                    self.debug_print("Extension communication test successful")
                    return True

            return False

        except Exception as e:
            self.debug_print(f"Extension availability test failed: {e}")
            return False

    def create_tab_session_file(self, session_name, tabs_data):
        """Create a file with tab data for later restoration"""
        self.debug_print(f"Creating tab session file for: {session_name}")

        try:
            # Get session directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, "..")
            sessions_dir = os.path.expanduser("~/.config/hypr-sessions")

            # Create tab session file
            tab_file = os.path.join(sessions_dir, f"{session_name}-tabs.json")

            tab_session_data = {
                "session_name": session_name,
                "timestamp": time.time(),
                "tabs": tabs_data,
                "browser_type": "zen",
            }

            with open(tab_file, "w") as f:
                json.dump(tab_session_data, f, indent=2)

            self.debug_print(f"Created tab session file: {tab_file}")
            return tab_file

        except Exception as e:
            self.debug_print(f"Error creating tab session file: {e}")
            return None

    def capture_browser_tabs(self, session_name, browser_type="zen"):
        """Capture tabs from browser via extension using file-based trigger"""
        self.debug_print(f"Attempting to capture tabs for session: {session_name}")

        # Create trigger file for extension to detect
        if self.create_capture_trigger(session_name):
            self.debug_print("Created capture trigger file")

            # Wait for extension to process trigger and create tab file
            tab_file = self.wait_for_tab_file(session_name, timeout=10)
            if tab_file:
                self.debug_print(f"Tab file found: {tab_file}")
                # Clean up trigger file
                self.cleanup_trigger_file(session_name)
                return True
            else:
                self.debug_print("Tab file not created by extension")
                # Clean up trigger file even if failed
                self.cleanup_trigger_file(session_name)
                return False
        else:
            self.debug_print("Failed to create capture trigger")
            return False

    def send_capture_request(self, session_name, browser_type="zen"):
        """Send capture request directly to browser extension via native messaging"""
        try:
            # Get the path to the native host script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, "..")
            native_host_path = os.path.join(
                project_root, "browser_extension", "native_host.py"
            )

            if not os.path.exists(native_host_path):
                self.debug_print(f"Native host script not found at: {native_host_path}")
                return False

            # Create capture message
            capture_message = {
                "action": "capture_tabs",
                "session_name": session_name,
                "browser_type": browser_type,
                "timestamp": int(time.time()),
            }

            message_json = json.dumps(capture_message)
            message_bytes = message_json.encode("utf-8")
            message_length = len(message_bytes)
            binary_message = struct.pack("<I", message_length) + message_bytes

            # Send to native host (which should forward to extension)
            process = subprocess.Popen(
                ["python3", native_host_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout, stderr = process.communicate(input=binary_message, timeout=3)

            # The native host will acknowledge, but the real work happens in the browser
            self.debug_print("Capture request sent via native messaging")
            return True

        except Exception as e:
            self.debug_print(f"Error sending capture request: {e}")
            return False

    def create_capture_trigger(self, session_name):
        """Create a trigger file that the extension can detect"""
        try:
            # Create trigger in a location both Python and extension can access
            downloads_dir = os.path.expanduser("~/Downloads")
            trigger_file = os.path.join(
                downloads_dir, f".hypr-capture-{session_name}.trigger"
            )

            trigger_data = {
                "action": "capture_tabs",
                "session_name": session_name,
                "timestamp": time.time(),
                "browser_type": "zen",
            }

            with open(trigger_file, "w") as f:
                json.dump(trigger_data, f)

            self.debug_print(f"Created trigger file: {trigger_file}")
            return True

        except Exception as e:
            self.debug_print(f"Error creating trigger file: {e}")
            return False

    def cleanup_trigger_file(self, session_name):
        """Remove the trigger file"""
        try:
            downloads_dir = os.path.expanduser("~/Downloads")
            trigger_file = os.path.join(
                downloads_dir, f".hypr-capture-{session_name}.trigger"
            )

            if os.path.exists(trigger_file):
                os.remove(trigger_file)
                self.debug_print(f"Cleaned up trigger file: {trigger_file}")

        except Exception as e:
            self.debug_print(f"Error cleaning up trigger file: {e}")

    def wait_for_keyboard_shortcut_file(self, timeout=10):
        """Wait for keyboard shortcut extension to create hypr-session-tabs file"""
        import glob
        import time

        downloads_dir = os.path.expanduser("~/Downloads")
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
        for attempt in range(timeout * 4):  # Check every 0.25 seconds
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

            time.sleep(0.25)

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
                "keyboard_shortcut": tab_data.get("keyboardShortcut", "Alt+U"),
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

            # Send Alt+U keyboard shortcut using hyprctl sendshortcut (no focus needed)
            self.debug_print(
                "Sending Alt+U keyboard shortcut to capture tabs via sendshortcut"
            )
            shortcut_result = subprocess.run(
                [
                    "hyprctl",
                    "dispatch",
                    "sendshortcut",
                    f"ALT,u,address:{window_address}",
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
            tab_file = self.wait_for_keyboard_shortcut_file(timeout=10)
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

        base_command = "zen-browser"
        if browser_type == "firefox":
            base_command = "firefox"
        elif browser_type != "zen":
            self.debug_print(
                f"Unknown browser type: {browser_type}, using zen as default"
            )

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
