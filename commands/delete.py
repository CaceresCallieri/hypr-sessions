"""
Session archive functionality (formerly delete)
"""

import errno
import fcntl
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from .shared.config import get_config, SessionConfig
from .shared.debug import CommandDebugger
from .shared.operation_result import OperationResult
from .shared.utils import Utils
from .shared.validation import SessionValidator, SessionNotFoundError, SessionValidationError
from .shared.path_cache import path_cache


class SessionArchive(Utils):
    def __init__(self, debug: bool = False) -> None:
        super().__init__()
        self.debugger = CommandDebugger("SessionArchive", debug)
        self.config: SessionConfig = get_config()
    
    def _cleanup_temp_file(self, temp_file: Optional[Path]) -> None:
        """Remove a temporary metadata file if it exists.

        Handles None input gracefully and catches exceptions during cleanup
        to prevent masking the original error.
        """
        if not temp_file:
            return
        if not path_cache.exists(temp_file):
            return
        try:
            temp_file.unlink()
            self.debugger.debug(f"Cleaned up temporary metadata file: {temp_file}")
        except Exception as cleanup_error:
            self.debugger.debug(f"Warning: Could not clean up temporary metadata file: {cleanup_error}")

    def archive_session(self, session_name: str) -> OperationResult:
        """Archive a saved session to the archived directory"""
        result = OperationResult(operation_name=f"Archive session '{session_name}'")
        
        try:
            # Validate session name (already done in CLI, but adding here for direct usage)
            SessionValidator.validate_session_name(session_name)
            result.add_success("Session name validated")
            
            self.debugger.debug(f"Attempting to archive session: {session_name}")
            
            # Check if session exists BEFORE calling get_active_session_directory (which creates directory)
            session_dir = self.config.get_active_sessions_dir() / session_name
            SessionValidator.validate_session_exists(session_dir, session_name)
            result.add_success("Session exists and is accessible")
            
            self.debugger.debug(f"Session directory path: {session_dir}")
            
            # Validate archived sessions directory is accessible (ensure it exists for writing)
            SessionValidator.validate_archived_sessions_dir(self.config.ensure_archived_sessions_dir())
            result.add_success("Archived sessions directory accessible")
            
        except (SessionValidationError, SessionNotFoundError) as e:
            self.debugger.debug(f"Validation error: {e}")
            result.add_error(str(e))
            return result

        self.debugger.debug(f"Session directory exists, proceeding with archiving")
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
            archived_sessions_dir = self.config.ensure_archived_sessions_dir()
            temp_metadata_file = archived_sessions_dir / f".archive-metadata-{archived_name}.tmp"
            metadata = self._create_archive_metadata(session_name, archived_name, file_count)
            
            self.debugger.debug(f"Creating temporary metadata: {temp_metadata_file}")
            with open(temp_metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            self.debugger.debug(f"Temporary metadata created successfully")
            
            # Now perform the irreversible operation: move session directory
            self.debugger.debug(f"Moving session to archive: {archived_dir}")
            shutil.move(str(session_dir), str(archived_dir))
            
            # Invalidate cache for both source and destination paths
            path_cache.invalidate(session_dir)  # Original location (now gone)
            path_cache.invalidate(archived_dir)  # New archived location
            path_cache.invalidate(session_dir.parent)  # Active sessions directory
            path_cache.invalidate(archived_dir.parent)  # Archived sessions directory
            self.debugger.debug(f"Cache invalidated for archive operation: {session_dir} -> {archived_dir}")
            
            self.debugger.debug(f"Successfully moved session directory to archive")
            
            # Move metadata to final location (atomic rename)
            final_metadata_file = archived_dir / ".archive-metadata.json"
            temp_metadata_file.rename(final_metadata_file)
            temp_metadata_file = None  # Successfully moved, don't clean up
            self.debugger.debug(f"Moved metadata to final location: {final_metadata_file}")
            
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
        except (PermissionError, FileNotFoundError, OSError, IOError) as e:
            self.debugger.debug(f"Filesystem error archiving session directory {session_dir}: {e}")
            self._cleanup_temp_file(temp_metadata_file)
            result.add_filesystem_error(e, f"archive session '{session_name}'", str(session_dir))
            return result
        except json.JSONEncodeError as e:
            self.debugger.debug(f"JSON encoding error creating metadata: {e}")
            self._cleanup_temp_file(temp_metadata_file)
            result.add_error(f"Archive metadata creation failed: Cannot create archive metadata for session '{session_name}'. {str(e)}")
            return result
        except ValueError as e:
            self.debugger.debug(f"Data validation error archiving session directory {session_dir}: {e}")
            self._cleanup_temp_file(temp_metadata_file)
            result.add_error(f"Data validation error: Failed to archive session '{session_name}'. {str(e)}")
            return result
        except Exception as e:
            self.debugger.debug(f"Unexpected error archiving session directory {session_dir}: {e}")
            self._cleanup_temp_file(temp_metadata_file)
            result.add_error(f"Unexpected error: Failed to archive session '{session_name}'. {str(e)}")
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
            if not path_cache.exists(archived_sessions_dir):
                return ""

            # Create lock file for archive operations
            lock_file_path = archived_sessions_dir / ".archive-cleanup.lock"
            
            try:
                with open(lock_file_path, 'w') as lock_file:
                    # Acquire exclusive lock (non-blocking)
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.debugger.debug("Acquired archive cleanup lock")
                    
                    # Perform cleanup operations atomically within the lock
                    return self._perform_archive_cleanup_locked(archived_sessions_dir)
                    
            except (IOError, OSError) as e:
                if hasattr(e, 'errno') and e.errno in (errno.EAGAIN, errno.EACCES):
                    # Another process is cleaning up - this is expected and safe
                    self.debugger.debug("Archive cleanup skipped - another process is cleaning up")
                    return "Archive cleanup skipped (concurrent operation)"
                else:
                    # Unexpected error - propagate it
                    self.debugger.debug(f"Unexpected error acquiring archive lock: {e}")
                    raise e
                    
        except (OSError, PermissionError) as e:
            self.debugger.debug(f"File system error enforcing archive limits: {e}")
            return ""
        except Exception as e:
            self.debugger.debug(f"Unexpected error enforcing archive limits: {e}")
            return ""

    def _perform_archive_cleanup_locked(self, archived_sessions_dir: Path) -> str:
        """Perform the actual cleanup operations while holding the lock"""
        # Get all archived sessions
        archived_sessions = []
        for item in archived_sessions_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                metadata_file = item / ".archive-metadata.json"
                if path_cache.exists(metadata_file):
                    try:
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                        archived_sessions.append({
                            "path": item,
                            "timestamp": metadata.get("archive_timestamp", ""),
                            "name": item.name
                        })
                    except (OSError, PermissionError) as e:
                        self.debugger.debug(f"File system error reading metadata for {item}: {e}")
                    except json.JSONDecodeError as e:
                        self.debugger.debug(f"JSON decode error reading metadata for {item}: {e}")
                    except Exception as e:
                        self.debugger.debug(f"Unexpected error reading metadata for {item}: {e}")

        # Sort by timestamp (oldest first for cleanup)
        archived_sessions.sort(key=lambda x: x["timestamp"])

        # Check if we exceed the limit
        max_sessions = self.config.archive_max_sessions
        if len(archived_sessions) <= max_sessions:
            self.debugger.debug(f"Archive count {len(archived_sessions)} within limit {max_sessions}")
            return ""

        # Remove oldest sessions to get within limit
        sessions_to_remove = archived_sessions[:len(archived_sessions) - max_sessions]
        removed_count = 0
        cleanup_summary = []

        self.debugger.debug(f"Need to remove {len(sessions_to_remove)} sessions to stay within limit of {max_sessions}")

        for session_info in sessions_to_remove:
            try:
                shutil.rmtree(session_info["path"])
                removed_count += 1
                cleanup_summary.append(f"Removed {session_info['name']}")
                self.debugger.debug(f"Removed old archived session: {session_info['name']}")
            except (OSError, PermissionError) as e:
                self.debugger.debug(f"File system error removing archived session {session_info['name']}: {e}")
            except Exception as e:
                self.debugger.debug(f"Unexpected error removing archived session {session_info['name']}: {e}")

        if removed_count > 0:
            return f"removed {removed_count} old archived sessions"
        return ""

    def delete_session(self, session_name: str) -> OperationResult:
        """Legacy method - redirects to archive_session for backward compatibility"""
        return self.archive_session(session_name)
