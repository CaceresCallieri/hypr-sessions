"""
Structured operation results for better error handling and user feedback
Provides rich information about operation outcomes including partial failures
"""

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