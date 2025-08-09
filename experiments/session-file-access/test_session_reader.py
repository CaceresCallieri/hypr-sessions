#!/usr/bin/env python3
"""
Test script to verify Zen browser sessionstore.jsonlz4 files contain current tab data
This is a proof-of-concept before implementing the full feature
"""

import json
import os
import glob
from pathlib import Path

def find_zen_profiles():
    """Find all Zen browser profiles"""
    zen_base = Path.home() / '.zen'
    if not zen_base.exists():
        return []
    
    profiles = []
    for profile_dir in zen_base.iterdir():
        if profile_dir.is_dir() and not profile_dir.name.startswith('.'):
            session_file = profile_dir / 'sessionstore-backups' / 'recovery.jsonlz4'
            if session_file.exists():
                profiles.append({
                    'name': profile_dir.name,
                    'path': profile_dir,
                    'session_file': session_file
                })
    return profiles

def test_lz4_decompression(session_file):
    """Test if we can decompress the session file using Python"""
    try:
        # Try importing lz4 (might not be installed yet)
        import lz4.block
        
        with open(session_file, 'rb') as f:
            # Mozilla files start with 'mozLz40\0' (8 bytes)
            header = f.read(8)
            print(f"File header: {header}")
            
            if header != b'mozLz40\0':
                print("❌ Not a Mozilla LZ4 file (wrong header)")
                return None
                
            # Decompress the rest
            compressed_data = f.read()
            decompressed = lz4.block.decompress(compressed_data)
            
            # Parse JSON
            session_data = json.loads(decompressed.decode('utf-8'))
            return session_data
            
    except ImportError:
        print("❌ lz4 library not installed - run: pip install lz4")
        return None
    except Exception as e:
        print(f"❌ Decompression failed: {e}")
        return None

def analyze_session_data(session_data):
    """Analyze the structure of session data"""
    if not session_data:
        return
        
    print(f"\n📊 Session Analysis:")
    print(f"   Windows: {len(session_data.get('windows', []))}")
    
    for i, window in enumerate(session_data.get('windows', [])):
        tabs = window.get('tabs', [])
        print(f"   Window {i+1}: {len(tabs)} tabs")
        
        # Show first few tabs as examples
        for j, tab in enumerate(tabs[:3]):
            entries = tab.get('entries', [])
            if entries:
                current_entry = entries[tab.get('index', 1) - 1]
                url = current_entry.get('url', 'No URL')
                title = current_entry.get('title', 'No title')
                pinned = tab.get('pinned', False)
                print(f"      Tab {j+1}: {'📌' if pinned else '  '} {title[:50]}...")
                print(f"              {url[:80]}...")
        
        if len(tabs) > 3:
            print(f"      ... and {len(tabs) - 3} more tabs")

def main():
    print("🔍 Testing Zen Browser Session File Accessibility")
    print("=" * 50)
    
    # Find profiles
    profiles = find_zen_profiles()
    if not profiles:
        print("❌ No Zen browser profiles found")
        return
    
    print(f"✅ Found {len(profiles)} Zen profiles:")
    for profile in profiles:
        print(f"   - {profile['name']}")
        print(f"     Session file: {profile['session_file']}")
        print(f"     File size: {profile['session_file'].stat().st_size:,} bytes")
    
    # Test the most recent profile (largest file)
    main_profile = max(profiles, key=lambda p: p['session_file'].stat().st_size)
    print(f"\n🧪 Testing main profile: {main_profile['name']}")
    
    session_data = test_lz4_decompression(main_profile['session_file'])
    analyze_session_data(session_data)
    
    # Test if this matches what we expect
    if session_data:
        windows = session_data.get('windows', [])
        total_tabs = sum(len(w.get('tabs', [])) for w in windows)
        print(f"\n✅ Successfully extracted {total_tabs} tabs from {len(windows)} windows")
        print("🎯 This approach is viable for the hypr-sessions project!")
    else:
        print("\n❌ Could not extract session data - approach may not work")

if __name__ == '__main__':
    main()