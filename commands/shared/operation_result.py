"""
Structured operation results for better error handling and user feedback
Provides rich information about operation outcomes including partial failures
"""

import errno
import json
import subprocess
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from enum import Enum


class ResultStatus(Enum):
    """Status levels for operation results"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ResultMessage:
    """Individual result message with status and details"""
    status: ResultStatus
    message: str
    context: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        return self.message


@dataclass
class OperationResult:
    """
    Structured result for operations with support for partial success,
    warnings, errors, and rich debugging information
    """
    success: bool = True
    data: Any = None
    messages: List[ResultMessage] = field(default_factory=list)
    operation_name: Optional[str] = None
    
    def add_success(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Add a success message"""
        self.messages.append(ResultMessage(ResultStatus.SUCCESS, message, context))
    
    def add_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Add a warning message (doesn't affect success status)"""
        self.messages.append(ResultMessage(ResultStatus.WARNING, message, context))
    
    def add_error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Add an error message and mark operation as failed"""
        self.messages.append(ResultMessage(ResultStatus.ERROR, message, context))
        self.success = False
    
    def add_filesystem_error(self, error: Exception, operation: str, path: str) -> None:
        """Add filesystem error with specific guidance based on error type"""
        context = {"error_type": type(error).__name__, "path": path, "operation": operation}
        
        if isinstance(error, PermissionError):
            self.add_error(
                f"Permission denied: Cannot {operation}. Check file permissions for '{path}'.",
                context
            )
        elif isinstance(error, FileNotFoundError):
            self.add_error(
                f"File not found: Cannot {operation} because '{path}' does not exist.",
                context
            )
        elif isinstance(error, FileExistsError):
            self.add_error(
                f"File already exists: Cannot {operation} because '{path}' already exists.",
                context
            )
        elif isinstance(error, OSError) and hasattr(error, 'errno'):
            if error.errno == errno.ENOSPC:
                self.add_error(
                    f"Insufficient disk space: Cannot {operation}. Free up disk space and try again.",
                    context
                )
            elif error.errno == errno.ENAMETOOLONG:
                self.add_error(
                    f"Name too long: Cannot {operation} because the path name is too long for the filesystem.",
                    context
                )
            elif error.errno == errno.EACCES:
                self.add_error(
                    f"Access denied: Cannot {operation}. Check directory permissions for '{path}'.",
                    context
                )
            elif error.errno == errno.ENOTEMPTY:
                self.add_error(
                    f"Directory not empty: Cannot {operation} because '{path}' contains files.",
                    context
                )
            elif error.errno == errno.EROFS:
                self.add_error(
                    f"Read-only filesystem: Cannot {operation} because '{path}' is on a read-only filesystem.",
                    context
                )
            else:
                self.add_error(
                    f"Filesystem error: Cannot {operation}. {str(error)}",
                    context
                )
        elif isinstance(error, IsADirectoryError):
            self.add_error(
                f"Path is a directory: Cannot {operation} because '{path}' is a directory, not a file.",
                context
            )
        elif isinstance(error, NotADirectoryError):
            self.add_error(
                f"Path is not a directory: Cannot {operation} because '{path}' is not a directory.",
                context
            )
        else:
            # Fallback for other filesystem-related errors
            self.add_error(
                f"Filesystem error: Cannot {operation}. {str(error)}",
                context
            )
    
    def add_json_error(self, error: Exception, operation: str, file_path: str) -> None:
        """Add JSON processing error with specific guidance"""
        context = {"error_type": type(error).__name__, "file_path": file_path, "operation": operation}
        
        if isinstance(error, json.JSONDecodeError):
            self.add_error(
                f"Invalid JSON format: Cannot {operation} because '{file_path}' contains malformed JSON data. "
                f"Error at line {error.lineno}, column {error.colno}: {error.msg}",
                context
            )
        elif isinstance(error, FileNotFoundError):
            self.add_error(
                f"Session file not found: Cannot {operation} because '{file_path}' does not exist.",
                context
            )
        elif isinstance(error, PermissionError):
            self.add_error(
                f"Permission denied: Cannot {operation} due to insufficient permissions for '{file_path}'.",
                context
            )
        else:
            self.add_error(
                f"JSON processing error: Cannot {operation}. {str(error)}",
                context
            )
    
    def add_subprocess_error(self, error: Exception, command: str, operation: str) -> None:
        """Add subprocess error with specific guidance"""
        context = {"error_type": type(error).__name__, "command": command, "operation": operation}
        
        if isinstance(error, subprocess.TimeoutExpired):
            timeout = getattr(error, 'timeout', 'unknown')
            self.add_error(
                f"Command timeout: {operation} failed because the command '{command}' "
                f"took longer than {timeout} seconds to complete.",
                context
            )
        elif isinstance(error, subprocess.CalledProcessError):
            return_code = getattr(error, 'returncode', 'unknown')
            stderr = getattr(error, 'stderr', b'').decode() if hasattr(error, 'stderr') and error.stderr else 'No error details available'
            self.add_error(
                f"Command failed: {operation} failed because '{command}' "
                f"exited with code {return_code}. Error: {stderr.strip()}",
                context
            )
        elif isinstance(error, FileNotFoundError):
            self.add_error(
                f"Command not found: {operation} failed because '{command.split()[0] if command else 'unknown'}' "
                f"is not installed or not in PATH.",
                context
            )
        elif isinstance(error, PermissionError):
            self.add_error(
                f"Permission denied: {operation} failed due to insufficient permissions to execute '{command}'.",
                context
            )
        else:
            self.add_error(
                f"Process error: {operation} failed. {str(error)}",
                context
            )
    
    @property
    def errors(self) -> List[ResultMessage]:
        """Get all error messages"""
        return [msg for msg in self.messages if msg.status == ResultStatus.ERROR]
    
    @property
    def warnings(self) -> List[ResultMessage]:
        """Get all warning messages"""
        return [msg for msg in self.messages if msg.status == ResultStatus.WARNING]
    
    @property
    def successes(self) -> List[ResultMessage]:
        """Get all success messages"""
        return [msg for msg in self.messages if msg.status == ResultStatus.SUCCESS]
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
    
    @property
    def has_successes(self) -> bool:
        """Check if there are any successes"""
        return len(self.successes) > 0
    
    @property
    def error_count(self) -> int:
        """Get count of errors"""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """Get count of warnings"""
        return len(self.warnings)
    
    @property
    def success_count(self) -> int:
        """Get count of successes"""
        return len(self.successes)
    
    def has_data(self) -> bool:
        """Check if operation produced data"""
        return self.data is not None
    
    def get_summary(self) -> str:
        """Get a summary of the operation result"""
        if not self.messages:
            return "Operation completed" if self.success else "Operation failed"
        
        summary_parts = []
        if self.success_count > 0:
            summary_parts.append(f"{self.success_count} succeeded")
        if self.warning_count > 0:
            summary_parts.append(f"{self.warning_count} warnings")
        if self.error_count > 0:
            summary_parts.append(f"{self.error_count} errors")
        
        return ", ".join(summary_parts)
    
    def print_detailed_result(self, show_successes: bool = True) -> None:
        """Print a detailed, user-friendly result summary"""
        if self.operation_name:
            status = "✓" if self.success else "✗"
            print(f"{status} {self.operation_name}: {self.get_summary()}")
        
        # Print successes
        if show_successes and self.successes:
            for success in self.successes:
                print(f"  ✓ {success.message}")
        
        # Print warnings
        if self.warnings:
            for warning in self.warnings:
                print(f"  ⚠ Warning: {warning.message}")
        
        # Print errors
        if self.errors:
            for error in self.errors:
                print(f"  ✗ Error: {error.message}")
    
    def print_summary(self) -> None:
        """Print a concise summary"""
        if self.operation_name:
            status = "✓" if self.success else "✗"
            print(f"{status} {self.operation_name}: {self.get_summary()}")
        else:
            print(f"Operation {'succeeded' if self.success else 'failed'}: {self.get_summary()}")
    
    @classmethod
    def success_result(cls, message: str = None, data: Any = None, operation_name: str = None) -> 'OperationResult':
        """Create a successful operation result"""
        result = cls(success=True, data=data, operation_name=operation_name)
        if message:
            result.add_success(message)
        return result
    
    @classmethod
    def error_result(cls, message: str, operation_name: str = None) -> 'OperationResult':
        """Create a failed operation result"""
        result = cls(success=False, operation_name=operation_name)
        result.add_error(message)
        return result
    
    @classmethod
    def from_exception(cls, exception: Exception, operation_name: str = None) -> 'OperationResult':
        """Create a failed result from an exception"""
        return cls.error_result(str(exception), operation_name)


# Convenience functions for common patterns
def success(message: str = None, data: Any = None) -> OperationResult:
    """Create a simple success result"""
    return OperationResult.success_result(message, data)


def error(message: str) -> OperationResult:
    """Create a simple error result"""
    return OperationResult.error_result(message)


def from_bool(success: bool, success_message: str = None, error_message: str = None) -> OperationResult:
    """Convert a boolean result to OperationResult"""
    if success:
        return OperationResult.success_result(success_message or "Operation completed")
    else:
        return OperationResult.error_result(error_message or "Operation failed")