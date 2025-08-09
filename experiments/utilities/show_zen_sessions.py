#!/usr/bin/env python3
"""
Display current Zen browser session data - perfect for before/after window closure comparison
"""

from session_save.zen_session_reader import ZenSessionReader
import time

def show_session_summary():
    """Show a clean summary of current Zen browser sessions"""
    print(f"🕐 {time.strftime('%H:%M:%S')} - Zen Browser Session Summary")
    print("=" * 60)
    
    reader = ZenSessionReader(debug=False)
    
    if not reader.is_available():
        print("❌ No Zen browser profiles found")
        return
    
    # Show profile info
    profile_info = reader.get_profile_info()
    print(f"📁 Profile: {profile_info['profile_name']}")
    print(f"   File size: {profile_info['file_size']:,} bytes")
    
    # Get session data
    session_data = reader.get_current_session_data()
    if not session_data:
        print("❌ Could not read session data")
        return
    
    windows = session_data.get('windows', [])
    print(f"\n📊 Total browser windows: {len(windows)}")
    
    total_tabs = 0
    
    for i, window in enumerate(windows):
        tabs = window.get('tabs', [])
        tab_count = len(tabs)
        total_tabs += tab_count
        
        print(f"\n🪟 Window {i+1}: {tab_count} tabs")
        
        # Show first tab as identifier
        if tabs:
            first_tab = tabs[0]
            entries = first_tab.get('entries', [])
            if entries:
                current_entry = entries[first_tab.get('index', 1) - 1]
                title = current_entry.get('title', 'No title')
                url = current_entry.get('url', 'No URL')
                print(f"   First tab: {title[:45]}...")
                print(f"   URL: {url[:65]}...")
                
            # Show selected tab if different
            selected_index = window.get('selected', 1) - 1
            if 0 <= selected_index < len(tabs) and selected_index != 0:
                selected_tab = tabs[selected_index]
                entries = selected_tab.get('entries', [])
                if entries:
                    current_entry = entries[selected_tab.get('index', 1) - 1]
                    title = current_entry.get('title', 'No title')
                    print(f"   Active tab: {title[:45]}...")
        
        # Create a signature for this window
        signature_parts = []
        if tabs:
            first_tab = tabs[0]
            entries = first_tab.get('entries', [])
            if entries:
                current_entry = entries[first_tab.get('index', 1) - 1]
                first_url = current_entry.get('url', '')
                signature_parts.append(first_url[:30])
        signature_parts.append(f"{tab_count} tabs")
        signature = " | ".join(signature_parts)
        print(f"   Signature: {signature}")
    
    print(f"\n📊 Summary: {len(windows)} windows, {total_tabs} total tabs")
    print("=" * 60)

if __name__ == '__main__':
    show_session_summary()