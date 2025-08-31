# Hyprland Session Manager - TODO

## **TODO Management Rule**

**IMPORTANT**: Always delete completed todos immediately after implementation to maintain clear focus on remaining work. Mark items as ✅ COMPLETED with date only during implementation, then remove them entirely once documented in CLAUDE.md.

---

## Outstanding Improvements

### **IMMEDIATE CRITICAL SECURITY FIX** ⚠️

#### **0. Fix Path Traversal Vulnerability in Session Recovery** 
**Priority**: CRITICAL SECURITY - Must fix before any other work
**Context**: Code review identified critical security vulnerability in session recovery (Grade C+ → needs immediate upgrade to production-ready Grade A-).

**Problem**: `/home/jc/Dev/hypr-sessions/commands/recover.py` lines 47 and 58 contain path traversal vulnerability:
```python
# VULNERABLE: String manipulation on untrusted input
original_name = archived_session_name.split('-')[0] if '-' in archived_session_name else archived_session_name
```

**Attack Vector**: Malicious archive names like `../../../etc-passwd-20250831-123456` could compromise system security.

**Action Required**: Implement secure name extraction with validation (see ARCHIVE_FEATURE_IMPROVEMENTS_TODO.md for complete implementation plan)

**Success Criteria**: All extracted names validated through SessionValidator.validate_session_name() with safe fallbacks

---

### Critical Priority (Performance & Architecture)

#### 1. **Search Input Debouncing Implementation** 
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

### High Priority (Architectural Consistency)

#### 2. **Convert Save Panel to GTK Event-Based Handling**
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

#### 3. **Focus Management Race Condition Resolution**
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

### Medium Priority (Feature Enhancements)

#### 4. **Upgrade to Fuzzy Matching Algorithm**
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

#### 5. **International Keyboard Layout Testing**
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

#### 6. **Enhanced Error Handling Specificity** 
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

#### 7. **Unit Test Coverage for Search System**
**Context**: Complex search and focus logic lacks automated test coverage.

**Problem**: No automated testing for critical search functionality

**Action Required**:
1. Create test suite for character detection logic
2. Add tests for event routing decisions
3. Mock GTK events for navigation key testing  
4. Test search filtering with various edge cases

**Success Criteria**: Comprehensive test coverage for search system components

---

#### 8. **Performance Optimization for Large Session Lists**
**Context**: Current O(n) search could be optimized for 100+ sessions.

**Problem**: Performance degradation with large numbers of sessions

**Action Required**:
1. Implement search result caching for recently used queries
2. Add virtual scrolling for very large session lists
3. Consider background threading for complex fuzzy matching
4. Profile performance with large session collections

**Success Criteria**: Smooth performance with 100+ sessions

---

#### 9. **Search Result Highlighting**
**Context**: Visual feedback showing which characters matched would improve UX.

**Problem**: No visual indication of why sessions matched search query

**Action Required**:
1. Implement GTK markup for highlighting matched characters
2. Add different highlight styles for exact vs fuzzy matches
3. Update session button creation to support markup
4. Ensure highlighting works with Mac Tahoe theme

**Success Criteria**: Matched characters visually highlighted in session names

---

#### 10. **Enhanced Search UX Features**
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

**IMMEDIATE PHASE (Critical Security Issues)**:
0. **Fix Path Traversal Vulnerability in Session Recovery (#0) - CRITICAL SECURITY VULNERABILITY**

**CRITICAL PHASE (Performance Issues)**:
1. Search Input Debouncing Implementation (#1) - Performance Grade D issue

**Phase 1 (Architectural Consistency)**:
2. Convert Save Panel to GTK Event-Based Handling (#2)
3. Focus Management Race Condition Resolution (#3)  

**Phase 2 (Feature Enhancement)**:
4. Upgrade to Fuzzy Matching Algorithm (#4)
5. International Keyboard Layout Testing (#5)

**Phase 3 (Polish & Optimization)**:
6. Enhanced Error Handling Specificity (#6)
7. Unit Test Coverage for Search System (#7)
8. Performance Optimization for Large Session Lists (#8)
9. Search Result Highlighting (#9)
10. Enhanced Search UX Features (#10)

---

## Code Quality Context

**Current Project Status**: The project has successfully completed major architectural improvements including:

- **Modular Architecture**: 68% size reduction in browse_panel.py through 5-component extraction
- **Method Complexity Resolution**: Transformed complex methods into focused, maintainable components  
- **Widget Pooling System**: 95%+ reuse efficiency with GTK3-compliant lifecycle management
- **Enhanced Key Debugging**: Complete human-readable debugging system with event flow tracing
- **Production Debug Cleanup**: All raw print statements converted to controlled debug logging
- **Multi-Index Elimination**: Replaced fragile coordinate systems with robust name-based selection

**Overall Architecture Grade**: A- (code reviewer assessment) - Excellent component separation with focused remaining improvements.

---

## Getting Started for New Contributors

**Prerequisites**: 
- Read `/home/jc/Dev/hypr-sessions/CLAUDE.md` for complete project context
- Understand the Mac Tahoe UI aesthetic and GTK3 limitations
- Familiarize yourself with the Fabric framework and dual focus architecture

**Quick Start**:
1. Start with Critical Priority items for immediate performance improvements
2. Each item includes specific file locations and code examples
3. Test changes with the existing UI to ensure no regressions
4. Follow the established patterns for GTK event handling and error management

This roadmap provides clear context and actionable steps for continuing the project improvements with focus on the most impactful remaining enhancements.