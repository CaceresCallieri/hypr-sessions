#!/usr/bin/env python3
"""
Test correlation between Zen browser windows and Isolated Web Content processes
"""

import subprocess
import json
import re
import time
from collections import defaultdict

def get_zen_window_info():
    """Get detailed Zen browser window information"""
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
                    'title': client.get('title', ''),
                    'workspace': client.get('workspace', {}).get('id', -1),
                    'pid': client.get('pid')
                })
        return zen_windows
    except Exception as e:
        print(f"Error getting Zen windows: {e}")
        return []

def get_isolated_web_processes(main_pid):
    """Get all Isolated Web Content processes"""
    isolated_processes = []
    
    try:
        # Get process tree with PIDs
        result = subprocess.run(['pstree', '-p', str(main_pid)], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            # Find all Isolated Web Co processes
            isolated_matches = re.findall(r'Isolated Web Co\((\d+)\)', result.stdout)
            
            for pid_str in isolated_matches:
                pid = int(pid_str)
                
                # Get command line and other details
                cmdline = ''
                try:
                    with open(f'/proc/{pid}/cmdline', 'rb') as f:
                        cmdline_data = f.read()
                        cmdline = cmdline_data.decode('utf-8', errors='ignore').replace('\x00', ' ').strip()
                except:
                    pass
                
                isolated_processes.append({
                    'pid': pid,
                    'cmdline': cmdline
                })
                
    except Exception as e:
        print(f"Error getting isolated processes: {e}")
    
    return isolated_processes

def analyze_process_cmdlines(isolated_processes):
    """Analyze command lines for site-specific information"""
    site_patterns = defaultdict(list)
    
    print(f"🔍 Analyzing {len(isolated_processes)} Isolated Web Content processes:")
    
    for i, proc in enumerate(isolated_processes):
        cmdline = proc['cmdline']
        pid = proc['pid']
        
        print(f"\n   Process {i+1} (PID {pid}):")
        print(f"      Command: {cmdline[:100]}...")
        
        # Look for site-specific indicators in command line
        site_indicators = []
        
        # Common patterns that might indicate specific sites
        if 'youtube' in cmdline.lower():
            site_indicators.append('YouTube')
        if 'github' in cmdline.lower():
            site_indicators.append('GitHub')
        if 'nexus' in cmdline.lower() or 'mods' in cmdline.lower():
            site_indicators.append('NexusMods')
        if 'google' in cmdline.lower():
            site_indicators.append('Google')
        
        # Look for any URLs or domains
        url_matches = re.findall(r'https?://[^\s]+', cmdline)
        domain_matches = re.findall(r'[a-zA-Z0-9.-]+\.(com|org|net|edu)', cmdline)
        
        if url_matches:
            site_indicators.extend(url_matches)
        if domain_matches:
            site_indicators.extend(domain_matches)
        
        if site_indicators:
            print(f"      🎯 Site indicators: {', '.join(site_indicators)}")
            for indicator in site_indicators:
                site_patterns[indicator].append(pid)
        else:
            print(f"      ❓ No obvious site indicators")
    
    return site_patterns

def test_window_process_correlation():
    """Test correlation between windows and processes"""
    print("🔍 Testing Window-Process Correlation")
    print("=" * 50)
    
    # Get window information
    zen_windows = get_zen_window_info()
    if not zen_windows:
        print("❌ No Zen windows found")
        return
    
    print(f"📊 Found {len(zen_windows)} Zen browser windows:")
    for i, window in enumerate(zen_windows):
        print(f"   {i+1}: WS{window['workspace']} - {window['title'][:40]}...")
    
    # Get main PID
    main_pid = zen_windows[0]['pid']
    print(f"\n🎯 Main Zen browser PID: {main_pid}")
    
    # Get isolated web content processes
    isolated_processes = get_isolated_web_processes(main_pid)
    print(f"\n📊 Found {len(isolated_processes)} Isolated Web Content processes")
    
    # Analyze command lines
    site_patterns = analyze_process_cmdlines(isolated_processes)
    
    print(f"\n🎯 Site Pattern Analysis:")
    if site_patterns:
        for site, pids in site_patterns.items():
            print(f"   {site}: PIDs {pids}")
    else:
        print("   ❌ No site-specific patterns found in command lines")
    
    # Cross-reference with window titles
    print(f"\n🔗 Window Title Cross-Reference:")
    correlation_found = False
    
    for window in zen_windows:
        title = window['title'].lower()
        print(f"\n   Window: {window['title'][:40]}...")
        
        # Try to match with site patterns
        matched_sites = []
        for site, pids in site_patterns.items():
            if any(keyword in title for keyword in [site.lower(), 'youtube', 'github', 'nexus']):
                matched_sites.append((site, pids))
        
        if matched_sites:
            correlation_found = True
            print(f"      ✅ Potential matches:")
            for site, pids in matched_sites:
                print(f"         {site}: PIDs {pids}")
        else:
            print(f"      ❓ No clear process correlation")
    
    print(f"\n📊 Correlation Analysis Results:")
    if correlation_found:
        print("   ✅ Some window-process correlations detected!")
        print("   🎯 Site isolation approach might be viable")
    else:
        print("   ❌ No clear window-process correlations found")
        print("   ⚠️  Command line approach may not work")
    
    # Final recommendation
    print(f"\n💡 Recommendation:")
    if len(isolated_processes) >= len(zen_windows):
        print("   📊 Process count >= Window count: Correlation possible")
        print("   🔬 Further investigation into process memory/network might help")
    else:
        print("   📊 Process count < Window count: Direct correlation unlikely")
        print("   🔄 Consider alternative approaches (window elimination, pragmatic)")

if __name__ == '__main__':
    test_window_process_correlation()