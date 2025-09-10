"""
Centralized debug utility for all command components
"""

from typing import Optional
import sys
from datetime import datetime


class CommandDebugger:
    """Centralized debug utility for all commands"""
    
    def __init__(self, component_name: str, enabled: bool = False, verbose: bool = False):
        """Initialize debugger for a specific component
        
        Args:
            component_name: Name of the component for debug output
            enabled: Whether debug output is enabled
            verbose: Whether verbose debug output is enabled
        """
        self.component_name = component_name
        self.enabled = enabled
        self.verbose = verbose
        self.start_time = datetime.now()
    
    def debug(self, message: str, level: str = "info"):
        """Print debug message with consistent formatting
        
        Args:
            message: Debug message to print
            level: Debug level ("info" or "verbose")
        """
        if not self.enabled:
            return
        
        if level == "verbose" and not self.verbose:
            return
        
        elapsed = datetime.now() - self.start_time
        timestamp = elapsed.total_seconds()
        print(f"[DEBUG {self.component_name} {timestamp:.2f}s] {message}", file=sys.stderr)
    
    def debug_operation(self, operation: str, details: str = ""):
        """Debug specific operation with structured output
        
        Args:
            operation: Operation name or description
            details: Optional additional details
        """
        message = f"{operation}"
        if details:
            message += f" | {details}"
        self.debug(message)
    
    def debug_verbose(self, message: str):
        """Debug verbose information (only shown in verbose mode)
        
        Args:
            message: Verbose debug message
        """
        self.debug(message, level="verbose")
    
    def debug_error(self, error: Exception, context: str = ""):
        """Debug error with context information
        
        Args:
            error: Exception that occurred
            context: Context where error occurred
        """
        error_type = type(error).__name__
        message = f"ERROR: {error_type}: {error}"
        if context:
            message = f"{context} - {message}"
        self.debug(message)
    
    def debug_file_operation(self, operation: str, file_path: str, success: bool = True):
        """Debug file operations with standardized format
        
        Args:
            operation: File operation (read, write, delete, etc.)
            file_path: Path to file being operated on
            success: Whether operation was successful
        """
        status = "SUCCESS" if success else "FAILED"
        self.debug(f"FILE {operation.upper()} {status}: {file_path}")
    
    def debug_session_operation(self, operation: str, session_name: str, details: str = ""):
        """Debug session-specific operations
        
        Args:
            operation: Operation being performed
            session_name: Name of session being operated on
            details: Optional additional details
        """
        message = f"SESSION {operation.upper()}: {session_name}"
        if details:
            message += f" | {details}"
        self.debug(message)