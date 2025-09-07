# Add Archive Mode State Management

## Context & Background
- **Feature Goal**: Add archive mode toggle with Ctrl+A to browse archived sessions while maintaining all existing functionality (search, navigation, operations)
- **Current Architecture**: BrowsePanelWidget uses modular component architecture with SessionUtils for data loading, state-based operation system, and search/navigation components
- **User Story**: Users can press Ctrl+A to switch between "Available Sessions" and "Archived Sessions" views, maintaining search functionality and enabling archive recovery

## Task Description
Add core state management infrastructure to BrowsePanelWidget to support archive mode toggle. This includes adding the archive mode state variable and archived session data storage, providing the foundation for all subsequent archive functionality.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/widgets/browse_panel.py` (lines ~82-90) - Add state variables to __init__ method
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# In BrowsePanelWidget.__init__ method, around line 86-90:
# Add after existing state initialization:

# Archive mode state management
self.is_archive_mode = False  # Track current mode (False = active, True = archived)
self.archive_session_names = []  # Cache for archived session data
```

### Integration Points:
- Integrates with existing `self.all_session_names` pattern for data storage
- Works with existing search manager and window calculator systems
- Maintains compatibility with all existing state management

## Architecture Context
- **Component Relationships**: State variables will be used by KeyboardEventHandler for Ctrl+A toggle and SessionUtils for data loading
- **State Management**: Simple boolean flag controls which session list is displayed and operated on
- **Data Flow**: Archive mode → load different session data → all existing components work unchanged

## Dependencies
- **Prerequisite Tasks**: None (foundational task)
- **Blocking Tasks**: This enables all subsequent archive functionality
- **Related Systems**: Must work with existing BrowsePanelWidget state management patterns

## Acceptance Criteria
- [ ] `self.is_archive_mode` boolean flag added to BrowsePanelWidget
- [ ] `self.archive_session_names` list added for archived session storage
- [ ] No changes to existing functionality or behavior
- [ ] State variables follow existing naming conventions
- [ ] Code integrates cleanly with existing __init__ method

## Testing Strategy
- **Manual Testing**: Verify UI starts normally with no behavior changes
- **Integration Points**: Ensure all existing browse panel functionality works unchanged
- **Edge Cases**: Verify state variables initialize properly on widget creation

## Implementation Notes
- **Code Patterns**: Follow existing state variable initialization pattern in BrowsePanelWidget.__init__
- **Performance Considerations**: Minimal overhead - just two simple state variables
- **Future Extensibility**: Provides foundation for mode switching, data loading, and operation routing

## Commit Information
- **Commit Message**: "Add archive mode state management infrastructure to browse panel"
- **Estimated Time**: 15 minutes
- **Complexity Justification**: Medium - Core infrastructure change that affects multiple future components, requires careful integration with existing state management