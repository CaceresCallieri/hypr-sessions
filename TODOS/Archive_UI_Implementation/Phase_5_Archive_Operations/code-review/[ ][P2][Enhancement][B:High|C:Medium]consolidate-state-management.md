# Consolidate State Management System

## Priority: P2 | Type: Enhancement | Benefit: High | Complexity: Medium

## Problem Description

The archive system adds **4 new states** (`RECOVERY_CONFIRM_STATE`, `RECOVERING_STATE`, `RECOVERY_SUCCESS_STATE`, `RECOVERY_ERROR_STATE`) when the existing restore states could be reused with mode-aware behavior. This creates unnecessary state management complexity and duplicate state handling logic.

**Current Issue**: 50% more states than needed, with identical behavior patterns.

## Implementation Plan

1. **Analyze current state usage** in both restore and recovery workflows
2. **Identify consolidation opportunities** where states have identical behavior
3. **Add mode awareness** to existing state handling methods
4. **Update state constants** to reuse existing `RESTORE_*` states for both modes
5. **Modify state transition logic** to use mode flags for display differences
6. **Remove redundant recovery states** from constants
7. **Test state transitions** work correctly for both modes

## File Locations

- **Modify**: `fabric-ui/constants.py` - Remove redundant recovery state constants
- **Update**: `fabric-ui/widgets/browse_panel.py` - Consolidate state handling methods
- **Review**: All files using recovery states - update to use unified states

## Success Criteria

- [ ] Single set of operation states handles both restore and recovery
- [ ] Mode-aware display text shows "Restore" vs "Recover" appropriately
- [ ] State transition logic simplified by ~50%
- [ ] All existing functionality preserved
- [ ] No duplicate state handling methods
- [ ] Constants file cleaned of redundant states

## Dependencies

[Depends-On: eliminate-recovery-operation-class] - Operation class consolidation should be completed first

## Code Examples

**Current Redundant States**:
```python
# In constants.py - TOO MANY STATES
RESTORE_CONFIRM_STATE = "restore_confirm"
RESTORING_STATE = "restoring" 
RESTORE_SUCCESS_STATE = "restore_success"
RESTORE_ERROR_STATE = "restore_error"

RECOVERY_CONFIRM_STATE = "recovery_confirm"    # DUPLICATE BEHAVIOR
RECOVERING_STATE = "recovering"                # DUPLICATE BEHAVIOR  
RECOVERY_SUCCESS_STATE = "recovery_success"    # DUPLICATE BEHAVIOR
RECOVERY_ERROR_STATE = "recovery_error"        # DUPLICATE BEHAVIOR
```

**Proposed Unified Approach**:
```python
# In constants.py - SIMPLIFIED
OPERATION_CONFIRM_STATE = "operation_confirm"  # Replaces both confirm states
OPERATION_PROGRESS_STATE = "operation_progress" # Replaces both progress states
OPERATION_SUCCESS_STATE = "operation_success"   # Replaces both success states
OPERATION_ERROR_STATE = "operation_error"       # Replaces both error states

# OR even simpler - reuse existing restore states:
# RESTORE_CONFIRM_STATE = "restore_confirm"  # Use for both restore and recovery
# RESTORING_STATE = "restoring"              # Use for both operations  
# etc.
```

**Updated State Handling** (`browse_panel.py`):
```python
def _get_operation_display_text(self):
    """Get display text based on current operation mode"""
    if self.is_archive_mode:
        return {
            "action_verb": "Recover",
            "progress_text": "Recovering session...",
            "success_text": "Session recovered successfully",
        }
    else:
        return {
            "action_verb": "Restore", 
            "progress_text": "Restoring session...",
            "success_text": "Session restored successfully",
        }

# Single state handler instead of separate recovery/restore methods
def _handle_operation_confirm_state(self):
    display_text = self._get_operation_display_text()
    # Use display_text["action_verb"] etc. for UI elements
    return self._render_confirmation_ui(display_text)
```

**State Transition Simplification**:
```python
# Before: Mode-specific state transitions
if self.is_archive_mode:
    self.set_state(RECOVERY_CONFIRM_STATE)
else:
    self.set_state(RESTORE_CONFIRM_STATE)

# After: Unified state transitions  
self.set_state(RESTORE_CONFIRM_STATE)  # Same state, different display
```

**Benefits**:
- **50% fewer state constants** to maintain
- **Unified state handling logic** eliminates duplicate code
- **Mode-aware display** provides correct user messaging
- **Simpler state transitions** with consistent patterns
- **Easier to extend** for additional operation types

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.