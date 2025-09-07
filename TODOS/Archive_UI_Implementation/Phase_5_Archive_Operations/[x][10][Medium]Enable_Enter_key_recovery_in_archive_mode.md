# Enable Enter Key Recovery in Archive Mode

## Context & Background
- **Feature Goal**: Add Enter key functionality for archived sessions to trigger recovery operations while maintaining existing restore behavior for active sessions
- **Current Architecture**: Enter key in BrowsePanelWidget triggers RestoreOperation for active sessions through existing operation system
- **User Story**: When viewing archived sessions, users press Enter to recover archived session; when viewing active sessions, Enter continues to restore sessions as before

## Task Description
Modify Enter key handling in BrowsePanelWidget to be mode-aware: triggering RecoveryOperation for archived sessions and RestoreOperation for active sessions. This provides intuitive Enter key functionality that adapts to the current viewing mode.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/widgets/browse_panel.py` (modify Enter key handling) - Add mode-aware operation routing
  - `fabric-ui/widgets/browse_panel.py` (add recovery operation instance) - Add recovery operation support
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# In BrowsePanelWidget.__init__ method, add recovery operation:
from .operations import RecoveryOperation

def __init__(self, session_utils, on_session_clicked=None):
    # ... existing initialization ...
    
    # Add recovery operation alongside existing operations
    self.recovery_operation = RecoveryOperation(
        self.backend_client, debug_logger=self.debug_logger
    )

# Modify Enter key handling (likely in handle_key_press_event or similar):
def _handle_enter_key(self) -> bool:
    """Handle Enter key for session operations - mode aware"""
    selected_session = self.get_selected_session()
    if not selected_session:
        return False
    
    if self.is_archive_mode:
        # Archive mode: trigger recovery operation
        self.recovery_operation.selected_session = selected_session
        self.set_state(RECOVERY_CONFIRM_STATE)
        
        if self.debug_logger:
            self.debug_logger.debug_navigation_operation(
                "recovery_trigger", selected_session, None, "enter_key_archive_mode"
            )
    else:
        # Active mode: trigger restore operation (existing behavior)
        self.restore_operation.selected_session = selected_session  
        self.set_state(RESTORE_CONFIRM_STATE)
        
        if self.debug_logger:
            self.debug_logger.debug_navigation_operation(
                "restore_trigger", selected_session, None, "enter_key_active_mode"
            )
    
    return True
```

### Integration Points:
- Uses existing operation framework with BaseOperation patterns
- Integrates with existing state management system (set_state)
- Works with current Enter key handling infrastructure
- Maintains existing restore operation functionality

## Architecture Context
- **Component Relationships**: Coordinates BrowsePanelWidget, RecoveryOperation, and state management
- **State Management**: Routes to appropriate operation states based on current mode
- **Data Flow**: Enter key → mode check → appropriate operation setup → state transition

## Dependencies
- **Prerequisite Tasks**: Task 1 (archive mode state), Task 9 (RecoveryOperation class), Task 3 (recovery constants)
- **Blocking Tasks**: Enables complete archive mode functionality
- **Related Systems**: Uses existing operation system, state management, and keyboard handling

## Acceptance Criteria
- [ ] Enter key triggers recovery operation when in archive mode
- [ ] Enter key continues to trigger restore operation when in active mode
- [ ] RecoveryOperation instance properly initialized in BrowsePanelWidget
- [ ] State transitions work correctly for both recovery and restore operations
- [ ] Debug logging captures operation triggers with appropriate context
- [ ] No breaking changes to existing restore operation functionality

## Testing Strategy
- **Manual Testing**: 
  - In active mode: press Enter, verify restore confirmation appears
  - In archive mode: press Enter, verify recovery confirmation appears
  - Test operation completion and state transitions in both modes
- **Integration Points**: Ensure all existing Enter key functionality preserved in active mode
- **Edge Cases**: Test with no selection, during operations, rapid key presses

## Implementation Notes
- **Code Patterns**: Follow existing operation setup patterns used by restore and delete operations
- **Performance Considerations**: Minimal overhead - simple mode check with existing operation infrastructure
- **Future Extensibility**: Foundation for additional mode-specific operations

## Commit Information
- **Commit Message**: "Add mode-aware Enter key behavior for archive recovery operations"
- **Estimated Time**: 30 minutes
- **Complexity Justification**: Medium - Requires coordination between operation system, state management, and mode detection with careful preservation of existing functionality