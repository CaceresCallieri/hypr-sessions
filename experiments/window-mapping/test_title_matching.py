#!/usr/bin/env python3
"""
Test title-based window matching between hyprctl and session data
Backup method for window-to-tab mapping
"""

from session_save.zen_session_reader import ZenSessionReader
import subprocess
import json

def get_zen_windows_hyprctl():
    """Get Zen browser windows from hyprctl with titles"""
    try:
        result = subprocess.run(['hyprctl', 'clients', '-j'], 
                              capture_output=True, text=True, check=True)
        clients = json.loads(result.stdout)
        
        zen_windows = []
        for client in clients:
            class_name = client.get('class', '').lower()
            if class_name in ['zen-alpha', 'zen', 'zen-browser']:
                zen_windows.append({
                    'address': client.get('address'),
                    'pid': client.get('pid'),
                    'title': client.get('title', ''),
                    'class': client.get('class'),
                    'workspace': client.get('workspace', {}).get('id', -1)
                })
        return zen_windows
    except Exception as e:
        print(f"Error getting hyprctl data: {e}")
        return []

def extract_tab_title_from_window_title(window_title):
    """Extract the actual tab title from Zen's window title format"""
    # Zen format: "Tab Title — Zen Browser" or "Tab Title - Zen Browser"
    if ' — Zen Browser' in window_title:
        return window_title.split(' — Zen Browser')[0].strip()
    elif ' - Zen Browser' in window_title:
        return window_title.split(' - Zen Browser')[0].strip()
    else:
        return window_title.strip()

def get_active_tab_title(session_window):
    """Get the title of the active tab in a session window"""
    tabs = session_window.get('tabs', [])
    if not tabs:
        return None
    
    # Try to find selected tab
    selected_index = session_window.get('selected', 1) - 1  # 1-based to 0-based
    if 0 <= selected_index < len(tabs):
        tab = tabs[selected_index]
    else:
        tab = tabs[0]  # Fallback to first tab
    
    entries = tab.get('entries', [])
    if entries:
        current_entry = entries[tab.get('index', 1) - 1]
        return current_entry.get('title', '')
    
    return None

def match_window_by_title(target_window_address):
    """
    Match a specific hyprctl window to session data by title
    
    Returns:
        dict: Session window data if matched, None otherwise
    """
    hyprctl_windows = get_zen_windows_hyprctl()
    target_window = None
    
    # Find target window
    for window in hyprctl_windows:
        if window['address'] == target_window_address:
            target_window = window
            break
    
    if not target_window:
        return None
    
    # Get session data
    reader = ZenSessionReader(debug=False)
    session_data = reader.get_current_session_data()
    if not session_data:
        return None
    
    # Extract tab title from window title
    extracted_tab_title = extract_tab_title_from_window_title(target_window['title'])
    
    # Match against session windows
    session_windows = session_data.get('windows', [])
    for session_window in session_windows:
        active_tab_title = get_active_tab_title(session_window)
        if active_tab_title:
            # Check for title match
            if extracted_tab_title.lower() in active_tab_title.lower() or \
               active_tab_title.lower() in extracted_tab_title.lower():
                return session_window
    
    return None

def test_title_matching():
    """Test title matching functionality"""
    print("🎯 Testing Title-Based Window Matching (Backup Method)")
    print("=" * 55)
    
    hyprctl_windows = get_zen_windows_hyprctl()
    reader = ZenSessionReader(debug=False)
    session_data = reader.get_current_session_data()
    
    if not session_data:
        print("❌ No session data available")
        return
    
    session_windows = session_data.get('windows', [])
    
    print(f"📊 Available data:")
    print(f"   Hyprctl windows: {len(hyprctl_windows)}")
    print(f"   Session windows: {len(session_windows)}")
    
    print(f"\n🧪 Testing matches:")
    matches = 0
    
    for i, hypr_window in enumerate(hyprctl_windows):
        extracted_title = extract_tab_title_from_window_title(hypr_window['title'])
        session_match = match_window_by_title(hypr_window['address'])
        
        print(f"\n   Window {i}: {extracted_title[:40]}...")
        if session_match:
            active_tab = get_active_tab_title(session_match)
            tab_count = len(session_match.get('tabs', []))
            print(f"      ✅ Matched to session window with {tab_count} tabs")
            print(f"      Active tab: {active_tab[:50]}...")
            matches += 1
        else:
            print(f"      ❌ No match (generic title like 'Google', 'YouTube')")
    
    print(f"\n📊 Results: {matches}/{len(hyprctl_windows)} windows matched")
    print("⚠️  Limited by generic site titles - use window closing method for accuracy")

if __name__ == '__main__':
    test_title_matching()