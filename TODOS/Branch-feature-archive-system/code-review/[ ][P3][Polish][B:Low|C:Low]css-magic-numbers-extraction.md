# Extract CSS Magic Numbers to Variables

## Priority: P3 | Type: Polish | Benefit: Low | Complexity: Low

## Problem Description

Hardcoded values like `border-radius: 24px`, `padding: 40px` throughout CSS file make theming inconsistent and maintenance difficult. Using GTK3 `@define-color` pattern would improve maintainability and design consistency.

## Implementation Plan

1. **Identify Magic Numbers**: Audit CSS for hardcoded values (dimensions, timing, opacities)
2. **Group by Purpose**: Categorize values (border radius, spacing, timing, opacity levels)
3. **Extract to Variables**: Create `@define-color` variables using GTK3 syntax
4. **Update References**: Replace hardcoded values with variable references
5. **Test Rendering**: Verify visual appearance unchanged after refactoring

## File Locations

**Primary File**:
- `/home/jc/Dev/hypr-sessions/fabric-ui/session_manager.css`

**Common Magic Numbers Found**:
- Border radius: `12px`, `16px`, `18px`, `24px`
- Padding/margins: `8px`, `12px`, `15px`, `20px`, `40px`
- Transition timing: `0.3s`, `0.4s`
- Opacity levels: `0.05`, `0.08`, `0.1`, `0.15`, etc.

## Success Criteria

- [ ] All repeated dimensional values extracted to variables
- [ ] Consistent spacing system using base units
- [ ] All opacity levels use defined variables
- [ ] Transition timing standardized
- [ ] Visual appearance unchanged
- [ ] Easier theming customization for future development

## Dependencies

None

## Code Examples

**Current Magic Numbers** (examples from CSS):
```css
window {
    border-radius: 24px;        /* Magic number */
    padding: 40px;              /* Magic number */
    transition: background-color 0.4s ease-out;  /* Magic timing */
}

#session-button {
    border-radius: 12px;        /* Different magic number */
    padding: 14px 18px;         /* More magic numbers */
    transition-duration: 0.3s;  /* Different timing */
}
```

**Extracted Variables** (add to top of CSS file):
```css
/* Hypr Sessions Manager - Mac Tahoe Aesthetic (GTK3 Compatible) */

/* Existing color variables... */
@define-color primary_white #ffffff;
@define-color secondary_white #e0e0e0;
/* ... */

/* NEW: Dimensional Variables */
@define-color base_unit 4px;                    /* 4px base unit */
@define-color spacing_small 8px;                /* 2 * base_unit */
@define-color spacing_medium 12px;              /* 3 * base_unit */
@define-color spacing_large 16px;               /* 4 * base_unit */
@define-color spacing_xlarge 24px;              /* 6 * base_unit */
@define-color spacing_xxlarge 40px;             /* 10 * base_unit */

/* Border Radius Variables */
@define-color radius_small 12px;                /* Button radius */
@define-color radius_medium 16px;               /* Container radius */
@define-color radius_large 18px;                /* Toggle button radius */
@define-color radius_xlarge 24px;               /* Window radius */

/* Transition Variables */
@define-color transition_fast 0.3s;             /* Fast transitions */
@define-color transition_normal 0.4s;           /* Normal transitions */

/* Opacity Level Variables */
@define-color opacity_subtle 0.05;              /* Subtle backgrounds */
@define-color opacity_light 0.08;               /* Light backgrounds */
@define-color opacity_medium 0.15;              /* Medium backgrounds */
@define-color opacity_strong 0.25;              /* Strong backgrounds */
```

**Updated CSS Usage**:
```css
window {
    border-radius: @radius_xlarge;
    padding: @spacing_xxlarge;
    transition: background-color @transition_normal ease-out;
}

#session-button {
    border-radius: @radius_small;
    padding: @spacing_medium @spacing_large;
    transition-duration: @transition_fast;
}

#sessions-container {
    background-color: alpha(@glass_dark_secondary, 0.4);  /* Keep existing pattern */
    background-image: linear-gradient(
        to bottom,
        alpha(@primary_white, @opacity_subtle),            /* Use opacity variable */
        alpha(@primary_white, 0.02)                        /* Or extract this too */
    );
    padding: @spacing_medium;
    border-radius: @radius_medium;
}
```

**Spacing System Benefits**:
- **Consistent Rhythm**: All spacing follows 4px base unit system
- **Easy Scaling**: Change base unit to scale entire interface
- **Design Token Pattern**: Professional approach used by design systems
- **Maintainable**: Single place to adjust spacing relationships

**Implementation Notes**:
- Keep existing color variable system intact
- Add new dimensional variables following GTK3 `@define-color` syntax
- Update selectors incrementally to avoid breaking changes
- Test with different GTK themes to ensure compatibility

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.