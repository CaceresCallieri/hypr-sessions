#!/usr/bin/env python3
"""
Experiment to understand how to identify actual programs running in swallowed terminals
This will help us distinguish between shell aliases and actual executables
"""

import json
import subprocess
import os
from pathlib import Path

def get_hyprctl_clients():
    """Get current hyprctl clients data"""
    try:
        result = subprocess.run(
            ["hyprctl", "clients", "-j"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error getting hyprctl data: {e}")
        return []

def get_process_info(pid):
    """Get detailed process information from /proc"""
    try:
        # Read command line
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline_raw = f.read()
            cmdline = cmdline_raw.decode("utf-8", errors="ignore").split("\0")[:-1]
        
        # Read process status
        with open(f"/proc/{pid}/stat", "r") as f:
            stat_line = f.read().strip()
        
        # Read executable path
        exe_path = None
        try:
            exe_path = os.readlink(f"/proc/{pid}/exe")
        except:
            pass
        
        return {
            "cmdline": cmdline,
            "stat": stat_line,
            "exe_path": exe_path
        }
    except Exception as e:
        return {"error": str(e)}

def get_child_processes(pid):
    """Get all child processes of a given PID"""
    children = []
    try:
        # Read all processes and find children
        for proc_dir in Path("/proc").iterdir():
            if proc_dir.is_dir() and proc_dir.name.isdigit():
                child_pid = int(proc_dir.name)
                try:
                    with open(proc_dir / "stat", "r") as f:
                        stat_line = f.read().strip()
                        # Extract PPID (4th field after splitting by whitespace)
                        # Format: pid (comm) state ppid ...
                        parts = stat_line.split()
                        if len(parts) > 3:
                            ppid = int(parts[3])
                            if ppid == pid:
                                children.append(child_pid)
                except:
                    continue
    except Exception as e:
        print(f"Error getting children for PID {pid}: {e}")
    
    return children

def analyze_swallowed_terminals():
    """Analyze swallowed terminal processes to understand program identification"""
    print("=== SWALLOWED TERMINAL PROGRAM IDENTIFICATION ===")
    print()
    
    clients = get_hyprctl_clients()
    swallowing_relationships = []
    
    # Find swallowing relationships
    for client in clients:
        swallowing = client.get("swallowing", "")
        if swallowing and swallowing != "0x0":
            # Find the swallowed window
            swallowed_window = None
            for c in clients:
                if c.get("address") == swallowing:
                    swallowed_window = c
                    break
            
            if swallowed_window:
                swallowing_relationships.append({
                    "swallowing": client,
                    "swallowed": swallowed_window
                })
    
    if not swallowing_relationships:
        print("No swallowing relationships found. Launch neovide from a terminal first.")
        return
    
    print(f"Found {len(swallowing_relationships)} swallowing relationships")
    print()
    
    for i, rel in enumerate(swallowing_relationships):
        swallowing_window = rel["swallowing"]
        swallowed_window = rel["swallowed"]
        
        print(f"=== RELATIONSHIP {i+1} ===")
        print(f"Swallowing: {swallowing_window['class']} - {swallowing_window['title']}")
        print(f"Swallowed: {swallowed_window['class']} - {swallowed_window['title']}")
        print()
        
        # Analyze the swallowed terminal process
        terminal_pid = swallowed_window.get("pid")
        if terminal_pid:
            print(f"Analyzing swallowed terminal (PID: {terminal_pid}):")
            
            # Get terminal process info
            terminal_info = get_process_info(terminal_pid)
            print(f"  Terminal cmdline: {terminal_info.get('cmdline', 'N/A')}")
            print(f"  Terminal exe: {terminal_info.get('exe_path', 'N/A')}")
            
            # Get child processes
            children = get_child_processes(terminal_pid)
            print(f"  Terminal children: {children}")
            
            # Analyze each child
            for child_pid in children:
                child_info = get_process_info(child_pid)
                print(f"    Child {child_pid}:")
                print(f"      cmdline: {child_info.get('cmdline', 'N/A')}")
                print(f"      exe: {child_info.get('exe_path', 'N/A')}")
                
                # Check grandchildren (shell might spawn the actual program)
                grandchildren = get_child_processes(child_pid)
                if grandchildren:
                    print(f"      grandchildren: {grandchildren}")
                    for grandchild_pid in grandchildren:
                        gc_info = get_process_info(grandchild_pid)
                        print(f"        Grandchild {grandchild_pid}:")
                        print(f"          cmdline: {gc_info.get('cmdline', 'N/A')}")
                        print(f"          exe: {gc_info.get('exe_path', 'N/A')}")
        
        # Also analyze the swallowing window process
        swallowing_pid = swallowing_window.get("pid")
        if swallowing_pid:
            print(f"Analyzing swallowing window (PID: {swallowing_pid}):")
            swallowing_info = get_process_info(swallowing_pid)
            print(f"  Swallowing cmdline: {swallowing_info.get('cmdline', 'N/A')}")
            print(f"  Swallowing exe: {swallowing_info.get('exe_path', 'N/A')}")
        
        print("-" * 50)
        print()

def main():
    print("Program Identification in Swallowed Terminals Experiment")
    print("=" * 60)
    print()
    print("This will analyze swallowing relationships to understand:")
    print("1. How to identify the actual program running in swallowed terminals")
    print("2. Whether aliases affect our ability to detect the real executable")
    print("3. Process tree relationships in swallowing scenarios")
    print()
    
    analyze_swallowed_terminals()

if __name__ == "__main__":
    main()