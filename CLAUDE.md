# Hyprland Session Manager

> **CLAUDE.md Philosophy**: Keep this file short. The code is the source of truth.
> Only document non-obvious knowledge that agents cannot derive from reading the codebase.
> For deep dives, see `docs/`. Do NOT bloat this file with implementation details,
> code examples that mirror actual code, historical development logs, or completion statuses.

A Python session manager for Hyprland: saves and restores workspace sessions (windows, groups, terminal CWDs, Neovim sessions, browser tabs).

## Quick Orientation

- **CLI**: `hypr-sessions.py` -- commands: `save`, `restore`, `list`, `delete`, `recover`, `health`
- **Backend**: `commands/` -- modular handlers for each command, shared utilities in `commands/shared/`
- **UI (active)**: `quickshell-ui/` -- QuickShell/QML frontend with Symmetria M3 theme
- **UI (legacy)**: `fabric-ui/` -- GTK3 Fabric framework overlay (superseded, still in repo)
- **Storage**: `~/.config/hypr-sessions/{sessions,archived}/` -- folder-per-session with JSON metadata
- **Browser Extension**: `browser_extension/` -- Alt+U keyboard shortcut captures tabs from Zen browser
- **Tests**: `pytest` framework in `tests/`

## Critical Rules for AI Agents

### Never Use Raw print()

All debug output must use the structured logging systems:

- **Backend**: `CommandDebugger` from `commands/shared/debug.py`
- **UI (Fabric legacy)**: `debug_logger` from `fabric-ui/utils/debug_logger.py`

### Never Import fabric-ui Modules Directly (legacy fabric-ui only)

Fabric UI requires GTK3 + gobject + Fabric venv + Wayland. For validation use only:
`python -m py_compile fabric-ui/widgets/browse_panel.py`

QuickShell/QML components in `quickshell-ui/` have no such restriction.

### Other Rules

- No emojis in code or output (rendering issues in target environment)
- Use `shlex.quote()` for all path escaping in shell commands
- Use `Final` type annotations for constants
- Use `OperationResult` pattern for all command results (see `commands/shared/operation_result.py`)
- All commands support `--debug` and `--json` flags

## Non-Obvious Architecture Decisions

### "Delete" Actually Archives

The `delete` command archives sessions to `archived/session-name-YYYYMMDD-HHMMSS/` with metadata.
The `recover` command restores them. CLI semantics preserved for familiarity.

### Browser Tab Capture

Uses `hyprctl dispatch sendshortcut ALT,u,address:{window_address}` to trigger the extension
without stealing window focus. Extension writes `hypr-session-tabs-{timestamp}.json` to Downloads.
Previous approaches (Native Messaging, sessionstore.jsonlz4) were tried and abandoned -- don't re-explore.

### Neovide Session Capture

Captures live Neovim state via remote socket API:
`nvim --server <socket> --remote-send ':mksession /path/session.vim'`
Falls back to working directory if socket unavailable.

### Terminal Shell Wrapper

Programs launched with `exec $SHELL` suffix so the terminal persists after the program exits:
`ghostty --working-directory=/path -e sh -c 'yazi; exec $SHELL'`

### Subprocess Safety

All application launches in restore use 30s timeout, process group isolation (`os.setsid`),
and 5s startup validation to prevent hanging restore operations.

### Security: CLI Input Validation

Archive names validated with regex `^.+-\d{8}-\d{6}$` at CLI entry. Environment variable
overrides are bounds-checked (archive limits: 1-1000, delays: 0.0-10.0s, timeouts: 1-120s).

## Anti-Patterns Learned

- Don't create duplicate classes for mode variants -- use boolean flags (`is_archive_mode`)
- Don't create new UI states when existing ones work with display text changes
- Single event handler authority -- competing handlers for same events cause bugs
- Set mode flags **before** parent constructor calls to avoid `AttributeError`
- Always follow `OperationResult` patterns -- don't invent new error systems
- Encapsulate complex operations in focused methods, not inline in handlers

## See Also

- `docs/quickshell-ui.md` -- QuickShell/QML frontend architecture and patterns
- `docs/architecture.md` -- Data formats, archive system, error handling, configuration
- `docs/gtk3-gotchas.md` -- GTK3 CSS limitations and widget behavior (for fabric-ui work only)
- `docs/development-history.md` -- Past decisions and milestones (only needed when investigating history, not for routine work)
- `TODO.md` -- Improvement roadmap and prioritized tasks
- `tests/README.md` -- Test suite documentation
