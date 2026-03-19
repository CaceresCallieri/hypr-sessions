# GTK3 CSS and Widget Gotchas

Reference for non-obvious GTK3 behaviors in the legacy Fabric UI (`fabric-ui/`).

## CSS Limitations

- No `!important` declarations
- No `backdrop-filter` or advanced web CSS properties
- No CSS custom properties: `:root` and `var()` cause parsing errors
- No FASS variables: `:vars` from Fabric docs don't work
- `@define-color` only works for colors -- not dimensions, timing, or opacity
- No dimensional variables: use hardcoded values with semantic comments instead

### Color Variables (GTK3 Native)

```css
@define-color primary_white #ffffff;
@define-color warm_dark #262424;
color: @primary_white;
background-color: alpha(@primary_white, 0.8);
```

### Design System via Comments

```css
border-radius: 24px; /* @radius-xlarge */
padding: 40px; /* @spacing-massive */
```

## CSS Specificity

Broad `label` selectors override button text because GTK buttons contain nested labels:

```css
/* Must target BOTH element AND nested label */
#save-session-button { color: #262424; }
#save-session-button label { color: #262424; }
```

## GTK3-Compatible Glassmorphism

```css
background-color: alpha(#ffffff, 0.8);
background-image: linear-gradient(to bottom, alpha(#ffffff, 0.9), alpha(#e0e0e0, 0.8));
border: 2px solid alpha(#ffffff, 0.3);
```

## Widget Reparenting Bug

Widgets moved between containers lose rendering state (labels appear blank). Fix:

```python
current_label = button.get_label()
button.set_label("")           # Clear
button.set_label(current_label) # Restore -- forces GTK refresh
button.queue_draw()
```

Detect state transitions from confirmation states back to browsing and call refresh.

## Focus Management

- Startup focus unreliable during construction: use `GLib.timeout_add(100, delayed_setup)`
- Thread safety: always `GLib.idle_add()` for UI updates from background threads
- Layer shell exclusive keyboard mode prevents focus loss under Hyprland

## Fabric UI Component Hierarchy

```
SessionManagerWidget (WaylandWindow)
  ToggleSwitchWidget
  BrowsePanelWidget (orchestrator)
    SessionWidgetPool       -- widget pooling (95%+ reuse)
    SessionWindowCalculator -- windowing math
    SessionListRenderer     -- widget creation/layout
    KeyboardEventHandler    -- GTK event processing
    SessionSearchManager    -- search and focus management
  SavePanelWidget

Operations use BaseOperation abstract class with ~25-line concrete implementations.
```

## Dual Focus Search Architecture

- Search input: permanent GTK focus for continuous typing
- Session buttons: `set_can_focus(False)` prevents focus stealing
- Key routing: printable chars to search, navigation keys to session list
- Quit: `Ctrl+Q` (not `q`) to avoid conflicts while typing
- Navigation: name-based selection (not index-based) to avoid coordinate bugs
- Debug: human-readable key info via `get_human_readable_key()` in debug logger
