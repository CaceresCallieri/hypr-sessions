#!/usr/bin/env python3
"""
Setup script for hypr-sessions browser integration
This script registers the native messaging host and provides setup instructions
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🔧 Setting up Hyprland Session Manager browser integration...")
    
    # Get script directory
    script_dir = Path(__file__).parent
    extension_dir = script_dir / "browser_extension"
    register_script = extension_dir / "register_host.py"
    
    if not register_script.exists():
        print(f"❌ Register script not found: {register_script}")
        sys.exit(1)
    
    print("📋 Browser Integration Setup Steps:")
    print()
    
    print("1. 📁 Registering native messaging host...")
    try:
        result = subprocess.run([sys.executable, str(register_script)], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Native messaging host registered successfully")
            print(result.stdout)
        else:
            print("   ❌ Failed to register native messaging host")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"   ❌ Error running register script: {e}")
        return False
    
    print()
    print("2. 🔌 Load extension in your browser:")
    print(f"   - Open Zen Browser or Firefox")
    print(f"   - Navigate to about:debugging")
    print(f"   - Click 'This Firefox' (or 'This Browser')")
    print(f"   - Click 'Load Temporary Add-on'")
    print(f"   - Select: {extension_dir / 'manifest.json'}")
    print()
    
    print("3. 🧪 Test the extension:")
    print(f"   - Click the extension icon in the toolbar")
    print(f"   - Click 'Test Connection' - should show green status")
    print(f"   - Click 'Manual Tab Capture' to test tab collection")
    print()
    
    print("4. 🚀 Use with hypr-sessions:")
    print(f"   - Save session: ./hypr-sessions.py save test-session")
    print(f"   - Restore session: ./hypr-sessions.py restore test-session")
    print(f"   - Browser tabs will be captured during save and restored during session restore")
    print()
    
    print("🎉 Setup complete! Browser integration is ready to use.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)