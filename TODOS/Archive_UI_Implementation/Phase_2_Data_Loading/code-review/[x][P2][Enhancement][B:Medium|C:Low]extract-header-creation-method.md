# Extract Header Creation Method

## Priority: P2 | Type: Enhancement | Benefit: Medium | Complexity: Low

## Problem Description

Header creation logic is duplicated in two locations with identical parameter sets, violating the DRY (Don't Repeat Yourself) principle. This duplication increases maintenance burden and creates risk of inconsistencies if one location is updated but not the other.

**Current Issues:**
- Identical header creation calls in `_create_browsing_content()` and `_update_sessions_only()`
- Parameter list repeated in both locations
- Risk of inconsistent behavior if only one location is updated
- Maintenance overhead when header creation logic needs changes

## Implementation Plan

1. Create private method `_create_current_header()` to encapsulate header creation
2. Replace both duplicated calls with calls to the new method
3. Ensure both call sites use the new method correctly
4. Verify header creation still works in both contexts

## File Locations

- **fabric-ui/widgets/browse_panel.py**:
  - Lines 151-156: Header creation in `_create_browsing_content()` (replace)
  - Lines 243-248: Header creation in `_update_sessions_only()` (replace)
  - Add new method around line 164: `_create_current_header()` (new method location)

## Success Criteria

- [ ] New `_create_current_header()` method created with proper documentation
- [ ] Both duplicate header creation calls replaced with method calls
- [ ] Header display works correctly in both browsing and search update contexts
- [ ] No functional changes to header behavior
- [ ] Code is more maintainable with single source of truth

## Dependencies

None - this is a pure refactoring that doesn't affect functionality.

## Code Examples

**Before (Duplicated Code):**
```python
# In _create_browsing_content() around line 151
sessions_header = self.list_renderer.create_sessions_header(
    len(self.all_session_names),
    len(self.filtered_sessions),
    self.search_manager.has_search_query(),
    self.is_archive_mode,
)

# In _update_sessions_only() around line 243  
updated_header = self.list_renderer.create_sessions_header(
    len(self.all_session_names),
    len(self.filtered_sessions),
    self.search_manager.has_search_query(),
    self.is_archive_mode,
)
```

**After (DRY Principle Applied):**
```python
def _create_current_header(self):
    """Create header for current mode and state"""
    return self.list_renderer.create_sessions_header(
        len(self.all_session_names),
        len(self.filtered_sessions),
        self.search_manager.has_search_query(),
        self.is_archive_mode,
    )

# Usage in _create_browsing_content()
sessions_header = self._create_current_header()

# Usage in _update_sessions_only()
updated_header = self._create_current_header()
header.set_markup(updated_header.get_text())
```

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.