"""
Session recovery functionality - recover archived sessions back to active
"""

import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

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
        
        # Perform the atomic recovery operation
        final_active_dir = self.config.get_active_sessions_dir() / target_name
        try:
            # Count files for user feedback
            files_in_archive = list(archived_dir.iterdir())
            file_count = len(files_in_archive)
            
            self.debug_print(f"Recovering {file_count} files from archive using atomic recovery")
            
            # Perform atomic recovery with metadata-first pattern
            self._perform_atomic_recovery(archived_dir, final_active_dir, target_name, file_count)
            
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
            self.debug_print(f"File system error during atomic recovery: {e}")
            result.add_error(f"Failed to recover session due to file system error: {e}")
            return result
        except Exception as e:
            self.debug_print(f"Unexpected error during atomic recovery: {e}")
            result.add_error(f"Unexpected error during recovery: {e}")
            return result
    
    def _perform_atomic_recovery(self, archived_dir: Path, final_active_dir: Path, 
                               target_name: str, file_count: int) -> None:
        """
        Perform atomic recovery using metadata-first pattern for data safety.
        
        This method implements a robust atomic recovery process:
        1. Creates recovery-in-progress marker with operation metadata
        2. Performs atomic directory move (atomic on same filesystem)
        3. Cleans up archive metadata from recovered session
        4. Removes recovery marker on success
        5. Automatic rollback on any failure
        
        Args:
            archived_dir: Path to archived session directory
            final_active_dir: Target path in active sessions directory
            target_name: Name for recovered session
            file_count: Number of files being recovered (for logging)
            
        Raises:
            OSError, PermissionError: File system errors during recovery
            Exception: Any other errors during recovery process
        """
        from datetime import datetime
        import json
        
        # Step 1: Create recovery-in-progress marker
        recovery_marker = final_active_dir.parent / f".recovery-in-progress-{target_name}.tmp"
        recovery_info = {
            "target_name": target_name,
            "archived_dir": str(archived_dir),
            "recovery_timestamp": datetime.now().isoformat(),
            "recovery_version": "1.0",
            "file_count": file_count
        }
        
        try:
            # Write recovery marker with operation details
            self.debug_print(f"Creating recovery marker: {recovery_marker}")
            with open(recovery_marker, "w") as f:
                json.dump(recovery_info, f, indent=2)
            
            # Step 2: Perform atomic directory move (atomic on same filesystem)
            self.debug_print(f"Moving archive to active: {archived_dir} -> {final_active_dir}")
            shutil.move(str(archived_dir), str(final_active_dir))
            self.debug_print(f"Successfully moved session to active directory")
            
            # Step 3: Clean up archive metadata from recovered session
            archive_metadata_in_recovered = final_active_dir / ".archive-metadata.json"
            if archive_metadata_in_recovered.exists():
                archive_metadata_in_recovered.unlink()
                self.debug_print("Removed archive metadata from recovered session")
            
            # Step 4: Remove recovery marker (indicates successful completion)
            recovery_marker.unlink()
            self.debug_print("Recovery completed successfully, removed recovery marker")
            
        except Exception as e:
            # Automatic rollback: If final_active_dir exists, move it back to archived location
            self.debug_print(f"Recovery failed with error: {e}, attempting rollback")
            
            if final_active_dir.exists() and not archived_dir.exists():
                try:
                    self.debug_print("Rolling back: moving recovered session back to archive")
                    shutil.move(str(final_active_dir), str(archived_dir))
                    self.debug_print("Successfully rolled back partial recovery")
                except Exception as rollback_error:
                    self.debug_print(f"WARNING: Rollback failed: {rollback_error}")
                    # Note: Recovery marker will still exist to indicate failed state
            
            # Clean up recovery marker (whether rollback succeeded or failed)
            if recovery_marker.exists():
                try:
                    recovery_marker.unlink()
                    self.debug_print("Cleaned up recovery marker after failure")
                except Exception as marker_cleanup_error:
                    self.debug_print(f"WARNING: Could not clean up recovery marker: {marker_cleanup_error}")
            
            # Re-raise original exception to let caller handle it
            raise e
    
    def check_interrupted_recoveries(self) -> List[str]:
        """
        Check for any interrupted recovery operations and return list of recovery markers.
        This can be used for system health checks and cleanup operations.
        
        Returns:
            List of recovery marker filenames indicating interrupted operations
        """
        active_sessions_dir = self.config.get_active_sessions_dir()
        recovery_markers = []
        
        try:
            if not active_sessions_dir.exists():
                return recovery_markers
                
            for item in active_sessions_dir.iterdir():
                if item.name.startswith('.recovery-in-progress-') and item.suffix == '.tmp':
                    recovery_markers.append(item.name)
                    self.debug_print(f"Found interrupted recovery marker: {item.name}")
                    
        except Exception as e:
            self.debug_print(f"Error checking for interrupted recoveries: {e}")
        
        return recovery_markers
    
    def cleanup_interrupted_recovery(self, recovery_marker_name: str) -> bool:
        """
        Clean up an interrupted recovery operation by removing stale recovery marker.
        
        Args:
            recovery_marker_name: Name of the recovery marker file to clean up
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            active_sessions_dir = self.config.get_active_sessions_dir()
            marker_path = active_sessions_dir / recovery_marker_name
            
            if marker_path.exists() and marker_path.suffix == '.tmp':
                marker_path.unlink()
                self.debug_print(f"Cleaned up interrupted recovery marker: {recovery_marker_name}")
                return True
            else:
                self.debug_print(f"Recovery marker not found or invalid: {recovery_marker_name}")
                return False
                
        except Exception as e:
            self.debug_print(f"Error cleaning up recovery marker {recovery_marker_name}: {e}")
            return False
    
    def get_recovery_marker_info(self, recovery_marker_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information from a recovery marker file.
        
        Args:
            recovery_marker_name: Name of the recovery marker file
            
        Returns:
            Dictionary with recovery information, or None if marker cannot be read
        """
        try:
            active_sessions_dir = self.config.get_active_sessions_dir()
            marker_path = active_sessions_dir / recovery_marker_name
            
            if marker_path.exists():
                with open(marker_path, 'r') as f:
                    recovery_info = json.load(f)
                return recovery_info
            else:
                return None
                
        except Exception as e:
            self.debug_print(f"Error reading recovery marker {recovery_marker_name}: {e}")
            return None
    
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