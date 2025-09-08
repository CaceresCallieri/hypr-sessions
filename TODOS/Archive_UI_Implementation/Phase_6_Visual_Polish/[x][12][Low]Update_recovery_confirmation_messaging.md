# Update Recovery Confirmation Messaging

## Context & Background
- **Feature Goal**: Provide clear, user-friendly messaging for recovery operations that explains what recovery does and its implications
- **Current Architecture**: RecoveryOperation uses BaseOperation confirmation dialog system with configurable messaging
- **User Story**: Users should clearly understand that recovery will move the archived session back to active sessions and explain the process clearly

## Task Description
Review and refine the recovery confirmation messaging in RecoveryOperation to ensure it clearly communicates what recovery does, uses appropriate language, and follows UI messaging patterns established by other operations.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/widgets/operations/recovery_operation.py` (update description text) - Refine confirmation messaging
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# In RecoveryOperation.get_operation_config(), update description:

def get_operation_config(self) -> Dict[str, str]:
    """Get recovery-specific configuration"""
    return {
        "color": "#a6e3a1",  # Green theme for positive action
        "action_verb": "Recover", 
        "description": "Recover '{session_name}' from archive?\n\nThis will restore the session to your active sessions list where it can be used normally. The session will be removed from the archive.",
        "button_prefix": "recovery",
        "success_description": "recovered successfully and is now available in active sessions",
        "progress_state": RECOVERING_STATE,
        "operation_timeout": 45
    }
```

### Integration Points:
- Uses existing BaseOperation confirmation dialog system
- Maintains consistency with other operation messaging patterns
- Works with existing confirmation UI layout and styling

## Architecture Context
- **Component Relationships**: Updates user-facing messaging in recovery operation confirmation
- **State Management**: Improves user understanding of recovery operation implications
- **Data Flow**: User triggers recovery → clear confirmation message → informed decision

## Dependencies
- **Prerequisite Tasks**: Task 9 (RecoveryOperation class creation)
- **Blocking Tasks**: Completes user experience improvements for archive functionality
- **Related Systems**: Uses BaseOperation confirmation dialog framework

## Acceptance Criteria
- [ ] Recovery confirmation clearly explains what recovery does
- [ ] Message explains that session will move back to active sessions
- [ ] Success message confirms session is now available in active sessions  
- [ ] Messaging tone is consistent with other operation confirmations
- [ ] Text fits properly in existing confirmation dialog layout
- [ ] Language is clear and user-friendly

## Testing Strategy
- **Manual Testing**: 
  - Trigger recovery confirmation and verify messaging clarity
  - Test different archived session names for text formatting
  - Confirm success message appears correctly after recovery
- **Integration Points**: Ensure messaging works with existing confirmation dialog styling
- **Edge Cases**: Test with long session names, special characters in names

## Implementation Notes
- **Code Patterns**: Follow messaging patterns from RestoreOperation and DeleteOperation
- **Performance Considerations**: None - static text configuration
- **Future Extensibility**: Can be extended for additional recovery options or warnings

## Commit Information
- **Commit Message**: "Improve recovery operation confirmation messaging for better UX"
- **Estimated Time**: 10 minutes
- **Complexity Justification**: Low - Simple text updates for user experience improvement, no functional changes