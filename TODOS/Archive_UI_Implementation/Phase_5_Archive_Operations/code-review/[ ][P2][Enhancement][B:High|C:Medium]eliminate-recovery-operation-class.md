# Eliminate RecoveryOperation Class

## Priority: P2 | Type: Enhancement | Benefit: High | Complexity: Medium

## Problem Description

The `RecoveryOperation` class is **95% identical** to `RestoreOperation`, creating unnecessary code duplication and maintenance burden. The only difference is the backend method called (`recover_session` vs `restore_session`), but both follow identical UI workflows.

**Current Issue**: 30+ lines of duplicate code for what could be a simple mode flag.

## Implementation Plan

1. **Add mode awareness** to `RestoreOperation` class
2. **Update execute_backend_operation()** to check mode and call appropriate backend method
3. **Update get_operation_config()** to return mode-appropriate text and colors
4. **Replace RecoveryOperation usage** in `browse_panel.py` with mode-aware RestoreOperation
5. **Remove RecoveryOperation class** and clean up imports
6. **Test both archive and active mode** operations work correctly

## File Locations

- **Remove**: `fabric-ui/widgets/operations/recovery_operation.py` (entire file)
- **Modify**: `fabric-ui/widgets/operations/restore_operation.py` - Add mode awareness
- **Modify**: `fabric-ui/widgets/operations/__init__.py` - Remove RecoveryOperation import
- **Update**: `fabric-ui/widgets/browse_panel.py` - Use single operation with mode flag

## Success Criteria

- [ ] Single RestoreOperation handles both active and archive modes
- [ ] Archive recovery shows "Recover" text and appropriate messaging
- [ ] Active restore shows "Restore" text and existing messaging
- [ ] RecoveryOperation class completely removed
- [ ] ~40% reduction in operation system code complexity
- [ ] Both operation types work identically to current behavior

## Dependencies

[Depends-On: fix-enter-key-handler-conflict] - Enter key fix should be completed first

## Code Examples

**Current Duplicate Code** (RecoveryOperation):
```python
class RecoveryOperation(BaseOperation):
    def execute_backend_operation(self, session_name: str):
        return self.backend_client.recover_session(session_name)
    
    def get_operation_config(self):
        return {
            "color": "#a6e3a1",
            "action_verb": "Recover", 
            "description": "Recover '{session_name}' from archive?...",
            "button_prefix": "recovery",
            "success_description": "recovered from archive successfully",
            "progress_state": RECOVERING_STATE,
            "operation_timeout": 45
        }
```

**Proposed Unified Approach**:
```python
class RestoreOperation(BaseOperation):
    def __init__(self, backend_client, debug_logger=None, is_archive_mode=False):
        super().__init__(backend_client, debug_logger)
        self.is_archive_mode = is_archive_mode
    
    def execute_backend_operation(self, session_name: str):
        if self.is_archive_mode:
            return self.backend_client.recover_session(session_name)
        else:
            return self.backend_client.restore_session(session_name)
    
    def get_operation_config(self):
        if self.is_archive_mode:
            return {
                "color": "#a6e3a1",
                "action_verb": "Recover",
                "description": "Recover '{session_name}' from archive?...",
                "button_prefix": "recovery", 
                "success_description": "recovered from archive successfully",
                "progress_state": RECOVERING_STATE,  # Could also be unified
                "operation_timeout": 45
            }
        else:
            # Existing restore configuration
            return super().get_operation_config()
```

**Updated Browse Panel Usage**:
```python
# In browse_panel.py __init__
self.restore_operation = RestoreOperation(
    self.backend_client, debug_logger=self.debug_logger
)
# Remove: self.recovery_operation = RecoveryOperation(...)

# In activate_selected_session()
def activate_selected_session(self):
    selected_session = self.get_selected_session()
    if not selected_session:
        return False
    
    # Set mode on the single operation
    self.restore_operation.is_archive_mode = self.is_archive_mode
    self.restore_operation.selected_session = selected_session
    
    if self.is_archive_mode:
        self.set_state(RECOVERY_CONFIRM_STATE)  # Could be unified too
    else:
        self.set_state(RESTORE_CONFIRM_STATE)
    return True
```

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.