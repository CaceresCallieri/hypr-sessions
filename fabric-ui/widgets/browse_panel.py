"""
Browse Panel Widget for Hypr Sessions Manager
"""

import sys
from pathlib import Path

import gi
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.label import Label

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk

# Add parent directory to path for clean imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import constants and backend client
from constants import (
    BROWSING_STATE,
    DELETE_CONFIRM_STATE,
    DELETE_ERROR_STATE,
    DELETE_SUCCESS_STATE,
    DELETING_STATE,
    RESTORE_CONFIRM_STATE,
    RESTORE_ERROR_STATE,
    RESTORE_SUCCESS_STATE,
    RESTORING_STATE,
)

from utils import BackendClient
from utils.debug_logger import get_debug_logger

# Import operation classes
from .operations import DeleteOperation, RestoreOperation


class BrowsePanelWidget(Box):
    """Panel widget for browsing and selecting sessions"""

    def __init__(self, session_utils, on_session_clicked=None):
        super().__init__(orientation="vertical", spacing=10, name="browse-panel")

        self.session_utils = session_utils
        self.on_session_clicked = on_session_clicked

        # Initialize debug logger
        self.debug_logger = get_debug_logger()
        if self.debug_logger:
            self.debug_logger.debug_session_lifecycle("ui_startup", "browse_panel", "initializing")

        # Backend client for operations
        try:
            self.backend_client = BackendClient()
            if self.debug_logger:
                self.debug_logger.debug_backend_call("init", None, 0, True, {"status": "available"})
        except FileNotFoundError as e:
            if self.debug_logger:
                self.debug_logger.debug_backend_call("init", None, 0, False, {"error": str(e)})
            self.backend_client = None

        # Initialize operation handlers
        self.delete_operation = DeleteOperation(self, self.backend_client)
        self.restore_operation = RestoreOperation(self, self.backend_client)

        # Selection state management
        self.all_session_names = []  # Complete list of all sessions
        self.filtered_sessions = []  # Filtered session names based on search
        self.session_buttons = []  # List of currently visible session button widgets
        self.selected_session_name = None  # Single source of truth for selection
        
        # Widget pool for performance optimization
        self.session_button_pool = {}  # session_name -> Button widget mapping
        self.active_session_buttons = []  # Currently visible button widgets
        
        # Performance tracking (Phase 2 + 3)
        self._widget_creation_count = 0  # Count of new widgets created per update
        self._widget_reuse_count = 0     # Count of widgets reused per update
        self._property_update_count = 0  # Count of actual property changes (Phase 3)
        self._property_skip_count = 0    # Count of skipped updates (Phase 3)

        # Search functionality
        self.search_input = None  # GTK Entry widget for search
        self.search_query = ""  # Current search text

        # Scrollable window management
        self.VISIBLE_WINDOW_SIZE = (
            5  # Maximum sessions to display at once (configurable)
        )
        self.visible_start_index = (
            0  # First visible session index for scrolling display
        )

        # Scroll indicator symbols (Nerd Font triangles)
        self.ARROW_UP = "\uf077"  # nf-fa-chevron_down
        self.ARROW_DOWN = "\uf078"  # nf-fa-chevron_up

        # Widget pool configuration constants
        self.WIDGET_POOL_MAINTENANCE_THRESHOLD = 20
        self.WIDGET_POOL_MAX_SIZE = 50
        self.DEBUG_ENABLED = False  # Set to True for widget pool debugging

        # Panel state management
        self.state = BROWSING_STATE  # Browse panel state management using constants

        # Create panel content
        self._create_content()

    def _is_ui_navigation_key(self, keyval):
        """Check if keyval represents a UI navigation key using GTK constants"""
        ui_navigation = {
            # Session navigation
            Gdk.KEY_Up,
            Gdk.KEY_Down,
            # Actions
            Gdk.KEY_Return,
            Gdk.KEY_KP_Enter,  # Restore session
            Gdk.KEY_Escape,  # Clear search
            # Panel switching
            Gdk.KEY_Tab,
            Gdk.KEY_Left,
            Gdk.KEY_Right,
        }

        return keyval in ui_navigation

    def should_route_to_search(self, event):
        """Determine if event should route to search input using GTK event properties"""
        keyval = event.keyval

        # UI navigation keys go to navigation handlers
        is_navigation = self._is_ui_navigation_key(keyval)
        if is_navigation:
            if self.debug_logger:
                self.debug_logger.debug_key_detection(
                    keyval, "navigation", False, False,
                    {"routing_decision": "navigation_handler"}
                )
            return False

        # Handle modifier combinations (Ctrl+key, Alt+key, etc.)
        has_modifiers = bool(event.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK))
        if has_modifiers:
            if self.debug_logger:
                self.debug_logger.debug_key_detection(
                    keyval, "modifier_combo", False, has_modifiers,
                    {"routing_decision": "blocked", "modifiers": event.state}
                )
            return False  # Don't route modifier combinations to search

        # Everything else goes to search input for filtering/editing
        # This includes: letters, numbers, symbols, backspace, delete, etc.
        if self.debug_logger:
            self.debug_logger.debug_key_detection(
                keyval, "printable", True, has_modifiers,
                {"routing_decision": "search_input"}
            )
        return True

    def _create_content(self):
        """Create the browse panel content based on current state"""
        print(f"DEBUG CREATE CONTENT: Creating UI for state '{self.state}' - Widget pool size: {len(self.session_button_pool)}")
        
        # DEBUG: Check widget pool health before recreation
        if hasattr(self, 'session_button_pool'):
            print(f"DEBUG WIDGET POOL: Current pool sessions: {list(self.session_button_pool.keys())}")
            for session_name, button in self.session_button_pool.items():
                try:
                    current_label = button.get_label()
                    print(f"DEBUG POOL STATE: '{session_name}' -> '{current_label}'")
                except Exception as e:
                    print(f"DEBUG POOL ERROR: '{session_name}' -> Exception: {e}")
        
        if self.state == BROWSING_STATE:
            self.children = self._create_browsing_ui()
        elif self.state == DELETE_CONFIRM_STATE:
            self.children = self.delete_operation.create_confirmation_ui()
        elif self.state == DELETING_STATE:
            self.children = self.delete_operation.create_progress_ui()
        elif self.state == DELETE_SUCCESS_STATE:
            self.children = self.delete_operation.create_success_ui()
        elif self.state == DELETE_ERROR_STATE:
            self.children = self.delete_operation.create_error_ui()
        elif self.state == RESTORE_CONFIRM_STATE:
            self.children = self.restore_operation.create_confirmation_ui()
        elif self.state == RESTORING_STATE:
            self.children = self.restore_operation.create_progress_ui()
        elif self.state == RESTORE_SUCCESS_STATE:
            self.children = self.restore_operation.create_success_ui()
        elif self.state == RESTORE_ERROR_STATE:
            self.children = self.restore_operation.create_error_ui()

    def _create_browsing_ui(self):
        """Create the normal browsing UI"""
        # Get and create session buttons first
        sessions_container = self._create_sessions_list()

        # Sessions list section header with filtered/total count
        total_sessions = len(self.all_session_names)
        filtered_count = len(self.filtered_sessions)
        if self.search_query:
            header_text = f"Available Sessions ({filtered_count}/{total_sessions}):"
        else:
            header_text = f"Available Sessions ({total_sessions}):"
        sessions_header = Label(text=header_text, name="sessions-header")
        sessions_header.set_markup(f"<span weight='bold'>{header_text}</span>")

        # Create search input widget
        search_input = self._create_search_input()

        return [sessions_header, search_input, sessions_container]

    def _create_search_input(self):
        """Create the search input widget with permanent focus"""
        if not self.search_input:
            self.search_input = Entry(
                text=self.search_query,
                placeholder_text="🔍 Search sessions...",
                name="session-search-input",
            )
            # Connect search input change event
            self.search_input.connect("changed", self._on_search_changed)

            # Ensure search input can receive focus and maintains it
            self.search_input.set_can_focus(True)

        # Focus will be set by delayed focus setup in main session manager
        return self.search_input

    def _on_search_changed(self, entry):
        """Handle search input text changes"""
        import time
        start_time = time.time()
        
        self.search_query = entry.get_text().strip()
        self._update_filtered_sessions()
        self._update_session_list_only()
        
        # Log search operation performance
        timing_ms = (time.time() - start_time) * 1000
        if self.debug_logger:
            self.debug_logger.debug_search_operation(
                "filter_update", self.search_query, len(self.filtered_sessions), timing_ms
            )

    def _update_filtered_sessions(self):
        """Update filtered sessions based on current search query"""
        import time
        start_time = time.time()
        
        if not self.search_query:
            # No search query - show all sessions
            self.filtered_sessions = self.all_session_names.copy()
            filter_type = "show_all"
        else:
            # Filter sessions with case-insensitive substring matching
            query_lower = self.search_query.lower()
            self.filtered_sessions = [
                session
                for session in self.all_session_names
                if query_lower in session.lower()
            ]
            filter_type = "substring_match"
        
        # Log filtering performance
        timing_ms = (time.time() - start_time) * 1000
        if self.debug_logger:
            self.debug_logger.debug_search_operation(
                "filtering", self.search_query, len(self.filtered_sessions), timing_ms,
                {"filter_type": filter_type, "total_sessions": len(self.all_session_names)}
            )

        # Reset selection if current selection is not in filtered results
        if self.filtered_sessions:
            if self.selected_session_name not in self.filtered_sessions:
                # Reset to first filtered session using name-based selection
                self.selected_session_name = self.filtered_sessions[0]
        else:
            # No filtered results - clear selection
            self.selected_session_name = None

    def clear_search(self):
        """Clear the search input (maintains permanent focus)"""
        if self.search_input:
            self.search_input.set_text("")
            self.search_query = ""
            self._update_filtered_sessions()
            self._update_session_list_only()

    def _create_sessions_list(self):
        """Create the sessions list container using shared widget creation logic"""
        # Update global session state
        all_sessions = self.session_utils.get_available_sessions()
        self.all_session_names = all_sessions
        self.session_buttons = []

        # Initialize filtered sessions and selection on first load
        if not hasattr(self, "filtered_sessions") or not self.filtered_sessions:
            self._update_filtered_sessions()
            # Set initial selection to first session if available
            if self.filtered_sessions and not self.selected_session_name:
                self.selected_session_name = self.filtered_sessions[0]

        # Use shared widget creation logic
        session_widgets = self._create_sessions_widget_list()

        return Box(
            orientation="vertical",
            spacing=5,
            name="sessions-container",
            children=session_widgets,
        )

    def _create_session_button(self, session_name, is_selected=False):
        """Factory method with widget reuse - creates or reuses session buttons (Phase 2)"""
        # Phase 2+3: Check pool first for existing widget
        if session_name in self.session_button_pool:
            button = self.session_button_pool[session_name]
            
            
            # Phase 3: Use comprehensive property update with change detection
            self._update_button_properties(button, session_name, is_selected)
            # Track reuse for performance monitoring
            self._widget_reuse_count += 1
            
            # Debug widget pool reuse
            if self.debug_logger:
                self.debug_logger.debug_widget_pool_operation(
                    "reuse", session_name, reused=True, 
                    pool_size=len(self.session_button_pool)
                )
            return button
        
        # Phase 2: Only create new widget if not in pool
        button = Button(
            label=f"• {session_name}",
            name="session-button",  # Base CSS class
            on_clicked=lambda *_: self._handle_session_clicked(session_name),
        )

        # Make button non-focusable to prevent focus stealing from search input
        button.set_can_focus(False)

        # Add selected class if this is the selected session
        if is_selected:
            button.get_style_context().add_class("selected")

        # Store in widget pool for future reuse
        self.session_button_pool[session_name] = button
        
        # Track creation for performance monitoring (Phase 2)
        self._widget_creation_count += 1
        
        # Debug widget pool creation
        if self.debug_logger:
            self.debug_logger.debug_widget_pool_operation(
                "create", session_name, created=True, 
                pool_size=len(self.session_button_pool)
            )
        
        return button

    def _force_refresh_widget_pool(self):
        """Force refresh all pooled widgets to fix state transition issues"""
        if self.debug_logger:
            self.debug_logger.debug_widget_pool_maintenance(
                "force_refresh", len(self.session_button_pool), len(self.session_button_pool),
                {"trigger": "state_transition", "reason": "fix_button_labels"}
            )
        
        # Force update all buttons in pool to ensure properties are current
        invalid_sessions = []
        for session_name, button in self.session_button_pool.items():
            try:
                # DEBUG: Check button state before refresh
                current_label = button.get_label()
                expected_label = f"• {session_name}"
                
                print(f"DEBUG WIDGET STATE: Session '{session_name}' - Current: '{current_label}' Expected: '{expected_label}'")
                
                # Check if button widget is valid
                if not hasattr(button, 'get_label') or not hasattr(button, 'set_label'):
                    print(f"DEBUG WIDGET ERROR: Button for '{session_name}' missing label methods")
                    invalid_sessions.append(session_name)
                    continue
                
                # Try to update label
                if current_label != expected_label:
                    print(f"DEBUG WIDGET FIX: Updating label for '{session_name}' from '{current_label}' to '{expected_label}'")
                    button.set_label(expected_label)
                    
                    # Verify the fix worked
                    new_label = button.get_label()
                    if new_label != expected_label:
                        print(f"DEBUG WIDGET FAILURE: Label update failed for '{session_name}' - still shows '{new_label}'")
                    else:
                        print(f"DEBUG WIDGET SUCCESS: Label updated successfully for '{session_name}'")
                
                # Reset selection state - will be properly set during widget creation
                style_context = button.get_style_context()
                if style_context.has_class("selected"):
                    style_context.remove_class("selected")
                    
            except (AttributeError, RuntimeError) as e:
                print(f"DEBUG WIDGET EXCEPTION: Button for '{session_name}' threw exception: {e}")
                invalid_sessions.append(session_name)
                
        # Remove invalid widgets
        for session_name in invalid_sessions:
            print(f"DEBUG WIDGET CLEANUP: Removing invalid button for '{session_name}'")
            del self.session_button_pool[session_name]
            if self.debug_logger:
                self.debug_logger.debug_widget_pool_maintenance(
                    "remove_invalid", len(self.session_button_pool) + len(invalid_sessions), len(self.session_button_pool),
                    {"session": session_name, "total_removed": len(invalid_sessions)}
                )

    def _clear_widget_pool_for_state_transition(self, from_state):
        """Clear widget pool to fix GTK rendering issues during state transitions"""
        pool_size_before = len(self.session_button_pool)
        
        print(f"DEBUG STATE FIX: Clearing widget pool due to state transition from '{from_state}' - {pool_size_before} widgets")
        
        # Properly destroy all pooled widgets to prevent GTK resource leaks
        for session_name, button in self.session_button_pool.items():
            try:
                if hasattr(button, 'destroy'):
                    button.destroy()
                    print(f"DEBUG STATE FIX: Destroyed widget for '{session_name}'")
                else:
                    print(f"DEBUG STATE FIX: Widget for '{session_name}' has no destroy method")
            except Exception as e:
                print(f"DEBUG STATE FIX: Error destroying widget for '{session_name}': {e}")
        
        # Clear the pool completely - forces fresh widget creation
        self.session_button_pool.clear()
        self.active_session_buttons.clear()
        
        print(f"DEBUG STATE FIX: Widget pool cleared - now {len(self.session_button_pool)} widgets")
        
        if self.debug_logger:
            self.debug_logger.debug_widget_pool_maintenance(
                "clear_for_state_transition", pool_size_before, 0,
                {"from_state": from_state, "reason": "fix_gtk_rendering"}
            )

    def _create_sessions_widget_list(self):
        """Create complete widget list: scroll indicators + session buttons"""
        # Reset performance counters for this update (Phase 2+3)
        self._widget_creation_count = 0
        self._widget_reuse_count = 0
        self._property_update_count = 0
        self._property_skip_count = 0
        
        # Handle empty sessions case
        if not self.filtered_sessions:
            if not self.all_session_names:
                message = "No sessions found"
            else:
                message = f"No sessions match '{self.search_query}'"

            no_sessions_label = Label(text=message, name="no-sessions-label")
            no_sessions_label.set_markup(f"<span style='italic'>{message}</span>")
            return [no_sessions_label]

        # Ensure we have a valid selection
        if not self.selected_session_name or self.selected_session_name not in self.filtered_sessions:
            self.selected_session_name = self.filtered_sessions[0]

        # Get visible sessions and selected session for current window
        visible_sessions = self.get_visible_sessions()
        selected_session_name = self.get_selected_session()

        # Create complete widget list
        widgets = []

        # Always reserve space for "more sessions above" indicator
        more_above = self._create_scroll_indicator(
            self.ARROW_UP, self.has_sessions_above()
        )
        widgets.append(more_above)

        # Clear previous session buttons list (Phase 1: Preparation for pooling)
        self.session_buttons = []
        
        # Create session buttons for visible sessions using factory method
        for session_name in visible_sessions:
            is_selected = session_name == selected_session_name
            button = self._create_session_button(session_name, is_selected)
            self.session_buttons.append(button)
            widgets.append(button)
        
        # Track currently active buttons for pool management (Phase 1: Infrastructure)
        self.active_session_buttons = self.session_buttons.copy()
        
        # Phase 3: Periodic pool maintenance
        if len(self.session_button_pool) > self.WIDGET_POOL_MAINTENANCE_THRESHOLD:  # Only optimize when pool gets large
            self._validate_widget_pool_integrity()
            self._optimize_widget_pool_size()
        
        # Debug pool state (Phase 1-3: Remove this in production)
        if hasattr(self, '_debug_pool_enabled') and self._debug_pool_enabled:
            self._debug_widget_pool_state()

        # Always reserve space for "more sessions below" indicator
        more_below = self._create_scroll_indicator(
            self.ARROW_DOWN, self.has_sessions_below()
        )
        widgets.append(more_below)

        return widgets

    def _handle_session_clicked(self, session_name):
        """Handle session button click"""
        print(f"Session clicked: {session_name}")
        if self.on_session_clicked:
            self.on_session_clicked(session_name)

    def _get_selected_filtered_index(self):
        """Get index of selected session in filtered results, or 0 if none"""
        selected_session = self.get_selected_session()
        if selected_session and selected_session in self.filtered_sessions:
            return self.filtered_sessions.index(selected_session)
        return 0

    def _calculate_optimal_window_start(self, selected_index):
        """Calculate ideal window start position for given selection"""
        window_end = self.visible_start_index + self.VISIBLE_WINDOW_SIZE

        if selected_index < self.visible_start_index:
            # Selection is above visible window
            return selected_index
        elif selected_index >= window_end:
            # Selection is below visible window
            return selected_index - self.VISIBLE_WINDOW_SIZE + 1
        else:
            # Selection is within current window - no change needed
            return self.visible_start_index

    def _clamp_to_valid_bounds(self, window_start, total_sessions):
        """Ensure window position stays within valid bounds"""
        clamped = min(window_start, total_sessions - self.VISIBLE_WINDOW_SIZE)
        return max(0, clamped)

    def _get_visible_indices_range(self, total_sessions):
        """Generate list of visible session indices"""
        window_end = min(
            self.visible_start_index + self.VISIBLE_WINDOW_SIZE, total_sessions
        )
        return list(range(self.visible_start_index, window_end))

    def calculate_visible_window(self):
        """Calculate which sessions should be visible based on current selection and filtering"""
        total_filtered = len(self.filtered_sessions)

        # Early return for simple case - all sessions fit in window
        if total_filtered <= self.VISIBLE_WINDOW_SIZE:
            self.visible_start_index = 0
            return list(range(total_filtered))

        # Orchestrate the calculation using focused helpers
        selected_index = self._get_selected_filtered_index()
        optimal_start = self._calculate_optimal_window_start(selected_index)
        self.visible_start_index = self._clamp_to_valid_bounds(
            optimal_start, total_filtered
        )

        # Note: selected_local_index no longer needed with name-based selection

        return self._get_visible_indices_range(total_filtered)

    def get_visible_sessions(self):
        """Get the list of sessions that should be currently visible"""
        visible_indices = self.calculate_visible_window()
        return [self.filtered_sessions[i] for i in visible_indices]

    def has_sessions_above(self):
        """Check if there are sessions above the visible window"""
        return self.visible_start_index > 0

    def has_sessions_below(self):
        """Check if there are sessions below the visible window"""
        total_filtered = len(self.filtered_sessions)
        return (self.visible_start_index + self.VISIBLE_WINDOW_SIZE) < total_filtered

    def _create_scroll_indicator(self, arrow_symbol, show_condition):
        """Create a scroll indicator with reserved space"""
        indicator = Label(text="", name="scroll-indicator")
        if show_condition:
            indicator.set_markup(arrow_symbol)
        else:
            indicator.set_markup("")  # Empty but reserves space
        return indicator

    def refresh(self):
        """Refresh the sessions list"""
        self._create_content()

    def select_next(self):
        """Select the next session with intelligent scrolling"""
        if not self.filtered_sessions:
            return

        # Navigate using name-based selection - no coordinate conversion
        current_idx = self._get_current_filtered_position()
        next_idx = (current_idx + 1) % len(self.filtered_sessions)
        
        old_session = self.selected_session_name
        self.selected_session_name = self.filtered_sessions[next_idx]
        
        # Debug navigation
        if self.debug_logger:
            self.debug_logger.debug_navigation_operation(
                "select_next", old_session, self.selected_session_name, "arrow_key",
                {"current_idx": current_idx, "next_idx": next_idx, "wraparound": next_idx == 0}
            )

        # Refresh display to show new selection and handle scrolling
        self._update_session_list_only()

        # Ensure search input maintains focus after navigation
        self._ensure_search_focus()

    def select_previous(self):
        """Select the previous session with intelligent scrolling"""
        if not self.filtered_sessions:
            return

        # Navigate using name-based selection - no coordinate conversion
        current_idx = self._get_current_filtered_position()
        prev_idx = (current_idx - 1) % len(self.filtered_sessions)
        
        old_session = self.selected_session_name
        self.selected_session_name = self.filtered_sessions[prev_idx]
        
        # Debug navigation
        if self.debug_logger:
            self.debug_logger.debug_navigation_operation(
                "select_previous", old_session, self.selected_session_name, "arrow_key",
                {"current_idx": current_idx, "prev_idx": prev_idx, "wraparound": prev_idx == len(self.filtered_sessions) - 1}
            )

        # Refresh display to show new selection and handle scrolling
        self._update_session_list_only()
        
        # Ensure search input maintains focus after navigation
        self._ensure_search_focus()

    def _ensure_search_focus(self):
        """Ensure search input maintains focus for continuous typing"""
        try:
            if self.search_input and not self.search_input.has_focus():
                self.search_input.grab_focus()
                if self.debug_logger:
                    self.debug_logger.debug_focus_recovery(
                        "navigation", "search_input", True, {"trigger": "ensure_search_focus"}
                    )
        except Exception as e:
            if self.debug_logger:
                self.debug_logger.debug_focus_recovery(
                    "navigation", "search_input", False, 
                    {"trigger": "ensure_search_focus", "error": str(e)}
                )

    def update_display(self):
        """Update the display to show current selection and scroll position"""
        # Recalculate visible window and refresh content
        self._create_content()

    def _update_session_list_only(self):
        """Update only the session list while preserving persistent widgets like search input"""
        if self.state != BROWSING_STATE:
            # Only apply selective updates in browsing state
            self.update_display()
            return

        # Find the sessions container widget to update its contents
        sessions_container = None

        for child in self.children:
            if hasattr(child, "get_name") and child.get_name() == "sessions-container":
                sessions_container = child
                break

        if sessions_container is not None:
            # Update the sessions header with new count
            total_sessions = len(self.all_session_names)
            filtered_count = len(self.filtered_sessions)
            if self.search_query:
                header_text = f"Available Sessions ({filtered_count}/{total_sessions}):"
            else:
                header_text = f"Available Sessions ({total_sessions}):"

            # Find and update sessions header
            for child in self.children:
                if hasattr(child, "get_name") and child.get_name() == "sessions-header":
                    child.set_markup(f"<span weight='bold'>{header_text}</span>")
                    break

            # Create new session widgets using shared logic
            new_session_widgets = self._create_sessions_widget_list()

            # Update only the sessions container contents, not the container itself
            sessions_container.children = new_session_widgets
        else:
            # Fallback to full update if we can't find sessions container
            self.update_display()

    def get_selected_session(self):
        """Get the name of the currently selected session"""
        return self.selected_session_name

    def _get_current_filtered_position(self):
        """Get position of selected session in filtered list, default to 0"""
        if (
            self.selected_session_name
            and self.selected_session_name in self.filtered_sessions
        ):
            return self.filtered_sessions.index(self.selected_session_name)
        return 0

    def is_session_selected(self, session_name):
        """Check if given session is currently selected"""
        return session_name == self.selected_session_name
    
    def _debug_widget_pool_state(self):
        """Debug helper to inspect widget pool state (Phase 2: With reuse tracking)"""
        if not self.DEBUG_ENABLED:
            return
        pool_size = len(self.session_button_pool)
        active_count = len(self.active_session_buttons)
        total_sessions = len(self.all_session_names)
        
        print(f"DEBUG Widget Pool: {pool_size} pooled, {active_count} active, {total_sessions} total sessions")
        
        # Track comprehensive performance (Phase 2+3)
        if hasattr(self, '_widget_creation_count'):
            total_requests = self._widget_creation_count + self._widget_reuse_count
            if total_requests > 0:
                reuse_rate = (self._widget_reuse_count / total_requests) * 100
                print(f"DEBUG Widget Performance: {self._widget_creation_count} created, {self._widget_reuse_count} reused ({reuse_rate:.1f}% reuse rate)")
                
                # Phase 3: Property update efficiency
                if hasattr(self, '_property_update_count'):
                    total_property_checks = self._property_update_count + self._property_skip_count
                    if total_property_checks > 0:
                        skip_rate = (self._property_skip_count / total_property_checks) * 100
                        print(f"DEBUG Property Updates: {self._property_update_count} changes, {self._property_skip_count} skipped ({skip_rate:.1f}% efficiency)")
            else:
                print(f"DEBUG Widget Performance: No widget requests this update")
        
        # Verify pool integrity
        for session_name, button in self.session_button_pool.items():
            if not button or not hasattr(button, 'get_label'):
                print(f"WARNING: Invalid button in pool for session '{session_name}'")
        
        return {
            'pool_size': pool_size,
            'active_count': active_count, 
            'total_sessions': total_sessions
        }
    
    def enable_widget_pool_debug(self):
        """Enable widget pool debugging for testing (Phase 1)"""
        self.DEBUG_ENABLED = True
        print("DEBUG: Widget pool debugging enabled")
    
    def disable_widget_pool_debug(self):
        """Disable widget pool debugging (Phase 1)"""
        self.DEBUG_ENABLED = False
        print("DEBUG: Widget pool debugging disabled")
    
    def _update_button_selection(self, button, is_selected):
        """Update button selection state efficiently (Phase 3: Enhanced)"""
        style_context = button.get_style_context()
        current_selected = style_context.has_class("selected")
        
        # Phase 3: Only update if state actually changed
        if is_selected != current_selected:
            if is_selected:
                style_context.add_class("selected")
            else:
                style_context.remove_class("selected")
            # Track actual state changes for debugging
            if hasattr(self, '_property_update_count'):
                self._property_update_count += 1
    
    def _update_button_label(self, button, session_name):
        """Update button label efficiently (Phase 3: Enhanced)"""
        current_label = button.get_label()
        new_label = f"• {session_name}"
        
        # Phase 3: Only update if label actually changed
        if current_label != new_label:
            button.set_label(new_label)
            # Track actual label changes for debugging
            if hasattr(self, '_property_update_count'):
                self._property_update_count += 1
        else:
            # Track skipped updates for efficiency monitoring (Phase 3)
            if hasattr(self, '_property_skip_count'):
                self._property_skip_count += 1
    
    def _update_button_properties(self, button, session_name, is_selected):
        """Comprehensive property update with change detection (Phase 3)"""
        changes_made = 0
        
        # Update label efficiently
        current_label = button.get_label()
        new_label = f"• {session_name}"
        
        if current_label != new_label:
            button.set_label(new_label)
            changes_made += 1
        
        # Update selection state efficiently
        style_context = button.get_style_context()
        current_selected = style_context.has_class("selected")
        if is_selected != current_selected:
            if is_selected:
                style_context.add_class("selected")
            else:
                style_context.remove_class("selected")
            changes_made += 1
            
            # Debug property changes
            if self.debug_logger:
                self.debug_logger.debug_widget_property_change(
                    session_name, "selected", current_selected, is_selected, True
                )
        
        # Track efficiency metrics (Phase 3)
        if hasattr(self, '_property_update_count'):
            self._property_update_count += changes_made
        if hasattr(self, '_property_skip_count') and changes_made == 0:
            self._property_skip_count += 1
        
        return changes_made > 0
    
    def _validate_widget_pool_integrity(self):
        """Validate and clean widget pool for optimal performance (Phase 3)"""
        invalid_widgets = []
        
        for session_name, button in self.session_button_pool.items():
            # Check if widget is still valid
            try:
                # Attempt to access widget properties to verify it's not destroyed
                _ = button.get_label()
                _ = button.get_style_context()
            except (AttributeError, RuntimeError):
                # Widget has been destroyed or is invalid
                invalid_widgets.append(session_name)
                print(f"DEBUG: Found invalid widget for session '{session_name}', will remove")
        
        # Remove invalid widgets from pool
        for session_name in invalid_widgets:
            del self.session_button_pool[session_name]
        
        return len(invalid_widgets)
    
    def _optimize_widget_pool_size(self, max_pool_size=None):
        """Keep widget pool size reasonable for memory efficiency (Phase 3)"""
        if max_pool_size is None:
            max_pool_size = self.WIDGET_POOL_MAX_SIZE
        if len(self.session_button_pool) <= max_pool_size:
            return 0  # No optimization needed
        
        # Remove widgets for sessions that no longer exist
        current_sessions = set(self.all_session_names)
        pool_sessions = set(self.session_button_pool.keys())
        obsolete_sessions = pool_sessions - current_sessions
        
        removed_count = 0
        for session_name in obsolete_sessions:
            widget = self.session_button_pool.pop(session_name)
            try:
                widget.destroy()  # Proper GTK cleanup
            except (AttributeError, RuntimeError):
                pass  # Widget already destroyed
            removed_count += 1
        
        if removed_count > 0:
            print(f"DEBUG: Optimized widget pool, removed {removed_count} obsolete widgets")
        
        return removed_count

    def activate_selected_session(self):
        """Activate (restore) the currently selected session"""
        selected_session = self.get_selected_session()
        if selected_session and self.on_session_clicked:
            self.on_session_clicked(selected_session)

    def set_state(self, new_state):
        """Change the browse panel state and refresh content"""
        if new_state != self.state:
            old_state = self.state
            self.state = new_state
            
            # Debug state transitions
            if self.debug_logger:
                self.debug_logger.debug_state_transition(
                    "browse_panel", old_state, new_state, "set_state"
                )
            
            # Fix: Clear widget pool when returning to browsing state
            # GTK widget rendering gets corrupted when reusing widgets across state transitions
            if new_state == BROWSING_STATE and old_state in [RESTORE_CONFIRM_STATE, DELETE_CONFIRM_STATE]:
                self._clear_widget_pool_for_state_transition(old_state)
                
            self._create_content()
            self.show_all()

    # Operation methods removed - now handled by operation classes
    # DeleteOperation and RestoreOperation handle all operation logic

    def handle_key_press_event(self, widget, event):
        """Handle keyboard events using full GTK event context"""
        keyval = event.keyval
        
        # Debug event routing decisions
        if self.debug_logger:
            self.debug_logger.debug_event_routing(
                "key_press", keyval, "browse_panel", "handle_key_press_event",
                {"state": self.state, "widget": widget.__class__.__name__}
            )
        if self.state == DELETE_CONFIRM_STATE:
            return self._handle_confirmation_state_event(
                event, self.delete_operation, DELETE_CONFIRM_STATE
            )

        elif self.state == RESTORE_CONFIRM_STATE:
            return self._handle_confirmation_state_event(
                event, self.restore_operation, RESTORE_CONFIRM_STATE
            )

        elif self.state == BROWSING_STATE:
            # Use new GTK event-based routing
            if self.should_route_to_search(event):
                # Let GTK route to search input (don't handle here)
                return False
            else:
                # Handle UI navigation keys
                return self._handle_navigation_event(event)

        # Let main manager handle other keys
        return False

    def _handle_confirmation_state_event(self, event, operation, state):
        """Handle confirmation state with GTK event"""
        keyval = event.keyval

        if keyval in [Gdk.KEY_Return, Gdk.KEY_KP_Enter]:
            # Trigger the operation
            operation.trigger_operation()
            return True
        elif keyval == Gdk.KEY_Escape:
            # Cancel operation
            print(
                f"DEBUG: Cancelled {operation.get_operation_config()['action_verb'].lower()} for session: {operation.selected_session}"
            )
            operation.selected_session = None
            self.set_state(BROWSING_STATE)
            return True

        return False

    def _handle_navigation_event(self, event):
        """Handle navigation events in browsing state"""
        keyval = event.keyval

        if keyval == Gdk.KEY_Escape:
            # Clear search
            self.clear_search()
            return True
        elif keyval in [Gdk.KEY_Up, Gdk.KEY_Down]:
            # Handle session navigation directly
            if keyval == Gdk.KEY_Up:
                self.select_previous()
            else:
                self.select_next()
            return True
        elif keyval in [Gdk.KEY_Return, Gdk.KEY_KP_Enter]:
            # Let main manager handle session activation
            return False
        elif keyval == Gdk.KEY_Tab:
            # Let main manager handle panel switching
            return False
        elif keyval in [Gdk.KEY_Left, Gdk.KEY_Right]:
            # Let main manager handle panel switching
            return False

        return False
