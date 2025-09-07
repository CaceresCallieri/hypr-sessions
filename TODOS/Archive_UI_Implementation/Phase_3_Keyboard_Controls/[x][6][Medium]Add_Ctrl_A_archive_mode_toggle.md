# Add Ctrl+A Archive Mode Toggle

## Context & Background
- **Feature Goal**: Add archive mode toggle with Ctrl+A to browse archived sessions while maintaining search functionality and all existing UI behavior
- **Current Architecture**: KeyboardEventHandler processes Ctrl+key combinations with existing Ctrl+D (delete) and Ctrl+L (clear search) functionality
- **User Story**: Users press Ctrl+A to toggle between active sessions and archived sessions view, with search state preserved and UI updating seamlessly

## Task Description
Add Ctrl+A keyboard shortcut handling to KeyboardEventHandler that toggles archive mode, reloads appropriate session data, preserves search state, and maintains current selection where possible. This provides the primary user interface for switching between active and archive modes.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/widgets/components/keyboard_event_handler.py` (lines ~214 in _handle_ctrl_shortcuts) - Add Ctrl+A handler
  - `fabric-ui/widgets/components/keyboard_event_handler.py` (add new method) - Add toggle implementation
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# In _handle_ctrl_shortcuts method around line 214, add:
def _handle_ctrl_shortcuts(self, event, keyval) -> bool:
    # ... existing Ctrl+D and Ctrl+L handlers
    elif keyval == Gdk.KEY_a:
        return self._handle_ctrl_a_toggle_archive()
    
    return False

# Add new toggle method:
def _handle_ctrl_a_toggle_archive(self) -> bool:
    """Handle Ctrl+A archive mode toggle
    
    Returns:
        True if toggle operation was successful
    """
    # Debug log the toggle
    if self.debug_logger:
        current_mode = "archive" if self.browse_panel.is_archive_mode else "active"
        target_mode = "active" if self.browse_panel.is_archive_mode else "archive"
        self.debug_logger.debug_navigation_operation(
            "archive_mode_toggle", f"{current_mode}_to_{target_mode}", None, "ctrl_a_shortcut"
        )
    
    # Toggle archive mode state
    self.browse_panel.is_archive_mode = not self.browse_panel.is_archive_mode
    
    # Preserve current search query
    current_search = self.browse_panel.search_manager.get_current_search_query()
    
    # Reload sessions for new mode (this triggers UI update)
    self.browse_panel.reload_sessions()
    
    # Restore search query if it existed
    if current_search:
        self.browse_panel.search_manager.set_search_query(current_search)
        self.browse_panel.update_session_display()
    
    return True
```

### Integration Points:
- Leverages existing Ctrl+key handling infrastructure in KeyboardEventHandler
- Uses existing session reload mechanism from BrowsePanelWidget
- Integrates with search manager to preserve search state across mode switches

## Architecture Context
- **Component Relationships**: Coordinates between KeyboardEventHandler, BrowsePanelWidget, and SearchManager components
- **State Management**: Toggles archive mode state and triggers appropriate data reload
- **Data Flow**: Keyboard input → state toggle → session reload → search preservation → UI update

## Dependencies
- **Prerequisite Tasks**: Task 1 (archive mode state), Task 4 (session loading logic), Task 5 (header display)
- **Blocking Tasks**: Enables full archive mode functionality for subsequent phases
- **Related Systems**: Uses existing keyboard handling, session loading, and search management systems

## Acceptance Criteria
- [ ] Ctrl+A toggles between active and archive session modes
- [ ] Session list updates to show appropriate sessions (active vs archived)
- [ ] Header text updates to reflect current mode ("Available" vs "Archived")
- [ ] Search query is preserved when switching modes
- [ ] Current selection is maintained where possible
- [ ] All existing keyboard shortcuts continue to work
- [ ] Debug logging captures mode toggle operations

## Testing Strategy
- **Manual Testing**: 
  - Press Ctrl+A and verify mode switch with correct session data
  - Test with search query active and verify it's preserved
  - Verify selection behavior when switching modes
  - Test rapid mode switching for stability
- **Integration Points**: Ensure all existing keyboard shortcuts work in both modes
- **Edge Cases**: Test with empty session lists, during search operations, with different selection states

## Implementation Notes
- **Code Patterns**: Follow existing Ctrl+key handler patterns in KeyboardEventHandler
- **Performance Considerations**: Minimal overhead - leverages existing reload mechanisms
- **Future Extensibility**: Provides foundation for additional mode-specific keyboard shortcuts

## Commit Information
- **Commit Message**: "Add Ctrl+A keyboard shortcut for archive mode toggle"
- **Estimated Time**: 35 minutes
- **Complexity Justification**: Medium - Involves coordination between multiple components (keyboard, state, search, display) with careful state preservation