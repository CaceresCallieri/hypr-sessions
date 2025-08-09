#!/usr/bin/env python3
"""
Test process tree analysis for distinguishing Zen browser windows
Explore if we can match windows using process-level information
"""

import subprocess
import json
import os
import glob
from pathlib import Path

def get_zen_windows_with_pids():
    """Get Zen browser windows with their process information"""
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
                    'workspace': client.get('workspace', {}).get('id', -1),
                    'position': client.get('at', [0, 0]),
                    'size': client.get('size', [0, 0])
                })
        return zen_windows
    except Exception as e:
        print(f"Error getting Zen windows: {e}")
        return []

def analyze_process_tree(pid):
    """Analyze process tree structure for a given PID"""
    process_info = {
        'pid': pid,
        'children': [],
        'threads': [],
        'open_files': [],
        'cmdline': '',
        'environ_excerpt': {},
        'cwd': ''
    }
    
    try:
        # Get command line
        with open(f'/proc/{pid}/cmdline', 'rb') as f:
            cmdline_data = f.read()
            process_info['cmdline'] = cmdline_data.decode('utf-8', errors='ignore').replace('\x00', ' ').strip()
    except:
        pass
    
    try:
        # Get current working directory
        process_info['cwd'] = os.readlink(f'/proc/{pid}/cwd')
    except:
        pass
    
    try:
        # Get child processes
        result = subprocess.run(['pgrep', '-P', str(pid)], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            process_info['children'] = [int(p) for p in result.stdout.strip().split('\n') if p]
    except:
        pass
    
    try:
        # Get threads
        thread_dirs = glob.glob(f'/proc/{pid}/task/*')
        process_info['threads'] = [int(os.path.basename(t)) for t in thread_dirs]
    except:
        pass
    
    try:
        # Get some environment variables that might be window-specific
        with open(f'/proc/{pid}/environ', 'rb') as f:
            environ_data = f.read().decode('utf-8', errors='ignore')
            env_vars = environ_data.split('\x00')
            
            # Look for potentially window-specific env vars
            interesting_vars = ['DISPLAY', 'WAYLAND_DISPLAY', 'XDG_SESSION_ID', 
                              'WINDOWID', 'XAUTHORITY', 'XDG_RUNTIME_DIR']
            
            for var in env_vars:
                if '=' in var:
                    key, value = var.split('=', 1)
                    if key in interesting_vars or 'WINDOW' in key.upper():
                        process_info['environ_excerpt'][key] = value
    except:
        pass
    
    try:
        # Get open file descriptors (might show window handles)
        fd_dir = Path(f'/proc/{pid}/fd')
        if fd_dir.exists():
            fds = []
            for fd_link in fd_dir.iterdir():
                try:
                    target = fd_link.readlink()
                    # Look for interesting file descriptors
                    if any(keyword in str(target).lower() for keyword in 
                          ['socket', 'pipe', 'x11', 'wayland', 'dri', 'dev']):
                        fds.append(f"{fd_link.name} -> {target}")
                except:
                    pass
            process_info['open_files'] = fds[:10]  # Limit to first 10
    except:
        pass
    
    return process_info

def explore_window_specific_data():
    """Explore what window-specific data we can extract from processes"""
    print("🔍 Process Tree Analysis for Zen Browser Windows")
    print("=" * 60)
    
    zen_windows = get_zen_windows_with_pids()
    if not zen_windows:
        print("❌ No Zen browser windows found")
        return
    
    print(f"📊 Found {len(zen_windows)} Zen browser windows")
    
    # Group windows by PID
    windows_by_pid = {}
    for window in zen_windows:
        pid = window['pid']
        if pid not in windows_by_pid:
            windows_by_pid[pid] = []
        windows_by_pid[pid].append(window)
    
    print(f"📊 Windows distributed across {len(windows_by_pid)} processes:")
    for pid, windows in windows_by_pid.items():
        print(f"   PID {pid}: {len(windows)} windows")
    
    # Analyze each process
    for pid, windows in windows_by_pid.items():
        print(f"\n🔬 Process Analysis for PID {pid}:")
        print(f"   Associated windows: {len(windows)}")
        
        for i, window in enumerate(windows):
            print(f"      Window {i+1}: WS{window['workspace']} - {window['title'][:30]}...")
        
        # Get detailed process information
        process_info = analyze_process_tree(pid)
        
        print(f"\n📋 Process Details:")
        print(f"   Command: {process_info['cmdline'][:80]}...")
        print(f"   Working dir: {process_info['cwd']}")
        print(f"   Child processes: {len(process_info['children'])}")
        print(f"   Threads: {len(process_info['threads'])}")
        print(f"   Open files: {len(process_info['open_files'])}")
        
        if process_info['environ_excerpt']:
            print(f"   Environment variables:")
            for key, value in process_info['environ_excerpt'].items():
                print(f"      {key}={value[:50]}...")
        
        if process_info['open_files']:
            print(f"   Interesting file descriptors:")
            for fd in process_info['open_files'][:5]:  # Show first 5
                print(f"      {fd}")
        
        # Analyze child processes if any
        if process_info['children']:
            print(f"\n🌳 Child Process Analysis:")
            for child_pid in process_info['children'][:3]:  # Analyze first 3 children
                try:
                    child_info = analyze_process_tree(child_pid)
                    print(f"   Child {child_pid}: {child_info['cmdline'][:50]}...")
                except Exception as e:
                    print(f"   Child {child_pid}: Error analyzing - {e}")

def check_for_window_handles():
    """Check if we can find window handles or X11/Wayland identifiers"""
    print(f"\n🪟 Window Handle Detection:")
    
    zen_windows = get_zen_windows_with_pids()
    
    for window in zen_windows:
        pid = window['pid']
        address = window['address']
        
        print(f"\n   Window: {window['title'][:30]}... (WS{window['workspace']})")
        print(f"   Hyprland address: {address}")
        
        # Try to correlate with system-level window information
        try:
            # Check if we can find this window in system tools
            result = subprocess.run(['xwininfo', '-root', '-tree'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'zen' in result.stdout.lower():
                print(f"   X11 window info available")
        except:
            pass
        
        try:
            # Check for Wayland window information
            result = subprocess.run(['hyprctl', 'clients'], 
                                  capture_output=True, text=True)
            if address in result.stdout:
                print(f"   ✅ Found in hyprctl output")
        except:
            pass

if __name__ == '__main__':
    explore_window_specific_data()
    check_for_window_handles()