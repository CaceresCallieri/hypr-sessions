# Debug Logger Resource Management

## Priority: P3 | Type: Polish | Benefit: Low | Complexity: Low

## Problem Description
Current debug logger implementation may have potential resource leaks with file handles not being properly closed on application exit. While not critical, proper resource management is good practice for production applications and prevents accumulation of open file handles.

## Implementation Plan
1. Add context manager support for file operations with automatic cleanup
2. Implement `atexit` registration for cleanup on application termination
3. Add proper exception handling for file operations with console fallback
4. Cache file handle to avoid repeated open/close operations
5. Add cleanup method that can be called manually or automatically

## File Locations
- `/home/jc/Dev/hypr-sessions/fabric-ui/utils/debug_logger.py` - Main debug logger implementation
- Potentially other debug logging implementations if they exist

## Success Criteria
- File handles properly closed on application exit
- Context manager pattern implemented for safe file operations
- Console fallback works when file operations fail
- No resource leaks during normal operation
- Cleanup can be triggered manually or automatically

## Dependencies
None - standalone improvement to existing debug system

## Code Examples

**Current implementation pattern:**
```python
# Potential resource leak - file handle may not close properly
with open(self.log_file_path, 'a') as f:
    f.write(message)
```

**Proposed resource-safe implementation:**
```python
import atexit
from contextlib import contextmanager

class DebugLogger:
    def __init__(self):
        self._file_handle = None
        atexit.register(self.cleanup)
    
    @contextmanager
    def _file_context(self):
        try:
            if self._file_handle is None:
                self._file_handle = open(self.log_file_path, 'a')
            yield self._file_handle
        except IOError as e:
            yield None  # Console fallback
    
    def cleanup(self):
        if self._file_handle:
            try:
                self._file_handle.close()
            except:
                pass
            self._file_handle = None
```

## Reminder
Move this file to TODOS/code-quality-improvements/completed/ when implementation is finished.