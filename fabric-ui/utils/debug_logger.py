"""
UI Debug Logger for Hypr Sessions Manager

Comprehensive logging system for debugging UI interactions, state transitions,
and performance issues. Designed for minimal overhead when disabled.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk


class UIDebugLogger:
    """Centralized debug logging system for UI components"""
    
    # Log levels
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    
    def __init__(self, log_file_path: str = None, enabled: bool = False, verbose_mode: bool = False, 
                 output_to_terminal: bool = True, output_to_file: bool = False):
        """
        Initialize debug logger
        
        Args:
            log_file_path: Path to log file (optional if only using terminal output)
            enabled: Whether debug logging is active
            verbose_mode: Whether to show detailed widget/performance logging
            output_to_terminal: Whether to output debug logs to terminal (default: True)
            output_to_file: Whether to output debug logs to file (default: False)
        """
        self.enabled = enabled
        self.verbose_mode = verbose_mode
        self.output_to_terminal = output_to_terminal
        self.output_to_file = output_to_file
        self.log_file_path = Path(log_file_path) if log_file_path else None
        self.start_time = time.time()
        
        # Buffered logging to prevent UI lag
        self.log_buffer = []
        self.last_flush = time.time()
        self.FLUSH_INTERVAL = 1.0  # Flush every second
        self.MAX_BUFFER_SIZE = 100  # Flush when buffer gets large
        
        if self.enabled:
            # Terminal output header
            if self.output_to_terminal:
                print("=== Hypr Sessions Manager UI Debug Started ===")
                print(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                if self.output_to_file and self.log_file_path:
                    print(f"Also logging to file: {self.log_file_path}")
                print()
            
            # File output setup
            if self.output_to_file and self.log_file_path:
                # Ensure log directory exists
                self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Initialize log file with session header
                with open(self.log_file_path, 'w') as f:
                    f.write(f"=== Hypr Sessions Manager UI Debug Log ===\n")
                    f.write(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Log file: {self.log_file_path}\n\n")
    
    def _write_log(self, component: str, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Write log entry with structured format"""
        if not self.enabled:
            return
            
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Include milliseconds
        elapsed = f"{time.time() - self.start_time:.3f}s"
        
        log_line = f"[{timestamp}] [{elapsed}] [{component}] [{level}] {message}"
        
        if details:
            detail_str = ", ".join([f"{k}={v}" for k, v in details.items()])
            log_line += f" | {detail_str}"
        
        # Output to terminal if enabled
        if self.output_to_terminal:
            print(log_line)
            
        # Output to file if enabled (buffered)
        if self.output_to_file and self.log_file_path:
            self.log_buffer.append(log_line)
            
            # Flush buffer if it's time or buffer is full
            current_time = time.time()
            if (current_time - self.last_flush > self.FLUSH_INTERVAL or 
                len(self.log_buffer) >= self.MAX_BUFFER_SIZE):
                self._flush_buffer()
    
    def _flush_buffer(self):
        """Flush buffered log entries to file"""
        if not self.log_buffer or not self.output_to_file or not self.log_file_path:
            return
            
        try:
            with open(self.log_file_path, 'a') as f:
                for log_line in self.log_buffer:
                    f.write(log_line + '\n')
                f.flush()  # Single flush for entire buffer
            
            self.log_buffer.clear()
            self.last_flush = time.time()
            
        except Exception as e:
            # Fallback to console if file writing fails
            print(f"DEBUG LOG BUFFER FLUSH FAILED: {e}")
            for log_line in self.log_buffer:
                print(log_line)
            self.log_buffer.clear()
    
    def flush_on_exit(self):
        """Flush any remaining buffered logs on shutdown"""
        self._flush_buffer()
    
    # Widget Pool Debug Methods
    
    def debug_widget_pool_operation(self, operation: str, session_name: str, 
                                  reused: bool = False, created: bool = False,
                                  pool_size: int = 0, details: Optional[Dict] = None):
        """Log widget pool operations with context (verbose mode only)"""
        if not self.verbose_mode:
            return
            
        extra_details = {"session": session_name, "pool_size": pool_size}
        if details:
            extra_details.update(details)
            
        action = "reused" if reused else "created" if created else "processed"
        message = f"Widget {action} for '{session_name}' ({operation})"
        
        self._write_log("WIDGET_POOL", self.DEBUG, message, extra_details)
    
    def debug_widget_pool_maintenance(self, operation: str, before_size: int, 
                                    after_size: int, details: Optional[Dict] = None):
        """Log widget pool maintenance operations (verbose mode only)"""
        if not self.verbose_mode:
            return
        extra_details = {"before_size": before_size, "after_size": after_size}
        if details:
            extra_details.update(details)
            
        message = f"Pool {operation}: {before_size} -> {after_size} widgets"
        self._write_log("WIDGET_POOL", self.INFO, message, extra_details)
    
    def debug_widget_property_change(self, session_name: str, property_name: str, 
                                   old_value: Any, new_value: Any, changed: bool):
        """Log widget property change detection (verbose mode only)"""
        if not self.verbose_mode:
            return
        details = {
            "session": session_name,
            "property": property_name,
            "old": str(old_value),
            "new": str(new_value),
            "changed": changed
        }
        
        action = "changed" if changed else "unchanged"
        message = f"Property {property_name} {action} for '{session_name}'"
        
        self._write_log("WIDGET_POOL", self.DEBUG, message, details)
    
    # Focus Management Debug Methods
    
    def debug_focus_operation(self, operation: str, widget_name: str, 
                            success: bool, details: Optional[Dict] = None):
        """Log focus management operations"""
        extra_details = {"widget": widget_name, "success": success}
        if details:
            extra_details.update(details)
            
        result = "SUCCESS" if success else "FAILED"
        message = f"Focus {operation} on {widget_name}: {result}"
        
        level = self.INFO if success else self.WARN
        self._write_log("FOCUS", level, message, extra_details)
    
    def debug_focus_recovery(self, trigger: str, widget_name: str, 
                           recovery_success: bool, details: Optional[Dict] = None):
        """Log focus loss detection and recovery attempts"""
        extra_details = {"trigger": trigger, "widget": widget_name, "recovered": recovery_success}
        if details:
            extra_details.update(details)
            
        result = "RECOVERED" if recovery_success else "FAILED"
        message = f"Focus lost ({trigger}), recovery: {result}"
        
        level = self.INFO if recovery_success else self.ERROR
        self._write_log("FOCUS", level, message, extra_details)
    
    # State Transition Debug Methods
    
    def debug_state_transition(self, component: str, from_state: str, 
                             to_state: str, trigger: str, details: Optional[Dict] = None):
        """Log UI state transitions"""
        extra_details = {"from": from_state, "to": to_state, "trigger": trigger}
        if details:
            extra_details.update(details)
            
        message = f"{component} state: {from_state} -> {to_state} (trigger: {trigger})"
        self._write_log("STATE", self.INFO, message, extra_details)
    
    def debug_operation_state(self, operation_type: str, state: str, 
                            session_name: Optional[str] = None, details: Optional[Dict] = None):
        """Log operation state changes (delete, restore, save)"""
        extra_details = {"operation": operation_type, "state": state}
        if session_name:
            extra_details["session"] = session_name
        if details:
            extra_details.update(details)
            
        message = f"Operation {operation_type} entered state: {state}"
        if session_name:
            message += f" for '{session_name}'"
            
        self._write_log("OPERATION", self.INFO, message, extra_details)
    
    # Event Processing Debug Methods
    
    def debug_event_routing(self, event_type: str, keyval: int, 
                          routing_decision: str, target: str, details: Optional[Dict] = None):
        """Log event processing and routing decisions"""
        extra_details = {"event": event_type, "keyval": keyval, "target": target}
        if details:
            extra_details.update(details)
            
        message = f"Event {event_type} (keyval={keyval}) routed to {target}: {routing_decision}"
        self._write_log("EVENT", self.DEBUG, message, extra_details)
    
    def debug_key_detection(self, keyval: int, key_type: str, 
                          is_printable: bool, has_modifiers: bool, details: Optional[Dict] = None):
        """Log key detection and categorization (verbose mode only)"""
        if not self.verbose_mode:
            return
        extra_details = {
            "keyval": keyval,
            "type": key_type,
            "printable": is_printable,
            "has_modifiers": has_modifiers
        }
        if details:
            extra_details.update(details)
            
        message = f"Key detected: {key_type} (printable={is_printable}, modifiers={has_modifiers})"
        self._write_log("KEY_DETECT", self.DEBUG, message, extra_details)
    
    # Search & Navigation Debug Methods
    
    def debug_search_operation(self, operation: str, query: str, 
                             result_count: int, timing_ms: float, details: Optional[Dict] = None):
        """Log search filtering operations"""
        extra_details = {"query": query, "results": result_count, "timing_ms": timing_ms}
        if details:
            extra_details.update(details)
            
        message = f"Search {operation}: '{query}' -> {result_count} results ({timing_ms:.1f}ms)"
        self._write_log("SEARCH", self.DEBUG, message, extra_details)
    
    def debug_navigation_operation(self, operation: str, from_session: Optional[str], 
                                 to_session: Optional[str], method: str, details: Optional[Dict] = None):
        """Log session navigation operations"""
        extra_details = {"method": method}
        if from_session:
            extra_details["from"] = from_session
        if to_session:
            extra_details["to"] = to_session
        if details:
            extra_details.update(details)
            
        message = f"Navigation {operation}: {from_session or 'none'} -> {to_session or 'none'} (via {method})"
        self._write_log("NAVIGATION", self.DEBUG, message, extra_details)
    
    # Backend Integration Debug Methods
    
    def debug_backend_call(self, operation: str, session_name: Optional[str], 
                         timing_ms: float, success: bool, details: Optional[Dict] = None):
        """Log backend API calls"""
        extra_details = {"operation": operation, "timing_ms": timing_ms, "success": success}
        if session_name:
            extra_details["session"] = session_name
        if details:
            extra_details.update(details)
            
        result = "SUCCESS" if success else "FAILED"
        message = f"Backend {operation}: {result} ({timing_ms:.1f}ms)"
        if session_name:
            message += f" for '{session_name}'"
            
        level = self.INFO if success else self.ERROR
        self._write_log("BACKEND", level, message, extra_details)
    
    def debug_backend_timeout(self, operation: str, timeout_seconds: int, 
                            session_name: Optional[str] = None, details: Optional[Dict] = None):
        """Log backend operation timeouts"""
        extra_details = {"operation": operation, "timeout": timeout_seconds}
        if session_name:
            extra_details["session"] = session_name
        if details:
            extra_details.update(details)
            
        message = f"Backend {operation} TIMEOUT after {timeout_seconds}s"
        if session_name:
            message += f" for '{session_name}'"
            
        self._write_log("BACKEND", self.ERROR, message, extra_details)
    
    # Performance Debug Methods
    
    def debug_performance_metric(self, operation: str, timing_ms: float, 
                               items_processed: int = 0, details: Optional[Dict] = None):
        """Log performance measurements (verbose mode only)"""
        if not self.verbose_mode:
            return
        extra_details = {"operation": operation, "timing_ms": timing_ms}
        if items_processed > 0:
            extra_details["items"] = items_processed
            extra_details["per_item_ms"] = timing_ms / items_processed
        if details:
            extra_details.update(details)
            
        message = f"Performance {operation}: {timing_ms:.1f}ms"
        if items_processed > 0:
            message += f" ({items_processed} items, {timing_ms/items_processed:.2f}ms each)"
            
        # Warn if operations are slow
        level = self.WARN if timing_ms > 100 else self.DEBUG
        self._write_log("PERFORMANCE", level, message, extra_details)
    
    # Session Management Debug Methods
    
    def debug_session_lifecycle(self, operation: str, session_name: str, 
                              phase: str, details: Optional[Dict] = None):
        """Log session lifecycle events"""
        extra_details = {"operation": operation, "session": session_name, "phase": phase}
        if details:
            extra_details.update(details)
            
        message = f"Session {operation} ({session_name}): {phase}"
        self._write_log("SESSION", self.INFO, message, extra_details)
    
    # Enhanced Key Debugging Methods
    
    def get_human_readable_key(self, keyval: int, modifiers: int = 0) -> str:
        """Convert GTK keyval and modifiers to human-readable key name
        
        Args:
            keyval: GTK key value 
            modifiers: GTK modifier mask
            
        Returns:
            Human-readable key description (e.g., "Ctrl+D", "Escape", "Up")
        """
        # Common key mappings for better readability (GTK3 compatible)
        key_names = {
            # Navigation keys
            Gdk.KEY_Up: "Up",
            Gdk.KEY_Down: "Down", 
            Gdk.KEY_Left: "Left",
            Gdk.KEY_Right: "Right",
            
            # Action keys
            Gdk.KEY_Return: "Enter",
            Gdk.KEY_KP_Enter: "NumPad_Enter",
            Gdk.KEY_Escape: "Escape",
            Gdk.KEY_Tab: "Tab",
            Gdk.KEY_BackSpace: "Backspace",
            Gdk.KEY_Delete: "Delete",
            
            # Function keys
            Gdk.KEY_F1: "F1", Gdk.KEY_F2: "F2", Gdk.KEY_F3: "F3", Gdk.KEY_F4: "F4",
            Gdk.KEY_F5: "F5", Gdk.KEY_F6: "F6", Gdk.KEY_F7: "F7", Gdk.KEY_F8: "F8",
            Gdk.KEY_F9: "F9", Gdk.KEY_F10: "F10", Gdk.KEY_F11: "F11", Gdk.KEY_F12: "F12",
            
            # Special characters commonly used (GTK3 standard keys only)
            Gdk.KEY_space: "Space",
            Gdk.KEY_slash: "/",
            Gdk.KEY_backslash: "\\",
            Gdk.KEY_period: ".",
            Gdk.KEY_comma: ",",
            Gdk.KEY_semicolon: ";",
            Gdk.KEY_question: "?",
        }
        
        # Get base key name
        if keyval in key_names:
            key_name = key_names[keyval]
        elif 32 <= keyval <= 126:  # Printable ASCII characters
            key_name = chr(keyval).upper()
        elif keyval >= Gdk.KEY_a and keyval <= Gdk.KEY_z:  # Lowercase letters
            key_name = chr(keyval).upper()
        elif keyval >= Gdk.KEY_A and keyval <= Gdk.KEY_Z:  # Uppercase letters  
            key_name = chr(keyval)
        elif keyval >= Gdk.KEY_0 and keyval <= Gdk.KEY_9:  # Numbers
            key_name = chr(keyval)
        else:
            key_name = f"Key({keyval})"
        
        # Build modifier list
        modifier_list = []
        if modifiers & Gdk.ModifierType.CONTROL_MASK:
            modifier_list.append("Ctrl")
        if modifiers & Gdk.ModifierType.MOD1_MASK:  # Alt key
            modifier_list.append("Alt")
        if modifiers & Gdk.ModifierType.SHIFT_MASK:
            modifier_list.append("Shift")
        if modifiers & Gdk.ModifierType.SUPER_MASK:  # Windows/Cmd key
            modifier_list.append("Super")
        
        # Combine modifiers with key name
        if modifier_list:
            return f"{'+'.join(modifier_list)}+{key_name}"
        else:
            return key_name
    
    def debug_event_flow(self, key_name: str, widget_source: str, 
                        handler_method: str, action_taken: str, details: Optional[Dict] = None):
        """Log complete event flow from key press to action (verbose mode only)
        
        Args:
            key_name: Human-readable key name
            widget_source: Widget that received the event
            handler_method: Method that processed the event 
            action_taken: Description of action taken
            details: Additional context information
        """
        if not self.verbose_mode:
            return
            
        extra_details = {
            "key": key_name,
            "source": widget_source,
            "handler": handler_method,
            "action": action_taken
        }
        if details:
            extra_details.update(details)
            
        message = f"Key pressed: {key_name} → {widget_source} → {handler_method} → {action_taken}"
        self._write_log("TRACE", self.DEBUG, message, extra_details)
    
    def debug_action_outcome(self, key_name: str, outcome_type: str, 
                           details: Optional[Dict] = None):
        """Log the outcome/result of a key press action
        
        Args:
            key_name: Human-readable key name
            outcome_type: Type of outcome (e.g., "selection_changed", "state_transition")
            details: Specific outcome details (before/after values, etc.)
        """
        extra_details = {"key": key_name, "outcome": outcome_type}
        if details:
            extra_details.update(details)
            
        message = f"{key_name} key: {outcome_type}"
        if details:
            # Add context for common outcome types
            if "from" in details and "to" in details:
                message += f" ({details['from']} → {details['to']})"
            elif "session" in details:
                message += f" ({details['session']})"
            elif "state" in details:
                message += f" (state: {details['state']})"
                
        self._write_log("ACTION", self.INFO, message, extra_details)


# Global debug logger instance - will be initialized by session manager
ui_debug_logger: Optional[UIDebugLogger] = None


def get_debug_logger() -> Optional[UIDebugLogger]:
    """Get the global debug logger instance"""
    return ui_debug_logger


def initialize_debug_logger(log_file_path: str = None, enabled: bool = False, verbose_mode: bool = False,
                           output_to_terminal: bool = True, output_to_file: bool = False) -> UIDebugLogger:
    """Initialize the global debug logger"""
    global ui_debug_logger
    ui_debug_logger = UIDebugLogger(log_file_path, enabled, verbose_mode, output_to_terminal, output_to_file)
    return ui_debug_logger