#!/usr/bin/env python3
"""
Test the native host with binary protocol (simulating browser)
"""

import json
import struct
import subprocess
import sys

def test_binary_protocol():
    """Test native host with binary protocol like browser uses"""
    print("Testing native host with binary protocol...")
    
    # Test message
    test_message = {"action": "ping"}
    message_json = json.dumps(test_message)
    message_bytes = message_json.encode('utf-8')
    message_length = len(message_bytes)
    
    # Create binary message (length + data)
    binary_message = struct.pack('<I', message_length) + message_bytes
    
    try:
        # Run native host with binary input
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(script_dir, "..", "..")
        native_host_path = os.path.join(project_root, "browser_extension", "native_host.py")
        
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
            
            if response.get("status") == "pong":
                print("✅ Binary protocol test PASSED")
                return True
            else:
                print("❌ Unexpected response")
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
    test_binary_protocol()