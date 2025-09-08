# Simplify Archive Toggle Logic

## Priority: P3 | Type: Polish | Benefit: Medium | Complexity: Low

## Problem Description

The Ctrl+A archive toggle handler has unnecessary complexity for search preservation. The current implementation has 15 lines of complex state management when a simple 3-line approach would be more maintainable.

**Current Issue**: Over-engineered search preservation logic that could be encapsulated in a single method.

## Implementation Plan

1. **Create `toggle_archive_mode()` method** in `browse_panel.py` to encapsulate complexity
2. **Move search preservation logic** into the new method
3. **Simplify Ctrl+A handler** to just call the new method
4. **Add error handling** for edge cases in search restoration
5. **Test toggle behavior** preserves search state correctly

## File Locations

- **Modify**: `fabric-ui/widgets/browse_panel.py` - Add `toggle_archive_mode()` method
- **Simplify**: `fabric-ui/widgets/components/keyboard_event_handler.py` - Simplify Ctrl+A handler

## Success Criteria

- [ ] Ctrl+A handler reduced to 3 lines or fewer
- [ ] Search state preservation functionality maintained
- [ ] Archive mode toggle encapsulated in single method
- [ ] Error handling for edge cases in search restoration
- [ ] Improved code maintainability and readability

## Dependencies

None - this is an independent polish improvement

## Code Examples

**Current Complex Implementation** (`keyboard_event_handler.py`):
```python
def _handle_ctrl_a_toggle_archive(self) -> bool:
    # 15 lines of complex logic
    current_search = self.browse_panel.search_manager.get_search_query()
    self.browse_panel.is_archive_mode = not self.browse_panel.is_archive_mode
    self.browse_panel.update_display()
    if current_search:
        if hasattr(self.browse_panel.search_manager, 'search_input'):
            self.browse_panel.search_manager.search_input.set_text(current_search)
            self.browse_panel._on_search_changed(self.browse_panel.search_manager.search_input)
    
    # Debug logging...
    if self.browse_panel.debug_logger:
        self.browse_panel.debug_logger.debug_navigation_operation(
            "toggle_archive_mode", 
            "active_to_archive" if self.browse_panel.is_archive_mode else "archive_to_active",
            None, "ctrl_a_key"
        )
    return True
```

**Proposed Simplified Approach**:

**In `keyboard_event_handler.py`**:
```python
def _handle_ctrl_a_toggle_archive(self) -> bool:
    self.browse_panel.toggle_archive_mode()
    return True
```

**In `browse_panel.py`**:
```python
def toggle_archive_mode(self):
    """Toggle between active and archive modes with search state preservation"""
    # Preserve current search query
    current_search = self.search_manager.get_search_query() if hasattr(self, 'search_manager') else ""
    
    # Toggle mode
    self.is_archive_mode = not self.is_archive_mode
    
    # Update display with new mode data
    self.update_display()
    
    # Restore search query if it existed
    if current_search and hasattr(self.search_manager, 'search_input'):
        try:
            self.search_manager.search_input.set_text(current_search)
            self._on_search_changed(self.search_manager.search_input)
        except Exception as e:
            # Graceful fallback if search restoration fails
            if self.debug_logger:
                self.debug_logger.debug_event_routing("archive_toggle", "search_restoration_failed", str(e))
    
    # Debug logging
    if self.debug_logger:
        mode_change = "active_to_archive" if self.is_archive_mode else "archive_to_active"
        self.debug_logger.debug_navigation_operation("toggle_archive_mode", mode_change, None, "ctrl_a_key")
```

**Benefits**:
- **Simplified keyboard handler**: 3 lines instead of 15
- **Encapsulated complexity**: All toggle logic in one place
- **Better error handling**: Try-catch for search restoration edge cases
- **Improved maintainability**: Changes to toggle logic only affect one method
- **Consistent with existing patterns**: Similar to other panel methods

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.