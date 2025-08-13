"""
Input validation and custom exceptions for hypr-sessions
Provides comprehensive validation for session names, paths, and parameters
"""

import re
import os
from pathlib import Path
from typing import Any, Optional


# Custom Exception Classes
class SessionError(Exception):
    """Base exception for session operations"""
    pass


class SessionValidationError(SessionError):
    """Invalid session data or parameters"""
    pass


class SessionNotFoundError(SessionError):
    """Session does not exist"""
    pass


class InvalidSessionNameError(SessionValidationError):
    """Invalid session name format or characters"""
    pass


class SessionAlreadyExistsError(SessionValidationError):
    """Session already exists when trying to create new one"""
    pass


# Validation Functions
class SessionValidator:
    """Comprehensive validation for session operations"""
    
    # Reserved names that shouldn't be used as session names
    RESERVED_NAMES = {
        ".", "..",  # Directory navigation
    }
    
    # Characters not allowed in session names (filesystem unsafe)
    INVALID_CHARS = '<>:"/\\|?*\0'
    
    # Maximum length for session names (filesystem compatibility)
    MAX_SESSION_NAME_LENGTH = 200  # Conservative limit for cross-platform compatibility
    
    @classmethod
    def validate_session_name(cls, session_name: str) -> None:
        """
        Validate session name for filesystem compatibility and safety
        
        Args:
            session_name: The session name to validate
            
        Raises:
            InvalidSessionNameError: If session name is invalid
        """
        if not session_name:
            raise InvalidSessionNameError("Session name cannot be empty")
        
        if not isinstance(session_name, str):
            raise InvalidSessionNameError(f"Session name must be a string, got {type(session_name)}")
        
        # Check length
        if len(session_name) > cls.MAX_SESSION_NAME_LENGTH:
            raise InvalidSessionNameError(
                f"Session name too long ({len(session_name)} chars). "
                f"Maximum length is {cls.MAX_SESSION_NAME_LENGTH}"
            )
        
        # Check for invalid characters
        invalid_chars_found = [c for c in session_name if c in cls.INVALID_CHARS]
        if invalid_chars_found:
            chars_display = ", ".join(repr(c) for c in invalid_chars_found)
            raise InvalidSessionNameError(
                f"Session name contains invalid characters: {chars_display}. "
                f"Invalid characters: {cls.INVALID_CHARS}"
            )
        
        # Check for control characters
        if any(ord(c) < 32 for c in session_name):
            raise InvalidSessionNameError("Session name contains control characters")
        
        # Check reserved names
        if session_name.lower() in cls.RESERVED_NAMES:
            raise InvalidSessionNameError(
                f"'{session_name}' is a reserved name and cannot be used"
            )
        
        # Check for leading/trailing whitespace or dots
        if session_name != session_name.strip():
            raise InvalidSessionNameError("Session name cannot have leading or trailing whitespace")
        
        if session_name.startswith('.') or session_name.endswith('.'):
            raise InvalidSessionNameError("Session name cannot start or end with dots")
        
        # Check for consecutive spaces or special patterns
        if '  ' in session_name:
            raise InvalidSessionNameError("Session name cannot contain consecutive spaces")
        
        # Check for only whitespace/dots
        if not session_name.replace(' ', '').replace('.', ''):
            raise InvalidSessionNameError("Session name cannot consist only of spaces and dots")
    
    @classmethod
    def validate_session_exists(cls, session_path: Path, session_name: str) -> None:
        """
        Validate that a session exists
        
        Args:
            session_path: Path to the session directory
            session_name: Name of the session for error messages
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        if not session_path.exists():
            raise SessionNotFoundError(f"Session '{session_name}' not found")
        
        if not session_path.is_dir():
            raise SessionValidationError(
                f"Session path exists but is not a directory: {session_path}"
            )
        
        session_file = session_path / "session.json"
        if not session_file.exists():
            raise SessionValidationError(
                f"Session '{session_name}' exists but is missing session.json file"
            )
    
    @classmethod
    def validate_session_not_exists(cls, session_path: Path, session_name: str) -> None:
        """
        Validate that a session doesn't already exist (for save operations)
        
        Args:
            session_path: Path to the session directory
            session_name: Name of the session for error messages
            
        Raises:
            SessionAlreadyExistsError: If session already exists
        """
        if session_path.exists():
            raise SessionAlreadyExistsError(
                f"Session '{session_name}' already exists. Use a different name or delete the existing session first."
            )
    
    @classmethod
    def validate_directory_writable(cls, directory_path: Path) -> None:
        """
        Validate that a directory is writable
        
        Args:
            directory_path: Path to check for write access
            
        Raises:
            SessionValidationError: If directory is not writable
        """
        if not directory_path.exists():
            try:
                directory_path.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise SessionValidationError(
                    f"Cannot create sessions directory: {directory_path} - {e}"
                )
        
        if not directory_path.is_dir():
            raise SessionValidationError(
                f"Sessions path exists but is not a directory: {directory_path}"
            )
        
        # Test write access by creating a temporary file
        test_file = directory_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError) as e:
            raise SessionValidationError(
                f"No write permission for sessions directory: {directory_path} - {e}"
            )
    
    @classmethod
    def validate_workspace_number(cls, workspace: Any) -> int:
        """
        Validate workspace number parameter
        
        Args:
            workspace: Workspace identifier to validate
            
        Returns:
            int: Validated workspace number
            
        Raises:
            SessionValidationError: If workspace number is invalid
        """
        if workspace is None:
            raise SessionValidationError("Workspace number cannot be None")
        
        try:
            workspace_num = int(workspace)
        except (ValueError, TypeError):
            raise SessionValidationError(
                f"Workspace must be a number, got: {workspace} ({type(workspace)})"
            )
        
        if workspace_num < 1 or workspace_num > 10:  # Common Hyprland workspace range
            raise SessionValidationError(
                f"Workspace number must be between 1 and 10, got: {workspace_num}"
            )
        
        return workspace_num
    
    @classmethod
    def validate_debug_flag(cls, debug: Any) -> bool:
        """
        Validate debug flag parameter
        
        Args:
            debug: Debug flag to validate
            
        Returns:
            bool: Validated debug flag
            
        Raises:
            SessionValidationError: If debug flag is invalid
        """
        if not isinstance(debug, bool):
            if isinstance(debug, str):
                debug_lower = debug.lower()
                if debug_lower in ('true', '1', 'yes', 'on'):
                    return True
                elif debug_lower in ('false', '0', 'no', 'off'):
                    return False
                else:
                    raise SessionValidationError(
                        f"Invalid debug flag string: '{debug}'. "
                        f"Use 'true'/'false', '1'/'0', 'yes'/'no', or 'on'/'off'"
                    )
            else:
                raise SessionValidationError(
                    f"Debug flag must be boolean or string, got {type(debug)}: {debug}"
                )
        
        return debug


def validate_session_name(session_name: str) -> None:
    """Convenience function for session name validation"""
    SessionValidator.validate_session_name(session_name)


def validate_session_exists(session_path: Path, session_name: str) -> None:
    """Convenience function for session existence validation"""
    SessionValidator.validate_session_exists(session_path, session_name)


def validate_session_not_exists(session_path: Path, session_name: str) -> None:
    """Convenience function for session non-existence validation"""
    SessionValidator.validate_session_not_exists(session_path, session_name)