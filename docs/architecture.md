# Architecture Deep Dive

Detailed reference for the Hyprland Session Manager's backend, data formats, and system patterns.

## Session Data Format

### Storage Structure

```
~/.config/hypr-sessions/
  sessions/                          # Active sessions
    session_name/
      session.json                   # Main session metadata
      neovide-session-*.vim          # Neovide session files
  archived/                          # Archived sessions
    session_name-YYYYMMDD-HHMMSS/
      .archive-metadata.json         # Archive metadata
      session.json                   # Original session data
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
        "name": "yazi", "args": [], "full_command": "yazi", "shell_command": null
      },
      "launch_command": "ghostty --working-directory=/path -e sh -c 'yazi; exec $SHELL'",
      "browser_session": {
        "browser_type": "zen",
        "tabs": [{"url": "...", "title": "...", "active": false, "pinned": false}],
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

### Archive Metadata

```json
{
  "original_name": "session-name",
  "archived_name": "session-name-20250831-123456",
  "archive_timestamp": "2025-08-31T12:34:56.789012",
  "file_count": 3,
  "archive_version": "1.0"
}
```

## Archive System

- `delete` command archives to `archived/` with timestamped directory and metadata
- `recover` command restores archived sessions (original or custom name)
- Automatic cleanup when archive limit exceeded (configurable, default 20)
- `list --archived` / `list --all` for enumeration
- CLI validates archive names with regex `^.+-\d{8}-\d{6}$` to prevent path traversal
- Atomic operations with recovery markers and automatic rollback on failure

## Configuration

Central: `commands/shared/config.py` -- `SessionConfig` dataclass.

Environment variable overrides (all `HYPR_` prefixed, bounds-checked):

| Variable | Default | Bounds |
|----------|---------|--------|
| `HYPR_ARCHIVE_ENABLED` | true | boolean |
| `HYPR_ARCHIVE_MAX` | 20 | 1-1000 |
| `HYPR_ARCHIVE_AUTO_CLEANUP` | true | boolean |
| `HYPR_ARCHIVE_CLEANUP_STRATEGY` | oldest_first | oldest_first / largest_first |

Timing: delays 0.0-10.0s, timeouts 1-120s. Group restoration delay: 0.4s between instructions.

## Error Handling

All commands use `OperationResult` from `commands/shared/operation_result.py`:

- Success/warning/error categorization with partial failure support
- Enhanced helpers: `add_filesystem_error()`, `add_json_error()`, `add_subprocess_error()`
- Custom exceptions: `InvalidSessionNameError`, `SessionNotFoundError`, `SessionAlreadyExistsError`
- Specific exception handling (never bare `except Exception`)

## Health Check

`./hypr-sessions.py health` validates:
- Directory accessibility (read/write permissions)
- Configuration bounds
- Recovery system health (detects interrupted operations via recovery markers)

## Browser Integration

Keyboard shortcut extension approach:
- Extension registers Alt+U, captures all tabs with metadata
- Triggered via `hyprctl dispatch sendshortcut ALT,u,address:{addr}` (no focus steal)
- Output: `Downloads/hypr-session-tabs-{timestamp}.json`
- Works with Zen browser, 15+ tabs in ~2 seconds

Deprecated approaches (don't re-explore): Native Messaging (reliability), sessionstore.jsonlz4 (real-time updates).

## Backend Debug System

`CommandDebugger` from `commands/shared/debug.py`:
- Consistent format: `[DEBUG ComponentName timestamp] message`
- Stderr output for separation from regular output
- Specialized methods: `debug_operation()`, `debug_file_operation()`, `debug_session_operation()`
- Zero-cost when disabled (early return)
