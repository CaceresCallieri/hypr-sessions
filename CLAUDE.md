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
│   └── neovide_handler.py    # Neovide-specific session management
├── session_restore.py        # Restore with grouping logic and debug output
├── session_list.py           # List saved sessions with debug output
├── session_delete.py         # Delete sessions with debug output
└── utils.py                  # Shared session directory setup
```

## Key Features Implemented

1. **Basic session save/restore** - Captures windows, groups, positions
2. **Group restoration** - Recreates Hyprland window groups during restore
3. **Terminal working directories** - Captures and restores terminal CWD
4. **Improved grouping logic** - Launches grouped windows sequentially, locks groups
5. **Modular architecture** - Clean separation of concerns
6. **Neovide support** - Detects Neovide windows and restores working directory
7. **Debug mode** - Comprehensive logging with `--debug` flag for troubleshooting

## Technical Details

### Session Data Format

- **Location**: `~/.config/hypr-sessions/`
- **Format**: JSON files with session metadata, windows array, groups object
- **Window data**: class, title, PID, position, size, launch_command, working_directory (terminals)
- **Neovide data**: neovide_session object with working_directory and session_file paths

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

## Planned Features

1. **Enhanced Neovim session management** - Use Neovim's API to capture actual session state (open files, cursor position, etc.)
2. **Browser tab restoration** - Firefox/Chrome tab state
3. **Better window positioning** - More precise layout restoration
4. **Qt/QML UI** - Graphical interface for session management

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

## Browser Integration (2025-07-21)

### Implemented
1. **Zen Browser Support**: Complete implementation with native messaging extension
   - **Extension Architecture**: Firefox/Zen-compatible WebExtension with native messaging support
   - **Tab Capture**: Captures all tabs in current browser window with URL, title, active/pinned status
   - **File-based Triggers**: Python script creates trigger files that extension monitors for automatic capture
   - **Command-line Restoration**: Browser launches with all saved tab URLs as command arguments
   - **Host Registration**: Automated native messaging host registration for browser communication

2. **Extension Components**:
   - **Manifest (manifest.json)**: WebExtension configuration with tabs, downloads, nativeMessaging permissions
   - **Background Script (background.js)**: Main extension logic with native messaging and tab capture
   - **Popup Interface (popup.html/js)**: User interface for testing connection and manual tab capture
   - **Native Host (native_host.py)**: Python script handling browser-extension communication protocol
   - **Host Registration (register_host.py)**: Automated setup for Firefox/Chrome native messaging directories

3. **Communication Flow**:
   - **Session Save**: Python creates trigger file → Extension detects → Captures tabs → Saves JSON to Downloads
   - **Session Restore**: Browser launches with tab URLs as command-line arguments (no extension needed)
   - **Native Messaging**: Extension ↔ Host communication using binary protocol for status/acknowledgments

4. **Integration Points**:
   - **Browser Detection**: `browser_handler.py` identifies Zen/Firefox windows during session save
   - **Launch Commands**: `launch_commands.py` generates browser commands with tab URLs for restoration
   - **Session Data**: Browser session info stored in main session JSON with tab array and metadata

### Current Status
- **Browser Window Detection**: Automatically identifies Zen Browser and Firefox ✅
- **Tab Capture**: Extension captures all tabs with full metadata ⚠️ (Code complete, needs testing)
- **File-based Communication**: Trigger files enable Python→Extension communication ⚠️ (Implemented, needs debugging)
- **Command-line Restoration**: Tabs restored via browser launch arguments ✅
- **Native Messaging Setup**: Automated host registration for browsers ✅

### Technical Implementation Details
- **Supported Browsers**: Zen Browser (zen-alpha, zen), Firefox (future support)
- **Communication Protocol**: File-based triggers in Downloads folder for Python→Extension
- **Tab Data Format**: JSON with session_name, timestamp, tabs array, browser_type
- **Launch Integration**: Browser sessions generate commands with quoted URL arguments
- **Host Manifest**: Proper native messaging host registration in browser-specific directories

### Setup Instructions
1. **Register Native Host**: Run `./setup_browser_support.py` to configure native messaging
2. **Load Extension**: Install extension from `browser_extension/` directory in browser
3. **Test Connection**: Use extension popup to verify communication with native host
4. **Use Sessions**: Browser tabs automatically captured during save, restored during restore

### File Structure
```
browser_extension/
├── manifest.json              # Extension configuration
├── background.js              # Main extension logic  
├── popup.html/js              # User interface
├── content.js                 # Content script (minimal)
├── native_host.py             # Python communication handler
├── hypr_sessions_host.json    # Host manifest for browser registration
└── register_host.py           # Automated setup script
```

### Next Debugging Steps (Extension Not Responding)

**Current Issue**: Extension not detecting trigger files, falling back to basic session data

**Debugging Steps**:
1. **Register Native Host**: `./setup_browser_support.py` 
2. **Load Extension**: Install `browser_extension/manifest.json` in Zen Browser via `about:debugging`
3. **Test Extension Communication**:
   - Check extension popup shows green "Connected" status
   - Try "Manual Tab Capture" - should create JSON file in Downloads
   - Check browser console for extension errors (`Ctrl+Shift+I` → Console)
4. **Debug Trigger File Detection**:
   - Verify trigger files created in `~/Downloads/.hypr-capture-*.trigger`
   - Check extension background script logs for file detection
   - Ensure Downloads API permissions working properly
5. **Test Full Cycle**: `./hypr-sessions.py save test --debug` should show tab capture success

**Known Working**: Browser detection, trigger file creation, session fallback, command-line restoration

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
