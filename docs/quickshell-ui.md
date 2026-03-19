# QuickShell/QML Frontend

The active UI for hypr-sessions, replacing the legacy Fabric/GTK3 frontend.

## Architecture

- **Framework**: QuickShell (Qt/QML wrapper for desktop shells)
- **Window**: `PanelWindow` with Wayland layer shell support
- **Focus**: `HyprlandFocusGrab` for exclusive keyboard control
- **Theme**: Symmetria M3 palette system (`services/Theme.qml`)
- **State**: Singleton `SessionService.qml` manages all UI and backend state

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
    Paths.qml                      # Configuration paths
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
./install.sh                       # Install standalone (symlinks to ~/.config/quickshell/sessions-ui)
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
| Esc / Ctrl+Q | Exit |

## Backend Communication

`SessionService.qml` spawns the CLI as a subprocess with `--json` flag and parses
the structured JSON response. All operations are async with timeout protection.
