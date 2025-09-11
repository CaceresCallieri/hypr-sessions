# Clean Up Unused Code Branches

## Priority: P3 | Type: Polish | Benefit: Minimal | Complexity: Quickfix

## Problem Description

Empty methods with placeholder comments exist in the codebase, serving no functional purpose and adding maintenance overhead. These should be either implemented or removed for cleaner code.

## Implementation Plan

1. **Audit Empty Methods**: Find all methods with only placeholder comments
2. **Determine Intent**: Check if methods should be implemented or removed
3. **Remove or Implement**: Clean up unused branches or add proper implementation
4. **Update Documentation**: Ensure class contracts remain clear after cleanup

## File Locations

**Primary File**:
- `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/operations/restore_operation.py:52-59`

**Specific Empty Method**:
```python
def cleanup_after_success(self):
    """Handle post-operation cleanup based on mode"""
    if self.is_archive_mode:
        # After recovery, refresh to show updated session lists (archive → active)
        # The base class handles the actual panel refresh
        pass
    else:
        # No cleanup needed for restore - session list unchanged
        pass
```

## Success Criteria

- [ ] No methods with only `pass` statements and placeholder comments
- [ ] Clear distinction between abstract methods and implemented methods
- [ ] Reduced codebase size through unused code removal
- [ ] Maintained class contracts and inheritance patterns

## Dependencies

None

## Code Examples

**Current Unused Code**:
```python
def cleanup_after_success(self):
    """Handle post-operation cleanup based on mode"""
    if self.is_archive_mode:
        # After recovery, refresh to show updated session lists (archive → active)
        # The base class handles the actual panel refresh
        pass
    else:
        # No cleanup needed for restore - session list unchanged
        pass
```

**Option 1: Remove Entirely** (if base class handles everything):
```python
# Remove the method entirely - base class implementation will be used
```

**Option 2: Simplify to Essential** (if some logic needed):
```python
def cleanup_after_success(self):
    """Handle post-operation cleanup based on mode"""
    if self.is_archive_mode:
        # Recovery operations require session list refresh
        self.panel.refresh()
```

**Option 3: Document as No-Op** (if override is intentional):
```python
def cleanup_after_success(self):
    """No cleanup needed - base class handles refresh automatically"""
    pass  # Intentional no-op override
```

**Decision Criteria**:
1. **Does base class provide default behavior?** → Remove method
2. **Is different behavior needed per mode?** → Implement properly
3. **Is explicit no-op required?** → Document intention clearly

**Other Common Empty Method Patterns to Check**:
- Methods with only `# TODO:` comments
- Methods with only `raise NotImplementedError` (unless abstract)
- Methods with conditional blocks containing only `pass`
- Methods with extensive comments but no code

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.