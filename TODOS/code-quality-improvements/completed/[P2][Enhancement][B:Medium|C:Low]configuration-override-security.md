# Configuration Override Security

## Priority: P2 | Type: Enhancement | Benefit: Medium | Complexity: Low

## Problem Description
Environment variable overrides don't validate bounds, allowing potentially harmful values that could cause system instability or unexpected behavior. Current implementation accepts any integer/float values without range checking, which could lead to extreme configurations like negative delays or excessive archive limits.

## Implementation Plan
1. Create `_validate_and_set_env_overrides()` method in SessionConfig class
2. Add bounds checking for each environment variable with reasonable limits
3. Add warning messages for out-of-range values with fallback to defaults
4. Handle ValueError exceptions for non-numeric inputs gracefully
5. Test with various invalid inputs to ensure robustness

## File Locations
- `/home/jc/Dev/hypr-sessions/commands/shared/config.py:52-62` - Current environment override logic
- Lines around `ARCHIVE_MAX_SESSIONS` and `DELAY_BETWEEN_INSTRUCTIONS` handling

## Success Criteria
- Environment variables validated with reasonable bounds (1-1000 for max sessions, 0.0-10.0 for delays)
- Invalid values produce warning messages and use default values
- ValueError exceptions handled gracefully with user-friendly messages
- No breaking changes to existing valid configurations

## Dependencies
None - standalone enhancement

## Code Examples

**Current problematic code:**
```python
if "ARCHIVE_MAX_SESSIONS" in os.environ:
    self.archive_max_sessions = int(os.environ["ARCHIVE_MAX_SESSIONS"])
```

**Proposed secure implementation:**
```python
def _validate_and_set_env_overrides(self):
    if "ARCHIVE_MAX_SESSIONS" in os.environ:
        try:
            max_sessions = int(os.environ["ARCHIVE_MAX_SESSIONS"])
            if 1 <= max_sessions <= 1000:
                self.archive_max_sessions = max_sessions
            else:
                print(f"Warning: ARCHIVE_MAX_SESSIONS value {max_sessions} out of range (1-1000), using default")
        except ValueError:
            print("Warning: Invalid ARCHIVE_MAX_SESSIONS value, using default")
```

## Reminder
Move this file to TODOS/code-quality-improvements/completed/ when implementation is finished.