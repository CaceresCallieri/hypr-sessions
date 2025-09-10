# Fix Archive Mode Initialization Bug

## Priority: P1 | Type: Fix | Benefit: High | Complexity: Low

## Problem Description

Archive mode flag is set after RestoreOperation initialization, breaking encapsulation and potentially causing runtime errors. The operation is created with incorrect mode information, leading to inconsistent behavior.

## Implementation Plan

1. **Review Initialization Order**: Analyze current initialization sequence
2. **Fix Initialization Sequence**: Set archive mode before creating operations
3. **Add Initialization Validation**: Ensure proper dependency injection
4. **Test Mode Switching**: Verify archive mode works correctly
5. **Document Pattern**: Establish clear initialization pattern for future operations

## File Locations

**Primary File**:
- `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/browse_panel.py:74-78`

**Current Problematic Code**:
```python
self.is_archive_mode = False        # Set here
self.restore_operation = RestoreOperation(self, self.backend_client, self.is_archive_mode)  # But used here immediately
```

## Success Criteria

- [ ] Archive mode flag set before operation creation
- [ ] RestoreOperation receives correct mode during initialization
- [ ] Mode switching works reliably without reinitialization
- [ ] No AttributeError exceptions during operation config retrieval
- [ ] Archive mode behavior consistent throughout operation lifecycle

## Dependencies

None

## Code Examples

**Current Issue** (`browse_panel.py`):
```python
def __init__(self, backend_client):
    super().__init__()
    self.backend_client = backend_client
    
    # Problem: Flag set after operation creation
    self.is_archive_mode = False
    self.restore_operation = RestoreOperation(self, self.backend_client, self.is_archive_mode)  # Uses stale value
    
    # Later when mode changes, operation has wrong configuration
```

**Fixed Version Option 1** (Early Initialization):
```python
def __init__(self, backend_client):
    super().__init__()
    self.backend_client = backend_client
    
    # Fix: Set mode first
    self.is_archive_mode = False
    self.restore_operation = RestoreOperation(self, self.backend_client, self.is_archive_mode)
```

**Fixed Version Option 2** (Lazy Initialization):
```python
def __init__(self, backend_client):
    super().__init__()
    self.backend_client = backend_client
    self.is_archive_mode = False
    self._restore_operation = None  # Lazy initialization

@property
def restore_operation(self):
    """Get restore operation, creating with current mode if needed"""
    if self._restore_operation is None or self._restore_operation.is_archive_mode != self.is_archive_mode:
        self._restore_operation = RestoreOperation(self, self.backend_client, self.is_archive_mode)
    return self._restore_operation
```

**Mode Toggle Method** (if using lazy initialization):
```python
def toggle_archive_mode(self):
    """Toggle between archive and active mode"""
    self.is_archive_mode = not self.is_archive_mode
    # Reset operation to pick up new mode
    self._restore_operation = None
    self._update_mode_display()
```

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.