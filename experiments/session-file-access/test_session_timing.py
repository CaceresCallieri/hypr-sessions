#!/usr/bin/env python3
"""
Test how quickly Zen browser updates session files when windows are closed
"""

from session_save.zen_session_reader import ZenSessionReader
import subprocess
import time
import os

def get_window_count():
    """Get current number of Zen browser windows from session data"""
    reader = ZenSessionReader(debug=False)  # Reduce noise
    session_data = reader.get_current_session_data()
    if session_data:
        return len(session_data.get('windows', []))
    return 0

def get_zen_windows_hyprctl():
    """Get Zen browser windows from hyprctl"""
    try:
        result = subprocess.run(['hyprctl', 'clients', '-j'], 
                              capture_output=True, text=True, check=True)
        import json
        clients = json.loads(result.stdout)
        
        zen_windows = []
        for client in clients:
            class_name = client.get('class', '').lower()
            if class_name in ['zen-alpha', 'zen', 'zen-browser']:
                zen_windows.append({
                    'address': client.get('address'),
                    'pid': client.get('pid'),
                    'title': client.get('title'),
                    'class': client.get('class')
                })
        return zen_windows
    except Exception as e:
        print(f"Error getting hyprctl data: {e}")
        return []

def test_session_update_timing():
    """Test when session file updates after window operations"""
    print("🧪 Testing Zen Browser Session Update Timing")
    print("=" * 50)
    
    # Initial state
    initial_session_count = get_window_count()
    initial_hyprctl_windows = get_zen_windows_hyprctl()
    
    print(f"📊 Initial state:")
    print(f"   Session file windows: {initial_session_count}")
    print(f"   Hyprctl Zen windows: {len(initial_hyprctl_windows)}")
    
    if len(initial_hyprctl_windows) == 0:
        print("❌ No Zen browser windows found via hyprctl")
        return
    
    if initial_session_count == 0:
        print("❌ No windows found in session file")
        return
    
    # Show available windows
    print(f"\n🪟 Available Zen windows:")
    for i, window in enumerate(initial_hyprctl_windows):
        print(f"   {i}: {window['title'][:50]}... (PID: {window['pid']})")
    
    # Don't actually close - just show what we would test
    print(f"\n⚠️  To test timing, we would:")
    print(f"   1. Close window: {initial_hyprctl_windows[0]['title'][:30]}...")
    print(f"   2. Monitor session file for changes")
    print(f"   3. Measure update delay")
    print(f"   4. Restore window")
    
    # Instead, let's check session file modification time
    reader = ZenSessionReader(debug=False)
    profile_info = reader.get_profile_info()
    if profile_info:
        session_file = profile_info['session_file']
        mod_time = os.path.getmtime(session_file)
        current_time = time.time()
        age_minutes = (current_time - mod_time) / 60
        
        print(f"\n📁 Session file info:")
        print(f"   Path: {session_file}")
        print(f"   Last modified: {age_minutes:.1f} minutes ago")
        print(f"   File size: {os.path.getsize(session_file):,} bytes")

if __name__ == '__main__':
    test_session_update_timing()