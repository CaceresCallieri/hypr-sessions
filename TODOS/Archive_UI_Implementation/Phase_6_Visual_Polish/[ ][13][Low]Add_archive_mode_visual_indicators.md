# Add Archive Mode Visual Indicators

## Context & Background
- **Feature Goal**: Provide subtle visual cues to help users understand when they're viewing archived sessions vs active sessions
- **Current Architecture**: BrowsePanelWidget uses Mac Tahoe white theme with existing header text and session display styling
- **User Story**: Users should have additional visual feedback beyond header text to clearly distinguish between active and archive modes

## Task Description
Add subtle visual indicators to distinguish archive mode from active mode, such as styling changes to the header or session list, while maintaining the existing Mac Tahoe aesthetic and not disrupting the clean UI design.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/session_manager.css` (add archive mode styles) - Add archive-specific styling
  - `fabric-ui/widgets/browse_panel.py` (add CSS class management) - Apply mode-specific styling
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# In BrowsePanelWidget, add CSS class management:

def _update_mode_styling(self):
    """Update CSS classes based on current mode"""
    style_context = self.get_style_context()
    
    if self.is_archive_mode:
        style_context.add_class("archive-mode")
        style_context.remove_class("active-mode")
    else:
        style_context.add_class("active-mode") 
        style_context.remove_class("archive-mode")

# Call this method when mode changes (in toggle and ESC handlers)

# Add to CSS file:
/* Archive mode subtle visual indicators */
.archive-mode {
    /* Slightly different background tint */
    background-color: alpha(#f5f5f5, 0.95);
}

.archive-mode #browse-panel-header {
    /* Subtle header styling for archive mode */
    border-left: 3px solid #a6e3a1; /* Green accent to match recovery operation */
}

/* Ensure active mode has clean styling */
.active-mode {
    background-color: alpha(#ffffff, 0.9);
}
```

### Integration Points:
- Integrates with existing Mac Tahoe CSS theme and color system
- Works with existing header and panel styling
- Uses mode state from archive functionality

## Architecture Context
- **Component Relationships**: Provides visual feedback for mode state in main browse panel
- **State Management**: Visual representation of archive mode state
- **Data Flow**: Mode state → CSS class updates → visual styling changes

## Dependencies
- **Prerequisite Tasks**: Task 6 (Ctrl+A toggle), Task 7 (ESC return), Task 5 (header text)
- **Blocking Tasks**: Completes visual polish for archive mode functionality
- **Related Systems**: Uses existing Mac Tahoe CSS theme and BrowsePanelWidget styling

## Acceptance Criteria
- [ ] Archive mode has subtle visual distinction from active mode
- [ ] Styling maintains Mac Tahoe aesthetic and color harmony
- [ ] Visual indicators are noticeable but not distracting
- [ ] CSS classes update correctly when switching modes
- [ ] No impact on existing UI functionality or performance
- [ ] Styling works well with existing header text updates

## Testing Strategy
- **Manual Testing**: 
  - Toggle between modes and verify visual distinction
  - Ensure styling doesn't interfere with readability or function
  - Test with different session counts and search states
- **Integration Points**: Verify compatibility with existing Mac Tahoe theme
- **Edge Cases**: Test rapid mode switching, different screen sizes

## Implementation Notes
- **Code Patterns**: Follow existing CSS class management patterns in GTK/Fabric UI
- **Performance Considerations**: Minimal - simple CSS class updates
- **Future Extensibility**: Foundation for additional mode-specific visual enhancements

## Commit Information
- **Commit Message**: "Add subtle visual indicators for archive mode distinction"
- **Estimated Time**: 15 minutes
- **Complexity Justification**: Low - Simple CSS styling and class management, purely visual enhancements