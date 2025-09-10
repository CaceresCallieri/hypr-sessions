# Remove Production Debug Code

## Priority: P1 | Type: Fix | Benefit: High | Complexity: Quickfix

## Problem Description

Hardcoded debug print statements exist in production UI code, executing unconditionally and cluttering output. This affects production deployment quality and user experience.

## Implementation Plan

1. **Locate Debug Prints**: Find all hardcoded print statements in fabric-ui
2. **Replace with Debug Logger**: Use existing debug logging infrastructure
3. **Verify No Output**: Ensure production runs produce no debug output
4. **Test Debug Mode**: Confirm debug output still works when enabled

## File Locations

**Primary File**:
- `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/operations/base_operation.py:437`

**Problematic Code**:
```python
print(f"DEBUG: Cancelled {self.get_operation_config()['action_verb'].lower()} for session: {self.selected_session}")
```

**Replacement Pattern**:
```python
if self.panel.debug_logger and self.panel.debug_logger.enabled:
    self.panel.debug_logger.debug_operation_state(
        "operation_cancelled", 
        f"{self.get_operation_config()['action_verb'].lower()}", 
        self.selected_session,
        {}
    )
```

## Success Criteria

- [ ] No hardcoded print statements in fabric-ui production code
- [ ] Debug information still available when debug mode enabled
- [ ] Production deployment produces clean output
- [ ] Existing debug logging patterns maintained

## Dependencies

None

## Code Examples

**Current Issue**:
```python
def _handle_cancel_button(self, *args):
    """Handle cancel button click - returns to browsing state"""
    print(f"DEBUG: Cancelled {self.get_operation_config()['action_verb'].lower()} for session: {self.selected_session}")  # ← Remove this
    self.selected_session = None
    self.panel.set_state(BROWSING_STATE)
```

**Fixed Version**:
```python
def _handle_cancel_button(self, *args):
    """Handle cancel button click - returns to browsing state"""
    if hasattr(self.panel, 'debug_logger') and self.panel.debug_logger and self.panel.debug_logger.enabled:
        self.panel.debug_logger.debug_operation_state(
            "operation_cancelled", 
            self.get_operation_config()['action_verb'].lower(), 
            self.selected_session,
            {"state_transition": "return_to_browsing"}
        )
    self.selected_session = None
    self.panel.set_state(BROWSING_STATE)
```

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.