"""
Widget Helper Utilities

Common GTK widget utilities and helpers extracted from browse_panel.py
for reusability across session management components.
"""

from fabric.widgets.label import Label
from fabric.widgets.button import Button


def create_scroll_indicator(arrow_symbol: str, show_condition: bool) -> Label:
    """Create a scroll indicator with reserved space
    
    Args:
        arrow_symbol: Unicode arrow symbol to display
        show_condition: Whether to show the arrow or reserve empty space
        
    Returns:
        Label widget with arrow or empty space
    """
    indicator = Label(text="", name="scroll-indicator")
    if show_condition:
        indicator.set_markup(arrow_symbol)
    else:
        indicator.set_markup("")  # Empty but reserves space
    return indicator


def create_session_button(session_name: str, on_clicked_callback) -> Button:
    """Create a session button with standard configuration
    
    Args:
        session_name: Name of the session for the button
        on_clicked_callback: Callback function when button is clicked
        
    Returns:
        Configured Button widget
    """
    button = Button(
        label=f"• {session_name}",
        name="session-button",
        on_clicked=on_clicked_callback
    )
    # Make button non-focusable to preserve dual focus behavior
    button.set_can_focus(False)
    return button


def apply_selection_styling(button: Button, is_selected: bool) -> bool:
    """Apply or remove selection styling from a button
    
    Args:
        button: Button widget to style
        is_selected: Whether button should appear selected
        
    Returns:
        True if styling was changed, False if no change needed
    """
    style_context = button.get_style_context()
    current_selected = style_context.has_class("selected")
    
    # Only update if state actually changed
    if is_selected != current_selected:
        if is_selected:
            style_context.add_class("selected")
        else:
            style_context.remove_class("selected")
        return True
    
    return False


def update_button_label_efficiently(button: Button, session_name: str) -> bool:
    """Update button label only if changed
    
    Args:
        button: Button widget to update
        session_name: Session name for the label
        
    Returns:
        True if label was updated, False if no change needed
    """
    current_label = button.get_label()
    new_label = f"• {session_name}"
    
    if current_label != new_label:
        button.set_label(new_label)
        return True
    
    return False


def prepare_widget_for_reuse(button: Button, session_name: str, debug_logger=None) -> None:
    """Prepare a widget for reuse after container transitions
    
    Args:
        button: Button widget to prepare
        session_name: Session name for debugging
        debug_logger: Optional debug logger for troubleshooting
    """
    try:
        # Ensure widget is visible (basic requirement)
        if not button.get_visible():
            if debug_logger and debug_logger.enabled:
                debug_logger.debug_widget_pool_operation(
                    "visibility_fix", session_name, details={"made_visible": True}
                )
            button.set_visible(True)
        
        # Force property refresh to clear stale visual state
        current_label = button.get_label()
        if current_label:
            button.set_label("")  # Clear
            button.set_label(current_label)  # Restore - forces GTK refresh
        
        # Queue redraw to ensure fresh rendering
        button.queue_draw()
            
    except Exception as e:
        if debug_logger and debug_logger.enabled:
            debug_logger.debug_widget_pool_operation(
                "reuse_error", session_name, details={"error": str(e)}
            )