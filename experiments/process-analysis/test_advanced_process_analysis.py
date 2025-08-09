#!/usr/bin/env python3
"""
Advanced process analysis to find window-specific identifiers
Focus on child processes, network connections, and memory maps
"""

import subprocess
import json
import os
import re
from pathlib import Path

def get_zen_window_addresses():
    """Get mapping of window addresses to workspace/title info"""
    try:
        result = subprocess.run(['hyprctl', 'clients', '-j'], 
                              capture_output=True, text=True, check=True)
        clients = json.loads(result.stdout)
        
        address_map = {}
        for client in clients:
            class_name = client.get('class', '').lower()
            if class_name in ['zen-alpha', 'zen', 'zen-browser']:
                address = client.get('address', '')
                address_map[address] = {
                    'title': client.get('title', ''),
                    'workspace': client.get('workspace', {}).get('id', -1),
                    'pid': client.get('pid'),
                    'position': client.get('at', [0, 0]),
                    'size': client.get('size', [0, 0])
                }
        return address_map
    except Exception as e:
        print(f"Error getting window addresses: {e}")
        return {}

def analyze_child_processes(main_pid):
    """Analyze child processes for window-specific information"""
    child_info = []
    
    try:
        # Get all child processes recursively
        result = subprocess.run(['pstree', '-p', str(main_pid)], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            # Extract PIDs from pstree output
            pids = re.findall(r'\((\d+)\)', result.stdout)
            
            print(f"🌳 Process tree structure:")
            print(result.stdout)
            
            for pid in pids:
                try:
                    pid_int = int(pid)
                    if pid_int != main_pid:  # Skip the main process
                        
                        # Get command line
                        cmdline = ''
                        try:
                            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                                cmdline_data = f.read()
                                cmdline = cmdline_data.decode('utf-8', errors='ignore').replace('\x00', ' ').strip()
                        except:
                            pass
                        
                        # Get process status
                        status_info = {}
                        try:
                            with open(f'/proc/{pid}/status', 'r') as f:
                                for line in f:
                                    if ':' in line:
                                        key, value = line.split(':', 1)
                                        key = key.strip()
                                        if key in ['Name', 'State', 'PPid', 'Threads']:
                                            status_info[key] = value.strip()
                        except:
                            pass
                        
                        child_info.append({
                            'pid': pid_int,
                            'cmdline': cmdline,
                            'status': status_info
                        })
                        
                except ValueError:
                    pass
                    
    except Exception as e:
        print(f"Error analyzing child processes: {e}")
    
    return child_info

def check_memory_maps(pid):
    """Check memory maps for window-specific information"""
    interesting_mappings = []
    
    try:
        with open(f'/proc/{pid}/maps', 'r') as f:
            maps_content = f.read()
            
            # Look for interesting memory mappings
            for line in maps_content.split('\n'):
                if any(keyword in line.lower() for keyword in 
                      ['x11', 'wayland', 'dri', 'gpu', 'display', 'window']):
                    interesting_mappings.append(line.strip())
            
    except Exception as e:
        pass
    
    return interesting_mappings

def check_network_connections(pid):
    """Check network connections that might be window-specific"""
    connections = []
    
    try:
        # Use ss to get socket information for specific PID
        result = subprocess.run(['ss', '-tuln'], capture_output=True, text=True)
        if result.returncode == 0:
            # This won't directly show PID connections, but gives us network info
            lines = result.stdout.split('\n')
            for line in lines:
                if 'LISTEN' in line:
                    connections.append(line.strip())
                    
    except Exception as e:
        pass
    
    return connections

def analyze_file_descriptors_detailed(pid):
    """Detailed analysis of file descriptors"""
    fd_analysis = {
        'sockets': [],
        'pipes': [],
        'devices': [],
        'regular_files': [],
        'other': []
    }
    
    try:
        fd_dir = Path(f'/proc/{pid}/fd')
        if fd_dir.exists():
            for fd_link in fd_dir.iterdir():
                try:
                    target = str(fd_link.readlink())
                    fd_num = fd_link.name
                    
                    if target.startswith('socket:['):
                        fd_analysis['sockets'].append(f"fd{fd_num}: {target}")
                    elif target.startswith('pipe:['):
                        fd_analysis['pipes'].append(f"fd{fd_num}: {target}")
                    elif target.startswith('/dev/'):
                        fd_analysis['devices'].append(f"fd{fd_num}: {target}")
                    elif os.path.isfile(target):
                        fd_analysis['regular_files'].append(f"fd{fd_num}: {target}")
                    else:
                        fd_analysis['other'].append(f"fd{fd_num}: {target}")
                        
                except Exception:
                    pass
                    
    except Exception as e:
        pass
    
    return fd_analysis

def main():
    print("🔬 Advanced Process Analysis for Window Identification")
    print("=" * 65)
    
    # Get window address mapping
    address_map = get_zen_window_addresses()
    if not address_map:
        print("❌ No Zen browser windows found")
        return
    
    print(f"📊 Found {len(address_map)} Zen browser windows:")
    for address, info in address_map.items():
        print(f"   {address}: WS{info['workspace']} - {info['title'][:40]}...")
    
    # Get the main Zen process PID
    main_pid = next(iter(address_map.values()))['pid']
    print(f"\n🎯 Analyzing main process PID: {main_pid}")
    
    # Analyze child processes
    print(f"\n🌳 Child Process Analysis:")
    child_processes = analyze_child_processes(main_pid)
    
    for child in child_processes:
        print(f"\n   Child PID {child['pid']}:")
        print(f"      Command: {child['cmdline'][:60]}...")
        print(f"      Status: {child['status']}")
        
        # Analyze file descriptors of child processes
        child_fds = analyze_file_descriptors_detailed(child['pid'])
        
        if child_fds['sockets']:
            print(f"      Sockets: {len(child_fds['sockets'])}")
            for socket in child_fds['sockets'][:3]:
                print(f"         {socket}")
        
        if child_fds['pipes']:
            print(f"      Pipes: {len(child_fds['pipes'])}")
    
    # Check main process detailed FDs
    print(f"\n📂 Main Process File Descriptor Analysis:")
    main_fds = analyze_file_descriptors_detailed(main_pid)
    
    for category, fds in main_fds.items():
        if fds:
            print(f"   {category.title()}: {len(fds)}")
            for fd in fds[:3]:  # Show first 3
                print(f"      {fd}")
    
    # Check for window-specific patterns
    print(f"\n🔍 Looking for Window-Specific Patterns:")
    
    # Try to correlate socket/pipe information with window addresses
    all_sockets = main_fds['sockets'] + [fd for child in child_processes 
                                       for fd in analyze_file_descriptors_detailed(child['pid'])['sockets']]
    
    if all_sockets:
        print(f"   Total sockets across all processes: {len(all_sockets)}")
        if len(all_sockets) == len(address_map):
            print("   🎯 Socket count matches window count! Potential correlation.")
        else:
            print(f"   ⚠️  Socket count ({len(all_sockets)}) doesn't match window count ({len(address_map)})")
    
    # Check if process tree reveals window separation
    print(f"\n💡 Analysis Summary:")
    print(f"   - All windows run in single process (PID {main_pid})")
    print(f"   - {len(child_processes)} child processes detected")
    print(f"   - Process tree doesn't seem to separate windows")
    print(f"   - Need to explore other identification methods")

if __name__ == '__main__':
    main()