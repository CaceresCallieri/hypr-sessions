# System Health Check Command

## Priority: P3 | Type: Enhancement | Benefit: Medium | Complexity: Medium

## Problem Description
The system lacks a comprehensive health check command that can validate configuration, directory accessibility, and detect potential issues like interrupted recovery operations. This makes troubleshooting and system validation more difficult for users and administrators.

## Implementation Plan
1. Create new `health_check()` method in appropriate manager class
2. Implement directory permission and accessibility checks
3. Add configuration validation with bounds checking
4. Check for interrupted recovery operations using existing recovery system
5. Add CLI integration for the health check command
6. Design comprehensive reporting with success/warning/error categorization

## File Locations
- New CLI command integration in `/home/jc/Dev/hypr-sessions/hypr-sessions.py`
- Implementation likely in session manager or new health check module
- Integration with existing recovery system in `/home/jc/Dev/hypr-sessions/commands/recover.py`
- Configuration validation using `/home/jc/Dev/hypr-sessions/commands/shared/config.py`

## Success Criteria
- Health check validates directory permissions and accessibility
- Configuration bounds checking detects invalid settings
- Interrupted recovery operations are detected and reported
- Clear success/warning/error reporting using OperationResult system
- CLI integration allows `./hypr-sessions.py health` command
- JSON output support for programmatic usage

## Dependencies
[Depends-On: configuration-override-security] - Configuration validation component

## Code Examples

**Proposed health check implementation:**
```python
def health_check(self) -> OperationResult:
    """Perform comprehensive system health checks"""
    result = OperationResult("System Health Check")
    
    # Check directory permissions
    active_dir = self.config.get_active_sessions_dir()
    archived_dir = self.config.get_archived_sessions_dir()
    
    for directory, name in [(active_dir, "active sessions"), (archived_dir, "archived sessions")]:
        if not directory.exists():
            result.add_warning(f"{name.title()} directory does not exist: {directory}")
        elif not os.access(directory, os.R_OK | os.W_OK):
            result.add_error(f"Insufficient permissions for {name} directory: {directory}")
        else:
            result.add_success(f"{name.title()} directory accessible")
    
    # Check for interrupted recovery operations
    recover_manager = SessionRecovery(debug=self.debug_mode)
    interrupted_recoveries = recover_manager.check_interrupted_recoveries()
    
    if interrupted_recoveries:
        result.add_warning(f"Found {len(interrupted_recoveries)} interrupted recovery operations")
    else:
        result.add_success("No interrupted recovery operations found")
    
    return result
```

**CLI integration:**
```python
elif args.action == "health":
    result = manager.health_check()
    if args.json:
        manager._output_json_result(result)
    else:
        result.print_detailed_result()
```

## Reminder
Move this file to TODOS/code-quality-improvements/completed/ when implementation is finished.