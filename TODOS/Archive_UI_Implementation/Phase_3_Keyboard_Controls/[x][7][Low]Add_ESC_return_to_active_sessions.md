# Add ESC Return to Active Sessions

## Context & Background
- **Feature Goal**: Add intuitive ESC key behavior to return from archive mode to active sessions, providing natural navigation flow
- **Current Architecture**: ESC key currently bubbles up to session manager for application quit functionality
- **User Story**: When in archive mode, users can press ESC to return to active sessions view; when in active mode, ESC continues to quit application as before

## Task Description
Add ESC key handling in browse panel to return from archive mode to active sessions before allowing ESC to bubble up for application quit. This provides intuitive navigation where ESC acts as "back" from archive mode while preserving existing quit behavior.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/widgets/browse_panel.py` (modify ESC handling in key event processing) - Add archive mode ESC handling
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# In BrowsePanelWidget key event handling method (likely in handle_key_press_event):
# Add ESC handling before allowing event bubbling:

def handle_key_press_event(self, widget, event) -> bool:
    """Handle key press events for browse panel"""
    
    # Check for ESC key in archive mode
    if event.keyval == Gdk.KEY_Escape and self.is_archive_mode:
        # Return to active sessions mode
        self.is_archive_mode = False
        
        # Clear search to provide clean active session view
        self.search_manager.clear_search()
        
        # Reload active sessions
        self.reload_sessions()
        
        # Debug logging
        if hasattr(self, 'debug_logger') and self.debug_logger:
            self.debug_logger.debug_navigation_operation(
                "escape_return_to_active", "archive_to_active", None, "esc_key"
            )
        
        return True  # Event handled, don't bubble up
    
    # Allow other key handling to proceed as normal
    # (existing key event routing continues unchanged)
```

### Integration Points:
- Works with existing ESC key event bubbling for application quit
- Uses existing session loading and search clearing mechanisms
- Maintains existing key event handling hierarchy

## Architecture Context
- **Component Relationships**: Intercepts ESC events in BrowsePanelWidget before session manager handles them
- **State Management**: Resets archive mode state and reloads active sessions
- **Data Flow**: ESC key → archive mode check → return to active → session reload

## Dependencies
- **Prerequisite Tasks**: Task 1 (archive mode state), Task 4 (session loading), Task 6 (archive mode toggle)
- **Blocking Tasks**: Completes core navigation functionality for archive mode
- **Related Systems**: Integrates with existing key event handling and application quit functionality

## Acceptance Criteria
- [ ] ESC key returns from archive mode to active sessions
- [ ] Search is cleared when returning to active mode for clean view
- [ ] Active session data loads correctly after ESC
- [ ] ESC continues to quit application when already in active mode
- [ ] Header text updates correctly (back to "Available Sessions")
- [ ] No impact on existing ESC key quit functionality

## Testing Strategy
- **Manual Testing**: 
  - Enter archive mode, press ESC, verify return to active sessions
  - In active mode, press ESC, verify application quits as before  
  - Test ESC behavior with search active in archive mode
- **Integration Points**: Ensure ESC quit functionality works in active mode
- **Edge Cases**: Test rapid ESC pressing, ESC during session operations

## Implementation Notes
- **Code Patterns**: Follow existing key event handling patterns with early return for handled events
- **Performance Considerations**: Minimal - simple state check and existing reload mechanism
- **Future Extensibility**: Establishes pattern for mode-specific key handling

## Commit Information
- **Commit Message**: "Add ESC key return to active sessions from archive mode"
- **Estimated Time**: 20 minutes
- **Complexity Justification**: Low - Simple key handling with state check, uses existing mechanisms for all functionality