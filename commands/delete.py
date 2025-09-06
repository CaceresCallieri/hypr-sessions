"""
Session archive functionality (formerly delete)
"""

import errno
import fcntl
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from .shared.config import get_config, SessionConfig
from .shared.operation_result import OperationResult
from .shared.utils import Utils
from .shared.validation import SessionValidator, SessionNotFoundError, SessionValidationError


class SessionArchive(Utils):
    def __init__(self, debug: bool = False) -> None:
        super().__init__()
        self.debug: bool = debug
        self.config: SessionConfig = get_config()
    
    def debug_print(self, message: str) -> None:
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG SessionArchive] {message}")
    
    def archive_session(self, session_name: str) -> OperationResult:
        """Archive a saved session to the archived directory"""
        result = OperationResult(operation_name=f"Archive session '{session_name}'")
        
        try:
            # Validate session name (already done in CLI, but adding here for direct usage)
            SessionValidator.validate_session_name(session_name)
            result.add_success("Session name validated")
            
            self.debug_print(f"Attempting to archive session: {session_name}")
            
            # Check if session exists BEFORE calling get_active_session_directory (which creates directory)
            session_dir = self.config.get_active_sessions_dir() / session_name
            SessionValidator.validate_session_exists(session_dir, session_name)
            result.add_success("Session exists and is accessible")
            
            # Now get the session directory (it won't create since it exists)
            session_dir = self.config.get_active_session_directory(session_name)
            self.debug_print(f"Session directory path: {session_dir}")
            
            # Validate archived sessions directory is accessible
            SessionValidator.validate_archived_sessions_dir(self.config.get_archived_sessions_dir())
            result.add_success("Archived sessions directory accessible")
            
        except (SessionValidationError, SessionNotFoundError) as e:
            self.debug_print(f"Validation error: {e}")
            result.add_error(str(e))
            return result

        self.debug_print(f"Session directory exists, proceeding with archiving")
        temp_metadata_file = None
        try:
            # Count files before archiving for user feedback
            files_in_session = list(session_dir.iterdir())
            file_count = len(files_in_session)
            
            # Generate timestamped archive name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            archived_name = f"{session_name}-{timestamp}"
            
            # Create archived session directory path (don't create yet)
            archived_dir = self.config.get_archived_session_directory(archived_name)
            
            # METADATA-FIRST PATTERN: Create metadata in temporary location first
            archived_sessions_dir = self.config.get_archived_sessions_dir()
            temp_metadata_file = archived_sessions_dir / f".archive-metadata-{archived_name}.tmp"
            metadata = self._create_archive_metadata(session_name, archived_name, file_count)
            
            self.debug_print(f"Creating temporary metadata: {temp_metadata_file}")
            with open(temp_metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            self.debug_print(f"Temporary metadata created successfully")
            
            # Now perform the irreversible operation: move session directory
            self.debug_print(f"Moving session to archive: {archived_dir}")
            shutil.move(str(session_dir), str(archived_dir))
            self.debug_print(f"Successfully moved session directory to archive")
            
            # Move metadata to final location (atomic rename)
            final_metadata_file = archived_dir / ".archive-metadata.json"
            temp_metadata_file.rename(final_metadata_file)
            temp_metadata_file = None  # Successfully moved, don't clean up
            self.debug_print(f"Moved metadata to final location: {final_metadata_file}")
            
            result.add_success(f"Archived session directory and {file_count} files")
            
            # Enforce archive size limits if enabled
            if self.config.archive_auto_cleanup:
                cleanup_result = self._enforce_archive_limits()
                if cleanup_result:
                    result.add_success(f"Archive cleanup: {cleanup_result}")
            
            result.data = {
                "session_name": session_name,
                "archived_name": archived_name,
                "files_archived": file_count,
                "archived_dir": str(archived_dir)
            }
            return result
        except Exception as e:
            self.debug_print(f"Error archiving session directory {session_dir}: {e}")
            # Clean up temporary metadata file if it exists
            if temp_metadata_file and temp_metadata_file.exists():
                try:
                    temp_metadata_file.unlink()
                    self.debug_print(f"Cleaned up temporary metadata file: {temp_metadata_file}")
                except Exception as cleanup_error:
                    self.debug_print(f"Warning: Could not clean up temporary metadata file: {cleanup_error}")
            
            result.add_error(f"Failed to archive session directory: {e}")
            return result

    def _create_archive_metadata(self, original_name: str, archived_name: str, file_count: int) -> Dict[str, Any]:
        """Create metadata for archived session"""
        return {
            "original_name": original_name,
            "archived_name": archived_name,
            "archive_timestamp": datetime.now().isoformat(),
            "file_count": file_count,
            "archive_version": "1.0"
        }

    def _enforce_archive_limits(self) -> str:
        """Enforce archive size limits and cleanup old archives with concurrent access protection"""
        try:
            archived_sessions_dir = self.config.get_archived_sessions_dir()
            if not archived_sessions_dir.exists():
                return ""

            # Create lock file for archive operations
            lock_file_path = archived_sessions_dir / ".archive-cleanup.lock"
            
            try:
                with open(lock_file_path, 'w') as lock_file:
                    # Acquire exclusive lock (non-blocking)
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.debug_print("Acquired archive cleanup lock")
                    
                    # Perform cleanup operations atomically within the lock
                    return self._perform_archive_cleanup_locked(archived_sessions_dir)
                    
            except (IOError, OSError) as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EACCES:
                    # Another process is cleaning up - this is expected and safe
                    self.debug_print("Archive cleanup skipped - another process is cleaning up")
                    return "Archive cleanup skipped (concurrent operation)"
                else:
                    # Unexpected error - propagate it
                    self.debug_print(f"Unexpected error acquiring archive lock: {e}")
                    raise e
                    
        except Exception as e:
            self.debug_print(f"Error enforcing archive limits: {e}")
            return ""

    def _perform_archive_cleanup_locked(self, archived_sessions_dir: Path) -> str:
        """Perform the actual cleanup operations while holding the lock"""
        # Get all archived sessions
        archived_sessions = []
        for item in archived_sessions_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                metadata_file = item / ".archive-metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                        archived_sessions.append({
                            "path": item,
                            "timestamp": metadata.get("archive_timestamp", ""),
                            "name": item.name
                        })
                    except Exception as e:
                        self.debug_print(f"Error reading metadata for {item}: {e}")

        # Sort by timestamp (oldest first for cleanup)
        archived_sessions.sort(key=lambda x: x["timestamp"])

        # Check if we exceed the limit
        max_sessions = self.config.archive_max_sessions
        if len(archived_sessions) <= max_sessions:
            self.debug_print(f"Archive count {len(archived_sessions)} within limit {max_sessions}")
            return ""

        # Remove oldest sessions to get within limit
        sessions_to_remove = archived_sessions[:len(archived_sessions) - max_sessions]
        removed_count = 0
        cleanup_summary = []

        self.debug_print(f"Need to remove {len(sessions_to_remove)} sessions to stay within limit of {max_sessions}")

        for session_info in sessions_to_remove:
            try:
                shutil.rmtree(session_info["path"])
                removed_count += 1
                cleanup_summary.append(f"Removed {session_info['name']}")
                self.debug_print(f"Removed old archived session: {session_info['name']}")
            except Exception as e:
                self.debug_print(f"Error removing archived session {session_info['name']}: {e}")

        if removed_count > 0:
            return f"removed {removed_count} old archived sessions"
        return ""

    def delete_session(self, session_name: str) -> OperationResult:
        """Legacy method - redirects to archive_session for backward compatibility"""
        return self.archive_session(session_name)
