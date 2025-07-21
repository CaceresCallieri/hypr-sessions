#!/usr/bin/env python3
"""
Register the native messaging host with the browser
"""

import os
import sys
import json
import shutil
from pathlib import Path

def get_absolute_path():
    """Get absolute path to the current directory"""
    return os.path.dirname(os.path.abspath(__file__))

def update_host_manifest():
    """Update the host manifest with correct absolute paths"""
    script_dir = get_absolute_path()
    manifest_path = os.path.join(script_dir, "hypr_sessions_host.json")
    native_host_path = os.path.join(script_dir, "native_host.py")
    
    # Make native_host.py executable
    os.chmod(native_host_path, 0o755)
    
    # Read current manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Update path to absolute path
    manifest["path"] = native_host_path
    
    # Write updated manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Updated manifest path to: {native_host_path}")
    return manifest_path

def register_firefox():
    """Register with Firefox/Zen Browser"""
    try:
        manifest_path = update_host_manifest()
        
        # Firefox native messaging directory
        firefox_dir = Path.home() / ".mozilla" / "native-messaging-hosts"
        firefox_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy manifest to Firefox directory
        dest_path = firefox_dir / "hypr_sessions_host.json"
        shutil.copy2(manifest_path, dest_path)
        
        print(f"Registered with Firefox: {dest_path}")
        return True
        
    except Exception as e:
        print(f"Error registering with Firefox: {e}")
        return False

def register_chrome():
    """Register with Chrome/Chromium-based browsers"""
    try:
        manifest_path = update_host_manifest()
        
        # Chrome native messaging directory
        chrome_dir = Path.home() / ".config" / "google-chrome" / "NativeMessagingHosts"
        chrome_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy manifest to Chrome directory
        dest_path = chrome_dir / "hypr_sessions_host.json"
        shutil.copy2(manifest_path, dest_path)
        
        print(f"Registered with Chrome: {dest_path}")
        return True
        
    except Exception as e:
        print(f"Error registering with Chrome: {e}")
        return False

def main():
    print("Registering Hyprland Session Manager native messaging host...")
    
    # Register with both browsers
    firefox_success = register_firefox()
    chrome_success = register_chrome()
    
    if firefox_success or chrome_success:
        print("\n✅ Native messaging host registered successfully!")
        print("\nNext steps:")
        print("1. Load the extension in your browser")
        print("2. Test the connection using the extension popup")
        print("3. Use hypr-sessions save/restore with browser support")
    else:
        print("\n❌ Failed to register native messaging host")
        sys.exit(1)

if __name__ == "__main__":
    main()