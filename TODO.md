# Hyprland Session Manager - TODO

## Outstanding Improvements

### Critical Priority (Search System Performance & Architecture)

#### 1. **Widget Recreation Performance Problem** ⚠️ **PARTIALLY RESOLVED - NEEDS CLEANUP**

**Status**: Session visibility windowing system implemented and working correctly. However, code review identified this is still a performance concern requiring immediate attention.

**Code Review Findings (Grade: D for Performance)**:
- Widget recreation on every keystroke still occurring (lines 319-350 in browse_panel.py)
- Extensive debug print statements in production code (lines 483-590) indicating debugging difficulties
- Missing search debouncing causing unnecessary UI updates during rapid typing

**Immediate Actions Required**:
1. **Remove debug print statements** from production code (lines 483-590, 869-906)
2. **Implement search debouncing** (300ms delay) to prevent excessive UI updates
3. **Simplify widget pooling complexity** - current implementation adds 550+ lines without clear necessity


---

#### 2. **Session Visibility Windowing System** ✅ **FIXED - 2025-08-27**

**Problem Solved**: All 18 sessions were displaying simultaneously instead of windowed view (5 of N sessions) with scroll indicators.

**Root Cause**: During fuzzy search implementation, `_create_session_widgets()` was changed to iterate over `self.filtered_sessions` (all sessions) instead of `self.get_visible_sessions()` (windowed subset).

**Solution Applied**:
- Fixed widget creation to use `visible_sessions = self.get_visible_sessions()`
- Added missing constants: `VISIBLE_WINDOW_SIZE = 5`, `ARROW_UP = "\uf077"`, `ARROW_DOWN = "\uf078"`
- Restored scroll indicators for sessions above/below current window

**Code Location**: `/home/jc/Dev/hypr-sessions/fabric-ui/widgets/browse_panel.py:319-350`

**Verification**: Debug logging confirmed correct behavior - exactly 5 sessions displayed with dynamic window scrolling during navigation.

---

#### 3. **Search Input Debouncing Implementation** 
**Context**: Code review identified this as critical missing optimization (Grade D for Performance).

**Problem**: Every character typed triggers immediate UI updates, causing performance issues during rapid typing.

**Code Review Evidence**: Missing debouncing leads to excessive UI updates and potential character loss during expensive widget recreation operations.

**Action Required**:
1. **Implement 300ms Debounce Timer** (code review recommendation)
2. **Cancel Previous Timers**: Prevent multiple pending operations  
3. **Remove widget recreation on every keystroke**
4. **Performance Testing**: Measure improvement with rapid typing

**Success Criteria**: Smooth typing experience without UI lag during rapid input

---

#### 4. **Multi-Index Coordinate System Fragility** ✅ **COMPLETED**

**Implementation**: Replaced 4-index coordinate system with single `selected_session_name`, eliminated coordinate conversion logic and race conditions. Navigation uses direct name equality checks.

---

### IMMEDIATE PRIORITY (Code Review Cleanup)

#### 5. **Production Debug Code Removal** 🚨 **CRITICAL - GRADE F**

**Problem**: Extensive debug print statements throughout production code (identified in comprehensive code review).

**Impact**: Production code contains debugging artifacts that should not be in final releases.

**Locations to Clean**:
- Lines 483-590: Widget pooling debug statements in `browse_panel.py`
- Lines 869-906: Session list debug output throughout UI operations
- Various `print(f"DEBUG...")` statements scattered through the codebase

**Action Required**:
1. **Remove all debug print statements** from production code
2. **Replace with proper logging** where necessary using debug_logger system
3. **Verify no debug output in normal operation**

**Success Criteria**: Clean production code with no debug print statements visible during normal operation.

---

#### 6. **Method Complexity Reduction** ✅ **COMPLETED - 2025-08-27**

**Problem Solved**: Transformed complex monolithic methods into focused, maintainable components following Single Responsibility Principle.

**Implementation Completed**:
- **`_create_sessions_widget_list()`**: 64 lines → 12 lines (81% reduction) with 6 focused helpers
- **`_handle_navigation_event()`**: 52 lines → 8 lines (85% reduction) with clean delegation
- **Parameter validation**: Added comprehensive validation with clear error messages and examples
- **Documentation enhancement**: Complete Args/Returns/Examples/Raises documentation

**Results Achieved**:
- **Grade A- refactoring** (code reviewer assessment) - "exemplary transformation"
- **Single responsibility per method** - each helper has one clear purpose
- **Self-documenting code** - method names clearly indicate functionality
- **Improved testability** - each helper can be unit tested independently
- **Enhanced maintainability** - future changes isolated to specific concerns

**Code Quality Impact**: Established template methodology for addressing method complexity throughout project

**Date Completed**: August 27, 2025

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

**IMMEDIATE PHASE (Code Review Cleanup - Required Before Further Development)**:
1. 🚨 Production Debug Code Removal (#5) - CRITICAL Grade F issue
2. ✅ Method Complexity Reduction (#6) - COMPLETED Grade A- refactoring 
3. Search Input Debouncing Implementation (#3) - Performance Grade D issue

**Phase 1 (Performance & Stability Foundation)**:
4. ✅ Session Visibility Windowing System (#2) - COMPLETED 2025-08-27
5. ✅ Multi-Index Coordinate System Fragility (#4) - COMPLETED architectural robustness
6. ⚠️ Widget Recreation Performance Problem (#1) - PARTIALLY RESOLVED (needs cleanup)
7. ✅ Code Duplication in Widget Creation Methods - COMPLETED
8. ✅ Method Complexity Violation in Window Calculation - COMPLETED code quality

**Phase 2 (Architectural Consistency)**:
9. Convert Save Panel to GTK Event-Based Handling
10. Focus Management Race Condition Resolution  

**Phase 3 (Feature Enhancement)**:
11. Upgrade to Fuzzy Matching Algorithm
12. International Keyboard Layout Testing

**Phase 4 (Polish & Optimization)**:
13. Enhanced Error Handling Specificity
14. Unit Test Coverage for Search System
15. Performance Optimization for Large Session Lists
16. Search Result Highlighting
17. Enhanced Search UX Features

---

## Code Review Impact Summary

**Overall Project Grade: B+** - Strong architecture requiring immediate cleanup

**Critical Actions Required** (based on comprehensive code review):
- Remove all production debug code (Grade F issue)
- Simplify widget pooling complexity 
- Add search debouncing for performance
- Reduce method complexity in key functions

**Architectural Strengths Identified**:
- Revolutionary dual focus search system (Grade A)
- Excellent separation of concerns (Grade A-)
- Professional GTK3 integration (Grade A-)
- Robust backend communication (Grade A-)

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