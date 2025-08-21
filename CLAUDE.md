# Hyprland Session Manager - Claude Context

## Project Overview

A Python-based session manager for Hyprland that saves and restores workspace sessions manually. Captures window states, groups, and application-specific data like terminal working directories, Neovim sessions, and browser tabs.

### Architecture

-   **CLI Interface**: `hypr-sessions.py` - Main entry point with commands: `save`, `restore`, `list`, `delete`
-   **Modular Structure**: Specialized handlers for different application types (terminals, Neovide, browsers)
-   **Fabric UI**: Professional graphical interface using Fabric framework for desktop widgets
-   **JSON API**: Clean API for UI integration with structured responses and error handling

### File Structure

```
├── hypr-sessions.py              # Main CLI with --debug and --json flags
├── session_save/                 # Modular save functionality
│   ├── session_saver.py          # Main orchestration with debug logging
│   ├── hyprctl_client.py         # Hyprctl data retrieval
│   ├── launch_commands.py        # Launch command generation
│   ├── terminal_handler.py       # Terminal working directory capture
│   ├── neovide_handler.py        # Neovide session management via remote API
│   └── browser_handler.py        # Browser tab capture via keyboard extension
├── session_restore.py            # Restore with grouping logic and timing
├── session_list.py, session_delete.py  # Session management operations
├── utils.py, validation.py       # Shared utilities and input validation
├── operation_result.py           # Structured error handling system
├── session_types.py              # Type definitions and data structures
├── fabric-ui/                    # Graphical user interface
│   ├── session_manager.py        # Main UI application (166 lines)
│   ├── constants.py              # Shared UI constants with type hints
│   ├── widgets/                  # Modular UI components
│   │   ├── browse_panel.py       # Session navigation with scrolling
│   │   ├── save_panel.py         # Session creation with state management
│   │   └── toggle_switch.py      # Panel switching control
│   ├── utils/                    # UI utilities
│   │   ├── backend_client.py     # CLI communication with JSON parsing
│   │   └── session_utils.py      # Session directory operations
│   ├── session_manager.css       # External stylesheet with Catppuccin theme
│   └── venv/                     # Fabric framework virtual environment
├── browser_extension/            # Browser integration
│   ├── manifest.json             # Extension configuration
│   └── background.js             # Tab capture logic (140 lines)
└── experiments/                  # Research and investigation scripts
```

## Core Features

### Session Management

-   **Folder-Based Storage**: `~/.config/hypr-sessions/session_name/` - each session in self-contained directory
-   **Window Data**: Class, title, PID, position, size, launch commands, working directories
-   **Group Restoration**: Recreates Hyprland window groups with sequential launching and proper timing
-   **Input Validation**: Comprehensive validation with filesystem-safe names, existence checking, custom exceptions
-   **Structured Results**: OperationResult system with success/warning/error categorization and partial failure support

### Application Support

#### Terminal Support

-   **Supported**: Ghostty terminal with comprehensive working directory capture
-   **Running Programs**: Detects active programs (yazi, npm run dev, vim, etc.) via process tree analysis
-   **Launch Commands**: `ghostty --working-directory=/path -e program; exec $SHELL` for persistence
-   **Shell Wrapper**: Programs wrapped to return to shell when exiting, with signal handling

#### Neovide Support

-   **Detection**: Window class "neovide" for GUI-based Neovim
-   **Live Session Capture**: Uses Neovim remote API via socket detection (`nvim --server --remote-send :mksession`)
-   **Session Files**: Creates comprehensive session files in session directory
-   **Restoration**: `neovide -- -S session.vim` with full buffer/cursor/layout restoration
-   **Fallback**: Basic working directory if remote API unavailable

#### Browser Support

-   **Method**: Keyboard shortcut extension approach (Alt+U trigger)
-   **Communication**: `hyprctl dispatch sendshortcut ALT,u,address:{window_address}` - no window focus needed
-   **File Transfer**: Extension saves `hypr-session-tabs-{timestamp}.json` to Downloads folder
-   **Tab Data**: Full navigation history, pinned status, active tab detection, URL filtering
-   **Status**: ✅ Working with Zen browser, 15+ tabs in ~2 seconds

### Technical Implementation

-   **JSON API**: `--json` flag produces clean, parseable output for UI integration
-   **Error Handling**: Custom exception classes, structured validation, graceful degradation
-   **Debug Mode**: `--debug` flag with comprehensive logging across all components
-   **Workspace-Scoped Data**: HyprctlClient filters to current workspace immediately, never exposing other workspace data
-   **Timing System**: Configurable delays for group restoration (`DELAY_BETWEEN_INSTRUCTIONS = 0.4s`)
-   **Thread Safety**: Proper async patterns with UI thread protection in Fabric UI

## Fabric UI Implementation

### Architecture Excellence

-   **Wayland Layer Widget**: Native overlay using WaylandWindow with layer shell support
-   **Focus Management**: GTK Layer Shell exclusive keyboard mode prevents focus loss under Hyprland compositor
-   **State-Based UI**: Save panel with input/saving/success/error states and smooth transitions
-   **Asynchronous Operations**: Non-blocking save operations with proper thread safety and timeout handling
-   **Keyboard Navigation**: Comprehensive control (Tab, arrows, Enter, Esc) with mode-aware routing
-   **Modular Design**: Clean separation of concerns with specialized widget components

### UI Components

```python
# Main widget hierarchy
SessionManagerWidget (WaylandWindow)
├── ToggleSwitchWidget          # Browse/Save mode switching with visual feedback
├── BrowsePanelWidget           # Session navigation with intelligent scrolling
└── SavePanelWidget             # Session creation with Enter key support
```

### Advanced Features

#### Scalable Session Navigation

-   **Scrollable Window**: Fixed 5-session display with intelligent positioning
-   **Wraparound Navigation**: Seamless navigation through unlimited session collections
-   **Visual Indicators**: Nerd Font chevrons (↑↓) for scroll state with layout stability
-   **Performance**: On-demand rendering - only creates widgets for visible sessions
-   **Session Count**: Dynamic header showing "Available Sessions (N)" with real-time updates

#### Professional Save Experience

-   **Enter Key Support**: Type session name → press Enter → save operation
-   **State Management**: Clean UI transitions with loading indicators and status feedback
-   **Error Recovery**: Retry functionality with session name preservation
-   **Validation**: Real-time input validation with user-friendly error messages
-   **Backend Integration**: Async communication with 30s timeout and proper error handling

#### Complete Restore Functionality

-   **Confirmation Workflow**: Enter key → confirmation modal → Enter to restore → async operation
-   **State Machine**: Four restore states (confirm/restoring/success/error) integrated with existing architecture
-   **Visual Feedback**: Green-themed confirmation UI with professional progress indicators
-   **Error Recovery**: Retry mechanisms with timeout protection and graceful fallback
-   **Code Quality**: DRY principles with shared session action logic and consistent patterns
-   **Backend Integration**: Complete end-to-end functionality with real CLI backend integration

#### Modular Operation Architecture

-   **Abstract Base Class**: `BaseOperation` with shared UI logic, threading, and error handling
-   **Concrete Implementations**: `DeleteOperation` and `RestoreOperation` require only ~25 lines each
-   **Code Reduction**: Eliminated 400+ lines of duplication from `browse_panel.py`
-   **Extensible Design**: New operations inherit full UI workflow (confirmation/progress/success/error states)
-   **Thread Safety**: Async backend operations with `GLib.idle_add()` for UI thread safety
-   **Configuration-Driven**: Operation behavior defined via config dictionaries with validation
-   **State Constants**: Type-safe state management eliminates magic strings and typos
-   **Error Handling**: Specific exception types (FileNotFoundError, PermissionError, ConnectionError, TimeoutError)
-   **Operation Timeouts**: Delete 10s (fast), Restore 60s (application launching) for optimal UX
-   **Config Validation**: Early validation prevents runtime errors from invalid configurations
-   **Enhanced Logging**: Context-aware error messages with operation type and detailed debugging

#### Keyboard Navigation System

```
Panel Navigation:
- Tab: Toggle between Browse/Save panels
- ← →: Directional panel switching
- Esc or Q: Exit application

Session Navigation (Browse Mode):
- ↑ ↓: Navigate sessions with wraparound
- Scroll Wheel: Navigate sessions (scroll up = next, scroll down = previous)
- Enter: Restore confirmation for selected session
- d: Delete confirmation for selected session

Restore Confirmation:
- Enter: Confirm restoration (launches all session applications)
- Esc or Q: Cancel restoration and return to browsing

Delete Confirmation:
- Enter: Confirm deletion (permanent action)
- Esc or Q: Cancel deletion and return to browsing

Save Panel:
- Enter: Trigger save operation (input state only)
- Esc or Q: Cancel operations or return to input
```

### Constants Management

```python
# fabric-ui/constants.py - Professional constant organization
from typing import Final

# GTK Keycodes with type safety
KEYCODE_ESCAPE: Final[int] = 9
KEYCODE_TAB: Final[int] = 23
KEYCODE_ENTER: Final[int] = 36
KEYCODE_LEFT_ARROW: Final[int] = 113
KEYCODE_RIGHT_ARROW: Final[int] = 114
KEYCODE_UP_ARROW: Final[int] = 111
KEYCODE_DOWN_ARROW: Final[int] = 116

# Import pattern across files
from constants import KEYCODE_ENTER, KEYCODE_ESCAPE
```

## Recent Development (2025-08-17)

### Enter Key Enhancement Implementation

-   **State-Aware Trigger**: Enter key triggers save only in "input" state, preventing accidental saves
-   **DRY Principle**: Extracted `_trigger_save_operation()` method for unified save logic
-   **Consistent Validation**: Same validation, error handling, and state management for both triggers
-   **User Experience**: Natural keyboard workflow eliminates mouse dependency

### Constants Refactoring Achievement

-   **Centralized Management**: Created `fabric-ui/constants.py` with comprehensive type hints
-   **Type Safety**: `Final[int]` annotations prevent accidental constant modification
-   **Import Safety**: Enhanced path handling prevents duplicate path additions
-   **IDE Integration**: Better auto-completion, error detection, and code navigation
-   **Maintainability**: Single source of truth for all UI constants

### Complete Delete Functionality Implementation

-   **Full Delete Workflow**: 'd' key → confirmation → async backend operation → success/error states
-   **State-Based Architecture**: Five states ("browsing", "delete_confirm", "deleting", "delete_success", "delete_error")
-   **Async Backend Integration**: Threading with BackendClient.delete_session(), timeout protection, session list refresh
-   **Professional UX**: Progress indicators, auto-return timers, retry mechanisms, comprehensive error handling
-   **Consistent Styling**: Catppuccin theme integration matching SavePanelWidget patterns

### Scroll Wheel Navigation Implementation

-   **GTK Event Integration**: Proper scroll-event handling with SCROLL_MASK and SMOOTH_SCROLL_MASK event masks
-   **Natural Navigation**: Scroll up moves down in list (select_next), scroll down moves up in list (select_previous)
-   **Smooth Scrolling Support**: Handles both discrete wheel clicks and smooth trackpad scrolling via delta detection
-   **State-Aware Operation**: Only active in browse mode during "browsing" state, disabled during delete confirmation
-   **Clean Architecture**: Helper methods _get_scroll_direction() and _can_handle_scroll() for maintainability

### GTK Layer Shell Focus Management Implementation (2025-08-20)

-   **Problem Resolution**: Fixed keyboard focus loss in Hyprland compositor where layer UI becomes unresponsive to keyboard input
-   **Solution Approach**: Implemented exclusive keyboard mode using GTK Layer Shell protocol (Solution 1 from focus guide)
-   **Technical Implementation**: Added `GtkLayerShell.set_keyboard_mode(window, GtkLayerShell.KeyboardMode.EXCLUSIVE)`
-   **Reliability**: Prevents focus loss at compositor level - most reliable solution for application launcher use case
-   **Graceful Handling**: Error handling ensures application continues with default behavior if layer shell unavailable
-   **Debug Output**: Added logging to confirm successful focus management configuration

```python
def _configure_layer_shell_focus(self):
    """Configure layer shell properties for reliable keyboard focus management"""
    try:
        if not GtkLayerShell.is_layer_window(self):
            GtkLayerShell.init_for_window(self)
        
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        print("DEBUG: Configured layer shell with exclusive keyboard mode")
        
    except Exception as e:
        print(f"Warning: Failed to configure layer shell focus management: {e}")
```

## Browser Integration Evolution

### Current: Keyboard Shortcut Extension (2025-08-10)

**✅ Working Solution**: Browser extension with keyboard shortcut triggers

#### Technical Architecture

-   **Extension**: Registers Alt+U command, captures tabs with metadata
-   **Communication**: `hyprctl sendshortcut` sends Alt+U directly to browser window
-   **Data Flow**: Extension → Downloads/hypr-session-tabs-{timestamp}.json → Python processing
-   **Performance**: Captures 15+ tabs in ~2 seconds without workflow disruption

#### Implementation Details

```javascript
// Extension background.js - tab capture
chrome.commands.onCommand.addListener((command) => {
  if (command === "capture-tabs") {
    captureTabs();
  }
});

// Session data structure
{
  "browser_session": {
    "browser_type": "zen",
    "capture_method": "keyboard_shortcut",
    "tab_count": 15,
    "tabs": [{"url": "...", "title": "...", "active": false, "pinned": false}]
  }
}
```

### Previous Approaches (Deprecated)

1. **Native Messaging (2025-07-21)**: Complex extension system - abandoned due to reliability issues
2. **sessionstore.jsonlz4 (2025-08-08)**: Direct file access - abandoned due to real-time update problems

## Session Data Format & Storage

### Current Structure (Folder-Based, 2025-08-13)

```
~/.config/hypr-sessions/
├── session_name/
│   ├── session.json           # Main session metadata
│   ├── neovide-session-*.vim  # Neovide session files
│   └── (future: browser-*.json, app-specific data)
```

### Session JSON Schema

```json
{
  "windows": [
    {
      "class": "com.mitchellh.ghostty",
      "title": "Terminal",
      "working_directory": "/path/to/dir",
      "running_program": {
        "name": "yazi",
        "args": [],
        "full_command": "yazi",
        "shell_command": null
      },
      "launch_command": "ghostty --working-directory=/path -e sh -c 'yazi; exec $SHELL'",
      "browser_session": {
        "browser_type": "zen",
        "tabs": [...],
        "capture_method": "keyboard_shortcut"
      },
      "neovide_session": {
        "working_directory": "/path",
        "session_file": "session_name/neovide-session-12345.vim"
      }
    }
  ],
  "groups": [[window_id_1, window_id_2]],
  "workspace": 1
}
```

### Storage Benefits

-   **Self-Contained**: Each session directory contains all related files
-   **No Conflicts**: Elimination of file name collisions between sessions
-   **Easy Cleanup**: Delete entire session with single directory removal
-   **Extensible**: Ready for additional per-session data (configs, caches, etc.)

## Development Guidelines

### Code Quality Standards

-   **Type Safety**: Use `Final` annotations for constants, proper type hints throughout
-   **Error Handling**: Structured OperationResult system with graceful degradation
-   **DRY Principle**: Extract common logic, avoid code duplication
-   **Documentation**: Clear docstrings, inline comments for complex logic
-   **Testing**: Debug modes for troubleshooting, comprehensive error reporting

### UI Development Best Practices

-   **State Management**: Clear UI state machines with proper transitions
-   **Keyboard Accessibility**: Comprehensive keyboard navigation support
-   **Visual Feedback**: Immediate user feedback for all operations
-   **Performance**: Lazy loading, efficient rendering for large data sets
-   **Thread Safety**: Proper async patterns with UI thread protection

### Session Management Patterns

-   **Validation**: Early input validation with actionable error messages
-   **Atomicity**: Operations succeed completely or fail cleanly
-   **Recovery**: Error recovery with user context preservation
-   **Logging**: Comprehensive debug output for troubleshooting

## Dependencies & Setup

### System Requirements

```bash
# Arch Linux
sudo pacman -S gtk3 cairo gtk-layer-shell python-gobject

# Python Environment (fabric-ui/)
cd fabric-ui
python -m venv venv
source venv/bin/activate
pip install git+https://github.com/Fabric-Development/fabric.git
```

### Browser Extension Setup

1. Install Zen browser
2. Load hypr-sessions extension (browser_extension/)
3. Enable keyboard shortcuts for Alt+U trigger
4. Verify Downloads folder write permissions

### Testing Commands

```bash
# CLI Testing
./hypr-sessions.py save work-session --debug
./hypr-sessions.py restore work-session --json
hyprctl dispatch workspace 4 && ./hypr-sessions.py restore work-session

# UI Testing
cd fabric-ui && source venv/bin/activate && python session_manager.py

# Integration Testing
./hypr-sessions.py list --json  # Test JSON API
```

## Configuration Constants

### Timing Configuration

-   **Group Restoration**: `DELAY_BETWEEN_INSTRUCTIONS = 0.4` seconds between group operations
-   **Save Operations**: `OPERATION_TIMEOUT = 35` seconds (longer than backend timeout)
-   **UI Feedback**: `MIN_DISPLAY_TIME = 0.5` seconds minimum for saving state visibility
-   **Auto-Return**: `SUCCESS_AUTO_RETURN_DELAY = 2` seconds from success to input state

### UI Configuration

-   **Scrolling**: `VISIBLE_WINDOW_SIZE = 5` sessions in browse panel window
-   **Navigation**: Wraparound behavior for unlimited session collections
-   **Indicators**: Nerd Font chevrons `\uf077` (up) and `\uf078` (down) for scroll state

### Validation Rules

-   **Session Names**: Max 200 chars, no `<>:"/\|?*`, no leading/trailing whitespace
-   **Reserved Names**: Prevents `.`, `..`, system directories
-   **File Safety**: Filesystem-safe validation with cross-platform compatibility

## Input Validation System

### Custom Exception Architecture

```python
# validation.py - Structured validation with specific exceptions
class SessionValidationError(Exception): pass
class InvalidSessionNameError(SessionValidationError): pass
class SessionNotFoundError(SessionValidationError): pass
class SessionAlreadyExistsError(SessionValidationError): pass

# Usage patterns
try:
    SessionValidator.validate_session_name(name)
except InvalidSessionNameError as e:
    return OperationResult.error(str(e))
```

### Validation Points

-   **CLI Entry**: All session operations validate inputs before execution
-   **Component Entry**: Each session component includes validation for direct usage
-   **Operation-Specific**: Tailored validation for different operation types
-   **Early Failure**: Validates inputs before performing expensive operations

## Error Handling Architecture

### Structured Results System

```python
# operation_result.py - Comprehensive result tracking
@dataclass
class OperationResult:
    success: bool
    operation: str
    messages: List[Dict[str, Any]]
    summary: Dict[str, int]
    data: Optional[Dict[str, Any]] = None

# Usage patterns
result = OperationResult.success("Session saved")
result.add_warning("Browser tabs unavailable")
return result.with_data({"session_file": path})
```

### Benefits

-   **Partial Success**: Operations can succeed with warnings
-   **Rich Context**: Detailed operation feedback with structured messages
-   **UI Integration**: Clean display formatting for debug vs normal modes
-   **Debugging**: Comprehensive logging without breaking user experience

## Important Development Notes

### CRITICAL Documentation Update Rule

After every change to this codebase:

1. Update this CLAUDE.md with new features, changes, and knowledge gained
2. Include technical details for debugging and future development
3. Document issues discovered and their solutions
4. Update implementation approaches and current status

### Code Style Requirements

-   **NO EMOJIS**: Use clear text instead (rendering issues in target environment)
-   **Type Hints**: Comprehensive type annotations for better IDE support
-   **Constants**: Use `Final` for immutable values, centralized in constants.py
-   **Shell Safety**: Use `shlex.quote()` for path escaping in commands

### Session Directory Migration (2025-08-13)

**Completed**: Transition from flat file storage to folder-based organization

-   All session operations now use directory-based storage
-   Legacy support methods available but not used in production
-   Comprehensive testing verified across save/restore/list/delete operations

## Mac Tahoe UI Aesthetic

### Design System Implementation

**Status**: Complete transformation from Catppuccin to white-based Mac Tahoe aesthetic

#### Core Design Principles
- **Glassmorphism**: GTK3-compatible transparency using `alpha()` function with layered gradients
- **Rounded Design**: 16-24px container radius, 12-18px button radius for Mac-like softness
- **White Color Palette**: Primary white (#ffffff) with warm gray accents (#e0e0e0, #f5f5f5)
- **Warm Text**: Dark button text uses #262424 (warm gray) instead of harsh black

#### Critical Technical Knowledge

**GTK3 CSS Limitations Discovered**:
- No `!important` declarations supported
- No backdrop-filter or advanced web CSS properties
- Button styling requires targeting both element AND nested labels

**CSS Specificity Issue & Solution**:
```css
/* PROBLEM: Broad label selector overrides specific button colors */
label { color: #ffffff; }  /* This overrides button text colors */

/* SOLUTION: Nested selectors for proper specificity */
#save-session-button { color: #262424; }
#save-session-button label { color: #262424; }  /* Required for GTK buttons */
```

**GTK3-Compatible Glassmorphism Pattern**:
```css
background-color: alpha(#ffffff, 0.8);
background-image: linear-gradient(to bottom, alpha(#ffffff, 0.9), alpha(#e0e0e0, 0.8));
border: 2px solid alpha(#ffffff, 0.3);
```

#### Color System Reference
- **Primary**: #ffffff (buttons, accents, borders)
- **Secondary**: #e0e0e0 (gradients, hover states)  
- **Tertiary**: #f5f5f5 (subtle highlights)
- **Text Dark**: #262424 (warm gray for button text)
- **Text Light**: #ffffff (general UI text)
- **Error**: #ff6b7a (status messages)

#### Implementation Notes
- Font stack: "SF Pro Rounded", "JetBrains Mono", monospace
- Transitions: 0.3-0.4s ease-out for smooth interactions
- Spacing: Increased padding/margins by 25-50% for breathing room
- Opacity ranges: 0.05-0.9 depending on context and layering needs

This documentation provides comprehensive guidance while maintaining clarity and avoiding redundancy. It serves as both development reference and architectural overview for the Hyprland Session Manager project.

