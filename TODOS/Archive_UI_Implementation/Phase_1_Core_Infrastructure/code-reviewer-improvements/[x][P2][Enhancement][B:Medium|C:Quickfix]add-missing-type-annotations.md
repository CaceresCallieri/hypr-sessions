# Add Missing Type Annotations to SessionUtils Archive Methods

## Priority: P2 | Type: Enhancement | Benefit: Medium | Complexity: Quickfix

## Problem Description
The newly added archive methods in SessionUtils lack proper type annotations, reducing IDE support and code clarity. The `get_archived_sessions()` method is missing its return type hint, breaking consistency with existing codebase patterns.

## Implementation Plan
1. Add missing `List[str]` import from typing module
2. Add proper return type annotation to `get_archived_sessions()` method
3. Add return type annotation to `get_archived_sessions_directory()` method
4. Ensure consistency with existing method signatures in the class

## File Locations
- **Primary**: `fabric-ui/utils/session_utils.py` 
  - Line 5: Add `List` to existing typing import
  - Line 62: Add return type to `get_archived_sessions_directory()`
  - Line 70: Add return type to `get_archived_sessions()`

## Success Criteria
- [ ] `from typing import List` added to imports (or updated existing import)
- [ ] `get_archived_sessions_directory()` has `-> Path` return type
- [ ] `get_archived_sessions()` has `-> List[str]` return type
- [ ] All type annotations match existing codebase patterns
- [ ] No breaking changes to functionality

## Dependencies
[Depends-On: fix-path-traversal-vulnerability] - Security fix should be completed first

## Code Examples

**Current Missing Type Annotations:**
```python
@staticmethod
def get_archived_sessions_directory():  # Missing -> Path
    """Get the archived sessions directory path"""
    # ...

@staticmethod
def get_archived_sessions():  # Missing -> List[str]
    """Get list of archived session names with timestamps"""
    # ...
```

**Proposed Type Annotations:**
```python
from pathlib import Path
from typing import List  # Add this import

@staticmethod
def get_archived_sessions_directory() -> Path:
    """Get the archived sessions directory path"""
    # ...

@staticmethod
def get_archived_sessions() -> List[str]:
    """Get list of archived session names with timestamps"""
    # ...
```

## Reminder
When implementation is finished, update the filename prefix from `[ ]` to `[x]`.