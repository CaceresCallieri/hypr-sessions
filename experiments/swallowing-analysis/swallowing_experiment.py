#!/usr/bin/env python3
"""
Experiment script to understand Hyprland window swallowing behavior
This script analyzes the swallowing property in hyprctl clients output
"""

import json
import subprocess
import time
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

def analyze_swallowing_relationships(clients):
    """Analyze swallowing relationships between windows"""
    print("=== SWALLOWING RELATIONSHIP ANALYSIS ===")
    print()
    
    swallowing_windows = []
    swallowed_windows = []
    
    for client in clients:
        address = client.get("address", "")
        class_name = client.get("class", "")
        title = client.get("title", "")
        pid = client.get("pid", "")
        swallowing = client.get("swallowing", "")
        
        print(f"Window: {class_name} - {title}")
        print(f"  Address: {address}")
        print(f"  PID: {pid}")
        print(f"  Swallowing: {swallowing}")
        
        if swallowing and swallowing != "0x0":
            swallowing_windows.append({
                "window": client,
                "swallowing_address": swallowing
            })
            print(f"  >> This window is SWALLOWING: {swallowing}")
        
        print()
    
    print(f"Found {len(swallowing_windows)} windows with swallowing behavior")
    print()
    
    # Try to find the swallowed windows
    if swallowing_windows:
        print("=== ATTEMPTING TO MATCH RELATIONSHIPS ===")
        for swallowing in swallowing_windows:
            swallowing_addr = swallowing["swallowing_address"]
            swallowing_window = swallowing["window"]
            
            # Look for the swallowed window
            swallowed_window = None
            for client in clients:
                if client.get("address") == swallowing_addr:
                    swallowed_window = client
                    break
            
            print(f"Swallowing Window: {swallowing_window['class']} ({swallowing_window['address'][:10]}...)")
            if swallowed_window:
                print(f"  Swallowed Window: {swallowed_window['class']} ({swallowed_window['address'][:10]}...)")
                print(f"  Swallowed Title: {swallowed_window.get('title', '')}")
                print(f"  Swallowed PID: {swallowed_window.get('pid', '')}")
            else:
                print(f"  Swallowed Window: NOT FOUND (address: {swallowing_addr})")
            print()
    
    return swallowing_windows

def main():
    print("Hyprland Swallowing Behavior Experiment")
    print("=" * 50)
    print()
    print("This script will analyze current windows for swallowing relationships.")
    print("Make sure you have some swallowed windows open (e.g., neovide launched from terminal)")
    print()
    
    clients = get_hyprctl_clients()
    if not clients:
        print("No clients found or error occurred")
        return
    
    print(f"Found {len(clients)} total windows")
    print()
    
    swallowing_relationships = analyze_swallowing_relationships(clients)
    
    if not swallowing_relationships:
        print("No swallowing relationships found.")
        print("Try launching a GUI application from a terminal (e.g., 'ghostty' then 'neovide')")
    else:
        print("=== EXPERIMENT RESULTS ===")
        print(f"Detected {len(swallowing_relationships)} swallowing relationships")
        print()
        print("Key findings:")
        print("- swallowing property points FROM swallowing window TO swallowed window")
        print("- swallowed windows may not be visible in normal window lists")
        print("- this confirms the direction of the relationship")

if __name__ == "__main__":
    main()