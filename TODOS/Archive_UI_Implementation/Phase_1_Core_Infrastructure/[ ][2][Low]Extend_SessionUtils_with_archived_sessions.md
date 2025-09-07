# Extend SessionUtils with Archived Sessions

## Context & Background
- **Feature Goal**: Add archive mode toggle with Ctrl+A to browse archived sessions while maintaining all existing functionality
- **Current Architecture**: SessionUtils provides `get_available_sessions()` for loading active session data with automatic directory detection (new vs legacy structure)
- **User Story**: UI needs to load archived session data when in archive mode, using the same patterns as active session loading

## Task Description
Extend SessionUtils class with methods to load archived session data, following the established patterns for session directory operations and data loading. This provides the data source for archive mode display.

## Files to Modify
- **Primary Files**: 
  - `fabric-ui/utils/session_utils.py` (add new methods) - Add archived session loading methods
- **Supporting Files**: None for this task

## Implementation Details
### Code Changes Required:
```python
# Add to SessionUtils class after existing methods:

@staticmethod
def get_archived_sessions_directory():
    """Get the archived sessions directory path"""
    home = Path.home()
    sessions_root = home / ".config" / "hypr-sessions"
    archived_dir = sessions_root / "archived"
    return archived_dir

@staticmethod
def get_archived_sessions():
    """Get list of archived session names with timestamps"""
    archived_dir = SessionUtils.get_archived_sessions_directory()
    if not archived_dir.exists():
        return []
    
    sessions = []
    for item in archived_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Verify it has session data
            session_file = item / "session.json"
            if session_file.exists():
                sessions.append(item.name)
    
    return sorted(sessions)
```

### Integration Points:
- Follows exact same patterns as existing `get_available_sessions()` method
- Uses established directory structure from archive system
- Maintains compatibility with existing SessionUtils API

## Architecture Context
- **Component Relationships**: Used by BrowsePanelWidget for loading archived session data
- **State Management**: Provides data source for archive mode functionality
- **Data Flow**: SessionUtils → BrowsePanelWidget → existing search/display components

## Dependencies
- **Prerequisite Tasks**: Task 1 (archive mode state variables)
- **Blocking Tasks**: Enables Task 4 (archive session loading logic)
- **Related Systems**: Uses existing archive directory structure from backend recovery system

## Acceptance Criteria
- [ ] `get_archived_sessions_directory()` method returns correct archived sessions path
- [ ] `get_archived_sessions()` method loads archived session names with timestamps
- [ ] Methods follow same patterns as existing `get_available_sessions()` method
- [ ] Returns empty list gracefully when archived directory doesn't exist
- [ ] Archived session validation includes session.json file check

## Testing Strategy
- **Manual Testing**: 
  - Test with existing archived sessions (should return timestamped names)
  - Test with no archived directory (should return empty list)
- **Integration Points**: Ensure no impact on existing `get_available_sessions()` functionality
- **Edge Cases**: Test with malformed archive directories, permission issues

## Implementation Notes
- **Code Patterns**: Follow exact same structure as `get_available_sessions()` method for consistency
- **Performance Considerations**: Minimal - same performance profile as existing session loading
- **Future Extensibility**: Can be extended for archive metadata loading if needed

## Commit Information
- **Commit Message**: "Add archived session loading methods to SessionUtils"
- **Estimated Time**: 20 minutes
- **Complexity Justification**: Low - Simple data loading methods following established patterns, minimal complexity