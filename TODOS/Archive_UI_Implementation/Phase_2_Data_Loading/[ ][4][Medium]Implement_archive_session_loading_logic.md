# Implement Archive Session Loading Logic

## Context & Background
- **Feature Goal**: Add archive mode toggle with Ctrl+A to browse archived sessions while maintaining all existing functionality (search, navigation, windowing)
- **Current Architecture**: BrowsePanelWidget loads sessions via `self.session_utils.get_available_sessions()` and stores in `self.all_session_names`, with all components working off this data
- **User Story**: When in archive mode, UI should load archived sessions instead of active sessions, with all existing functionality (search, navigation, windowing) working identically

## Task Description
Implement session loading logic that switches between active and archived sessions based on archive mode state. This involves modifying the existing session loading in BrowsePanelWidget to be mode-aware while maintaining all existing functionality.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/widgets/browse_panel.py` (lines ~177 in reload_sessions method) - Modify session loading logic
  - `fabric-ui/widgets/browse_panel.py` (add new method) - Add mode-aware loading helper
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# Modify existing reload_sessions method around line 177:
def reload_sessions(self):
    """Reload session list and refresh UI - supports both active and archive modes"""
    self._load_sessions_for_current_mode()
    
    # Rest of method remains unchanged
    self.filtered_sessions, suggested_selection = (
        self.search_manager.update_filtered_sessions(self.all_session_names)
    )
    # ... existing code continues unchanged

# Add new helper method:
def _load_sessions_for_current_mode(self):
    """Load sessions based on current mode (active vs archive)"""
    if self.is_archive_mode:
        self.all_session_names = self.session_utils.get_archived_sessions()
        # Update cache for archive mode
        self.archive_session_names = self.all_session_names.copy()
    else:
        self.all_session_names = self.session_utils.get_available_sessions()
```

### Integration Points:
- Works with existing `self.all_session_names` that all components expect
- All search, navigation, and windowing components work unchanged
- Maintains existing data loading patterns and error handling

## Architecture Context
- **Component Relationships**: Provides data for SearchManager, WindowCalculator, SessionListRenderer components
- **State Management**: Uses archive mode state from Task 1 to determine data source
- **Data Flow**: Mode state → load appropriate session data → existing components work unchanged

## Dependencies
- **Prerequisite Tasks**: Task 1 (archive mode state), Task 2 (SessionUtils archived methods)
- **Blocking Tasks**: Enables Task 5 (header display updates) and Task 6 (Ctrl+A toggle)
- **Related Systems**: Integrates with existing SessionUtils data loading and component architecture

## Acceptance Criteria
- [ ] `_load_sessions_for_current_mode()` method loads appropriate session data based on mode
- [ ] Archive mode loads archived sessions via `get_archived_sessions()`
- [ ] Active mode loads active sessions via existing `get_available_sessions()`
- [ ] All existing functionality (search, navigation, windowing) works in both modes
- [ ] Session data caching works correctly for both modes
- [ ] No breaking changes to existing session loading behavior

## Testing Strategy
- **Manual Testing**: 
  - Toggle archive mode and verify correct session data loads
  - Verify search functionality works with both active and archived sessions
  - Test navigation and windowing with different session counts
- **Integration Points**: Ensure all existing browse panel functionality works in both modes
- **Edge Cases**: Test with no archived sessions, mixed session counts, permission issues

## Implementation Notes
- **Code Patterns**: Follow existing session loading patterns, maintain compatibility with all components
- **Performance Considerations**: Minimal overhead - same data loading pattern with mode check
- **Future Extensibility**: Foundation for mode switching and enhanced data loading

## Commit Information
- **Commit Message**: "Implement mode-aware session loading for archive functionality"
- **Estimated Time**: 30 minutes
- **Complexity Justification**: Medium - Core data loading modification that affects multiple components, requires careful integration with existing architecture