# Update Operation Routing for Archive Mode

## Context & Background
- **Feature Goal**: Ensure all operation state management works correctly with recovery operations, completing the operation framework integration
- **Current Architecture**: BrowsePanelWidget handles operation state transitions for delete and restore operations through unified state management
- **User Story**: Recovery operation confirmation, progress, and success/error states should work seamlessly with existing UI operation framework

## Task Description
Update BrowsePanelWidget operation state handling to include recovery operation states, ensuring that recovery confirmation, progress, success, and error states are properly managed alongside existing restore and delete operations.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/widgets/browse_panel.py` (update state handling methods) - Add recovery state support
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# Update state transition handling (likely in set_state or state management methods):

# Import recovery states at top of file:
from constants import (
    RECOVERY_CONFIRM_STATE, RECOVERING_STATE, 
    RECOVERY_SUCCESS_STATE, RECOVERY_ERROR_STATE
)

# Update state handling to include recovery states:
def _handle_state_transitions(self):
    """Handle UI state transitions for all operations"""
    
    # ... existing restore and delete state handling ...
    
    # Add recovery state handling
    if self.current_state == RECOVERY_CONFIRM_STATE:
        return self._handle_recovery_confirmation_state()
    elif self.current_state == RECOVERING_STATE:
        return self._handle_recovery_progress_state()
    elif self.current_state == RECOVERY_SUCCESS_STATE:
        return self._handle_recovery_success_state()
    elif self.current_state == RECOVERY_ERROR_STATE:
        return self._handle_recovery_error_state()

# Add recovery operation to existing operation routing:
def _get_current_operation(self):
    """Get current operation based on state"""
    if self.current_state in [RECOVERY_CONFIRM_STATE, RECOVERING_STATE, 
                             RECOVERY_SUCCESS_STATE, RECOVERY_ERROR_STATE]:
        return self.recovery_operation
    # ... existing restore/delete operation routing ...
```

### Integration Points:
- Integrates recovery states with existing state management system
- Uses same operation handling patterns as restore and delete operations
- Works with existing BaseOperation framework for consistent UI behavior

## Architecture Context
- **Component Relationships**: Completes integration between RecoveryOperation and BrowsePanelWidget state system
- **State Management**: Extends unified state handling to include all recovery operation states
- **Data Flow**: Recovery operation states → state management → appropriate UI display and behavior

## Dependencies
- **Prerequisite Tasks**: Task 3 (recovery constants), Task 9 (RecoveryOperation class), Task 10 (Enter key behavior)
- **Blocking Tasks**: Completes core archive mode operation functionality
- **Related Systems**: Integrates with existing BaseOperation framework and state management system

## Acceptance Criteria
- [ ] Recovery confirmation state properly displays confirmation UI
- [ ] Recovery progress state shows operation progress
- [ ] Recovery success state displays success message and returns to browsing
- [ ] Recovery error state shows error information with retry options
- [ ] State transitions work consistently with existing operation patterns
- [ ] All recovery states integrate with existing operation framework

## Testing Strategy
- **Manual Testing**: 
  - Trigger recovery operation and verify all state transitions work
  - Test recovery success and error scenarios
  - Confirm UI behavior matches restore/delete operation patterns
- **Integration Points**: Ensure no impact on existing restore/delete operation state handling
- **Edge Cases**: Test rapid state transitions, error conditions, operation cancellation

## Implementation Notes
- **Code Patterns**: Follow exact same patterns as existing restore and delete state handling
- **Performance Considerations**: Minimal - same performance profile as existing state management
- **Future Extensibility**: Establishes pattern for additional operation types

## Commit Information
- **Commit Message**: "Add recovery operation state routing to complete archive functionality"
- **Estimated Time**: 20 minutes
- **Complexity Justification**: Low - Simple state routing additions following established patterns, completing existing operation framework