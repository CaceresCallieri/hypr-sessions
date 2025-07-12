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
- **Supported**: alacritty, kitty, foot, ghostty, wezterm, gnome-terminal, etc.
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