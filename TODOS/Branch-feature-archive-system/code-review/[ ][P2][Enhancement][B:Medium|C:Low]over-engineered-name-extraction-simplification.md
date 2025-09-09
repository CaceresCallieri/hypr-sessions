# Simplify Over-Engineered Name Extraction

## Priority: P2 | Type: Enhancement | Benefit: Medium | Complexity: Low

## Problem Description

The `_extract_safe_original_name` method in recovery operations has 62 lines for a simple string operation, representing unnecessary complexity for basic functionality. This makes the code harder to understand and maintain.

## Implementation Plan

1. **Analyze Current Logic**: Understand all edge cases the current method handles
2. **Identify Essential Validation**: Determine what validation is truly necessary
3. **Simplify Implementation**: Reduce to essential string manipulation and validation
4. **Preserve Safety**: Maintain security validation while reducing complexity
5. **Test Edge Cases**: Ensure simplified version handles all necessary scenarios

## File Locations

**Primary File**:
- `/home/jc/Dev/hypr-sessions/commands/recover.py:96-157`

**Current Method**: `_extract_safe_original_name` (62 lines)

## Success Criteria

- [ ] Reduce method from 62 lines to ~15-20 lines
- [ ] Maintain all security validation
- [ ] Handle all current edge cases correctly
- [ ] Improve code readability and maintainability
- [ ] Preserve existing behavior for valid inputs
- [ ] Maintain safe fallback for invalid inputs

## Dependencies

None

## Code Examples

**Current Over-Engineered Implementation** (excerpt):
```python
def _extract_safe_original_name(self, archived_name: str) -> str:
    """Extract original session name from archived name with comprehensive validation"""
    # 62 lines of complex logic with multiple validation layers
    # Multiple try-catch blocks
    # Complex string manipulation
    # Extensive error handling
    # ... (many lines of complexity)
```

**Simplified Target Implementation**:
```python
def _extract_original_name(self, archived_name: str) -> str:
    """Extract original session name with essential validation"""
    if not archived_name or not isinstance(archived_name, str):
        return "recovered-session"
    
    # Split archive name: "session-name-20250831-123456" → ["session-name", "20250831", "123456"]
    parts = archived_name.split('-')
    if len(parts) < 3:
        return "recovered-session"
    
    # Extract original name by removing timestamp suffix (last 2 parts)
    original_name = '-'.join(parts[:-2])
    
    # Validate extracted name using existing validator
    try:
        SessionValidator.validate_session_name(original_name)
        return original_name
    except (InvalidSessionNameError, SessionValidationError):
        return "recovered-session"  # Safe fallback
```

**Usage Simplification**:
```python
# Current complex usage
try:
    original_name = self._extract_safe_original_name(archived_session_name)
    # Complex error handling for extraction failures
except Exception as e:
    # Multiple error paths...

# Simplified usage  
original_name = self._extract_original_name(archived_session_name)
# Always returns valid name - no exception handling needed
```

**Benefits of Simplification**:
- **Readability**: Clear, linear logic flow
- **Maintainability**: Fewer edge cases to track
- **Performance**: Fewer operations and checks
- **Reliability**: Simpler code has fewer bugs
- **Testability**: Easier to write comprehensive tests

**Preserved Functionality**:
- Security validation via `SessionValidator`
- Safe fallback for all invalid inputs
- Timestamp suffix removal logic
- Hyphenated name support

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.