"""
Session Widget Pool Component

Manages reusable session button widgets for performance optimization.
Extracted from BrowsePanelWidget to improve maintainability and testability.
"""

from fabric.widgets.button import Button

from utils import (
    WIDGET_POOL_MAINTENANCE_THRESHOLD,
    WIDGET_POOL_MAX_SIZE,
    create_session_button,
    apply_selection_styling,
    update_button_label_efficiently,
    prepare_widget_for_reuse
)


class SessionWidgetPool:
    """Manages a pool of reusable session button widgets for performance optimization"""

    def __init__(self, debug_logger=None):
        """Initialize the widget pool
        
        Args:
            debug_logger: Optional debug logger for performance monitoring
        """
        self.pool = {}  # session_name -> Button widget mapping
        self.debug_logger = debug_logger
        
        # Performance tracking
        self._widget_creation_count = 0
        self._widget_reuse_count = 0
        self._property_update_count = 0
        self._property_skip_count = 0

    def get_or_create_button(self, session_name: str, is_selected: bool = False, 
                           on_clicked_callback=None) -> Button:
        """Get button from pool or create new one
        
        Args:
            session_name: Name of the session for the button
            is_selected: Whether button should appear selected
            on_clicked_callback: Callback for button click events
            
        Returns:
            Button widget ready for use
        """
        # Check pool first for existing widget
        if session_name in self.pool:
            button = self.pool[session_name]
            
            # GTK3 Requirement: Remove widget from previous container before reuse
            current_parent = button.get_parent()
            if current_parent:
                current_parent.remove(button)
            
            # Prepare widget for reuse after container transitions
            prepare_widget_for_reuse(button, session_name, self.debug_logger)
            
            # Update properties efficiently with change detection
            changes_made = self._update_button_properties(button, session_name, is_selected)
            
            # Track reuse for performance monitoring
            self._widget_reuse_count += 1
            
            # Debug widget pool reuse
            if self.debug_logger:
                self.debug_logger.debug_widget_pool_operation(
                    "reuse", session_name, reused=True, 
                    pool_size=len(self.pool)
                )
            return button
        
        # Create new widget if not in pool
        if on_clicked_callback:
            button = Button(
                label=f"• {session_name}",
                name="session-button",
                on_clicked=lambda *_: on_clicked_callback(session_name)
            )
        else:
            button = create_session_button(session_name, None)

        # Add selected styling if needed
        if is_selected:
            apply_selection_styling(button, True)

        # Store in pool for future reuse
        self.pool[session_name] = button
        
        # Track creation for performance monitoring
        self._widget_creation_count += 1
        
        # Debug widget pool creation
        if self.debug_logger:
            self.debug_logger.debug_widget_pool_operation(
                "create", session_name, created=True, 
                pool_size=len(self.pool)
            )
        
        return button

    def _update_button_properties(self, button: Button, session_name: str, is_selected: bool) -> bool:
        """Update button properties efficiently with change detection
        
        Args:
            button: Button widget to update
            session_name: Session name for the button
            is_selected: Whether button should appear selected
            
        Returns:
            True if any changes were made, False if no updates needed
        """
        changes_made = 0
        
        # Update label efficiently
        if update_button_label_efficiently(button, session_name):
            changes_made += 1
        
        # Update selection styling efficiently  
        if apply_selection_styling(button, is_selected):
            changes_made += 1
            
            # Debug property changes
            if self.debug_logger:
                self.debug_logger.debug_widget_property_change(
                    session_name, "selected", not is_selected, is_selected, True
                )
        
        # Track efficiency metrics
        if changes_made > 0:
            self._property_update_count += changes_made
        else:
            self._property_skip_count += 1
        
        return changes_made > 0

    def prepare_for_reparenting(self):
        """Prepare all pooled widgets for container transitions"""
        pool_size = len(self.pool)
        
        if self.debug_logger and self.debug_logger.enabled:
            self.debug_logger.debug_widget_pool_maintenance(
                "prepare_for_transition", pool_size, pool_size,
                {"reason": "gtk3_state_refresh", "method": "widget_refresh_approach"}
            )
        
        # Prepare each widget for container transitions
        for session_name, button in self.pool.items():
            try:
                # Clear visual state that might be corrupted
                if hasattr(button, 'queue_draw'):
                    button.queue_draw()
                
                # Ensure basic properties are set
                if hasattr(button, 'set_sensitive'):
                    button.set_sensitive(True)
                    
            except Exception as e:
                if self.debug_logger and self.debug_logger.enabled:
                    self.debug_logger.debug_widget_pool_operation(
                        "prepare_error", session_name, details={"error": str(e)}
                    )

    def validate_integrity(self) -> int:
        """Validate and clean widget pool for optimal performance
        
        Returns:
            Number of invalid widgets removed
        """
        invalid_widgets = []
        
        for session_name, button in self.pool.items():
            # Check if widget is still valid
            try:
                # Attempt to access widget properties to verify it's not destroyed
                _ = button.get_label()
                _ = button.get_style_context()
            except (AttributeError, RuntimeError):
                # Widget has been destroyed or is invalid
                invalid_widgets.append(session_name)
                if self.debug_logger and self.debug_logger.enabled:
                    self.debug_logger.debug_widget_pool_operation(
                        "found_invalid", session_name, details={"will_remove": True}
                    )
        
        # Remove invalid widgets from pool
        for session_name in invalid_widgets:
            del self.pool[session_name]
        
        if len(invalid_widgets) > 0 and self.debug_logger:
            self.debug_logger.debug_widget_pool_maintenance(
                "remove_invalid", len(self.pool) + len(invalid_widgets), len(self.pool),
                {"total_removed": len(invalid_widgets)}
            )
        
        return len(invalid_widgets)

    def optimize_size(self, current_sessions: set = None, max_pool_size: int = None) -> int:
        """Keep widget pool size reasonable for memory efficiency
        
        Args:
            current_sessions: Set of currently existing session names
            max_pool_size: Maximum pool size (uses default if None)
            
        Returns:
            Number of widgets removed during optimization
        """
        if max_pool_size is None:
            max_pool_size = WIDGET_POOL_MAX_SIZE
            
        if len(self.pool) <= max_pool_size:
            return 0  # No optimization needed
        
        removed_count = 0
        
        # Remove widgets for sessions that no longer exist
        if current_sessions:
            pool_sessions = set(self.pool.keys())
            obsolete_sessions = pool_sessions - current_sessions
            
            for session_name in obsolete_sessions:
                widget = self.pool.pop(session_name)
                try:
                    widget.destroy()  # Proper GTK cleanup
                except (AttributeError, RuntimeError):
                    pass  # Widget already destroyed
                removed_count += 1
        
        if removed_count > 0 and self.debug_logger:
            self.debug_logger.debug_widget_pool_maintenance(
                "optimize", len(self.pool) + removed_count, len(self.pool),
                {"removed_count": removed_count}
            )
        
        return removed_count

    def perform_maintenance_if_needed(self, current_sessions: set = None):
        """Perform periodic maintenance when threshold is exceeded
        
        Args:
            current_sessions: Set of currently existing session names
        """
        if len(self.pool) > WIDGET_POOL_MAINTENANCE_THRESHOLD:
            self.validate_integrity()
            self.optimize_size(current_sessions)

    def reset_performance_counters(self):
        """Reset performance counters for widget creation tracking"""
        self._widget_creation_count = 0
        self._widget_reuse_count = 0
        self._property_update_count = 0
        self._property_skip_count = 0

    def get_performance_stats(self) -> dict:
        """Get performance statistics for debugging
        
        Returns:
            Dictionary with performance metrics
        """
        total_requests = self._widget_creation_count + self._widget_reuse_count
        total_property_checks = self._property_update_count + self._property_skip_count
        
        return {
            'pool_size': len(self.pool),
            'widget_creation_count': self._widget_creation_count,
            'widget_reuse_count': self._widget_reuse_count,
            'reuse_rate': (self._widget_reuse_count / total_requests * 100) if total_requests > 0 else 0,
            'property_update_count': self._property_update_count,
            'property_skip_count': self._property_skip_count,
            'property_skip_rate': (self._property_skip_count / total_property_checks * 100) if total_property_checks > 0 else 0
        }