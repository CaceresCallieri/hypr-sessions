"""
Zen Browser Session Reader
Handles direct access to Zen browser's sessionstore.jsonlz4 files for tab extraction
"""

import json
import lz4.block
import os
from pathlib import Path


class ZenSessionReader:
    def __init__(self, debug=False):
        self.debug = debug
        self.zen_profile_paths = [
            Path.home() / '.zen',  # Standard installation
            Path.home() / '.var/app/app.zen_browser.zen/zen'  # Flatpak
        ]
        self.active_profile = None
        self._find_active_profile()
    
    def debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG ZenSessionReader] {message}")
    
    def _find_active_profile(self):
        """
        Locate the active Zen browser profile directory
        
        Logic:
        1. Check standard locations (~/.zen, flatpak location)
        2. Look for profile directories (usually contain 'Default' or have .extension)
        3. Find the one with the largest/most recent sessionstore file
        """
        self.debug_print("Searching for Zen browser profiles")
        
        candidates = []
        
        for base_path in self.zen_profile_paths:
            if not base_path.exists():
                self.debug_print(f"Base path doesn't exist: {base_path}")
                continue
                
            self.debug_print(f"Scanning base path: {base_path}")
            
            # Find profile subdirectories
            for profile_dir in base_path.iterdir():
                if not profile_dir.is_dir() or profile_dir.name.startswith('.'):
                    continue
                
                session_file = profile_dir / 'sessionstore-backups' / 'recovery.jsonlz4'
                if session_file.exists():
                    file_size = session_file.stat().st_size
                    candidates.append({
                        'name': profile_dir.name,
                        'path': profile_dir,
                        'session_file': session_file,
                        'size': file_size,
                        'modified': session_file.stat().st_mtime
                    })
                    self.debug_print(f"Found profile: {profile_dir.name} ({file_size:,} bytes)")
        
        if not candidates:
            self.debug_print("No Zen profiles with session files found")
            return None
        
        # Use the profile with the largest session file (most active)
        self.active_profile = max(candidates, key=lambda x: x['size'])
        self.debug_print(f"Selected active profile: {self.active_profile['name']} "
                         f"({self.active_profile['size']:,} bytes)")
        
        return self.active_profile
    
    def get_profile_info(self):
        """Return information about the detected profile"""
        if not self.active_profile:
            return None
            
        return {
            'profile_name': self.active_profile['name'],
            'profile_path': str(self.active_profile['path']),
            'session_file': str(self.active_profile['session_file']),
            'file_size': self.active_profile['size'],
            'last_modified': self.active_profile['modified']
        }
    
    def is_available(self):
        """Check if Zen session reading is available"""
        return self.active_profile is not None
    
    def _decompress_session_file(self, session_file_path):
        """
        Decompress Mozilla LZ4 session file and return parsed JSON
        
        Mozilla format:
        - First 8 bytes: 'mozLz40\0' header
        - Remaining bytes: LZ4 compressed JSON data
        
        Returns:
            dict: Parsed session data or None if failed
        """
        try:
            self.debug_print(f"Reading session file: {session_file_path}")
            
            with open(session_file_path, 'rb') as f:
                # Read and validate Mozilla LZ4 header
                header = f.read(8)
                if header != b'mozLz40\0':
                    self.debug_print(f"Invalid header: {header} (expected: mozLz40\\0)")
                    return None
                
                # Read compressed data
                compressed_data = f.read()
                self.debug_print(f"Compressed data size: {len(compressed_data):,} bytes")
                
                # Decompress using LZ4
                decompressed_data = lz4.block.decompress(compressed_data)
                self.debug_print(f"Decompressed data size: {len(decompressed_data):,} bytes")
                
                # Parse JSON
                session_data = json.loads(decompressed_data.decode('utf-8'))
                self.debug_print(f"Successfully parsed session JSON")
                
                return session_data
                
        except lz4.block.LZ4BlockError as e:
            self.debug_print(f"LZ4 decompression failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.debug_print(f"JSON parsing failed: {e}")
            return None
        except Exception as e:
            self.debug_print(f"Session file reading failed: {e}")
            return None
    
    def get_current_session_data(self):
        """
        Get the current session data from the active profile
        
        Returns:
            dict: Complete session data with windows and tabs, or None if failed
        """
        if not self.active_profile:
            self.debug_print("No active profile available")
            return None
        
        session_file = self.active_profile['session_file']
        return self._decompress_session_file(session_file)
    
    def _extract_tab_info(self, tab_data):
        """
        Extract relevant information from a single tab's data
        
        Tab structure in session data:
        - entries[]: List of navigation history for this tab
        - index: Current position in navigation history (1-based)
        - pinned: Whether tab is pinned
        - userTypedValue: URL being typed (if any)
        
        Args:
            tab_data (dict): Raw tab data from session file
            
        Returns:
            dict: Cleaned tab information for hypr-sessions
        """
        try:
            # Get current entry from navigation history
            entries = tab_data.get('entries', [])
            if not entries:
                return None
            
            # Get current entry (index is 1-based in Mozilla format)
            current_index = tab_data.get('index', 1) - 1
            if current_index < 0 or current_index >= len(entries):
                current_index = len(entries) - 1  # Use last entry as fallback
            
            current_entry = entries[current_index]
            
            # Extract tab information
            tab_info = {
                'url': current_entry.get('url', ''),
                'title': current_entry.get('title', ''),
                'pinned': tab_data.get('pinned', False),
                'active': tab_data.get('selected', False)  # Whether this tab is selected
            }
            
            # Skip invalid URLs
            if not tab_info['url'] or tab_info['url'].startswith('about:'):
                return None
                
            # Skip extension URLs
            if tab_info['url'].startswith(('moz-extension:', 'chrome-extension:', 'ext+')):
                return None
            
            self.debug_print(f"Extracted tab: {tab_info['title'][:50]}... -> {tab_info['url'][:80]}...")
            return tab_info
            
        except Exception as e:
            self.debug_print(f"Failed to extract tab info: {e}")
            return None
    
    def get_structured_tab_data(self, window_index=None):
        """
        Get structured tab data organized by browser windows
        
        Args:
            window_index (int, optional): Get tabs for specific window only
            
        Returns:
            dict: Structure matching your project's needs:
            {
                'total_windows': int,
                'total_tabs': int,
                'windows': [
                    {
                        'window_index': int,
                        'tabs': [
                            {
                                'url': str,
                                'title': str,
                                'pinned': bool,
                                'active': bool
                            }
                        ]
                    }
                ]
            }
        """
        session_data = self.get_current_session_data()
        if not session_data:
            self.debug_print("No session data available")
            return None
        
        windows_data = session_data.get('windows', [])
        self.debug_print(f"Processing {len(windows_data)} browser windows")
        
        structured_data = {
            'total_windows': len(windows_data),
            'total_tabs': 0,
            'windows': []
        }
        
        for idx, window_data in enumerate(windows_data):
            # Skip if specific window requested and this isn't it
            if window_index is not None and idx != window_index:
                continue
            
            window_info = {
                'window_index': idx,
                'tabs': []
            }
            
            tabs = window_data.get('tabs', [])
            self.debug_print(f"Processing window {idx}: {len(tabs)} tabs")
            
            for tab_data in tabs:
                tab_info = self._extract_tab_info(tab_data)
                if tab_info:  # Only add valid tabs
                    window_info['tabs'].append(tab_info)
            
            if window_info['tabs']:  # Only add windows with valid tabs
                structured_data['windows'].append(window_info)
                structured_data['total_tabs'] += len(window_info['tabs'])
                self.debug_print(f"Window {idx}: {len(window_info['tabs'])} valid tabs extracted")
        
        self.debug_print(f"Structured data: {structured_data['total_windows']} windows, "
                         f"{structured_data['total_tabs']} total tabs")
        
        return structured_data