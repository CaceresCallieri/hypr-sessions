# Hyprland Session Manager - Archive System Implementation Plan

## Overview

This document outlines the complete implementation plan for the archive system feature in the Hyprland Session Manager. The archive system transforms the delete functionality from permanent deletion to archiving sessions in a dedicated directory structure.

## Project Goals

- **Data Safety**: Replace permanent session deletion with recoverable archiving
- **Space Management**: Automatic cleanup with configurable limits to prevent unlimited storage growth
- **Backward Compatibility**: Maintain existing CLI interface while transparently archiving instead of deleting
- **User Experience**: Preserve familiar workflows while adding data recovery capabilities
- **Future Extensibility**: Prepare foundation for session recovery features

## Architecture Design

### Directory Structure

```
~/.config/hypr-sessions/
├── sessions/                     # Active sessions (Phase 1 ✅)
│   ├── session-name-1/
│   │   ├── session.json
│   │   ├── neovide-session-*.vim
│   │   └── (other session files)
│   └── session-name-2/
│       └── ...
└── archived/                     # Archived sessions (Phase 2 ✅)
    ├── session-name-1-20250829-181728/
    │   ├── .archive-metadata.json
    │   ├── session.json
    │   └── (original session files)
    └── session-name-2-20250830-142315/
        └── ...
```

### Archive Metadata Format

```json
{
  "original_name": "session-name",
  "archived_name": "session-name-20250829-181728", 
  "archive_timestamp": "2025-08-29T18:17:28.628714",
  "file_count": 3,
  "archive_version": "1.0"
}
```

## Implementation Phases

### Phase 1: Infrastructure Setup ✅ COMPLETED
**Status**: Completed August 29, 2025

**Objectives**:
- Create new directory structure with `sessions/` and `archived/` folders
- Implement automatic migration from flat structure to nested structure
- Update all path resolution throughout the codebase
- Ensure backward compatibility for existing installations

**Key Changes**:
- Extended `SessionConfig` with archive configuration and path management methods
- Added automatic migration logic in `_migrate_to_new_structure()`
- Updated all command files to use active session directory methods
- Modified UI session utilities for new structure compatibility

**Testing Results**:
- ✅ Migration from flat to nested structure
- ✅ All existing functionality preserved (list, save, delete, restore)
- ✅ UI compatibility maintained
- ✅ No disruption to existing installations

### Phase 2: Archive Operations ✅ COMPLETED  
**Status**: Completed August 29, 2025

**Objectives**:
- Transform delete functionality to archive sessions instead of permanent deletion
- Implement archive metadata creation and management
- Add archive size limit enforcement with automatic cleanup
- Maintain backward compatibility with existing delete command

**Key Changes**:
- Renamed `SessionDelete` → `SessionArchive` with legacy alias for compatibility
- Implemented timestamped archive directory naming (`session-name-YYYYMMDD-HHMMSS`)
- Added archive metadata generation with JSON format
- Created archive size limit enforcement with oldest-first cleanup strategy
- Added environment variable support for configuration overrides
- Enhanced validation for archive directory accessibility

**Configuration Options**:
```python
# Archive Configuration (configurable via environment variables)
archive_enabled: bool = True                    # ARCHIVE_ENABLED
archive_max_sessions: int = 20                  # ARCHIVE_MAX_SESSIONS  
archive_auto_cleanup: bool = True               # ARCHIVE_AUTO_CLEANUP
archive_cleanup_strategy: str = "oldest_first" # Future: "largest_first"
```

**Testing Results**:
- ✅ Archive creation with timestamped naming
- ✅ Archive metadata generation and parsing
- ✅ Archive size limit enforcement (tested with limit of 2, successfully removed 3 old archives)
- ✅ Environment variable configuration overrides
- ✅ Error handling for invalid sessions and malformed names
- ✅ JSON API integration with archive-specific data fields
- ✅ Backward compatibility maintained - `delete` command transparently archives

### Phase 3: Enhanced Commands ✅ COMPLETED
**Status**: Phase 3.1 ✅ Complete, Phase 3.2 ✅ Complete  
**Completion Date**: August 31, 2025

**Objectives**:
- Add archive browsing and management capabilities
- Implement session recovery from archives
- Enhance list command with archive visibility options
- Add archive maintenance utilities

**Planned Features**:

#### 3.1 Enhanced List Command ✅ COMPLETED
**Status**: Completed August 30, 2025

```bash
./hypr-sessions.py list --archived          # Show only archived sessions
./hypr-sessions.py list --all              # Show both active and archived
./hypr-sessions.py list --archived --json  # JSON output for UI integration
```

**Expected Output**:
```
Active sessions (18):
  session-1    Windows: 8    Files: 3    Saved: 2025-08-29T12:30:00
  session-2    Windows: 5    Files: 2    Saved: 2025-08-28T15:45:00

Archived sessions (12):  
  session-old-20250825-143022    Archived: 2025-08-25T14:30:22    Files: 4
  session-test-20250824-091530   Archived: 2025-08-24T09:15:30    Files: 2
```

#### 3.2 Session Recovery Command ✅ COMPLETED
**Status**: Completed August 30, 2025

```bash  
./hypr-sessions.py recover <archived-session-name>    # Recover to original name
./hypr-sessions.py recover <archived-session-name> <new-name>  # Recover with new name
```

**Recovery Logic** (Implemented):
- ✅ Move archived session back to active sessions directory
- ✅ Remove timestamp suffix to restore original name (or use provided name)
- ✅ Validate that target name doesn't conflict with existing active sessions
- ✅ Parse archive metadata to determine original session name
- ✅ Remove archive metadata file from recovered session
- ✅ Error handling with backup/restore capability on failure
- ✅ JSON API integration for UI compatibility

**Testing Results**:
- ✅ Recovery to original name: `./hypr-sessions.py recover debug-test-20250829-191042`
- ✅ Recovery to custom name: `./hypr-sessions.py recover session-name new-session-name`
- ✅ Name conflict detection: Returns error when target session already exists
- ✅ Non-existent archive handling: Returns error for invalid archive names
- ✅ JSON output format: Complete structured data for UI integration
- ✅ Metadata parsing: Reads original names from `.archive-metadata.json`
- ✅ Archive cleanup: Removes archive directory after successful recovery

#### 3.3 Archive Management
```bash
./hypr-sessions.py archive-info <archived-session-name>  # Show archive metadata
./hypr-sessions.py empty-trash                           # Permanently delete all archived sessions
./hypr-sessions.py empty-trash --older-than 30d         # Delete archives older than 30 days
```

**Implementation Requirements**:
- Archive metadata parsing and display utilities
- Date-based filtering for cleanup operations
- Confirmation prompts for permanent deletion operations
- Integration with existing validation and error handling systems

### Phase 4: UI Integration (PENDING) 
**Status**: Not started

**Objectives**:
- Update Fabric UI to reflect archiving instead of deletion
- Add archive browsing interface
- Implement recovery operations through UI
- Update confirmation dialogs and messaging

**UI Changes Required**:

#### 4.1 Delete Operation Language Update (HIGH PRIORITY)
**Current Issue**: UI still shows "Delete" terminology when actually archiving
```python
# fabric-ui/widgets/operations/delete_operation.py:25
"description": "Are you sure you wish to delete '{session_name}' session files?\nThis action cannot be undone."
```

**Required Fix**: Update to reflect archiving reality
```python
"description": "Archive '{session_name}' session?\nSession will be moved to archive and can be recovered later."
```

#### 4.2 Archive Browse Panel
- New panel for browsing archived sessions
- Recovery functionality with name conflict resolution
- Archive metadata display (original name, archive date, file count)
- Permanent deletion option with strong confirmation

#### 4.3 Enhanced Session List
- Visual distinction between active and archived sessions
- Archive count display in main UI
- Search functionality across both active and archived sessions

### Phase 5: Testing & Polish (PENDING)
**Status**: Not started

**Objectives**:
- Implement comprehensive test suite for archive operations
- Performance optimization for large archive collections
- Security hardening and data safety improvements
- Documentation updates

**Critical Testing Requirements** (Code Review Grade: D-):
- Unit tests for archive operations and metadata handling
- Integration tests for CLI → archive workflow
- Edge case testing (disk full, permission errors, concurrent access)
- Migration testing for structure changes  
- UI integration tests for archive functionality
- Performance testing with large numbers of archived sessions

**Security Improvements Required**:
- Implement atomic operations with rollback capability for failed archive operations
- Add explicit file permissions on archive metadata files
- Address TOCTOU race condition vulnerability in session validation
- Implement file locking mechanism for concurrent operation safety

## Code Quality Improvements (IN PROGRESS)

Based on comprehensive code review, the following improvements are being implemented:

### Completed ✅
1. **Debug Pattern Standardization** (August 29, 2025)
   - Fixed inconsistent debug patterns across all components
   - Standardized to use `self.debug_print()` throughout codebase
   - Added proper constructor and debug state management to `TerminalHandler`

### Critical Items (PENDING)
2. **Add Missing Type Hints** (Next Priority)
   - Fix incomplete type annotations in `_enforce_archive_limits` method
   - Add comprehensive type hints throughout archive-related code
   - Improve code maintainability and IDE support

3. **Implement Atomic Operations** (Critical for Data Safety)
   - Add rollback capability for failed archive operations
   - Implement transaction-like semantics for file moves
   - Prevent data loss from partial operation failures

4. **Address Security Vulnerabilities**
   - Fix TOCTOU race condition in session validation  
   - Set explicit permissions on archive metadata files
   - Implement file locking for concurrent operation safety

5. **Add Comprehensive Testing** (Critical Gap)
   - Create test infrastructure for archive operations
   - Unit tests for all archive functionality
   - Integration and edge case testing

## Configuration Reference

### Environment Variables
```bash
# Archive system configuration
export ARCHIVE_ENABLED=true              # Enable/disable archive system
export ARCHIVE_MAX_SESSIONS=20           # Maximum archived sessions to keep
export ARCHIVE_AUTO_CLEANUP=true         # Automatic cleanup when limit exceeded
```

### Runtime Configuration
```python
# commands/shared/config.py - SessionConfig dataclass
archive_enabled: bool = True                    # Master archive enable/disable
archive_max_sessions: int = 20                  # Cleanup limit (configurable via env)
archive_auto_cleanup: bool = True               # Auto-cleanup on archive operations  
archive_cleanup_strategy: str = "oldest_first" # Cleanup strategy (future: size-based)
```

## Technical Implementation Details

### Automatic Migration System
The system automatically detects old flat directory structures and migrates them to the new nested structure:

```python
def _migrate_to_new_structure(self) -> None:
    """Migrate from flat structure to nested active/archived structure"""
    # 1. Detect old flat structure (session directories in root)
    # 2. Create new sessions/ directory
    # 3. Move session directories to sessions/ subdirectory  
    # 4. Create archived/ directory for future use
    # 5. Handle migration errors gracefully
```

**Migration Scenarios Handled**:
- Empty directory (first-time setup)
- Single session in flat structure  
- Multiple sessions in flat structure
- Already migrated installations (no-op)
- Permission errors and disk space issues

### Archive Metadata System
Each archived session contains detailed metadata for recovery and management:

```python
def _create_archive_metadata(self, original_name: str, archived_name: str, file_count: int) -> Dict[str, Any]:
    return {
        "original_name": original_name,           # Original session name for recovery
        "archived_name": archived_name,           # Timestamped archive directory name
        "archive_timestamp": datetime.now().isoformat(),  # ISO format timestamp
        "file_count": file_count,                 # Number of files archived
        "archive_version": "1.0"                  # Metadata format version
    }
```

### Archive Cleanup Algorithm
```python
def _enforce_archive_limits(self) -> str:
    # 1. Scan archive directory for sessions with valid metadata
    # 2. Sort by timestamp (oldest first for cleanup)
    # 3. Calculate excess sessions beyond configured limit
    # 4. Remove oldest sessions to get within limit
    # 5. Return cleanup summary for user feedback
```

**Cleanup Strategy**: Currently implements "oldest_first" - removes sessions with earliest archive timestamps. Future versions will support "largest_first" and custom strategies.

## Error Handling & Edge Cases

### Archive Operation Failures
- **Partial File Moves**: Currently vulnerable to data corruption if `shutil.move()` fails partially
- **Disk Space**: No pre-flight disk space validation
- **Permissions**: Basic permission validation but no atomic permission handling
- **Concurrent Access**: No locking mechanism for simultaneous operations

### Recovery Scenarios  
- **Metadata Corruption**: Archive directories without valid `.archive-metadata.json` 
- **Name Conflicts**: Recovery attempts when active session with same name exists
- **Orphaned Archives**: Archive directories that don't match metadata format

### Migration Edge Cases
- **Incomplete Migration**: System crashes during migration process
- **Mixed Structures**: Partially migrated installations with both old and new structure
- **Permission Changes**: User permission changes between migration and normal operation

## Future Enhancements

### Advanced Archive Features
- **Size-Based Cleanup**: Alternative cleanup strategy based on total archive size
- **Compression**: Optional compression of archived sessions to save disk space
- **Export/Import**: Archive sessions to/from external storage or other machines
- **Metadata Search**: Search archived sessions by metadata (date range, file count, etc.)

### Integration Improvements  
- **Plugin System**: Allow custom archive handlers for different session types
- **Cloud Backup**: Optional sync of archived sessions to cloud storage
- **Database Integration**: Optional metadata database for faster archive operations
- **Audit Trail**: Detailed logging of all archive/recovery operations

### Performance Optimizations
- **Metadata Caching**: Cache archive metadata for faster large-collection browsing
- **Lazy Loading**: Load archive details on-demand rather than scanning all archives
- **Parallel Operations**: Concurrent archive cleanup and metadata processing
- **Index Files**: Pre-computed indexes for archive search and filtering

## Implementation Status Summary

| Phase | Status | Completion Date | Grade |
|-------|--------|-----------------|-------|
| Phase 1: Infrastructure | ✅ Complete | August 29, 2025 | A- |  
| Phase 2: Archive Operations | ✅ Complete | August 29, 2025 | B+ |
| Debug Pattern Fix | ✅ Complete | August 29, 2025 | A |
| Type Hints Addition | 🔄 In Progress | - | - |
| Atomic Operations | ⏳ Pending | - | - |
| Security Hardening | ⏳ Pending | - | - |
| Phase 3.1: Enhanced List Command | ✅ Complete | August 30, 2025 | A |
| Phase 3.2: Session Recovery Command | ✅ Complete | August 31, 2025 | C+ (Security Issues) |
| Phase 4: UI Integration | ⏳ Pending | - | - |
| Phase 5: Testing & Polish | ⏳ Pending | - | - |

**Overall Project Grade**: C+ (Phase 3.2 functionally complete but contains critical security vulnerabilities requiring immediate attention)

## Next Steps Priority

1. **IMMEDIATE (Critical Security)**:
   - **FIX PATH TRAVERSAL VULNERABILITY** in session recovery (commands/recover.py lines 47, 58)
   - **IMPLEMENT METADATA TYPE VALIDATION** for archive recovery
   - **ADD CLI ARGUMENT VALIDATION** for recover command
   - **ALIGN ERROR HANDLING PATTERNS** with codebase standards

2. **HIGH PRIORITY (Data Safety)**:
   - Add missing type hints to archive methods
   - Implement atomic operations for data safety
   - Address remaining security vulnerabilities (TOCTOU, permissions)

3. **SHORT TERM (Next Sprint)**:
   - Update UI language to reflect archiving instead of deletion
   - Add comprehensive test infrastructure
   - ✅ Implement basic session recovery functionality (COMPLETED)

4. **MEDIUM TERM (Future Development)**:
   - ✅ Enhanced list command with archive visibility (COMPLETED)
   - ✅ Session recovery command implementation (COMPLETED)
   - Archive browsing UI panel
   - Performance optimizations for large collections

5. **LONG TERM (Feature Expansion)**:
   - Advanced archive management features
   - Cloud integration and export capabilities
   - Plugin system for extensibility

---

*This document serves as the complete technical specification and implementation roadmap for the Hyprland Session Manager Archive System. It should be updated as development progresses and new requirements are identified.*