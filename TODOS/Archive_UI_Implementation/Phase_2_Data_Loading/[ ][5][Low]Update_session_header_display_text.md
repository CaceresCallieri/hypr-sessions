# Update Session Header Display Text

## Context & Background
- **Feature Goal**: Add archive mode toggle with Ctrl+A to browse archived sessions with clear visual feedback about current mode
- **Current Architecture**: BrowsePanelWidget displays session count in header using dynamic text updates based on session data
- **User Story**: Users should clearly see whether they're viewing "Available Sessions (N)" or "Archived Sessions (N)" to understand current mode

## Task Description
Update the session header display text to indicate current mode (active vs archive sessions) while maintaining the existing session count display pattern. This provides clear visual feedback about which session list is currently active.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/widgets/browse_panel.py` (locate header/title text generation) - Update header text based on mode
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# Find the method that generates header text (likely in session list creation)
# Add mode-aware header text generation:

def _get_session_list_header_text(self):
    """Generate header text based on current mode and session count"""
    session_count = len(self.all_session_names)
    
    if self.is_archive_mode:
        return f"Archived Sessions ({session_count})"
    else:
        return f"Available Sessions ({session_count})"

# Update wherever header text is generated to use this method
# Example: replace existing text with self._get_session_list_header_text()
```

### Integration Points:
- Integrates with existing header/title display system in BrowsePanelWidget
- Works with existing session count display patterns
- Maintains consistent text formatting and styling

## Architecture Context
- **Component Relationships**: Updates visual display in main browse panel header
- **State Management**: Uses archive mode state to determine display text
- **Data Flow**: Mode state + session count → header text generation → UI display

## Dependencies
- **Prerequisite Tasks**: Task 1 (archive mode state), Task 4 (session loading logic)
- **Blocking Tasks**: Provides visual feedback for Task 6 (Ctrl+A toggle)
- **Related Systems**: Must work with existing UI text display and styling systems

## Acceptance Criteria
- [ ] Header displays "Available Sessions (N)" in active mode
- [ ] Header displays "Archived Sessions (N)" in archive mode  
- [ ] Session count accurately reflects loaded session data
- [ ] Text formatting matches existing header styling
- [ ] Header updates correctly when switching between modes
- [ ] No impact on existing header display functionality

## Testing Strategy
- **Manual Testing**: 
  - Verify header shows correct text in both modes
  - Test with different session counts in both modes
  - Confirm text updates when switching modes
- **Integration Points**: Ensure header styling and positioning remain unchanged
- **Edge Cases**: Test with zero sessions, very large session counts

## Implementation Notes
- **Code Patterns**: Follow existing UI text generation and display patterns
- **Performance Considerations**: Minimal - simple text generation based on state
- **Future Extensibility**: Can be extended for additional mode indicators or styling

## Commit Information
- **Commit Message**: "Add mode-aware header text display for archive functionality"
- **Estimated Time**: 15 minutes
- **Complexity Justification**: Low - Simple text display modification, straightforward UI update