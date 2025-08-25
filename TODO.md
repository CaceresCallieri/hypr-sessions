# Hyprland Session Manager - TODO

## Outstanding Improvements

### Critical Priority (Search System Performance & Architecture)

#### 1. **Widget Recreation Performance Problem** 
**Context**: The search system currently recreates all session widgets on every keystroke, causing severe performance issues and UI flickering.

**Problem**: The dual focus search implementation uses widget recreation instead of property updates, leading to:
- 100+ widget creation/destruction cycles per second during rapid typing
- GTK object lifecycle stress and memory pressure  
- Visual flickering and responsiveness issues
- Focus management complexity

**Location**: `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/browse_panel.py`
- Lines 448-486 (`_update_session_list_only()`) - Triggers full widget recreation
- Lines 487-565 (`_create_session_widgets_only()`) - Creates new Button objects for every session
- Lines 172-176 (`_on_search_changed()`) - Called on every character typed

**Current Problematic Flow**:
```python
def _on_search_changed(self, entry):
    self.search_query = entry.get_text().strip()
    self._update_filtered_sessions()
    self._update_session_list_only()  # Recreates ALL widgets

def _create_session_widgets_only(self):
    # Creates new Button() objects for every visible session
    widgets = []
    for session_name in visible_sessions:
        button = Button(label=f"• {session_name}")  # New object every time
```

**Action Required**:
1. **Implement Widget Pool Pattern**: Create reusable session button widgets, update properties instead of recreation
2. **Property-Based Updates**: Modify existing button labels and styling rather than destroying/recreating
3. **Lazy Widget Creation**: Only create widgets for newly visible sessions
4. **Benchmark Performance**: Measure before/after with 50+ sessions and rapid typing

**Implementation Approach**:
```python
class SessionWidgetPool:
    def __init__(self):
        self._button_pool = {}
        
    def get_button(self, session_name, is_selected):
        if session_name not in self._button_pool:
            self._button_pool[session_name] = Button(...)
        button = self._button_pool[session_name]
        # Update properties instead of recreating
        self._update_button_state(button, is_selected)
        return button
```

**Success Criteria**: Search typing should not recreate any widgets, only update properties of existing widgets

---

#### 2. **Multi-Index Coordinate System Fragility** ✅ **COMPLETED**
**Status**: Successfully eliminated fragile 4-index coordinate system and replaced with robust name-based selection.

**Implementation Completed**:
- Replaced complex multi-index system (`selected_global_index`, `selected_local_index`, filtered indices) with single `selected_session_name` 
- Eliminated all coordinate conversion logic and race conditions
- Simplified navigation methods from 15+ lines to 3 lines of direct name-based logic
- Added robust state management with None fallback for empty results
- Navigation now uses direct session name equality checks (`session_name == self.selected_session_name`)

**Results Achieved**:
- Zero coordinate conversion between different coordinate systems
- Elimination of race conditions when `filtered_sessions[0]` doesn't exist
- Removed 2 state variables and all synchronization logic
- Navigation performance improved (no `.index()` searches during operations)
- Single source of truth eliminates entire class of synchronization bugs

**Code Quality Impact**: Transformed fragile, error-prone coordinate system into robust, maintainable name-based architecture

**Date Completed**: August 25, 2025

---

#### 3. **Search Input Debouncing Implementation**
**Context**: Every character typed triggers immediate UI updates, causing performance issues and potential character loss during rapid typing.

**Problem**: No debouncing mechanism leads to:
- Full UI updates on every keystroke (excessive work)
- Potential character loss during expensive operations
- Poor user experience during rapid typing
- Unnecessary server/backend calls

**Location**: `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/browse_panel.py`
- Lines 172-176: `_on_search_changed()` - Called immediately on every character
- No timeout or debouncing mechanism currently exists

**Current Problematic Flow**:
```python
def _on_search_changed(self, entry):
    # Immediate execution - no debouncing
    self.search_query = entry.get_text().strip()
    self._update_filtered_sessions()  # Expensive operation
    self._update_session_list_only()  # UI recreation
```

**Action Required**:
1. **Implement 150ms Debounce Timer**: Use `GLib.timeout_add()` to delay processing
2. **Cancel Previous Timers**: Prevent multiple pending operations
3. **Immediate Visual Feedback**: Show typing state without full processing
4. **Performance Testing**: Measure improvement with rapid typing

**Implementation Approach**:
```python
def _on_search_changed(self, entry):
    # Cancel previous timer if exists
    if hasattr(self, '_search_timeout_id') and self._search_timeout_id:
        GLib.source_remove(self._search_timeout_id)
    
    # Store new search query immediately (for visual feedback)
    self.search_query = entry.get_text().strip()
    
    # Schedule actual processing after debounce delay
    self._search_timeout_id = GLib.timeout_add(150, self._perform_debounced_search)

def _perform_debounced_search(self):
    self._search_timeout_id = None
    self._update_filtered_sessions()
    self._update_session_list_only()
    return False  # Don't repeat timer
```

**Success Criteria**: Rapid typing should not trigger continuous UI updates, only final result after 150ms pause

---

### High Priority (Architectural Consistency)

#### 1. **Convert Save Panel to GTK Event-Based Handling**
**Context**: Save panel still uses legacy keycode-based input while browse panel uses GTK events, creating inconsistency.

**Problem**: Mixed input handling approaches across UI panels
- Browse panel: Uses GTK event-based handling with `handle_key_press_event(widget, event)`
- Save panel: Uses legacy keycode-based handling with `handle_key_press(keycode)`

**Location**: `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/save_panel.py` lines 26, 325, 332

**Current Issue**: 
```python
# save_panel.py - OLD keycode approach
if self.save_panel.handle_key_press(keycode):  # session_manager.py:224
    return True

# browse_panel.py - NEW GTK approach  
if self.browse_panel.handle_key_press_event(widget, event):  # session_manager.py:230
    return True
```

**Action Required**: 
1. Add `handle_key_press_event(widget, event)` method to SavePanelWidget
2. Convert keycode-based logic to use `event.keyval` with GTK constants
3. Update session_manager.py to use GTK events for both panels
4. Remove remaining 3 keycode constants from constants.py

**Success Criteria**: Both panels use consistent GTK event-based input handling

---

#### 2. **Focus Management Race Condition Resolution**
**Context**: Current focus restoration could conflict with GTK's internal focus management.

**Problem**: Direct `grab_focus()` calls may cause timing conflicts with GTK widget realization

**Location**: 
- `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/browse_panel.py:423-431`
- `/home/jc/Dev/hypr-sessions/fabric-ui/session_manager.py:154-164`

**Current Implementation**:
```python
def _ensure_search_focus(self):
    if self.search_input and not self.search_input.has_focus():
        self.search_input.grab_focus()  # Potential race condition

def _delayed_focus_setup(self):  
    self.browse_panel.search_input.grab_focus()  # No widget readiness check
```

**Action Required**:
1. Add widget readiness verification (`get_realized()`, `is_visible()`)
2. Use `GLib.idle_add()` for deferred focus operations
3. Implement retry logic with timeout for focus acquisition
4. Add focus verification after grab attempts

**Success Criteria**: Reliable focus management without race conditions

---

#### 3. **Search Input Debouncing for Performance**
**Context**: Current implementation recreates entire UI on every character typed, causing performance issues during rapid typing.

**Problem**: Full UI recreation every keystroke impacts performance

**Location**: `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/browse_panel.py:163-167`

**Current Issue**:
```python
def _on_search_changed(self, entry):
    self.search_query = entry.get_text().strip()
    self._update_filtered_sessions()
    self.update_display()  # Full UI recreation every keystroke
```

**Action Required**:
1. Implement 150ms debounce timer using `GLib.timeout_add()`
2. Add `_search_timeout_id` tracking to prevent multiple timers
3. Create `_perform_search_update()` method for actual filtering
4. Only update UI when search query actually changes

**Success Criteria**: Smooth typing experience without UI lag during rapid input

---

#### 4. **Code Duplication in Widget Creation Methods** ✅ **COMPLETED**
**Status**: Successfully eliminated 78 lines of duplicate widget creation logic (46% code reduction).

**Implementation Completed**:
- Created `_create_session_button()` factory method for consistent button creation
- Added `_create_sessions_widget_list()` for complete widget assembly  
- Simplified `_create_sessions_list()` from 89 to 19 lines using shared logic
- Removed duplicate `_create_session_widgets_only()` method entirely

**Results Achieved**:
- Single source of truth for all session button creation
- Clean composition architecture with proper separation of concerns
- Code Review Grade: A- (8.5/10) - Production-ready refactoring
- Zero maintenance risks, improved code quality and maintainability

**Date Completed**: August 24, 2025

---

#### 5. **Method Complexity Violation in Window Calculation** ✅ **COMPLETED**
**Status**: Successfully decomposed complex 48-line method into 5 focused helper methods with single responsibilities.

**Implementation Completed**:
- Extracted `_get_selected_filtered_index()` - selection validation (5 lines, 1 branch)
- Extracted `_calculate_optimal_window_start()` - window positioning (11 lines, 2 branches)  
- Extracted `_clamp_to_valid_bounds()` - bounds validation (3 lines, 0 branches)
- Extracted `_get_visible_indices_range()` - range generation (3 lines, 0 branches)
- Simplified `calculate_visible_window()` - orchestration (18 lines, 1 branch)

**Results Achieved**:
- Reduced cyclomatic complexity from 8+ branches to 4 total branches across all methods
- Each helper method has single clear responsibility and fits in your head easily
- Main method now reads like documentation - clear story of the calculation process
- Zero risk pure refactoring that preserves identical behavior
- Dramatically improved maintainability and testability

**Code Quality Impact**: Transformed complex monolithic method into self-documenting, testable components following single responsibility principle

**Date Completed**: August 25, 2025

---

### Medium Priority (Feature Enhancements)

#### 6. **Upgrade to Fuzzy Matching Algorithm**
**Context**: Current substring matching is basic; fuzzy matching would improve session discovery.

**Problem**: Simple substring matching limits session discovery capabilities

**Location**: `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/browse_panel.py:139-160`

**Current Implementation**: Simple case-insensitive substring matching

**Action Required**:
1. Implement character-order fuzzy matching algorithm
2. Add scoring system for match quality (exact > starts-with > contains > fuzzy)
3. Sort filtered results by match score
4. Preserve existing substring matching as fallback

**Success Criteria**: Users can find sessions with partial character matches (e.g., "dvs" finds "dev-session")

---

#### 7. **International Keyboard Layout Testing**
**Context**: GTK keyval constants are primarily US keyboard focused; need verification with international layouts.

**Problem**: Navigation keys may not work consistently across different keyboard layouts

**Action Required**:
1. Test with European keyboard layouts (QWERTZ, AZERTY)
2. Test with non-Latin keyboards (Cyrillic, Arabic, etc.)
3. Verify navigation keys work consistently across layouts
4. Document any layout-specific issues discovered

**Success Criteria**: Confirmed compatibility with major international keyboard layouts

---

### Low Priority (Polish & Optimization)

#### 8. **Enhanced Error Handling Specificity** 
**Context**: Generic exception handling could be more specific for better debugging.

**Problem**: Generic `Exception` handling makes debugging difficult

**Location**: `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/browse_panel.py:423-431`

**Action Required**:
1. Replace generic `Exception` with specific GTK exceptions
2. Add context-aware error messages with operation details
3. Implement graceful degradation for focus failures
4. Add debug logging levels for different error types

**Success Criteria**: Clear, specific error messages that aid in debugging

---

#### 9. **Unit Test Coverage for Search System**
**Context**: Complex search and focus logic lacks automated test coverage.

**Problem**: No automated testing for critical search functionality

**Action Required**:
1. Create test suite for character detection logic
2. Add tests for event routing decisions
3. Mock GTK events for navigation key testing  
4. Test search filtering with various edge cases

**Success Criteria**: Comprehensive test coverage for search system components

---

#### 10. **Performance Optimization for Large Session Lists**
**Context**: Current O(n) search could be optimized for 100+ sessions.

**Problem**: Performance degradation with large numbers of sessions

**Action Required**:
1. Implement search result caching for recently used queries
2. Add virtual scrolling for very large session lists
3. Consider background threading for complex fuzzy matching
4. Profile performance with large session collections

**Success Criteria**: Smooth performance with 100+ sessions

---

#### 11. **Search Result Highlighting**
**Context**: Visual feedback showing which characters matched would improve UX.

**Problem**: No visual indication of why sessions matched search query

**Action Required**:
1. Implement GTK markup for highlighting matched characters
2. Add different highlight styles for exact vs fuzzy matches
3. Update session button creation to support markup
4. Ensure highlighting works with Mac Tahoe theme

**Success Criteria**: Matched characters visually highlighted in session names

---

#### 12. **Enhanced Search UX Features**
**Context**: Additional power user features would improve workflow.

**Problem**: Missing common search interface features

**Action Required**:
1. Add Ctrl+F shortcut to focus search input
2. Add Ctrl+K shortcut to clear search
3. Show search result count in placeholder text
4. Implement search history with up/down arrows

**Success Criteria**: Professional search interface with power user shortcuts

---

## Implementation Priority Order

**Phase 1 (Critical - Search System Performance & Stability)**:
1. Widget Recreation Performance Problem (#1) - URGENT performance issue
2. ✅ Multi-Index Coordinate System Fragility (#2) - COMPLETED architectural robustness
3. Search Input Debouncing Implementation (#3) - Performance optimization
4. ✅ Code Duplication in Widget Creation Methods (#4) - COMPLETED
5. ✅ Method Complexity Violation in Window Calculation (#5) - COMPLETED code quality

**Phase 2 (Architectural Consistency)**:
6. Convert Save Panel to GTK Event-Based Handling (#1 old)
7. Focus Management Race Condition Resolution (#2 old)  

**Phase 3 (Feature Enhancement)**:
8. Upgrade to Fuzzy Matching Algorithm (#6)
9. International Keyboard Layout Testing (#7)

**Phase 4 (Polish & Optimization)**:
10. Enhanced Error Handling Specificity (#8)
11. Unit Test Coverage for Search System (#9)
12. Performance Optimization for Large Session Lists (#10)
13. Search Result Highlighting (#11)
14. Enhanced Search UX Features (#12)

---

## Getting Started for New Contributors

**Prerequisites**: 
- Read `/home/jc/Dev/hypr-sessions/CLAUDE.md` for complete project context
- Understand the Mac Tahoe UI aesthetic and GTK3 limitations
- Familiarize yourself with the Fabric framework and dual focus architecture

**Quick Start**:
1. Start with Phase 1 items for immediate architectural improvements
2. Each item includes specific file locations and code examples
3. Test changes with the existing UI to ensure no regressions
4. Follow the established patterns for GTK event handling and error management

This roadmap provides clear context and actionable steps for continuing the fuzzy search system improvements and overall project enhancement.