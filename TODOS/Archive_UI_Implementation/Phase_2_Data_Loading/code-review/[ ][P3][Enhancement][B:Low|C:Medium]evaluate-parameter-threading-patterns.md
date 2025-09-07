# Evaluate Parameter Threading Patterns

## Priority: P3 | Type: Enhancement | Benefit: Low | Complexity: Medium

## Problem Description

The current implementation uses "parameter threading" - passing `is_archive_mode` state through multiple component layers instead of allowing components to access parent state directly. While functional, this pattern creates unnecessary coupling and parameter proliferation that could be simplified.

**Current Issues:**
- Mode state passed through browse_panel → list_renderer → header creation
- Parameter lists growing as more state needs to be shared
- Tight coupling between component layers through parameter contracts
- Potential for parameter mismatching if interfaces change

## Implementation Plan

1. Analyze current parameter threading patterns in component architecture
2. Evaluate alternative approaches:
   - Direct parent state access through established references
   - Context objects for complex state sharing
   - Event-based state notifications
3. Choose appropriate approach that maintains component boundaries
4. Implement pilot change in header creation component
5. Assess impact on maintainability and coupling

## File Locations

- **fabric-ui/widgets/browse_panel.py**:
  - Lines 151-156: `create_sessions_header()` call with mode parameter
  - Lines 243-248: Duplicate call in `_update_sessions_only()`
- **fabric-ui/widgets/components/session_list_renderer.py**:
  - Lines 140-166: `create_sessions_header()` method signature and implementation

## Success Criteria

- [ ] Analysis completed of current parameter threading patterns
- [ ] Alternative approaches evaluated with pros/cons documented
- [ ] Recommendation made for approach that best balances simplicity vs coupling
- [ ] If changes implemented, component boundaries maintained appropriately
- [ ] No functional regression in header display or mode switching

## Dependencies

[Depends-On: extract-header-creation-method] - Should complete header method extraction first to reduce code duplication before evaluating architectural changes.

## Code Examples

**Current Pattern (Parameter Threading):**
```python
# browse_panel.py - Mode passed through layers
sessions_header = self.list_renderer.create_sessions_header(
    len(self.all_session_names),
    len(self.filtered_sessions),
    self.search_manager.has_search_query(),
    self.is_archive_mode,  # ← Threaded through layers
)

# session_list_renderer.py - Mode received as parameter
def create_sessions_header(self, all_count, filtered_count, has_query, is_archive_mode):
    if is_archive_mode:  # ← Used here
        mode_text = "Archived Sessions"
    else:
        mode_text = "Available Sessions"
```

**Alternative Option 1 (Direct Access):**
```python
# session_list_renderer.py - Access parent state directly
def create_sessions_header(self, all_count, filtered_count, has_query):
    # Access mode through established parent reference
    mode_text = "Archived Sessions" if self.parent.is_archive_mode else "Available Sessions"
```

**Alternative Option 2 (Context Object):**
```python
# browse_panel.py - Bundle related state
session_context = SessionContext(
    all_count=len(self.all_session_names),
    filtered_count=len(self.filtered_sessions),
    has_search_query=self.search_manager.has_search_query(),
    is_archive_mode=self.is_archive_mode
)
sessions_header = self.list_renderer.create_sessions_header(session_context)
```

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.