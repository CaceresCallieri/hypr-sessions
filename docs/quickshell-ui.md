# QuickShell/QML Frontend

The active UI for hypr-sessions, replacing the legacy Fabric/GTK3 frontend.

## Architecture

- **Framework**: QuickShell (Qt/QML wrapper for desktop shells)
- **Window**: `PanelWindow` with Wayland layer shell support
- **Focus**: `WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive` for exclusive keyboard
  capture; `HyprlandFocusGrab` dismisses the window when clicking outside
- **Theme**: Symmetria M3 palette system (`services/Theme.qml`)
- **State**: `SessionService.qml` (pragma Singleton) manages all UI and backend state;
  `Paths.qml` (pragma Singleton, also in `services/`) provides CLI path resolution

## File Structure

```
quickshell-ui/
  shell.qml                        # Root entry point
  modules/sessions/
    SessionsModule.qml             # Module wrapper
    SessionsPopup.qml              # Main window (card-based layout)
    BrowsePanel.qml                # Session list with search and navigation
    SavePanel.qml                  # Save dialog with state machine (idle/executing/success/error)
    ConfirmationModal.qml          # Restore/delete/recover confirmation overlay
    SearchBar.qml                  # Live filtering search input
    SessionItem.qml                # Individual session list item
    ToggleSwitch.qml               # Browse/Save mode toggle
  services/
    SessionService.qml             # Singleton: process management, operation orchestration
    Theme.qml                      # M3 palette, typography, spacing design tokens
    Paths.qml                      # Singleton: CLI path resolution and home directory helpers
  config/
    Config.qml                     # Config wrapper
    SessionsConfig.qml             # Timing and dimension constants
  components/                      # Reusable components
    StyledText.qml, StyledRect.qml, ClippingRect.qml,
    StateLayer.qml, MaterialIcon.qml, Anim.qml, CAnim.qml
```

## Running

```bash
cd quickshell-ui && ./run.sh       # Development (clears QML cache)
qs -c sessions-ui                  # Installed version
./install.sh                       # Install standalone (symlinks ~/.config/quickshell/sessions-ui -> project dir)
```

## Key Features

- Full session management: browse, save, restore, delete, recover
- Archive mode toggle (Ctrl+A) switches between active/archived sessions
- Real-time search filtering via SearchBar
- Keyboard navigation: Up/Down, Enter, Tab, d (delete), Ctrl+L (clear search)
- Operation state machine with confirmation modal
- Automatic session reload after operations
- Success auto-return (2s default), operation timeout (35s default)

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Up/Down | Navigate sessions |
| Enter | Confirm operation (restore/save) |
| Tab | Toggle Browse/Save panels |
| d | Delete selected session |
| Ctrl+A | Toggle archive mode |
| Ctrl+L | Clear search |
| Esc | Clear search (when search is non-empty), otherwise quit |
| Ctrl+Q | Quit |

## Backend Communication

`SessionService.qml` spawns the CLI as a subprocess with `--json` flag and parses
the structured JSON response. Operations (restore/delete/recover/save) have a 35s timeout;
the session list call (`loadSessions`) has no timeout.
