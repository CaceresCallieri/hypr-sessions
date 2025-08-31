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
    
    def _extract_safe_original_name(self, archived_session_name: str, result: OperationResult) -> str:
        """
        Safely extract original session name from archived session name with validation.
        
        Args:
            archived_session_name: The archived session name (e.g., 'session-name-20250831-123456')
            result: OperationResult to add warnings to
            
        Returns:
            Validated original session name or safe fallback
        """
        try:
            # Attempt to extract original name using standard archive format
            if '-' in archived_session_name:
                potential_original = archived_session_name.split('-')[0]
            else:
                potential_original = archived_session_name
            
            # Validate the extracted name using SessionValidator
            SessionValidator.validate_session_name(potential_original)
            
            self.debug_print(f"Successfully extracted safe original name: {potential_original}")
            return potential_original
            
        except SessionValidationError as e:
            # If extracted name is invalid, use safe fallback
            self.debug_print(f"Extracted name '{potential_original}' is invalid: {e}")
            result.add_warning(f"Cannot determine safe original name from archive name '{archived_session_name}': {e}")
            result.add_warning("Using safe fallback name 'recovered-session'")
            return "recovered-session"
        except Exception as e:
            # Handle any unexpected errors during extraction
            self.debug_print(f"Unexpected error during name extraction: {e}")
            result.add_warning(f"Error extracting original name from '{archived_session_name}': {e}")
            result.add_warning("Using safe fallback name 'recovered-session'")
            return "recovered-session"
    
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
                result.add_warning("Archive metadata missing, will extract from archive name")
                original_name = self._extract_safe_original_name(archived_session_name, result)
            else:
                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                    
                    # Validate metadata structure
                    if not isinstance(metadata, dict):
                        raise ValueError(f"Archive metadata is not a valid dictionary: {type(metadata)}")
                    
                    # Extract original name from metadata with validation
                    original_name = str(metadata.get("original_name", archived_session_name))
                    if not original_name.strip():
                        result.add_warning("Archive metadata contains empty original name")
                        original_name = self._extract_safe_original_name(archived_session_name, result)
                    else:
                        # Validate extracted name from metadata
                        try:
                            SessionValidator.validate_session_name(original_name)
                            self.debug_print(f"Found valid original name in metadata: {original_name}")
                            result.add_success("Archive metadata read successfully")
                        except SessionValidationError:
                            result.add_warning(f"Archive metadata contains invalid original name: {original_name}")
                            original_name = self._extract_safe_original_name(archived_session_name, result)
                except (json.JSONDecodeError, ValueError) as e:
                    self.debug_print(f"Error reading metadata: {e}")
                    result.add_warning(f"Could not read archive metadata: {e}")
                    original_name = self._extract_safe_original_name(archived_session_name, result)
                except Exception as e:
                    self.debug_print(f"Unexpected error reading metadata: {e}")
                    result.add_warning(f"Unexpected error reading archive metadata: {e}")
                    original_name = self._extract_safe_original_name(archived_session_name, result)
            
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
            
        except (OSError, PermissionError, shutil.Error) as e:
            self.debug_print(f"File system error during recovery operation: {e}")
            result.add_error(f"Failed to recover session due to file system error: {e}")
            
            # Attempt to restore from backup after file system error
            self._attempt_backup_restoration(temp_metadata_file, archived_dir, final_active_dir, metadata_file, result)
            return result
        except Exception as e:
            self.debug_print(f"Unexpected error during recovery operation: {e}")
            result.add_error(f"Unexpected error during recovery: {e}")
            
            # Attempt to restore from backup after unexpected error
            self._attempt_backup_restoration(temp_metadata_file, archived_dir, final_active_dir, metadata_file, result)
            return result
    
    def _attempt_backup_restoration(self, temp_metadata_file: Optional[Path], 
                                  archived_dir: Path, final_active_dir: Path, 
                                  metadata_file: Path, result: OperationResult) -> None:
        """Attempt to restore archive from backup after recovery failure"""
        
        if not temp_metadata_file or not temp_metadata_file.exists():
            self.debug_print("No backup available for restoration")
            return
        
        try:
            # Case 1: Archive directory was moved but recovery failed
            if not archived_dir.exists() and final_active_dir.exists():
                self.debug_print("Restoring archive directory from recovered location")
                shutil.move(str(final_active_dir), str(archived_dir))
                
                # Restore metadata
                if metadata_file.exists():
                    metadata_file.unlink()
                shutil.move(str(temp_metadata_file), str(metadata_file))
                
                self.debug_print("Successfully restored archive from backup")
                result.add_warning("Recovery failed, session restored to archive")
                return
            
            # Case 2: Just cleanup temp metadata
            temp_metadata_file.unlink()
            self.debug_print("Cleaned up temporary metadata file")
            
        except (OSError, PermissionError) as restore_error:
            self.debug_print(f"Warning: Could not restore from backup: {restore_error}")
            result.add_warning("Recovery failed and backup restoration also failed")
            # Try to at least cleanup temp file
            try:
                if temp_metadata_file.exists():
                    temp_metadata_file.unlink()
            except:
                pass  # Best effort cleanup