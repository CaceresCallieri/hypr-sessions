#!/usr/bin/env python3
"""
Test enhanced window matching strategies using available data
"""

import subprocess
import json
from session_save.zen_session_reader import ZenSessionReader

def get_detailed_window_info():
    """Get detailed window information from both sources"""
    
    # Get hyprctl data
    result = subprocess.run(['hyprctl', 'clients', '-j'], 
                          capture_output=True, text=True, check=True)
    hyprctl_windows = json.loads(result.stdout)
    
    zen_windows = []
    for client in hyprctl_windows:
        class_name = client.get('class', '').lower()
        if class_name in ['zen-alpha', 'zen', 'zen-browser']:
            zen_windows.append(client)
    
    # Get session data  
    reader = ZenSessionReader(debug=False)
    session_data = reader.get_current_session_data()
    session_windows = session_data.get('windows', []) if session_data else []
    
    print("🔍 Enhanced Window Matching Analysis")
    print("=" * 50)
    
    print(f"\n📊 Data Summary:")
    print(f"   Hyprctl Zen windows: {len(zen_windows)}")
    print(f"   Session windows: {len(session_windows)}")
    
    # Analyze what unique identifiers we have
    print(f"\n🏷️  Available Identification Data:")
    
    print(f"\n   From hyprctl:")
    print(f"   - Window title (changes with active tab)")
    print(f"   - Position & size")
    print(f"   - Workspace ID") 
    print(f"   - PID (same for all: {zen_windows[0]['pid'] if zen_windows else 'N/A'})")
    print(f"   - Window address/handle")
    
    print(f"\n   From session data:")
    for i, window in enumerate(session_windows[:3]):  # First 3 for analysis
        tabs = window.get('tabs', [])
        selected_idx = window.get('selected', 1) - 1
        
        print(f"   Session Window {i+1}:")
        if tabs:
            if 0 <= selected_idx < len(tabs):
                active_tab = tabs[selected_idx]
                entries = active_tab.get('entries', [])
                if entries:
                    current_entry = entries[active_tab.get('index', 1) - 1]
                    title = current_entry.get('title', '')
                    print(f"     Active tab title: {title[:40]}...")
            
            # Check for any window-level identifying info
            interesting_keys = ['screenX', 'screenY', 'width', 'height', 'title']
            for key in interesting_keys:
                if key in window:
                    print(f"     {key}: {window[key]}")
    
    # Try to find patterns for matching
    print(f"\n🎯 Matching Potential:")
    
    # Title-based matching
    potential_matches = 0
    for hypr_window in zen_windows:
        hypr_title = hypr_window.get('title', '')
        workspace = hypr_window.get('workspace', {}).get('id', -1)
        
        print(f"\n   Hyprctl: WS{workspace} - {hypr_title[:30]}...")
        
        # Try to find in session data
        for i, session_window in enumerate(session_windows):
            tabs = session_window.get('tabs', [])
            if tabs:
                selected_idx = session_window.get('selected', 1) - 1
                if 0 <= selected_idx < len(tabs):
                    active_tab = tabs[selected_idx]
                    entries = active_tab.get('entries', [])
                    if entries:
                        current_entry = entries[active_tab.get('index', 1) - 1]
                        session_title = current_entry.get('title', '')
                        
                        # Simple title matching
                        if hypr_title and session_title:
                            # Remove browser suffix from hyprctl title
                            clean_hypr_title = hypr_title.replace(' — Zen Browser', '').replace(' - Zen Browser', '')
                            
                            if clean_hypr_title.lower() in session_title.lower() or \
                               session_title.lower() in clean_hypr_title.lower():
                                print(f"      ✅ Potential match: Session Window {i+1}")
                                print(f"         Session title: {session_title[:30]}...")
                                potential_matches += 1
                                break
                else:
                    print(f"      ⚠️  No active tab in session window {i+1}")
    
    print(f"\n📊 Matching Results:")
    print(f"   Potential title matches: {potential_matches}/{len(zen_windows)}")
    
    if potential_matches < len(zen_windows):
        print(f"   ⚠️  {len(zen_windows) - potential_matches} windows couldn't be matched by title")
        print(f"   This confirms the limitation of title-based matching")

if __name__ == '__main__':
    get_detailed_window_info()