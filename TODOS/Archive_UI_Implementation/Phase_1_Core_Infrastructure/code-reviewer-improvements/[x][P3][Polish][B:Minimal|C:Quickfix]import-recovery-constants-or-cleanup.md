# Import Recovery Constants or Clean Up Unused Definitions

## Priority: P3 | Type: Polish | Benefit: Minimal | Complexity: Quickfix

## Problem Description
The recovery operation constants (RECOVERY_CONFIRM_STATE, RECOVERING_STATE, etc.) were added to `constants.py` but are not imported in `browse_panel.py`, suggesting they may be premature or unused. This creates inconsistency and potential confusion about which constants are actually utilized.

## Implementation Plan
**Option A: Import Constants (if Phase 2+ will use them)**
1. Add recovery constants to browse_panel.py imports
2. Verify constants will be used in upcoming phases
3. Document intended usage in comments

**Option B: Remove Constants (if not needed until later phases)**
1. Remove RECOVERY_* constants from constants.py
2. Re-add them in the phase where they're actually implemented
3. Keep git history for easy restoration

**Recommended Approach**: Check Phase 2+ task definitions to determine if these constants are needed immediately or later.

## File Locations
- **Primary**: `fabric-ui/constants.py` lines 24-28 (recovery constants)
- **Secondary**: `fabric-ui/widgets/browse_panel.py` lines 8-16 (import section)

## Success Criteria
- [ ] Decision made: import constants OR remove them based on Phase 2+ requirements
- [ ] If importing: Constants properly imported and documented for future use
- [ ] If removing: Constants removed with clear plan for re-introduction
- [ ] Consistency between constants.py and browse_panel.py maintained

## Dependencies
None - independent polish task

## Code Examples

**Current State (Constants Defined but Not Imported):**
```python
# In constants.py (lines 24-28):
RECOVERY_CONFIRM_STATE: Final[str] = "recovery_confirm"
RECOVERING_STATE: Final[str] = "recovering" 
RECOVERY_SUCCESS_STATE: Final[str] = "recovery_success"
RECOVERY_ERROR_STATE: Final[str] = "recovery_error"

# In browse_panel.py - these are NOT imported
from constants import (
    BROWSING_STATE,
    DELETE_CONFIRM_STATE,
    # ... missing RECOVERY_* constants
)
```

**Option A - Import for Future Use:**
```python
# In browse_panel.py imports:
from constants import (
    BROWSING_STATE,
    DELETE_CONFIRM_STATE,
    DELETING_STATE,
    DELETE_SUCCESS_STATE, 
    DELETE_ERROR_STATE,
    RESTORE_CONFIRM_STATE,
    RESTORING_STATE,
    RESTORE_SUCCESS_STATE,
    RESTORE_ERROR_STATE,
    # Archive recovery constants (for Phase 2+ implementation)
    RECOVERY_CONFIRM_STATE,
    RECOVERING_STATE,
    RECOVERY_SUCCESS_STATE,
    RECOVERY_ERROR_STATE,
)
```

**Option B - Remove Until Needed:**
```python
# Remove lines 24-28 from constants.py
# Re-add in the phase where recovery operations are actually implemented
```

## Reminder
When implementation is finished, update the filename prefix from `[ ]` to `[x]`.