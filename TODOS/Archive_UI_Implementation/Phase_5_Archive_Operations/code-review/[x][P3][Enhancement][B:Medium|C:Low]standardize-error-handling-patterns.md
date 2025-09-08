# Standardize Error Handling Patterns

## Priority: P3 | Type: Enhancement | Benefit: Medium | Complexity: Low

## Problem Description

Recovery operations don't follow the established error handling patterns used elsewhere in the codebase. The archive system should use consistent error handling with the existing `OperationResult` system and structured error messages.

**Current Issue**: Inconsistent error handling between archive and active mode operations.

## Implementation Plan

1. **Review existing error handling patterns** in restore and delete operations
2. **Identify inconsistencies** in recovery operation error handling
3. **Update recovery backend method** to use established error patterns
4. **Standardize error messages** to match existing operation format
5. **Add proper error categorization** using existing OperationResult types
6. **Test error scenarios** for consistency across all operation types

## File Locations

- **Review**: `commands/restore.py` - Reference for established patterns
- **Update**: `commands/recover.py` - Standardize error handling
- **Modify**: `fabric-ui/utils/backend_client.py` - Consistent error parsing
- **Test**: Error handling consistency across all operations

## Success Criteria

- [ ] Recovery operations use identical error handling patterns to restore operations
- [ ] Error messages follow established format and categorization
- [ ] OperationResult system used consistently for recovery errors
- [ ] Error types properly categorized (filesystem, permission, timeout, etc.)
- [ ] User-facing error messages provide actionable guidance
- [ ] Debug error context consistent with existing operations

## Dependencies

None - this is an independent consistency improvement

## Code Examples

**Current Inconsistent Pattern** (if exists):
```python
# In recover.py - potentially inconsistent error handling
def recover_session(session_name, new_name=None):
    try:
        # Recovery logic...
        return {"success": True}  # Inconsistent format
    except Exception as e:
        return {"success": False, "error": str(e)}  # Basic error handling
```

**Proposed Standardized Pattern**:
```python
# In recover.py - follow restore.py patterns
def recover_session(session_name, new_name=None):
    result = OperationResult.success("Archive recovery", "recover_session")
    
    try:
        # Recovery logic...
        result.add_info(f"Successfully recovered '{session_name}' from archive")
        
    except PermissionError as e:
        result.add_filesystem_error(e, f"recover archived session '{session_name}'", archive_path)
    except FileNotFoundError as e:
        result.add_error(f"Archived session '{session_name}' not found")
    except TimeoutError as e:
        result.add_subprocess_error(e, "recovery operation", "session restoration")
    except Exception as e:
        result.add_error(f"Unexpected error during recovery: {str(e)}")
        result.add_context("error_type", type(e).__name__)
    
    return result.to_dict()
```

**Backend Client Consistency** (`backend_client.py`):
```python
def recover_session(self, archived_session_name: str, new_name: str = None) -> Dict[str, Any]:
    """Recover archived session with consistent error handling"""
    try:
        if new_name:
            result = self._run_command(['recover', archived_session_name, new_name])
        else:
            result = self._run_command(['recover', archived_session_name])
        
        # Consistent success/error parsing with existing operations
        return self._parse_operation_result(result, "recover_session")
        
    except subprocess.TimeoutExpired as e:
        return self._create_timeout_error("Recovery operation", 45)
    except subprocess.CalledProcessError as e:
        return self._create_subprocess_error("Recovery command", e)
```

**Error Message Standardization**:
```python
# Consistent error message format across all operations
OPERATION_ERROR_MESSAGES = {
    "restore": "Failed to restore session '{session_name}': {error_detail}",
    "recover": "Failed to recover session '{session_name}': {error_detail}",
    "delete": "Failed to archive session '{session_name}': {error_detail}",
}

def format_operation_error(operation_type: str, session_name: str, error_detail: str) -> str:
    template = OPERATION_ERROR_MESSAGES.get(operation_type, "Operation failed: {error_detail}")
    return template.format(session_name=session_name, error_detail=error_detail)
```

**Benefits**:
- **Consistent user experience** across all operations
- **Predictable error handling** for UI integration
- **Standardized debug information** for troubleshooting
- **Reusable error handling patterns** for future operations
- **Better error categorization** for appropriate user guidance

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.