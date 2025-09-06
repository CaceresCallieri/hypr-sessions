# Enhanced Error Granularity

## Priority: P2 | Type: Enhancement | Benefit: Medium | Complexity: Medium

## Problem Description
Current error handling uses generic exceptions and error messages, making it difficult for users to understand specific failure reasons and take appropriate action. Operations could benefit from more specific error types that provide clear guidance on resolution steps.

## Implementation Plan
1. Identify common error scenarios in archive operations (permissions, disk space, file system limits)
2. Add specific exception handling for each error type with targeted error messages
3. Enhance OperationResult error messages with actionable guidance
4. Update error handling patterns across command files for consistency
5. Test error scenarios to ensure messages are helpful and accurate

## File Locations
- Various command files (archive, restore, save operations)
- Primary focus: `/home/jc/Dev/hypr-sessions/commands/delete.py` archive operations
- `/home/jc/Dev/hypr-sessions/commands/restore.py` restore operations
- `/home/jc/Dev/hypr-sessions/commands/save/session_saver.py` save operations

## Success Criteria
- Specific error types handle common failure scenarios (PermissionError, FileNotFoundError, OSError variants)
- Error messages provide clear explanation and suggested actions
- Users can distinguish between different failure types (permissions vs disk space vs filesystem limits)
- Consistent error handling patterns across all command operations

## Dependencies
None - enhancement to existing error handling

## Code Examples

**Current generic handling:**
```python
except Exception as e:
    result.add_error(f"Failed to archive session directory: {e}")
    return result
```

**Proposed specific handling:**
```python
except PermissionError as e:
    result.add_error(f"Permission denied: Cannot archive session '{session_name}'. Check file permissions.")
    return result
except FileNotFoundError as e:
    result.add_error(f"Session not found: '{session_name}' does not exist in active sessions.")
    return result
except OSError as e:
    if e.errno == errno.ENOSPC:
        result.add_error(f"Insufficient disk space to archive session '{session_name}'.")
    elif e.errno == errno.ENAMETOOLONG:
        result.add_error(f"Session name too long for filesystem: '{session_name}'.")
    else:
        result.add_error(f"File system error archiving session: {e}")
    return result
```

## Reminder
Move this file to TODOS/code-quality-improvements/completed/ when implementation is finished.