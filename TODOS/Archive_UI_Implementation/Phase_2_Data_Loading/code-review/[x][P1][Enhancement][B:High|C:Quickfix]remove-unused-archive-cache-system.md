# Remove Unused Archive Cache System

## Priority: P1 | Type: Enhancement | Benefit: High | Complexity: Quickfix

## Problem Description

The `archive_session_names` cache serves no practical purpose in the current implementation. It's rebuilt on every mode switch and never actually used for caching, adding unnecessary complexity and memory usage without providing any performance benefits.

**Current Issues:**
- Unnecessary `copy()` operation on session list
- Cache clearing logic that serves no purpose
- Additional state variable that complicates debugging
- Memory overhead for unused data structure

## Implementation Plan

1. Remove `archive_session_names` from class initialization
2. Remove cache management logic from `_load_sessions_for_current_mode()`
3. Clean up any references to the unused cache variable
4. Verify no other code depends on this cache

## File Locations

- **fabric-ui/widgets/browse_panel.py**:
  - Line 98: `self.archive_session_names = []` (remove initialization)
  - Lines 202-203: `self.archive_session_names = self.all_session_names.copy()` (remove cache update)
  - Lines 206-207: `self.archive_session_names = []` (remove cache clearing)

## Success Criteria

- [ ] `archive_session_names` variable completely removed from browse_panel.py
- [ ] No `copy()` operations in `_load_sessions_for_current_mode()`
- [ ] Mode switching still works correctly
- [ ] No references to removed cache variable remain
- [ ] Memory usage reduced (one less list in memory)

## Dependencies

None - this is a pure removal of unused code.

## Code Examples

**Before (Current - Unnecessary Complexity):**
```python
# Line 98 - Unused initialization
self.archive_session_names = []     # ← Remove this

def _load_sessions_for_current_mode(self):
    """Load sessions based on current mode (active vs archive)"""
    if self.is_archive_mode:
        self.all_session_names = self.session_utils.get_archived_sessions()
        # Update cache for archive mode
        self.archive_session_names = self.all_session_names.copy()  # ← Remove this
    else:
        self.all_session_names = self.session_utils.get_available_sessions()
        # Clear archive cache when in active mode
        self.archive_session_names = []  # ← Remove this
```

**After (Simplified - Only What's Needed):**
```python
def _load_sessions_for_current_mode(self):
    """Load sessions based on current mode (active vs archive)"""
    if self.is_archive_mode:
        self.all_session_names = self.session_utils.get_archived_sessions()
    else:
        self.all_session_names = self.session_utils.get_available_sessions()
```

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.