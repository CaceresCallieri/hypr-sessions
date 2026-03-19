# Development History

Historical notes preserved for context on past decisions.

## Major Milestones

- **2025-08**: Browser integration settled on keyboard shortcut extension after trying Native Messaging and sessionstore.jsonlz4
- **2025-08-13**: Session storage migrated from flat files to folder-per-session
- **2025-08-27**: Code review (grade B+) drove cleanup: debug print removal, method complexity reduction, widget pooling
- **2025-08-28**: Monolithic browse_panel.py (1260 lines) refactored into 5-component architecture (68% reduction)
- **2025-08-31**: Archive system completed with security fixes (path traversal prevention)
- **2025-09-01**: Archive system production-ready with atomic operations, recovery markers, health monitoring
- **2025-09-10**: GTK3 design system variables and CSS documentation
- **2026-03**: QuickShell/QML frontend added, replacing Fabric/GTK3 as the active UI
- **2026-03**: Matte theme system replaced glass transparency in QuickShell UI

## Key Decisions

- **Archive over delete**: Legal/safety -- sessions archived with metadata, recoverable, auto-cleanup when limit hit
- **Name-based selection over index-based**: Eliminated coordinate system bugs between filtered/full session lists
- **Dynamic property pattern**: Components read parent state via `@property` instead of cached copies
- **CommandDebugger over raw print**: Consistent format, stderr, zero-cost when disabled
- **Widget pooling in Fabric UI**: 95%+ reuse efficiency, but complexity was borderline over-engineered
- **Subprocess timeout protection**: 30s timeout + process group isolation prevents hanging restores
