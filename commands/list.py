"""
Session list functionality
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from .shared.config import get_config, SessionConfig
from .shared.debug import CommandDebugger
from .shared.operation_result import OperationResult
from .shared.utils import Utils
from .shared.path_cache import path_cache


class SessionList(Utils):
    def __init__(self, debug: bool = False) -> None:
        super().__init__()
        self.debugger = CommandDebugger("SessionList", debug)
        self.config: SessionConfig = get_config()
    
    def list_sessions(self, archived: bool = False, show_all: bool = False) -> OperationResult:
        """List sessions based on requested type (active, archived, or all)"""
        if show_all:
            result = OperationResult(operation_name="List all sessions")
        elif archived:
            result = OperationResult(operation_name="List archived sessions")
        else:
            result = OperationResult(operation_name="List active sessions")
        
        active_sessions_data = []
        archived_sessions_data = []
        
        # Get active sessions unless only archived requested
        if not archived:
            active_result = self._list_active_sessions()
            if not active_result.success:
                return active_result
            active_sessions_data = active_result.data.get("active_sessions", [])
            # Copy messages from active result
            for message in active_result.messages:
                result.messages.append(message)
        
        # Get archived sessions if requested
        if archived or show_all:
            archived_result = self._list_archived_sessions()
            if not archived_result.success:
                if archived:  # Only archived was requested, return the error
                    return archived_result
                else:  # show_all was requested, add warnings but continue
                    for message in archived_result.messages:
                        result.messages.append(message)
            else:
                archived_sessions_data = archived_result.data.get("archived_sessions", [])
                # Copy messages from archived result
                for message in archived_result.messages:
                    result.messages.append(message)
        
        # Build final result data with consistent schema regardless of mode
        result.data = {
            "active_sessions": active_sessions_data,
            "archived_sessions": archived_sessions_data,
            "active_count": len(active_sessions_data),
            "archived_count": len(archived_sessions_data),
        }
        
        return result
    
    def _list_active_sessions(self) -> OperationResult:
        """List all active sessions in folder format"""
        result = OperationResult(operation_name="List active sessions")
        
        active_sessions_dir = self.config.get_active_sessions_dir()
        self.debugger.debug(f"Searching for active session directories in: {active_sessions_dir}")
        
        try:
            # Find session directories (exclude hidden dirs and zen-browser-backups)
            session_dirs = [d for d in active_sessions_dir.iterdir() 
                           if d.is_dir() and not d.name.startswith('.') and d.name != 'zen-browser-backups']
        except (OSError, PermissionError) as e:
            result.add_error(f"File system error: Cannot scan active sessions directory: {e}")
            return result
        except Exception as e:
            result.add_error(f"Unexpected error scanning active sessions directory: {e}")
            return result
        
        self.debugger.debug(f"Found {len(session_dirs)} active session directories")
        result.add_success(f"Found {len(session_dirs)} active session directories")

        if not session_dirs:
            result.data = {"active_sessions": [], "active_count": 0}
            return result

        sessions_data = []
        valid_sessions = 0
        invalid_sessions = 0

        for session_dir in sorted(session_dirs):
            session_name = session_dir.name
            session_file = session_dir / "session.json"

            self.debugger.debug(f"Processing active session directory: {session_dir}")

            if path_cache.exists(session_file):
                try:
                    with open(session_file, "r") as f:
                        session_data = json.load(f)

                    timestamp = session_data.get("timestamp", "Unknown")
                    window_count = len(session_data.get("windows", []))

                    # Count all files in session directory
                    all_files = list(session_dir.iterdir())
                    file_count = len(all_files)

                    self.debugger.debug(f"Active session '{session_name}': {window_count} windows, {file_count} files, saved {timestamp}")

                    sessions_data.append({
                        "name": session_name,
                        "windows": window_count,
                        "files": file_count,
                        "timestamp": timestamp,
                        "valid": True
                    })
                    valid_sessions += 1
                    result.add_success(f"Processed active session '{session_name}': {window_count} windows")

                except (OSError, PermissionError) as e:
                    self.debugger.debug(f"File system error reading active session file {session_file}: {e}")

                    sessions_data.append({
                        "name": session_name,
                        "valid": False,
                        "error": f"File access error: {e}"
                    })
                except json.JSONDecodeError as e:
                    self.debugger.debug(f"JSON decode error reading active session file {session_file}: {e}")

                    sessions_data.append({
                        "name": session_name,
                        "valid": False,
                        "error": f"JSON decode error: line {e.lineno}"
                    })
                except Exception as e:
                    self.debugger.debug(f"Unexpected error reading active session file {session_file}: {e}")

                    sessions_data.append({
                        "name": session_name,
                        "valid": False,
                        "error": str(e)
                    })
                    invalid_sessions += 1
                    result.add_warning(f"Failed to read active session '{session_name}': {e}")
            else:
                self.debugger.debug(f"Active session directory {session_dir} missing session.json")

                sessions_data.append({
                    "name": session_name,
                    "valid": False,
                    "error": "Missing session.json"
                })
                invalid_sessions += 1
                result.add_warning(f"Active session '{session_name}' is incomplete: missing session.json")

        result.data = {
            "active_sessions": sessions_data,
            "active_count": len(session_dirs),
        }
        
        if invalid_sessions > 0:
            result.add_warning(f"Found {invalid_sessions} invalid/incomplete active sessions")
        
        return result
    
    def _list_archived_sessions(self) -> OperationResult:
        """List all archived sessions"""
        result = OperationResult(operation_name="List archived sessions")
        
        archived_sessions_dir = self.config.get_archived_sessions_dir()
        self.debugger.debug(f"Searching for archived session directories in: {archived_sessions_dir}")
        
        if not path_cache.exists(archived_sessions_dir):
            self.debugger.debug("Archived sessions directory does not exist")
            result.data = {"archived_sessions": [], "archived_count": 0}
            return result

        try:
            # Find archived session directories (exclude hidden files)
            session_dirs = [d for d in archived_sessions_dir.iterdir() 
                           if d.is_dir() and not d.name.startswith('.')]
        except (OSError, PermissionError) as e:
            result.add_error(f"File system error: Cannot scan archived sessions directory: {e}")
            return result
        except Exception as e:
            result.add_error(f"Unexpected error scanning archived sessions directory: {e}")
            return result
        
        self.debugger.debug(f"Found {len(session_dirs)} archived session directories")
        result.add_success(f"Found {len(session_dirs)} archived session directories")

        if not session_dirs:
            result.data = {"archived_sessions": [], "archived_count": 0}
            return result

        sessions_data = []
        valid_sessions = 0
        invalid_sessions = 0

        for session_dir in sorted(session_dirs, key=lambda x: x.name):
            session_name = session_dir.name
            metadata_file = session_dir / ".archive-metadata.json"
            
            self.debugger.debug(f"Processing archived session directory: {session_dir}")
            
            if path_cache.exists(metadata_file):
                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                    
                    # Get archive metadata
                    original_name = metadata.get("original_name", session_name)
                    archive_timestamp = metadata.get("archive_timestamp", "Unknown")
                    file_count = metadata.get("file_count", 0)
                    
                    # Count actual files in directory for verification
                    all_files = list(session_dir.iterdir())
                    actual_file_count = len(all_files)
                    
                    self.debugger.debug(f"Archived session '{session_name}': originally '{original_name}', archived {archive_timestamp}, {file_count} files")
                    
                    sessions_data.append({
                        "name": session_name,
                        "original_name": original_name,
                        "archive_timestamp": archive_timestamp,
                        "files": actual_file_count,
                        "metadata_file_count": file_count,
                        "valid": True
                    })
                    valid_sessions += 1
                    result.add_success(f"Processed archived session '{session_name}': {file_count} files")

                except (OSError, PermissionError) as e:
                    self.debugger.debug(f"File system error reading archive metadata file {metadata_file}: {e}")
                    
                    sessions_data.append({
                        "name": session_name,
                        "valid": False,
                        "error": f"File access error: {e}"
                    })
                except json.JSONDecodeError as e:
                    self.debugger.debug(f"JSON decode error reading archive metadata file {metadata_file}: {e}")
                    
                    sessions_data.append({
                        "name": session_name,
                        "valid": False,
                        "error": f"JSON decode error: line {e.lineno}"
                    })
                except Exception as e:
                    self.debugger.debug(f"Unexpected error reading archive metadata file {metadata_file}: {e}")
                    
                    sessions_data.append({
                        "name": session_name,
                        "valid": False,
                        "error": str(e)
                    })
                    invalid_sessions += 1
                    result.add_warning(f"Failed to read archived session metadata '{session_name}': {e}")
            else:
                self.debugger.debug(f"Archived session directory {session_dir} missing .archive-metadata.json")
                
                # Try to get some basic info from the directory
                try:
                    all_files = list(session_dir.iterdir())
                    file_count = len(all_files)
                    
                    sessions_data.append({
                        "name": session_name,
                        "original_name": "Unknown",
                        "archive_timestamp": "Unknown",
                        "files": file_count,
                        "valid": False,
                        "error": "Missing archive metadata"
                    })
                except Exception as e:
                    sessions_data.append({
                        "name": session_name,
                        "valid": False,
                        "error": f"Missing metadata and directory read error: {e}"
                    })
                
                invalid_sessions += 1
                result.add_warning(f"Archived session '{session_name}' is incomplete: missing .archive-metadata.json")
        
        result.data = {
            "archived_sessions": sessions_data,
            "archived_count": len(session_dirs),
        }
        
        if invalid_sessions > 0:
            result.add_warning(f"Found {invalid_sessions} invalid/incomplete archived sessions")
        
        return result
