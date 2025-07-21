#!/usr/bin/env python3
"""
Test tab capture functionality with native host
"""

import json
import struct
import subprocess
import sys
import os

def test_tab_capture():
    """Test native host tab capture communication"""
    print("Testing tab capture communication...")
    
    # Test message for tab capture
    test_message = {
        "action": "capture_tabs",
        "session_name": "test_session",
        "browser_type": "zen",
        "timestamp": 1234567890
    }
    
    message_json = json.dumps(test_message)
    message_bytes = message_json.encode('utf-8')
    message_length = len(message_bytes)
    
    # Create binary message (length + data)
    binary_message = struct.pack('<I', message_length) + message_bytes
    
    try:
        # Get path to native host
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(script_dir, "..", "..")
        native_host_path = os.path.join(project_root, "browser_extension", "native_host.py")
        
        # Run native host with binary input
        process = subprocess.Popen(
            [sys.executable, native_host_path, "--debug"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Send binary message
        stdout, stderr = process.communicate(input=binary_message, timeout=5)
        
        print("STDERR (debug output):")
        print(stderr.decode())
        
        print("\nSTDOUT (binary response):")
        print(repr(stdout))
        
        # Try to parse binary response
        if len(stdout) >= 4:
            response_length = struct.unpack('<I', stdout[:4])[0]
            response_data = stdout[4:4+response_length]
            response = json.loads(response_data.decode('utf-8'))
            print(f"\nParsed response: {response}")
            
            expected_status = "capture_requested"
            if response.get("status") == expected_status:
                print("✅ Tab capture communication test PASSED")
                print(f"   Session: {response.get('session_name')}")
                print(f"   Browser: {response.get('browser_type')}")
                print(f"   Message: {response.get('message')}")
                return True
            else:
                print(f"❌ Unexpected status: {response.get('status')}")
                return False
        else:
            print("❌ No valid binary response received")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_tab_capture()