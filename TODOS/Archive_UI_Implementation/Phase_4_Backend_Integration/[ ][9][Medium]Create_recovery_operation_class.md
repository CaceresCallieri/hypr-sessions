# Create Recovery Operation Class

## Context & Background
- **Feature Goal**: Add recovery operation support for archived sessions using the established operation framework
- **Current Architecture**: UI uses BaseOperation with RestoreOperation and DeleteOperation classes providing confirmation → progress → success/error workflows
- **User Story**: Users can press Enter on archived sessions to get recovery confirmation dialog, then recover session back to active status with progress feedback

## Task Description
Create RecoveryOperation class extending BaseOperation to handle archived session recovery with confirmation workflow, progress display, and success/error handling. This follows the established operation patterns used by restore and delete operations.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/widgets/operations/recovery_operation.py` (new file) - Create recovery operation class
  - `fabric-ui/widgets/operations/__init__.py` (add import) - Export recovery operation
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# Create new file: fabric-ui/widgets/operations/recovery_operation.py

"""
Recovery operation implementation for browse panel
"""

from typing import Dict, Any
from .base_operation import BaseOperation

from utils.path_setup import setup_fabric_ui_imports

from constants import RECOVERING_STATE


class RecoveryOperation(BaseOperation):
    """Recovery operation implementation for archived sessions"""
    
    def execute_backend_operation(self, session_name: str) -> Dict[str, Any]:
        """Execute the recovery operation via backend"""
        return self.backend_client.recover_session(session_name)
    
    def get_operation_config(self) -> Dict[str, str]:
        """Get recovery-specific configuration"""
        return {
            "color": "#a6e3a1",  # Green theme for positive action (same as restore)
            "action_verb": "Recover", 
            "description": "Recover '{session_name}' from archive?\nSession will be restored to active sessions and can be used normally.",
            "button_prefix": "recovery",
            "success_description": "recovered from archive successfully",
            "progress_state": RECOVERING_STATE,
            "operation_timeout": 45  # Recovery can involve file operations - moderate timeout
        }

# Update fabric-ui/widgets/operations/__init__.py:
# Add to existing imports:
from .recovery_operation import RecoveryOperation

# Add to __all__ list:
__all__ = ["BaseOperation", "DeleteOperation", "RestoreOperation", "RecoveryOperation"]
```

### Integration Points:
- Extends BaseOperation for consistent confirmation → progress → success/error workflow
- Uses RECOVERING_STATE constant from Task 3
- Integrates with backend_client.recover_session() from Task 8
- Follows exact same patterns as RestoreOperation and DeleteOperation

## Architecture Context
- **Component Relationships**: Used by BrowsePanelWidget for archive session recovery operations
- **State Management**: Provides recovery-specific states and configuration for operation workflow
- **Data Flow**: User Enter key → RecoveryOperation → confirmation → backend recovery → success/error display

## Dependencies
- **Prerequisite Tasks**: Task 3 (recovery constants), Task 8 (backend recovery method)
- **Blocking Tasks**: Enables Task 10 (archive mode operations) and Task 11 (operation routing)
- **Related Systems**: Uses BaseOperation framework and backend client infrastructure

## Acceptance Criteria
- [ ] RecoveryOperation class extends BaseOperation with all required methods
- [ ] `execute_backend_operation()` calls `recover_session()` on backend client
- [ ] `get_operation_config()` returns recovery-specific configuration
- [ ] Operation uses green theme consistent with positive actions (restore)
- [ ] Confirmation dialog explains recovery functionality clearly
- [ ] Operation timeout appropriate for file operations (45 seconds)
- [ ] Class follows patterns established by RestoreOperation and DeleteOperation

## Testing Strategy
- **Manual Testing**: 
  - Verify recovery confirmation dialog appears with correct messaging
  - Test recovery progress display and success/error handling
  - Confirm operation timeout behavior
- **Integration Points**: Ensure consistent with existing operation framework
- **Edge Cases**: Test with invalid archived sessions, network timeouts, permission issues

## Implementation Notes
- **Code Patterns**: Follow exact same structure as RestoreOperation and DeleteOperation classes
- **Performance Considerations**: Moderate timeout for file operations, consistent with restore operations
- **Future Extensibility**: Can be extended for custom name recovery, batch recovery

## Commit Information
- **Commit Message**: "Add recovery operation class for archived session recovery"
- **Estimated Time**: 25 minutes
- **Complexity Justification**: Medium - New operation class requiring integration with multiple systems (BaseOperation, backend client, constants), but following established patterns