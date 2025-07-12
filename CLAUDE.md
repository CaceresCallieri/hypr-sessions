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
1. **Neovide Integration**: Added dedicated `neovide_handler.py` for GUI Neovim support
   - Detects Neovide windows by class name "neovide"
   - Captures working directory from process `/proc/{pid}/cwd`
   - Creates basic session files for working directory restoration
   - Uses `neovide -- -S session.vim` for restoration

2. **Debug Infrastructure**: Comprehensive `--debug` flag implementation
   - Added debug parameter to all session classes
   - Detailed logging throughout save/restore/list/delete operations
   - Process tracking, file operations, and command execution visibility
   - Essential for troubleshooting and future development

3. **Code Organization**: Renamed `neovim_handler.py` → `neovide_handler.py`
   - Reserved "neovim" namespace for future terminal-based Neovim support
   - Updated all imports and class references
   - Maintained clean separation between GUI and terminal Neovim approaches

### Current Status
- Neovide opens in correct working directory ✅
- Basic session file creation works ✅ 
- **Missing**: Actual Neovim session state (open files, cursor position, buffers) ❌

### Next Steps (Priority Order)
1. **Implement Neovim Session API**: Use Neovim's remote API to capture/restore actual session state
2. **Enhanced session capture**: Save open files, cursor positions, buffer states
3. **Session validation**: Verify session files contain meaningful data before restoration
4. **Error handling**: Graceful fallbacks when Neovim API is unavailable

## Important Development Guidelines

**⚠️ CRITICAL**: After every change to this codebase, update this CLAUDE.md file to reflect:
- **New features implemented** with technical details
- **Changes made** to existing functionality  
- **Knowledge gained** about the system behavior
- **Issues discovered** and their solutions
- **Future objectives** and implementation approaches
- **Debugging insights** and troubleshooting notes

This file serves as the primary knowledge base for understanding the project's evolution, current capabilities, and development roadmap. Keep it comprehensive and up-to-date to ensure effective collaboration and debugging.