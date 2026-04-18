---
name: QuickShell Frontend Rework
description: Major frontend migration from Fabric/GTK3 to QuickShell with Symmetria integration, layer-shell popup, full feature parity
type: project
---

Hypr-sessions is migrating from Fabric (GTK3/Python) to QuickShell (QML) for the frontend UI.

**Key Architectural Decisions:**
- **Window type**: Layer-shell popup (PanelWindow + WlrLayershell.Overlay) with exclusive keyboard focus
- **Symmetria integration**: YASI-style Theme.qml IPC bridge — queries Symmetria for colors/tokens, falls back to hardcoded M3 palette
- **Shared component library**: Aspirational goal to extract shared components (StyledRect, StyledText, etc.) into ~/.config/quickshell/shared/ for use by YASI, sessions-ui, and future apps. For now, duplicate YASI's components locally. Track extraction as future work.
- **Backend**: Keep Python CLI (`hypr-sessions.py --json`) via Process + StdioCollector
- **Feature scope**: Full parity with Fabric UI (browse, save, restore, delete/archive, search, keyboard nav, confirmation modals)
- **Deployment**: Standalone QuickShell config at ~/.config/quickshell/sessions-ui/ (symlinked from project's quickshell-ui/ dir). Assumes Symmetria is running.
- **Config name**: `sessions-ui` (may change later)
- **Fabric UI**: Deleted — no longer maintained

**Why:** Unify the desktop environment under QuickShell for consistency with Symmetria shell and YASI file manager. QML eliminates GTK3 limitations (CSS specificity, widget pooling complexity, thread safety concerns).

**How to apply:** All frontend work should use QML/QuickShell patterns. Reference YASI's Theme.qml for Symmetria integration pattern. Reference Symmetria's Colours.qml for glassmorphism. Use the existing Python CLI backend unchanged.
