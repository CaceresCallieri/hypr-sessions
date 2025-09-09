# ✅ Fix Over-Broad Exception Handling - COMPLETED

## Priority: P1 | Type: Fix | Benefit: High | Complexity: Medium

## Problem Description

Generic `except Exception as e:` catches throughout codebase (69+ occurrences) mask specific error conditions and make debugging difficult. This prevents proper error handling and reduces system reliability by catching and suppressing critical errors that should be handled differently.

## Implementation Plan

1. **Audit Exception Usage**: Review all generic exception handlers
2. **Categorize Errors**: Group by expected error types (filesystem, network, validation, etc.)
3. **Replace Generic Handlers**: Implement specific exception handling per category
4. **Add Proper Logging**: Include context-aware error messages
5. **Test Error Scenarios**: Verify proper handling of each error type

## File Locations

**Primary Files**:
- `/home/jc/Dev/hypr-sessions/commands/recover.py:319` - Generic exception in recovery operation
- `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/operations/base_operation.py:306` - UI operation error handling
- Multiple command files in `commands/` directory with similar patterns

**Pattern to Fix**:
```python
# Current (problematic)
try:
    some_operation()
except Exception as e:
    self.add_error(f"Unexpected error: {e}")

# Target (specific)
try:
    some_operation()
except (OSError, PermissionError) as e:
    self.add_error(f"File system error: {e}")
except ValueError as e:
    self.add_error(f"Invalid data: {e}")
except Exception as e:
    # Only for truly unexpected errors
    self.add_error(f"Unexpected error: {e}")
    logger.exception("Unexpected error in operation")
```

## Success Criteria

- [ ] Reduce generic `except Exception` handlers by 80%+
- [ ] All filesystem operations use specific exception types
- [ ] All JSON operations handle JSONDecodeError specifically
- [ ] All subprocess operations handle TimeoutExpired and CalledProcessError
- [ ] Debug logging includes proper exception context
- [ ] Error messages provide actionable information to users

## Dependencies

None

## Code Examples

**Archive Operations** (`commands/recover.py`):
```python
# Replace generic handling with specific types
try:
    metadata = self._load_archive_metadata(archived_session_path)
except (FileNotFoundError, PermissionError) as e:
    result.add_error(f"Cannot access archive metadata: {e}")
except json.JSONDecodeError as e:
    result.add_error(f"Corrupted archive metadata: line {e.lineno}")
except Exception as e:
    result.add_error(f"Unexpected metadata error: {e}")
    self.debug_print(f"Unexpected error in metadata loading: {type(e).__name__}: {e}")
```

**UI Operations** (`fabric-ui/widgets/operations/base_operation.py`):
```python
# Specific exception handling for backend operations
try:
    result = self.execute_backend_operation(session_name)
except subprocess.TimeoutExpired as e:
    self.debug_print(f"Backend operation timed out: {e}")
    GLib.idle_add(self._handle_error_async, session_name, "Operation timed out")
except subprocess.CalledProcessError as e:
    self.debug_print(f"Backend command failed: {e.stderr}")
    GLib.idle_add(self._handle_error_async, session_name, f"Command failed: {e}")
```

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.