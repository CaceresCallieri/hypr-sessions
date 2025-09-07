# Add Archive Constants and States

## Context & Background
- **Feature Goal**: Add archive mode toggle with Ctrl+A to browse archived sessions with recovery operations
- **Current Architecture**: UI uses constants.py for state management with existing states like BROWSING_STATE, RESTORE_CONFIRM_STATE, etc.
- **User Story**: UI needs recovery-specific states for archive session recovery operations, following established state management patterns

## Task Description
Add recovery-related constants to support archive mode operations, particularly recovery confirmation and progress states. This maintains consistency with existing operation state patterns (restore/delete operations).

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/constants.py` (lines ~22 after existing states) - Add recovery operation states
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# Add after existing operation states (around line 22):

# Recovery Operation States (for archived session recovery)
RECOVERY_CONFIRM_STATE: Final[str] = "recovery_confirm"
RECOVERING_STATE: Final[str] = "recovering" 
RECOVERY_SUCCESS_STATE: Final[str] = "recovery_success"
RECOVERY_ERROR_STATE: Final[str] = "recovery_error"
```

### Integration Points:
- Follows exact same naming conventions as existing RESTORE_* and DELETE_* states
- Will be used by recovery operation class (Phase 4) and archive mode operations (Phase 5)
- Maintains type safety with Final annotations

## Architecture Context
- **Component Relationships**: Used by recovery operations, browse panel state management, and keyboard event handling
- **State Management**: Provides state constants for recovery operation workflow
- **Data Flow**: Constants → Operation classes → BrowsePanelWidget state management

## Dependencies
- **Prerequisite Tasks**: None (foundational constants)
- **Blocking Tasks**: Enables Task 9 (recovery operation class) and Task 10 (archive mode operations)
- **Related Systems**: Must follow existing state constant patterns for consistency

## Acceptance Criteria
- [ ] RECOVERY_CONFIRM_STATE constant added with correct typing
- [ ] RECOVERING_STATE constant added with correct typing  
- [ ] RECOVERY_SUCCESS_STATE constant added with correct typing
- [ ] RECOVERY_ERROR_STATE constant added with correct typing
- [ ] Constants follow existing naming conventions and Final typing
- [ ] No impact on existing constants or functionality

## Testing Strategy
- **Manual Testing**: Verify UI starts normally with no behavior changes
- **Integration Points**: Ensure all existing state-dependent functionality works unchanged  
- **Edge Cases**: Verify constants are properly typed and accessible

## Implementation Notes
- **Code Patterns**: Follow exact same pattern as existing RESTORE_* and DELETE_* state constants
- **Performance Considerations**: Zero overhead - compile-time constants
- **Future Extensibility**: Provides foundation for recovery operation state management

## Commit Information
- **Commit Message**: "Add recovery operation state constants for archive functionality"
- **Estimated Time**: 10 minutes
- **Complexity Justification**: Low - Simple constant additions following established patterns, minimal complexity