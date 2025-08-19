"""
Base operation class for browse panel operations (delete, restore, etc.)
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from fabric.widgets.button import Button
from fabric.widgets.label import Label

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib

import sys
from pathlib import Path

# Add grandparent directory to path for clean imports
grandparent_dir = str(Path(__file__).parent.parent.parent)
if grandparent_dir not in sys.path:
    sys.path.append(grandparent_dir)

from utils import BackendError
from constants import BROWSING_STATE


class BaseOperation(ABC):
    """Abstract base class for session operations"""
    
    # Configuration constants shared by all operations
    OPERATION_TIMEOUT = 35  # seconds (longer than backend timeout)
    MIN_DISPLAY_TIME = 0.5  # seconds (minimum operation state visibility)
    SUCCESS_AUTO_RETURN_DELAY = 2  # seconds (auto-return from success)
    
    # Required configuration keys for concrete operations
    REQUIRED_CONFIG_KEYS = {
        "color", "action_verb", "description", "button_prefix", 
        "success_description", "progress_state", "operation_timeout"
    }
    
    def __init__(self, panel, backend_client):
        """
        Initialize the operation
        
        Args:
            panel: The browse panel widget that owns this operation
            backend_client: Backend client for API calls
            
        Raises:
            ValueError: If operation configuration is invalid
        """
        self.panel = panel
        self.backend_client = backend_client
        self.selected_session = None
        self.operation_in_progress = False
        self.timeout_id = None
        
        # Validate configuration early to catch implementation errors
        self._validate_configuration()
    
    # Abstract methods - must be implemented by concrete operations
    
    @abstractmethod
    def execute_backend_operation(self, session_name: str) -> Dict[str, Any]:
        """Execute the specific backend operation"""
        pass
    
    @abstractmethod
    def get_operation_config(self) -> Dict[str, str]:
        """
        Get operation-specific configuration
        
        Returns:
            Dict with keys: color, action_verb, description, button_prefix, success_description, progress_state
        """
        pass
    
    @abstractmethod
    def cleanup_after_success(self):
        """Handle any post-success cleanup (e.g., refresh session list)"""
        pass
    
    # Shared implementation methods
    
    def create_confirmation_ui(self) -> List:
        """Create the confirmation UI"""
        session_name = self.selected_session or "Unknown"
        config = self.get_operation_config()
        
        # Main confirmation message
        warning_message = Label(
            text=f"{config['action_verb']} Session: {session_name}",
            name=f"{config['button_prefix']}-title"
        )
        warning_message.set_markup(f"<span weight='bold' color='{config['color']}'>{config['action_verb']} Session: {session_name}</span>")
        
        # Confirmation text
        confirm_message = Label(text=config['description'].format(session_name=session_name), name=f"{config['button_prefix']}-confirmation")
        
        # Instructions
        instructions = Label(
            text=f"Press Enter to {config['action_verb'].upper()} • Esc to Cancel",
            name=f"{config['button_prefix']}-instructions"
        )
        instructions.set_markup(f"<span size='small' style='italic'>Press Enter to {config['action_verb'].upper()} • Esc to Cancel</span>")
        
        return [warning_message, confirm_message, instructions]
    
    def create_progress_ui(self) -> List:
        """Create the operation progress UI"""
        session_name = self.selected_session or "Unknown"
        config = self.get_operation_config()
        
        # Center-aligned progress message
        progress_message = Label(
            text=f"{config['action_verb']}ing session '{session_name}'...",
            name=f"{config['button_prefix']}-status-info"
        )
        progress_message.set_markup(
            f"<span size='large'>{config['action_verb']}ing session</span>\n"
            f"<span weight='bold'>'{session_name}'</span>\n"
            f"<span size='small' style='italic'>Please wait...</span>"
        )
        
        return [progress_message]
    
    def create_success_ui(self) -> List:
        """Create the success state UI"""
        session_name = self.selected_session or "Unknown"
        config = self.get_operation_config()
        
        success_message = Label(
            text=f"Session '{session_name}' {config['success_description']}!",
            name=f"{config['button_prefix']}-status-success"
        )
        success_message.set_markup(
            f"<span size='large'>Success!</span>\n"
            f"<span weight='bold'>Session '{session_name}'</span>\n"
            f"<span>{config['success_description']}</span>"
        )
        
        # Auto-return to browsing state after configured delay
        GLib.timeout_add_seconds(self.SUCCESS_AUTO_RETURN_DELAY, self._return_to_browsing)
        
        return [success_message]
    
    def create_error_ui(self) -> List:
        """Create the error state UI with retry option"""
        session_name = self.selected_session or "Unknown"
        config = self.get_operation_config()
        
        error_message = Label(
            text=f"Failed to {config['action_verb'].lower()} session",
            name=f"{config['button_prefix']}-status-error"
        )
        error_message.set_markup(
            f"<span size='large'>{config['action_verb']} Failed</span>\n"
            f"<span size='small'>Session '{session_name}'</span>\n"
            f"<span size='small' style='italic'>Check the error and try again</span>"
        )
        
        # Retry button
        retry_button = Button(
            label="Try Again",
            name=f"{config['button_prefix']}-retry-button",
            on_clicked=self._handle_retry_clicked,
        )
        
        # Back button
        back_button = Button(
            label="Back to Sessions",
            name=f"{config['button_prefix']}-back-button",
            on_clicked=self._handle_back_to_browsing_clicked,
        )
        
        return [error_message, retry_button, back_button]
    
    def trigger_operation(self):
        """Trigger the operation for the selected session"""
        # Prevent multiple concurrent operations
        if self.operation_in_progress:
            print(f"{self.get_operation_config()['action_verb']} already in progress, ignoring request")
            return
            
        if not self.selected_session:
            print(f"No session selected for {self.get_operation_config()['action_verb'].lower()}")
            return
            
        if not self.backend_client:
            print("Backend client unavailable")
            return

        # Mark operation as in progress
        self.operation_in_progress = True
        
        # Transition to progress state
        self.panel.set_state(self.get_operation_config()['progress_state'])

        # Start operation with timeout protection
        self._start_operation(self.selected_session)
    
    def _start_operation(self, session_name):
        """Start the actual operation asynchronously"""
        # Set operation-specific timeout
        operation_timeout = self.get_operation_config().get("operation_timeout", self.OPERATION_TIMEOUT)
        self.timeout_id = GLib.timeout_add_seconds(operation_timeout, self._handle_timeout)
        
        def run_operation():
            """Run the operation in a separate thread"""
            try:
                # Ensure progress state is visible for at least 500ms for better UX
                start_time = time.time()
                
                # Call backend operation
                result = self.execute_backend_operation(session_name)
                
                # Calculate minimum delay to show progress state
                elapsed = time.time() - start_time
                if elapsed < self.MIN_DISPLAY_TIME:
                    time.sleep(self.MIN_DISPLAY_TIME - elapsed)
                
                # Schedule UI update on main thread
                GLib.idle_add(self._handle_success, session_name, result)
                
            except BackendError as e:
                # Backend-specific error with clear context
                error_msg = f"Backend error: {e}"
                print(f"{self.get_operation_config()['action_verb']} operation failed: {error_msg}")
                GLib.idle_add(self._handle_error_async, session_name, error_msg)
                
            except FileNotFoundError as e:
                # File system error - likely missing session files
                error_msg = f"Session files not found: {e}"
                print(f"{self.get_operation_config()['action_verb']} operation failed: {error_msg}")
                GLib.idle_add(self._handle_error_async, session_name, error_msg)
                
            except PermissionError as e:
                # Permission error - filesystem access issues
                error_msg = f"Permission denied: {e}"
                print(f"{self.get_operation_config()['action_verb']} operation failed: {error_msg}")
                GLib.idle_add(self._handle_error_async, session_name, error_msg)
                
            except ConnectionError as e:
                # Network or IPC connection issues
                error_msg = f"Connection failed: {e}"
                print(f"{self.get_operation_config()['action_verb']} operation failed: {error_msg}")
                GLib.idle_add(self._handle_error_async, session_name, error_msg)
                
            except TimeoutError as e:
                # Operation-specific timeout (different from our UI timeout)
                error_msg = f"Operation timed out: {e}"
                print(f"{self.get_operation_config()['action_verb']} operation failed: {error_msg}")
                GLib.idle_add(self._handle_error_async, session_name, error_msg)
                
            except Exception as e:
                # Unexpected error - log more details for debugging
                error_msg = f"Unexpected error: {e}"
                print(f"{self.get_operation_config()['action_verb']} operation failed with unexpected error: {type(e).__name__}: {e}")
                GLib.idle_add(self._handle_error_async, session_name, error_msg)
        
        # Start the operation in a background thread
        operation_thread = threading.Thread(target=run_operation, daemon=True)
        operation_thread.start()
    
    def _handle_success(self, session_name, result):
        """Handle successful operation on main thread"""
        self._cleanup_operation()
        
        if result.get("success", False):
            # Success - transition to success state
            self.panel.set_state(f"{self.get_operation_config()['button_prefix']}_success")
        else:
            # Backend returned error - transition to error state
            error_msg = result.get("messages", [{}])[0].get(
                "message", "Unknown error"
            )
            self.panel.set_state(f"{self.get_operation_config()['button_prefix']}_error")
        
        return False  # Don't repeat this idle callback

    def _handle_error_async(self, session_name, error_message):
        """Handle operation error on main thread"""
        self._cleanup_operation()
            
        # Backend communication error
        self.panel.set_state(f"{self.get_operation_config()['button_prefix']}_error")
        
        return False  # Don't repeat this idle callback

    def _cleanup_operation(self):
        """Clean up the current operation"""
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        self.operation_in_progress = False

    def _handle_timeout(self):
        """Handle operation timeout"""
        print(f"{self.get_operation_config()['action_verb']} operation timed out")
        self._cleanup_operation()
        self.panel.set_state(f"{self.get_operation_config()['button_prefix']}_error")
        return False  # Don't repeat timeout

    def _return_to_browsing(self):
        """Return to browsing state after success"""
        self.selected_session = None
        self.panel.set_state(BROWSING_STATE)
        self.cleanup_after_success()
        return False  # Don't repeat timeout

    def _handle_retry_clicked(self, button):
        """Handle retry button click in error state"""
        # Prevent multiple concurrent operations
        if self.operation_in_progress:
            return
            
        # Mark operation as in progress and transition back to progress state
        self.operation_in_progress = True
        self.panel.set_state(self.get_operation_config()['progress_state'])
        self._start_operation(self.selected_session)

    def _handle_back_to_browsing_clicked(self, button):
        """Handle back to browsing button click in error state"""
        self.selected_session = None
        self.panel.set_state(BROWSING_STATE)
    
    def _validate_configuration(self):
        """
        Validate that the operation configuration contains all required keys
        
        Raises:
            ValueError: If configuration is missing required keys or has invalid values
        """
        try:
            config = self.get_operation_config()
        except Exception as e:
            raise ValueError(f"Failed to get operation configuration: {e}")
        
        if not isinstance(config, dict):
            raise ValueError(f"Configuration must be a dictionary, got {type(config)}")
        
        # Check for required keys
        missing_keys = self.REQUIRED_CONFIG_KEYS - set(config.keys())
        if missing_keys:
            operation_name = self.__class__.__name__
            raise ValueError(f"{operation_name} missing required config keys: {missing_keys}")
        
        # Validate specific key values
        if not config.get("color") or not isinstance(config["color"], str):
            raise ValueError("Config 'color' must be a non-empty string")
            
        if not config.get("action_verb") or not isinstance(config["action_verb"], str):
            raise ValueError("Config 'action_verb' must be a non-empty string")
            
        if not config.get("button_prefix") or not isinstance(config["button_prefix"], str):
            raise ValueError("Config 'button_prefix' must be a non-empty string")
            
        if not config.get("progress_state") or not isinstance(config["progress_state"], str):
            raise ValueError("Config 'progress_state' must be a non-empty string")
            
        # Validate operation timeout
        timeout = config.get("operation_timeout")
        if timeout is not None:
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ValueError("Config 'operation_timeout' must be a positive number")