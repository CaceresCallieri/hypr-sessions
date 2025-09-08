# Fix Enter Key Handler Conflict

## Priority: P1 | Type: Fix | Benefit: Highest | Complexity: Quickfix

## Problem Description

**CRITICAL BUG**: Archive mode Enter key functionality is broken due to competing handlers. Two different handlers process Enter keys:

1. `session_manager.py:191` - Always calls restore operation regardless of mode
2. `browse_panel.py:activate_selected_session()` - Has correct mode-aware logic but never executes

**Impact**: Users pressing Enter in archive mode get restore behavior instead of recovery, making the archive system partially non-functional.

## Implementation Plan

1. **Remove hardcoded Enter handler** from `session_manager.py`
2. **Delegate Enter key handling** to `browse_panel.py` exclusively
3. **Test archive mode Enter key** functionality works correctly
4. **Verify active mode** Enter key still works for restore operations

## File Locations

- **Primary**: `fabric-ui/session_manager.py:191` - Remove hardcoded restore call
- **Verification**: `fabric-ui/widgets/browse_panel.py:activate_selected_session()` - Ensure this executes

## Success Criteria

- [ ] Enter key in archive mode triggers recovery confirmation
- [ ] Enter key in active mode triggers restore confirmation  
- [ ] No duplicate Enter key processing occurs
- [ ] All existing keyboard navigation remains functional

## Dependencies

None - this is a critical standalone bug fix

## Code Examples

**Current Broken Code** (`session_manager.py:191`):
```python
def _handle_enter_key(self):
    # This ignores archive mode completely - BROKEN
    selected_session = self.browse_panel.get_selected_session()
    if selected_session:
        self.browse_panel.restore_operation.selected_session = selected_session
        self.browse_panel.set_state(RESTORE_CONFIRM_STATE)
```

**Correct Approach**:
```python
def _handle_enter_key(self):
    # Delegate to browse_panel's mode-aware logic
    return self.browse_panel.activate_selected_session()
```

**Existing Correct Logic** (`browse_panel.py`):
```python
def activate_selected_session(self):
    selected_session = self.get_selected_session()
    if not selected_session:
        return False
    if self.is_archive_mode:
        # Archive mode: trigger recovery operation
        self.recovery_operation.selected_session = selected_session
        self.set_state(RECOVERY_CONFIRM_STATE)
    else:
        # Active mode: trigger restore operation  
        self.restore_operation.selected_session = selected_session
        self.set_state(RESTORE_CONFIRM_STATE)
    return True
```

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.