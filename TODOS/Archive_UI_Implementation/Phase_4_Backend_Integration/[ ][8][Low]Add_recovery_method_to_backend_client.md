# Add Recovery Method to Backend Client

## Context & Background
- **Feature Goal**: Add archive mode toggle with recovery operations to restore archived sessions back to active status
- **Current Architecture**: BackendClient provides methods like `save_session()`, `restore_session()`, `delete_session()` using `_run_command()` infrastructure
- **User Story**: UI needs to call the backend recovery functionality to recover archived sessions, following the same patterns as other backend operations

## Task Description
Add `recover_session()` method to BackendClient class to enable UI recovery operations for archived sessions. This method should follow existing patterns and integrate with the established CLI backend communication system.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/utils/backend_client.py` (add new method after existing session methods ~119) - Add recover_session method
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# Add after existing delete_session method around line 119:

def recover_session(self, archived_session_name: str, new_name: str = None) -> Dict[str, Any]:
    """
    Recover an archived session back to active status
    
    Args:
        archived_session_name: Name of archived session (with timestamp suffix)
        new_name: Optional new name for recovered session
        
    Returns:
        Dict containing recovery result with success status and details
        
    Raises:
        BackendError: If recovery operation fails
    """
    if new_name:
        return self._run_command(['recover', archived_session_name, new_name])
    else:
        return self._run_command(['recover', archived_session_name])
```

### Integration Points:
- Uses existing `_run_command()` infrastructure for consistent error handling
- Follows same patterns as `restore_session()`, `delete_session()` methods
- Returns structured JSON data matching other backend operations

## Architecture Context
- **Component Relationships**: Provides backend interface for recovery operations in UI components
- **State Management**: Enables UI to trigger backend session recovery operations
- **Data Flow**: UI recovery operation → BackendClient.recover_session() → CLI backend → JSON response

## Dependencies
- **Prerequisite Tasks**: Task 3 (recovery constants for error handling)
- **Blocking Tasks**: Enables Task 9 (recovery operation class) and Task 10 (archive mode operations)
- **Related Systems**: Backend recovery functionality already exists and is tested in CLI

## Acceptance Criteria
- [ ] `recover_session()` method added with proper type hints and documentation
- [ ] Method supports both original name recovery and custom name recovery
- [ ] Uses existing `_run_command()` infrastructure for consistency
- [ ] Returns structured JSON response matching other backend methods
- [ ] Proper error handling through existing BackendError system
- [ ] Method signature matches established patterns in BackendClient

## Testing Strategy
- **Manual Testing**: 
  - Test recovery with original name (single parameter)
  - Test recovery with custom name (two parameters) 
  - Verify error handling for invalid archived sessions
- **Integration Points**: Ensure consistent with existing backend communication patterns
- **Edge Cases**: Test with malformed archive names, non-existent sessions, permission issues

## Implementation Notes
- **Code Patterns**: Follow exact same structure as existing `restore_session()` and `delete_session()` methods
- **Performance Considerations**: Same performance profile as existing backend operations
- **Future Extensibility**: Can be extended for batch recovery operations if needed

## Commit Information
- **Commit Message**: "Add recovery session method to backend client"
- **Estimated Time**: 15 minutes
- **Complexity Justification**: Low - Simple method addition following established patterns, leverages existing infrastructure