#!/usr/bin/env python3
"""
Test script to understand workspace-specific browser window detection
"""

import subprocess
import json
from session_save.zen_session_reader import ZenSessionReader

def get_current_workspace():
    """Get the current active workspace ID"""
    try:
        result = subprocess.run(['hyprctl', 'activeworkspace', '-j'], 
                              capture_output=True, text=True, check=True)
        workspace_data = json.loads(result.stdout)
        return workspace_data.get('id', -1)
    except Exception as e:
        print(f"Error getting current workspace: {e}")
        return -1

def get_zen_windows_by_workspace():
    """Get Zen browser windows organized by workspace"""
    try:
        result = subprocess.run(['hyprctl', 'clients', '-j'], 
                              capture_output=True, text=True, check=True)
        clients = json.loads(result.stdout)
        
        zen_windows_by_workspace = {}
        
        for client in clients:
            class_name = client.get('class', '').lower()
            if class_name in ['zen-alpha', 'zen', 'zen-browser']:
                workspace_id = client.get('workspace', {}).get('id', -1)
                
                if workspace_id not in zen_windows_by_workspace:
                    zen_windows_by_workspace[workspace_id] = []
                
                zen_windows_by_workspace[workspace_id].append({
                    'address': client.get('address'),
                    'pid': client.get('pid'),
                    'title': client.get('title', ''),
                    'class': client.get('class'),
                    'workspace': workspace_id,
                    'position': (client.get('at', [0, 0])[0], client.get('at', [0, 0])[1]),
                    'size': (client.get('size', [0, 0])[0], client.get('size', [0, 0])[1])
                })
        
        return zen_windows_by_workspace
    except Exception as e:
        print(f"Error getting Zen windows: {e}")
        return {}

def analyze_workspace_browser_situation():
    """Analyze the current workspace browser situation"""
    print("🔍 Workspace-Specific Browser Window Analysis")
    print("=" * 55)
    
    # Get current workspace
    current_workspace = get_current_workspace()
    print(f"📍 Current workspace: {current_workspace}")
    
    # Get all Zen windows by workspace
    zen_by_workspace = get_zen_windows_by_workspace()
    
    print(f"\n🪟 Zen Browser Windows by Workspace:")
    total_zen_windows = 0
    
    for workspace_id, windows in zen_by_workspace.items():
        total_zen_windows += len(windows)
        marker = "← CURRENT" if workspace_id == current_workspace else ""
        print(f"   Workspace {workspace_id}: {len(windows)} windows {marker}")
        
        for i, window in enumerate(windows):
            title_preview = window['title'][:40] + "..." if len(window['title']) > 40 else window['title']
            print(f"      {i+1}: {title_preview}")
            print(f"          Position: {window['position']}, Size: {window['size']}")
    
    # Get session data
    reader = ZenSessionReader(debug=False)
    session_data = reader.get_current_session_data()
    
    if session_data:
        session_windows = session_data.get('windows', [])
        print(f"\n📊 Session Data Summary:")
        print(f"   Total session windows: {len(session_windows)}")
        print(f"   Total hyprctl Zen windows: {total_zen_windows}")
        print(f"   Current workspace Zen windows: {len(zen_by_workspace.get(current_workspace, []))}")
    
    # Show the mapping challenge
    print(f"\n❓ The Challenge:")
    print(f"   We need to identify which {len(zen_by_workspace.get(current_workspace, []))} session window(s)")
    print(f"   correspond to the {len(zen_by_workspace.get(current_workspace, []))} Zen window(s) in workspace {current_workspace}")
    
    # Check if we can use process matching
    current_workspace_windows = zen_by_workspace.get(current_workspace, [])
    if current_workspace_windows:
        print(f"\n🔗 Potential Matching Strategies:")
        print(f"   1. Title matching (limited by generic titles)")
        print(f"   2. Window elimination (timing issues)")
        print(f"   3. Process inspection (all windows share same PID)")
        
        # Show PIDs
        pids = set(w['pid'] for w in current_workspace_windows)
        print(f"   PIDs in current workspace: {pids}")
    
    return current_workspace, zen_by_workspace.get(current_workspace, [])

if __name__ == '__main__':
    current_ws, current_windows = analyze_workspace_browser_situation()