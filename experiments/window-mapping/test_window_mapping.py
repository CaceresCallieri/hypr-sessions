#!/usr/bin/env python3
"""
Test script to investigate how to map Zen browser windows to session data
"""

from session_save.zen_session_reader import ZenSessionReader
import json

def analyze_window_data():
    """Analyze what identifying data is available in session windows"""
    reader = ZenSessionReader(debug=True)
    
    if not reader.is_available():
        print("❌ Zen session reader not available")
        return
    
    session_data = reader.get_current_session_data()
    if not session_data:
        print("❌ Could not get session data")
        return
    
    print("🔍 Analyzing browser window data for identification:")
    print("=" * 60)
    
    windows = session_data.get('windows', [])
    for i, window in enumerate(windows):
        print(f"\n🪟 Window {i}:")
        
        # Check what identifying information is available
        interesting_keys = ['screenX', 'screenY', 'width', 'height', 'sizemode', 
                           'title', 'tabs', 'selected', 'windowId', 'id']
        
        for key in interesting_keys:
            if key in window:
                value = window[key]
                if key == 'tabs':
                    print(f"   {key}: {len(value)} tabs")
                    # Show first tab for identification
                    if value:
                        first_tab = value[0]
                        entries = first_tab.get('entries', [])
                        if entries:
                            current_entry = entries[first_tab.get('index', 1) - 1]
                            print(f"      First tab: {current_entry.get('title', 'No title')[:50]}...")
                elif key in ['screenX', 'screenY', 'width', 'height']:
                    print(f"   {key}: {value}")
                else:
                    print(f"   {key}: {value}")
    
    print("\n🎯 Summary:")
    print(f"   Total windows in session: {len(windows)}")
    return windows

if __name__ == '__main__':
    analyze_window_data()