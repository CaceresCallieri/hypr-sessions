# Consolidate Duplicate Debug Infrastructure

## Priority: P2 | Type: Performance | Benefit: Medium | Complexity: Low

## Problem Description

10+ files implement identical debug printing logic, leading to code duplication and inconsistent debug output formatting. This creates maintenance burden and potential for divergent debug behavior across components.

## Implementation Plan

1. **Create Shared Debug Utility**: Extract common debug patterns into centralized utility
2. **Update Command Files**: Replace individual debug methods with shared utility
3. **Standardize Debug Format**: Ensure consistent output formatting across all components
4. **Add Configuration Support**: Support debug levels and component-specific filtering
5. **Test Integration**: Verify debug output works consistently across all commands

## File Locations

**Files with Duplicate Debug Code**:
- All command files in `commands/` directory (save.py, restore.py, list.py, delete.py, recover.py, etc.)
- Each has individual `debug_print` method with identical logic

**New Shared Utility Location**:
- `/home/jc/Dev/hypr-sessions/commands/shared/debug.py`

## Success Criteria

- [ ] Single shared debug utility replaces 10+ individual implementations
- [ ] Consistent debug output formatting across all commands
- [ ] Configurable debug levels (basic, verbose)
- [ ] Component-specific debug filtering capability
- [ ] Zero breaking changes to existing debug functionality
- [ ] Reduced overall codebase size through deduplication

## Dependencies

None

## Code Examples

**Current Duplicate Pattern** (in multiple files):
```python
def debug_print(self, message):
    """Print debug message if debug mode is enabled"""
    if self.debug_enabled:
        print(f"[DEBUG {self.__class__.__name__}] {message}")
```

**New Shared Utility** (`commands/shared/debug.py`):
```python
from typing import Optional
import sys
from datetime import datetime

class CommandDebugger:
    """Centralized debug utility for all commands"""
    
    def __init__(self, component_name: str, enabled: bool = False, verbose: bool = False):
        self.component_name = component_name
        self.enabled = enabled
        self.verbose = verbose
        self.start_time = datetime.now()
    
    def debug(self, message: str, level: str = "info"):
        """Print debug message with consistent formatting"""
        if not self.enabled:
            return
        
        if level == "verbose" and not self.verbose:
            return
        
        elapsed = datetime.now() - self.start_time
        timestamp = elapsed.total_seconds()
        print(f"[DEBUG {self.component_name} {timestamp:.2f}s] {message}", file=sys.stderr)
    
    def debug_operation(self, operation: str, details: str = ""):
        """Debug specific operation with structured output"""
        message = f"{operation}"
        if details:
            message += f" | {details}"
        self.debug(message)
    
    def debug_verbose(self, message: str):
        """Debug verbose information (only shown in verbose mode)"""
        self.debug(message, level="verbose")
```

**Updated Command Usage** (example in `commands/save/session_saver.py`):
```python
from commands.shared.debug import CommandDebugger

class SessionSaver:
    def __init__(self, debug_enabled: bool = False):
        self.debugger = CommandDebugger("SessionSaver", debug_enabled)
    
    def save_session(self, session_name: str):
        self.debugger.debug_operation("save_session_start", f"session={session_name}")
        # ... operation logic ...
        self.debugger.debug_operation("save_session_complete", f"files_saved={len(files)}")
```

**Import Update Pattern** (for all command files):
```python
# Remove
def debug_print(self, message):
    if self.debug_enabled:
        print(f"[DEBUG {self.__class__.__name__}] {message}")

# Add
from commands.shared.debug import CommandDebugger

# In __init__:
self.debugger = CommandDebugger(self.__class__.__name__, debug_enabled)

# Replace debug_print calls:
# self.debug_print("message") → self.debugger.debug("message")
```

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.