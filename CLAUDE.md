# Hyprland Session Manager - Claude Context

## Project Overview

A Python-based session manager for Hyprland that saves and restores workspace sessions manually. Captures window states, groups, and application-specific data like terminal working directories.

## Architecture

- **CLI Interface**: `hypr-sessions.py` - Main entry point
- **Commands**: `save`, `restore`, `list`, `delete`
- **Modular Structure**: Each command in separate files
- **Utils**: Shared configuration and session directory setup

## File Structure

```
├── hypr-sessions.py          # Main CLI interface with --debug flag
├── session_save/             # Modular save functionality
│   ├── session_saver.py      # Main orchestration with debug logging
│   ├── hyprctl_client.py     # Hyprctl data retrieval
│   ├── launch_commands.py    # Launch command generation
│   ├── terminal_handler.py   # Terminal working directory capture
│   ├── neovide_handler.py    # Neovide-specific session management
│   └── browser_handler.py    # Browser window detection and tab capture
├── session_restore.py        # Restore with grouping logic and debug output
├── session_list.py           # List saved sessions with debug output
├── session_delete.py         # Delete sessions with debug output
├── utils.py                  # Shared session directory setup
├── browser_extension/        # DEPRECATED: Extension-based browser integration
├── setup_browser_support.py  # DEPRECATED: Extension setup script
└── experiments/              # Research and investigation scripts
    ├── browser-extension/    # Extension communication experiments
    ├── session-file-access/  # sessionstore.jsonlz4 parsing experiments
    ├── window-mapping/       # Window-to-session correlation research
    ├── process-analysis/     # Process tree investigation experiments
    └── utilities/            # Research helper tools (session viewers, etc.)
```

## Key Features Implemented

1. **Basic session save/restore** - Captures windows, groups, positions
2. **Group restoration** - Recreates Hyprland window groups during restore
3. **Terminal working directories** - Captures and restores terminal CWD with running programs
4. **Enhanced Neovide session management** - Live Neovim session capture via remote API
5. **Browser tab capture** - Zen browser extension with keyboard shortcut integration
6. **Improved grouping logic** - Launches grouped windows sequentially, locks groups
7. **Modular architecture** - Clean separation of concerns with specialized handlers
8. **Debug mode** - Comprehensive logging with `--debug` flag for troubleshooting

## Technical Details

### Session Data Format (2025-08-13)

- **Location**: `~/.config/hypr-sessions/`
- **Structure**: **Folder-based storage** - each session is a self-contained directory
- **Format**: 
  ```
  ~/.config/hypr-sessions/
  ├── session_name/
  │   ├── session.json           # Main session metadata and windows
  │   ├── neovide-session-*.vim  # Neovide session files
  │   └── (future: browser-*.json, other app data)
  ```
- **Benefits**: Self-contained sessions, easier cleanup, no file conflicts, extensible
- **Window data**: class, title, PID, position, size, launch_command, working_directory (terminals)
- **Neovide data**: neovide_session object with working_directory and session_file paths within session directory

### Terminal Support

- **Supported**: Only ghostty
- **Working directory capture**: Reads from `/proc/{pid}/cwd` and child processes
- **Launch flags**: Terminal-specific directory arguments

### Neovide Support

- **Detection**: Window class "neovide" for GUI-based Neovim
- **Working directory**: Captured from Neovide process `/proc/{pid}/cwd`
- **Session files**: Creates basic session files in `~/.config/hypr-sessions/`
- **Restoration**: Uses `neovide -- -S session.vim` for session loading
- **Current limitation**: Only restores working directory, not actual Neovim session state

### Group Restoration Process

1. Launch ungrouped windows normally
2. For each group: launch leader → togglegroup → launch members → lockactivegroup
3. Uses natural focus (no focuswindow calls) to avoid workspace switching

## Constants and Configuration

- **Timing**: `SessionRestore.DELAY_BETWEEN_INSTRUCTIONS = 0.4` seconds
- **Sessions directory**: `~/.config/hypr-sessions/`
- **Gitignore**: `__pycache__/` excluded

## Future Development Roadmap

### **Immediate Priorities (Current Work)**
1. **Firefox browser support** - Extend extension approach to Firefox
2. **Better window positioning** - More precise layout restoration for all applications

### **Planned Enhancements**
1. **Multi-browser sessions** - Handle mixed browser environments (Zen + Firefox)
2. **Better window positioning** - More precise layout restoration for all applications
3. **Qt/QML UI** - Graphical interface for session management
4. **Session validation** - Verify restored sessions match saved state
5. **Workspace-specific sessions** - Different session profiles per workspace type

## Development Notes

- **Python style**: Class constants in UPPER_CASE
- **Error handling**: Graceful fallbacks for permission/file errors
- **Shell safety**: Uses `shlex.quote()` for path escaping
- **Process discovery**: Finds shell children of terminal processes for accurate CWD

## Testing Notes

- Test grouping with multiple terminal windows
- Verify working directory capture across different terminals
- Check workspace isolation (no unintended workspace switching)

## Debug Mode

The `--debug` flag provides comprehensive troubleshooting output:

```bash
# Debug session save (shows window detection, Neovide capture, file creation)
./hypr-sessions.py save work-session --debug

# Debug session restore (shows file loading, launch process, group creation)
./hypr-sessions.py restore work-session --debug

# Debug session listing (shows directory scanning, file parsing)
./hypr-sessions.py list --debug

# Debug session deletion (shows file path validation, deletion process)
./hypr-sessions.py delete work-session --debug
```

Debug output includes:

- Window detection and classification
- Process ID and working directory capture
- Session file creation and validation
- Launch command generation and execution
- Group organization and restoration logic

## Common Commands

```bash
# Save current workspace
./hypr-sessions.py save work-session

# Restore session
./hypr-sessions.py restore work-session

# List all sessions
./hypr-sessions.py list

# Delete session
./hypr-sessions.py delete work-session
```

## Browser Integration Evolution (2025-08-08)

### Phase 1: Native Messaging Extension Approach (2025-07-21) - DEPRECATED

**Original Implementation**: Complex native messaging extension system
- **Extension Architecture**: Firefox/Zen WebExtension with native messaging
- **Communication**: File-based triggers + native messaging protocol
- **Issues**: Extension not responding to triggers, complex debugging, maintenance overhead
- **Status**: ⚠️ Deprecated in favor of sessionstore.jsonlz4 direct access

### Phase 2: sessionstore.jsonlz4 Direct Access (2025-08-08) - ABANDONED

**Attempted Implementation**: Direct access to Zen browser's session storage files
- **Method**: Parse Mozilla's LZ4-compressed session files directly
- **Issues**: Session files don't update in real-time, window-to-tab mapping complexity
- **Status**: ⚠️ Abandoned due to unreliable session data correlation

### Phase 3: Keyboard Shortcut Extension Approach (2025-08-10) - ✅ CURRENT

**Final Solution**: Browser extension with keyboard shortcut triggers via hyprctl sendshortcut
- **Method**: Extension responds to Alt+U, saves tab data to Downloads folder
- **Communication**: hyprctl sendshortcut sends Alt+U directly to specific browser window
- **File Transfer**: Extension creates timestamped JSON files for Python script to process
- **Advantages**: Simple, reliable, non-disruptive to user workflow

#### **✅ Working Implementation**

**Browser Extension** (`browser_extension/`):
- ✅ **Keyboard Command**: Alt+U registered in manifest.json
- ✅ **Tab Capture**: Captures all tabs from current window with metadata
- ✅ **File Output**: Saves `hypr-session-tabs-{timestamp}.json` to Downloads
- ✅ **Clean Architecture**: Focused 140-line background.js, no native messaging complexity

**Python Integration** (`session_save/browser_handler.py`):
- ✅ **Direct Shortcut**: Uses `hyprctl dispatch sendshortcut ALT,u,address:{window_address}`
- ✅ **No Window Focus**: Sends shortcut directly to specific window without focusing
- ✅ **File Monitoring**: Detects new tab files by comparing before/after file lists
- ✅ **Tab Processing**: Loads JSON data and integrates into session structure
- ✅ **Cleanup**: Automatically removes temporary tab files after processing

#### **Technical Architecture**

**Workflow**:
1. **Window Detection**: Python script identifies Zen browser windows via hyprctl
2. **Shortcut Delivery**: `hyprctl dispatch sendshortcut ALT,u,address:{window_address}`
3. **Extension Response**: Browser extension captures current window tabs
4. **File Creation**: Extension saves `hypr-session-tabs-{timestamp}.json` to Downloads
5. **Python Processing**: Script detects new file, loads tab data, cleans up file
6. **Session Integration**: Tab data merged into window's browser_session object

**Key Components**:
- ✅ `capture_tabs_via_keyboard_shortcut()`: Main orchestration method
- ✅ `wait_for_keyboard_shortcut_file()`: Monitors Downloads for new files  
- ✅ `load_keyboard_shortcut_tab_data()`: Parses extension JSON format
- ✅ File cleanup and error handling with clear diagnostics

#### **Technical Implementation Details**

**Session Data Structure**:
```json
{
  "windows": [
    {
      "tabs": [
        {
          "entries": [{"url": "https://...", "title": "Page Title"}],
          "index": 1,
          "pinned": false
        }
      ],
      "selected": 2
    }
  ]
}
```

**Tab Extraction Logic**:
- ✅ Navigation history handling (entries array with index)
- ✅ URL filtering (skip about: pages, extensions)
- ✅ Active tab detection via selected index
- ✅ Pinned status capture

**File Structure**:
```
session_save/
├── browser_handler.py         # Keyboard shortcut integration
├── session_saver.py           # Main session orchestration
└── launch_commands.py         # Browser restoration commands
browser_extension/             # Zen browser extension
├── manifest.json              # Extension configuration
└── background.js              # Tab capture logic
```

#### **Session Data Example**

```json
{
  "browser_session": {
    "browser_type": "zen",
    "capture_method": "keyboard_shortcut", 
    "keyboard_shortcut": "Alt+U",
    "tab_count": 15,
    "window_id": 21884,
    "tabs": [
      {
        "id": 717,
        "url": "https://example.com",
        "title": "Example Page",
        "active": false,
        "pinned": false,
        "index": 1,
        "windowId": 21884
      }
    ]
  }
}
```

#### **Current Status (2025-08-10)**

✅ **COMPLETED - Browser Session Saving**:
- ✅ Zen browser window detection
- ✅ Keyboard shortcut delivery via hyprctl sendshortcut
- ✅ Extension tab capture and file generation
- ✅ Python script file monitoring and processing  
- ✅ Session JSON integration with full tab metadata
- ✅ Automatic cleanup of temporary files
- ✅ Comprehensive debug logging and error handling

🚧 **IN PROGRESS - Browser Session Restoration**:
- ✅ Launch command generation with tab URLs
- ⏳ Tab restoration testing and optimization
- ⏳ Workspace-specific browser window positioning

**Performance**: Successfully captures 15+ tabs in ~2 seconds with no user workflow disruption.

#### **Dependencies**
- Zen browser with installed hypr-sessions extension
- Extension must be loaded and keyboard shortcuts enabled
- Downloads folder write permissions for tab data files

## Recent Session Directory Reorganization (2025-08-13)

### Implemented

1. **Folder-Based Session Storage**: Complete restructuring from flat files to directory-based organization
    - **Self-Contained Sessions**: Each session stored in its own directory with all related files
    - **Collision Prevention**: No more conflicts between session file names across different sessions
    - **Easier Management**: Single directory deletion removes entire session including all artifacts
    - **Future Extensibility**: Ready for additional per-session files (browser data, custom configs)

2. **Updated Configuration System**:
    - **New Path Methods**: `get_session_directory()`, `get_session_file_path()` with automatic directory creation
    - **Legacy Support Methods**: Migration helpers for development transition (not used in production)
    - **Backward Compatibility**: All existing code updated to use new folder structure seamlessly

3. **Enhanced Session Operations**:
    - **Save**: Creates session directory and stores session.json plus neovide session files within directory
    - **List**: Shows folder-based sessions with file count and comprehensive metadata
    - **Delete**: Removes entire session directory with user feedback on files deleted
    - **Restore**: Works seamlessly with new folder paths, including swallowing and grouping

4. **Cleanup and Migration**:
    - **Deprecated Files Removed**: zen-browser-backups directory and old flat session files cleaned up
    - **Application Command Fixes**: Fixed org.kde.dolphin -> dolphin mapping for proper restoration
    - **Testing Verified**: Full end-to-end testing of save/list/delete/restore with complex sessions

### Technical Implementation Details

- **Directory Structure**: `~/.config/hypr-sessions/session_name/session.json` + auxiliary files
- **Automatic Creation**: Session directories created on-demand during save operations
- **Neovide Integration**: Session files now stored within session directory using session name context
- **Error Handling**: Comprehensive error handling for directory operations and file management

### Current Status (2025-08-13)

✅ **COMPLETED - Folder-Based Session Storage**:
- ✅ Configuration system updated with new path methods
- ✅ Session saving to individual directories with all files contained
- ✅ Session listing showing directory-based sessions with metadata
- ✅ Session deletion removing entire directories safely
- ✅ Session restoration working with new folder paths
- ✅ Swallowing and grouping functionality fully compatible
- ✅ Legacy file cleanup and application command fixes

**Benefits Realized**:
- **Cleaner Organization**: Session directories clearly show what belongs to each session
- **Safer Operations**: Deleting a session removes only that session's files
- **Development Friendly**: Easier to debug and inspect session contents
- **Future Ready**: Architecture supports additional per-session data files

## Recent Input Validation Implementation (2025-08-13)

### Implemented

1. **Comprehensive Input Validation System**: Complete validation framework for session operations
    - **Custom Exception Classes**: Specific exception types for different validation failures
    - **Session Name Validation**: Filesystem-safe names with comprehensive character and pattern checks
    - **Existence Validation**: Proper session existence checking without creating directories
    - **Directory Permission Validation**: Ensures write access to sessions directory

2. **Validation Module** (`validation.py`):
    - **SessionValidator Class**: Centralized validation logic with comprehensive checks
    - **Custom Exceptions**: `SessionValidationError`, `InvalidSessionNameError`, `SessionNotFoundError`, `SessionAlreadyExistsError`
    - **Input Sanitization**: Prevents invalid characters, control characters, reserved names
    - **Boundary Validation**: Length limits, whitespace trimming, pattern enforcement

3. **Enhanced Error Handling**:
    - **CLI Integration**: All session operations validate inputs before execution
    - **Component-Level Validation**: Each session component includes validation for direct usage
    - **User-Friendly Messages**: Clear, actionable error messages with specific guidance
    - **Early Failure**: Validates inputs before performing expensive operations

4. **Validation Rules Implemented**:
    - **Character Restrictions**: No filesystem-unsafe characters (`<>:"/\\|?*`)
    - **Length Limits**: Maximum 200 characters for cross-platform compatibility
    - **Pattern Validation**: No leading/trailing whitespace, no consecutive spaces
    - **Reserved Names**: Prevents use of system directories (`.`, `..`)
    - **Control Characters**: Blocks non-printable characters that could cause issues

### Technical Implementation Details

- **Validation Points**: CLI entry, component entry, and operation-specific validation
- **Directory Creation Prevention**: Checks existence before auto-creating directories
- **Exception Hierarchy**: Structured exception types for specific error handling
- **Convenience Functions**: Simple validation functions for common use cases

### Current Status (2025-08-13)

✅ **COMPLETED - Input Validation System**:
- ✅ Custom exception classes for validation scenarios
- ✅ Comprehensive session name validation with filesystem safety
- ✅ Session existence validation without side effects
- ✅ Integration across all session operations (save/restore/list/delete)
- ✅ Edge case testing with invalid inputs, control characters, length limits
- ✅ User-friendly error messages with actionable guidance

**Validation Examples**:
- **Invalid Characters**: `Error: Session name contains invalid characters: '/'. Invalid characters: <>:"/\|?*`
- **Reserved Names**: `Error: '..' is a reserved name and cannot be used`
- **Length Limits**: `Error: Session name too long (201 chars). Maximum length is 200`
- **Existence Checks**: `Error: Session 'nonexistent' not found`
- **Duplicate Detection**: `Error: Session 'existing' already exists. Delete it first or use a different name.`

**Benefits Realized**:
- **Prevented Errors**: Invalid inputs caught before operations begin
- **Better UX**: Clear error messages guide users to valid inputs
- **System Safety**: Filesystem-safe names prevent directory traversal and corruption
- **Development Quality**: Consistent validation across all components

## Recent Structured Error Results Implementation (2025-08-13)

### Implemented

1. **Comprehensive OperationResult System**: Complete structured error tracking implementation
    - **OperationResult Class**: Centralized result tracking with success/warning/error categorization
    - **Rich Message Context**: Detailed operation feedback with contextual information
    - **Partial Failure Support**: Operations can succeed with warnings, enabling graceful degradation
    - **User-Friendly Display**: Smart formatting for debug vs normal operation modes

2. **Enhanced Session Operations with Structured Results**:
    - **SessionSaver**: Returns OperationResult with detailed window capture tracking, validation results, and file operation status
    - **SessionRestore**: Tracks validation, file loading, application launching with granular success/failure reporting
    - **SessionList**: Provides structured session scanning with invalid session warnings and detailed metadata
    - **SessionDelete**: File-by-file deletion tracking with comprehensive validation and cleanup reporting

3. **CLI Integration with Smart Result Display**:
    - **Debug Mode**: Full detailed results showing all success/warning/error messages for troubleshooting
    - **Normal Mode**: Concise summaries with error details when operations fail
    - **Consistent Formatting**: Unified ✓/⚠/✗ symbols for immediate status recognition
    - **Graceful Error Handling**: Clear failure messages without technical stack traces

4. **Individual Window Processing with Error Recovery**:
    - **Granular Exception Handling**: Each window capture wrapped in try-catch for isolation
    - **Partial Success Tracking**: Failed windows don't abort entire session save operation
    - **Detailed Failure Context**: Specific error messages for terminal, neovide, and browser window failures
    - **Fallback Mechanisms**: Graceful degradation when specialized handlers fail

### Current Status

- **Structured Error Results**: Complete implementation across all session operations ✅
- **Partial Failure Handling**: Operations continue despite individual component failures ✅
- **Rich Debugging Information**: Comprehensive logging and result tracking ✅
- **User Experience**: Clean error reporting with actionable feedback ✅
- **Backward Compatibility**: Existing CLI behavior preserved with enhanced feedback ✅

### Technical Implementation Details

- **OperationResult Architecture**: Dataclass-based result system with typed message categorization
- **Message Aggregation**: Centralized collection of operation events with context preservation
- **CLI Response Adaptation**: Different output verbosity based on debug flag state
- **Exception Integration**: Seamless conversion of validation errors to structured results
- **Data Preservation**: Operation results include structured data for programmatic access

### Error Handling Improvements Completed

1. **Input Validation System**: Comprehensive session name and directory validation ✅
2. **Structured Error Results**: Rich operation feedback with partial failure support ✅
3. **Remaining Improvement Options**:
   - **Retry Mechanisms**: Automatic retry for transient failures
   - **Configuration Validation**: Startup-time environment and dependency checking
   - **Recovery Suggestions**: Contextual hints for resolving common issues
   - **Operation Rollback**: Undo capability for failed operations

### Debug Output Examples

```bash
# Detailed structured results in debug mode
./hypr-sessions.py save work-session --debug
✓ Save session 'work-session': 15 succeeded, 2 warnings
  ✓ Session name validated
  ✓ Sessions directory accessible
  ✓ Found 8 windows in current workspace
  ✓ Captured working directory for com.mitchellh.ghostty
  ⚠ Could not capture running program for com.mitchellh.ghostty
  ✓ Session saved to /home/user/.config/hypr-sessions/work-session/session.json

# Concise results in normal mode
./hypr-sessions.py save work-session
✓ Session saved successfully
  ⚠ 2 warnings occurred during save

# Error case handling
./hypr-sessions.py restore nonexistent-session
✗ Session restore failed
  Error: Session 'nonexistent-session' not found
```

### File Structure Updates

```
├── operation_result.py           # NEW: Structured result system
├── session_save/
│   └── session_saver.py          # Updated: Returns OperationResult with window tracking
├── session_restore.py            # Updated: Structured restore feedback
├── session_list.py               # Updated: Session validation and metadata tracking
├── session_delete.py             # Updated: File-by-file deletion tracking
└── hypr-sessions.py              # Updated: Smart result display based on debug mode
```

## Recent Session Work (2025-07-12)

### Implemented

1. **Enhanced Neovide Session Management**: Complete implementation using Neovim remote API
    - **Socket Detection**: Automatically finds Neovim server sockets for running Neovide instances
    - **Live Session Capture**: Uses `nvim --server --remote-send :mksession` to capture actual session state
    - **Comprehensive Session Files**: Captures open buffers, cursor positions, window layouts, working directories
    - **Intelligent Fallback**: Falls back to basic working directory session if remote API fails
    - **Debug Integration**: Full debug logging for troubleshooting session capture/restore

2. **Neovim Remote API Integration**:
    - Detects sockets in `/run/user/{uid}/nvim.{pid}.*` and other standard locations
    - Searches process tree for child Neovim processes if direct PID socket not found
    - Executes `:mksession!` command remotely to generate comprehensive session files
    - Validates session file creation with timeout handling

3. **Enhanced Debug Infrastructure**:
    - Added debug parameter to all session classes including LaunchCommandGenerator
    - Detailed logging for socket detection, session capture, and command execution
    - Process tracking and validation throughout the session management pipeline

4. **Robust Session Restoration**:
    - Prioritizes full Neovim session files over basic working directory restoration
    - Uses `neovide -- -S session.vim` for comprehensive session restoration
    - Maintains backward compatibility with existing basic session approach

### Current Status

- **Neovide Socket Detection**: Automatically finds Neovim server sockets ✅
- **Live Session Capture**: Captures actual Neovim session state via remote API ✅
- **Comprehensive Session Files**: Saves buffers, cursor positions, layouts ✅
- **Enhanced Restoration**: Restores full Neovim sessions with all state ✅
- **Fallback Support**: Graceful degradation when remote API unavailable ✅

### Technical Implementation Details

- **Socket Patterns**: Supports multiple socket location patterns for compatibility
- **Process Tree Search**: Finds Neovim processes in complex process hierarchies
- **Timeout Handling**: 10-second timeout for remote commands, 3-second wait for file creation
- **Session File Naming**: Uses `neovide-session-{pid}.vim` format to avoid conflicts
- **Error Recovery**: Comprehensive error handling with detailed debug output

### Next Steps (Future Enhancements)

1. **Session Validation**: Verify session files contain expected Neovim session markers
2. **Plugin State Capture**: Enhanced session capture for complex plugin configurations
3. **Multi-instance Support**: Handle multiple Neovide instances with different sessions
4. **Session Merging**: Combine multiple Neovim sessions into workspace-level sessions

## Important Development Guidelines

**⚠️ CRITICAL**: Documentation and development workflow requirements:

1. After every change to this codebase, update this CLAUDE.md file to reflect:
2. Going forward, always update CLAUDE.md with relevant implementation details during development
3. Include CLAUDE.md updates in commits when making changes

**⚠️ CRITICAL**: After every change to this codebase, update this CLAUDE.md file to reflect:

- **New features implemented** with technical details
- **Changes made** to existing functionality
- **Knowledge gained** about the system behavior
- **Issues discovered** and their solutions
- **Future objectives** and implementation approaches
- **Debugging insights** and troubleshooting notes

This file serves as the primary knowledge base for understanding the project's evolution, current capabilities, and development roadmap. Keep it comprehensive and up-to-date to ensure effective collaboration and debugging.

## Recent Terminal Program Detection Work (2025-07-13)

### Implemented

1. **Running Program Detection in Terminals**: Complete implementation for detecting and restoring active programs
    - **Process Tree Analysis**: Recursively analyzes terminal process trees to find non-shell programs
    - **Command Line Parsing**: Extracts program names, arguments, and shell commands from `/proc/{pid}/cmdline`
    - **Shell Command Detection**: Special handling for shell commands executed with `-c` flag (npm run dev, complex commands)
    - **Intelligent Filtering**: Skips shell processes unless they're executing specific commands

2. **Enhanced Session Data Format**:
    - **running_program Object**: Stores detected program information including name, args, full_command, and optional shell_command
    - **Backward Compatibility**: New data is optional, existing sessions continue to work
    - **Debug Integration**: Comprehensive logging for program detection and command building

3. **Advanced Launch Command Generation**:
    - **Ghostty-Specific Execution**: Uses `-e` flag for program execution with working directory
    - **Shell Command Handling**: Properly executes complex shell commands through `sh -c`
    - **Direct Program Execution**: Launches simple programs directly without shell intermediary
    - **Working Directory Integration**: Combines working directory and program execution seamlessly

4. **Fixed Process Detection Issues**:
    - **Process Stat Parsing**: Fixed parsing of `/proc/*/stat` for processes with spaces in names (like "npm run dev")
    - **Recursive Process Search**: Enhanced process tree traversal to find programs in complex hierarchies
    - **Conflict Resolution**: Prevents conflicts between terminal program detection and dedicated neovide session management

### Technical Implementation Details

- **Process Discovery**: Reads `/proc/{pid}/cmdline` for command line information and `/proc/*/stat` for parent-child relationships
- **Command Parsing**: Handles null-separated arguments with proper Unicode decoding
- **Shell Detection**: Identifies bash, zsh, fish, sh, dash and analyzes their child processes
- **Process Filtering**: Skips hypr-sessions save commands, neovide processes, and embedded nvim instances
- **Launch Command Building**: Constructs proper Ghostty commands with working directory and program execution

### Current Status

- **Program Detection**: Automatically detects running programs in Ghostty terminals ✅
- **Command Restoration**: Restores terminals with detected programs running ✅
- **Shell Command Support**: Handles complex shell commands (npm run dev) ✅
- **Process Tree Analysis**: Recursive search through complex process hierarchies ✅
- **Conflict Prevention**: Avoids conflicts with neovide session management ✅

### Examples of Supported Programs

- **File Managers**: yazi, ranger, nnn, lf
- **Development Tools**: npm run dev, yarn start, cargo run
- **Editors**: vim, nvim (standalone, not embedded)
- **System Tools**: htop, btop, top, ps
- **Custom Scripts**: Any executable program or shell command

### Terminal Persistence Enhancement (2025-07-14)

**✅ RESOLVED**: Implemented shell wrapper approach to keep terminals open after programs exit

- **Shell Wrapper Implementation**: Programs are wrapped with `; exec $SHELL` to return to shell when program exits
- **Signal Handling**: Added trap for shell commands to handle Ctrl+C gracefully without killing terminal
- **Multi-word Command Detection**: Enhanced detection for package manager commands (npm run dev, yarn start, etc.)
- **Proper Quoting**: Fixed command generation with proper shell escaping and quoting

**Technical Details:**
- **Direct Programs**: `ghostty --working-directory=/path -e sh -c "yazi; exec $SHELL"`
- **Shell Commands**: `ghostty --working-directory=/path -e sh -c "trap 'echo Program interrupted' INT; npm run dev; exec $SHELL"`
- **Package Manager Support**: npm, yarn, pnpm, bun commands are automatically treated as shell commands
- **Argument Filtering**: Removes empty arguments from process cmdline parsing

### Known Limitations

- **None currently identified** - Terminal persistence feature is complete and working
