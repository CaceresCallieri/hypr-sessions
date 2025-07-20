#!/usr/bin/env python3
"""
Native messaging host for hypr-sessions browser extension
Handles communication between Zen Browser extension and Python session manager
"""

import json
import struct
import sys
import os
from pathlib import Path


class NativeHost:
    def __init__(self, debug=False):
        self.debug = debug
        
    def debug_print(self, message):
        """Print debug message to stderr (stdout is reserved for messaging)"""
        if self.debug:
            print(f"[DEBUG NativeHost] {message}", file=sys.stderr)
    
    def read_message(self):
        """Read a message from stdin using native messaging protocol"""
        try:
            # Check if stdin is a TTY (testing with text input)
            if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                line = sys.stdin.readline().strip()
                if not line:
                    return None
                message = json.loads(line)
                self.debug_print(f"Received text message: {message}")
                return message
            
            # Binary protocol for browser communication
            raw_length = sys.stdin.buffer.read(4)
            if not raw_length or len(raw_length) != 4:
                return None
            
            message_length = struct.unpack('<I', raw_length)[0]
            self.debug_print(f"Reading binary message of length: {message_length}")
            
            # Sanity check message length
            if message_length > 1024 * 1024:  # 1MB limit
                self.debug_print(f"Message too large: {message_length}")
                return None
            
            # Read the actual message
            message_data = sys.stdin.buffer.read(message_length)
            if not message_data or len(message_data) != message_length:
                return None
                
            message = json.loads(message_data.decode('utf-8'))
            self.debug_print(f"Received binary message: {message}")
            return message
            
        except (json.JSONDecodeError, struct.error, UnicodeDecodeError) as e:
            self.debug_print(f"Error reading message: {e}")
            return None
    
    def send_message(self, message):
        """Send a message to stdout using native messaging protocol"""
        try:
            message_json = json.dumps(message)
            self.debug_print(f"Sending message: {message}")
            
            # Check if stdout is a TTY (testing mode)
            if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
                # Text mode for testing
                print(message_json)
                sys.stdout.flush()
            else:
                # Binary protocol for browser
                message_bytes = message_json.encode('utf-8')
                message_length = len(message_bytes)
                
                # Send length first (4 bytes, little endian)
                sys.stdout.buffer.write(struct.pack('<I', message_length))
                # Send the message
                sys.stdout.buffer.write(message_bytes)
                sys.stdout.buffer.flush()
            
        except Exception as e:
            self.debug_print(f"Error sending message: {e}")
    
    def handle_message(self, message):
        """Process incoming message and return response"""
        if not message:
            return {"error": "Invalid message"}
        
        action = message.get("action")
        self.debug_print(f"Handling action: {action}")
        
        if action == "ping":
            return {"status": "pong", "message": "Native host is working"}
            
        elif action == "capture_tabs":
            # For now, just acknowledge the request
            # Later this will trigger actual tab capture
            return {
                "status": "capture_requested", 
                "session_name": message.get("session_name", "unknown")
            }
            
        elif action == "restore_tabs":
            # For now, just acknowledge the request
            # Later this will handle tab restoration
            return {
                "status": "restore_requested",
                "session_name": message.get("session_name", "unknown")
            }
            
        else:
            return {"error": f"Unknown action: {action}"}
    
    def run(self):
        """Main message loop"""
        self.debug_print("Native host starting...")
        
        try:
            while True:
                message = self.read_message()
                if message is None:
                    break
                    
                response = self.handle_message(message)
                self.send_message(response)
                
        except KeyboardInterrupt:
            self.debug_print("Received interrupt signal")
        except Exception as e:
            self.debug_print(f"Unexpected error: {e}")
        
        self.debug_print("Native host shutting down")


def main():
    # Check for debug flag
    debug = "--debug" in sys.argv
    
    host = NativeHost(debug=debug)
    host.run()


if __name__ == "__main__":
    main()