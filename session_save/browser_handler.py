"""
Browser-specific functionality for session capture and restoration
Supports Zen Browser tab management via native messaging extension
"""

import json
import os
import subprocess
import time
import struct
from pathlib import Path


class BrowserHandler:
    def __init__(self, debug=False):
        self.debug = debug
        self.supported_browsers = [
            "zen-alpha",  # Zen Browser (alpha)
            "zen",        # Zen Browser (stable)
            "firefox",    # Firefox (future support)
        ]
    
    def debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG BrowserHandler] {message}")
    
    def is_browser_window(self, window_data):
        """Check if a window is running a supported browser"""
        class_name = window_data.get("class", "").lower()
        is_browser = class_name in self.supported_browsers
        self.debug_print(f"Checking window class '{class_name}' -> is_browser: {is_browser}")
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
        self.debug_print(f"Getting session info for browser window: {window_data.get('class')}")
        
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
                "capture_method": "basic"  # Will be upgraded to "extension" if available
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
        
        # Extract potential URL from window title (browsers often show URL in title)
        # This is a fallback when extension is not available
        basic_tab = {
            "title": title,
            "url": self.extract_url_from_title(title),
            "active": True,
            "pinned": False,
            "index": 0
        }
        
        return {
            "browser_type": browser_type,
            "tabs": [basic_tab] if basic_tab["url"] else [],
            "capture_method": "fallback",
            "has_extension": False
        }
    
    def extract_url_from_title(self, title):
        """Try to extract URL from browser window title"""
        if not title:
            return None
            
        # Common patterns in browser titles
        # "Page Title - Mozilla Firefox"
        # "GitHub - Mozilla Firefox" 
        # "https://example.com - Zen Browser"
        
        # Look for URLs in title
        if "http" in title.lower():
            parts = title.split()
            for part in parts:
                if part.startswith(("http://", "https://")):
                    return part.rstrip(" -")
        
        # If no URL found, return None (we'll rely on extension for actual URLs)
        return None
    
    def communicate_with_native_host(self, message, timeout=5):
        """Communicate with the native messaging host"""
        self.debug_print(f"Attempting to communicate with native host: {message}")
        
        try:
            # Get the path to the native host script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, "..")
            native_host_path = os.path.join(project_root, "browser_extension", "native_host.py")
            
            if not os.path.exists(native_host_path):
                self.debug_print(f"Native host script not found at: {native_host_path}")
                return None
            
            # Prepare the message
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')
            message_length = len(message_bytes)
            
            # Create binary message (length + data) for native messaging protocol
            binary_message = struct.pack('<I', message_length) + message_bytes
            
            # Execute the native host
            process = subprocess.Popen(
                ["python3", native_host_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send message and get response
            stdout, stderr = process.communicate(input=binary_message, timeout=timeout)
            
            self.debug_print(f"Native host stderr: {stderr.decode()}")
            
            # Parse binary response
            if len(stdout) >= 4:
                response_length = struct.unpack('<I', stdout[:4])[0]
                response_data = stdout[4:4+response_length]
                response = json.loads(response_data.decode('utf-8'))
                self.debug_print(f"Native host response: {response}")
                return response
            else:
                self.debug_print("No valid response from native host")
                return None
                
        except subprocess.TimeoutExpired:
            self.debug_print("Native host communication timed out")
            process.kill()
            return None
        except Exception as e:
            self.debug_print(f"Error communicating with native host: {e}")
            return None
    
    def capture_browser_tabs(self, session_name, browser_type="zen"):
        """Capture tabs from browser via extension"""
        self.debug_print(f"Attempting to capture tabs for session: {session_name}")
        
        # Send capture request to native host
        capture_message = {
            "action": "capture_tabs",
            "session_name": session_name,
            "browser_type": browser_type,
            "timestamp": int(time.time())
        }
        
        response = self.communicate_with_native_host(capture_message)
        
        if response and response.get("status") == "capture_requested":
            self.debug_print("Tab capture request sent successfully")
            return True
        else:
            self.debug_print("Failed to send tab capture request")
            return False
    
    def get_enhanced_browser_session_info(self, window_data, session_name):
        """Get enhanced session info with tab data via extension"""
        self.debug_print(f"Getting enhanced session info for: {window_data.get('class')}")
        
        # Start with basic session info
        session_info = self.get_browser_session_info(window_data)
        if not session_info:
            return None
        
        # Try to capture tabs via extension
        browser_type = session_info["browser_type"]
        if self.capture_browser_tabs(session_name, browser_type):
            session_info["has_extension"] = True
            session_info["capture_method"] = "extension"
            self.debug_print("Successfully requested tab capture via extension")
        else:
            # Fallback to basic session data
            fallback_data = self.create_basic_session_data(window_data)
            session_info.update(fallback_data)
            self.debug_print("Falling back to basic session data")
        
        return session_info

    def get_restore_command(self, browser_data, browser_type="zen"):
        """Generate restore command for browser"""
        self.debug_print(f"Generating restore command for browser type: {browser_type}")
        
        if browser_type == "zen":
            return "zen-browser"
        elif browser_type == "firefox":
            return "firefox"
        else:
            self.debug_print(f"Unknown browser type: {browser_type}, using zen as default")
            return "zen-browser"