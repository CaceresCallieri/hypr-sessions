"""
Session recovery functionality - recover archived sessions back to active
"""

import json
import shutil
from pathlib import Path
from typing import Optional

from .shared.config import get_config, SessionConfig
from .shared.operation_result import OperationResult
from .shared.utils import Utils
from .shared.validation import SessionValidator, SessionNotFoundError, SessionValidationError, SessionAlreadyExistsError


class SessionRecovery(Utils):
    def __init__(self, debug: bool = False) -> None:
        super().__init__()
        self.debug: bool = debug
        self.config: SessionConfig = get_config()
    
    def debug_print(self, message: str) -> None:
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG SessionRecovery] {message}")
    
    def recover_session(self, archived_session_name: str, new_name: Optional[str] = None) -> OperationResult:
        """Recover an archived session back to active sessions"""
        result = OperationResult(operation_name=f"Recover archived session '{archived_session_name}'")
        
        try:
            # Validate archived session name
            SessionValidator.validate_session_name(archived_session_name)
            result.add_success("Archived session name validated")
            
            self.debug_print(f"Attempting to recover archived session: {archived_session_name}")
            
            # Check if archived session exists
            archived_dir = self.config.get_archived_session_directory(archived_session_name)
            if not archived_dir.exists():
                raise SessionNotFoundError(f"Archived session '{archived_session_name}' not found")
            
            # Read archive metadata to get original name
            metadata_file = archived_dir / ".archive-metadata.json"
            if not metadata_file.exists():
                result.add_warning("Archive metadata missing, will use provided name")
                original_name = archived_session_name.split('-')[0] if '-' in archived_session_name else archived_session_name
            else:
                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                    original_name = metadata.get("original_name", archived_session_name)
                    self.debug_print(f"Found original name in metadata: {original_name}")
                    result.add_success("Archive metadata read successfully")
                except Exception as e:
                    self.debug_print(f"Error reading metadata: {e}")
                    result.add_warning(f"Could not read archive metadata: {e}")
                    original_name = archived_session_name.split('-')[0] if '-' in archived_session_name else archived_session_name
            
            # Determine target name (use new_name if provided, otherwise original_name)
            target_name = new_name if new_name else original_name
            
            # Validate target name
            if new_name:
                SessionValidator.validate_session_name(new_name)
                result.add_success("New session name validated")
            
            self.debug_print(f"Target recovery name: {target_name}")
            
            # Check if target name already exists in active sessions (without creating it)
            active_target_dir = self.config.get_active_sessions_dir() / target_name
            if active_target_dir.exists():
                raise SessionAlreadyExistsError(f"Active session '{target_name}' already exists")
            
            result.add_success("Target session name is available")
            
            # Ensure active sessions directory exists
            active_sessions_dir = self.config.get_active_sessions_dir()
            active_sessions_dir.mkdir(parents=True, exist_ok=True)
            
        except (SessionValidationError, SessionNotFoundError, SessionAlreadyExistsError) as e:
            self.debug_print(f"Validation error: {e}")
            result.add_error(str(e))
            return result
        
        # Perform the recovery operation
        temp_metadata_file = None
        final_active_dir = self.config.get_active_sessions_dir() / target_name
        try:
            # Count files for user feedback
            files_in_archive = list(archived_dir.iterdir())
            file_count = len(files_in_archive)
            
            self.debug_print(f"Recovering {file_count} files from archive")
            
            # Create backup of metadata before moving (in case of failure)
            if metadata_file.exists():
                temp_metadata_file = archived_dir.parent / f".recovery-backup-{archived_session_name}.json"
                shutil.copy2(str(metadata_file), str(temp_metadata_file))
                self.debug_print(f"Created metadata backup: {temp_metadata_file}")
            
            # Move archived session to active sessions (with target name)
            self.debug_print(f"Moving archive to active: {archived_dir} -> {final_active_dir}")
            shutil.move(str(archived_dir), str(final_active_dir))
            self.debug_print(f"Successfully moved session to active directory")
            
            # Remove archive metadata file (it's now in active directory)
            archive_metadata_in_active = final_active_dir / ".archive-metadata.json"
            if archive_metadata_in_active.exists():
                archive_metadata_in_active.unlink()
                self.debug_print("Removed archive metadata from recovered session")
            
            # Clean up backup metadata file
            if temp_metadata_file and temp_metadata_file.exists():
                temp_metadata_file.unlink()
                temp_metadata_file = None
                self.debug_print("Cleaned up metadata backup")
            
            result.add_success(f"Recovered session with {file_count} files")
            
            result.data = {
                "archived_session_name": archived_session_name,
                "recovered_session_name": target_name,
                "original_name": original_name,
                "files_recovered": file_count,
                "active_session_dir": str(final_active_dir)
            }
            
            return result
            
        except Exception as e:
            self.debug_print(f"Error during recovery operation: {e}")
            
            # Restore from backup if possible
            if temp_metadata_file and temp_metadata_file.exists():
                try:
                    # If we have a backup and the original archive dir is gone, try to restore
                    if not archived_dir.exists() and final_active_dir.exists():
                        shutil.move(str(final_active_dir), str(archived_dir))
                        if metadata_file.exists():
                            metadata_file.unlink()
                        shutil.move(str(temp_metadata_file), str(metadata_file))
                        self.debug_print("Restored archive from backup after recovery failure")
                        result.add_warning("Recovery failed, session restored to archive")
                    else:
                        temp_metadata_file.unlink()
                        self.debug_print("Cleaned up metadata backup after recovery failure")
                except Exception as restore_error:
                    self.debug_print(f"Could not restore from backup: {restore_error}")
                    result.add_warning("Recovery failed and backup restoration also failed")
            
            result.add_error(f"Failed to recover session: {e}")
            return result