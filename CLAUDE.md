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
├── hypr-sessions.py          # Main CLI interface
├── session_save/             # Modular save functionality
│   ├── session_saver.py      # Main orchestration
│   ├── hyprctl_client.py     # Hyprctl data retrieval  
│   ├── launch_commands.py    # Launch command generation
│   └── terminal_handler.py   # Terminal working directory capture
├── session_restore.py        # Restore with grouping logic
├── session_list.py           # List saved sessions
├── session_delete.py         # Delete sessions
└── utils.py                  # Shared session directory setup
```

## Key Features Implemented
1. **Basic session save/restore** - Captures windows, groups, positions
2. **Group restoration** - Recreates Hyprland window groups during restore
3. **Terminal working directories** - Captures and restores terminal CWD
4. **Improved grouping logic** - Launches grouped windows sequentially, locks groups
5. **Modular architecture** - Clean separation of concerns

## Technical Details

### Session Data Format
- **Location**: `~/.config/hypr-sessions/`
- **Format**: JSON files with session metadata, windows array, groups object
- **Window data**: class, title, PID, position, size, launch_command, working_directory (terminals)

### Terminal Support
- **Supported**: alacritty, kitty, foot, ghostty, wezterm, gnome-terminal, etc.
- **Working directory capture**: Reads from `/proc/{pid}/cwd` and child processes
- **Launch flags**: Terminal-specific directory arguments

### Group Restoration Process
1. Launch ungrouped windows normally
2. For each group: launch leader → togglegroup → launch members → lockactivegroup
3. Uses natural focus (no focuswindow calls) to avoid workspace switching

## Constants and Configuration
- **Timing**: `SessionRestore.DELAY_BETWEEN_INSTRUCTIONS = 0.4` seconds
- **Sessions directory**: `~/.config/hypr-sessions/`
- **Gitignore**: `__pycache__/` excluded

## Planned Features
1. **Neovim session management** - Save/restore vim sessions with `:mksession`
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