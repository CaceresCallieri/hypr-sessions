# Eliminate Code Duplication in Session Loading Methods

## Priority: P3 | Type: Enhancement | Benefit: Low | Complexity: Low

## Problem Description
The `get_archived_sessions()` method duplicates directory iteration logic from `get_available_sessions()`, violating DRY principles. Both methods follow identical patterns for session validation and listing, creating maintenance overhead and inconsistency risk.

## Implementation Plan
1. Extract shared directory iteration logic into private helper method
2. Create `_get_sessions_from_directory(directory: Path) -> List[str]` helper
3. Refactor both `get_available_sessions()` and `get_archived_sessions()` to use helper
4. Ensure helper method includes all security validations from the security fix
5. Maintain backward compatibility of public API

## File Locations
- **Primary**: `fabric-ui/utils/session_utils.py`
  - Lines 26-39: `get_available_sessions()` method (refactor to use helper)
  - Lines 70-83: `get_archived_sessions()` method (refactor to use helper)
  - New helper method: Insert around line 25 (before existing methods)

## Success Criteria
- [ ] `_get_sessions_from_directory()` helper method created with comprehensive validation
- [ ] `get_available_sessions()` refactored to use helper method
- [ ] `get_archived_sessions()` refactored to use helper method
- [ ] All existing functionality preserved (no breaking changes)
- [ ] Security validations maintained in helper method
- [ ] Code reduction of ~15-20 lines through deduplication

## Dependencies
[Depends-On: fix-path-traversal-vulnerability] - Security patterns must be established first
[Depends-On: add-missing-type-annotations] - Type system should be complete

## Code Examples

**Current Duplicated Code Pattern:**
```python
# In get_available_sessions():
for item in sessions_dir.iterdir():
    if item.is_dir():
        session_file = item / "session.json"
        if session_file.exists():
            sessions.append(item.name)

# In get_archived_sessions():
for item in archived_dir.iterdir():
    if item.is_dir() and not item.name.startswith('.'):
        session_file = item / "session.json"
        if session_file.exists():
            sessions.append(item.name)
```

**Proposed Deduplicated Implementation:**
```python
@staticmethod
def _get_sessions_from_directory(directory: Path, include_hidden: bool = False) -> List[str]:
    """Helper method to extract valid sessions from any directory"""
    if not directory.exists():
        return []
    
    sessions = []
    try:
        for item in directory.iterdir():
            # Security validation and directory filtering
            if (item.is_dir() and 
                (include_hidden or not item.name.startswith('.')) and
                not '..' in item.name and
                not item.name.startswith('/') and
                not item.name.startswith('\\')):
                try:
                    session_file = item / "session.json"
                    if session_file.exists():
                        sessions.append(item.name)
                except (PermissionError, OSError):
                    continue
    except (PermissionError, OSError):
        return []
    
    return sorted(sessions)

@staticmethod
def get_available_sessions() -> List[str]:
    """Get list of available session names"""
    return SessionUtils._get_sessions_from_directory(
        SessionUtils.get_sessions_directory(), 
        include_hidden=False
    )

@staticmethod  
def get_archived_sessions() -> List[str]:
    """Get list of archived session names with timestamps"""
    return SessionUtils._get_sessions_from_directory(
        SessionUtils.get_archived_sessions_directory(), 
        include_hidden=False
    )
```

## Reminder
When implementation is finished, update the filename prefix from `[ ]` to `[x]`.