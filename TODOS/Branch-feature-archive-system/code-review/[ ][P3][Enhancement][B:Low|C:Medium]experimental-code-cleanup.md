# Clean Up Experimental Code Directory

## Priority: P3 | Type: Enhancement | Benefit: Low | Complexity: Medium

## Problem Description

Large experimental codebase (likely 1000+ lines) exists in production repository under `/experiments/` directory, adding repository bloat and potential confusion for future developers. This should be archived or moved to maintain clean production codebase.

## Implementation Plan

1. **Audit Experimental Code**: Catalog all experimental code and assess value
2. **Identify Dependencies**: Check if any experimental code is referenced by production
3. **Extract Valuable Insights**: Document any useful patterns or approaches discovered
4. **Create Separate Repository**: Move experiments to dedicated research repository
5. **Update Documentation**: Document the separation and archive location
6. **Clean Production Repo**: Remove experimental directory from main repository

## File Locations

**Directory to Process**:
- `/home/jc/Dev/hypr-sessions/experiments/` (multiple subdirectories)

**Expected Subdirectories/Files**:
- Various experimental features and prototypes
- Research code and proof-of-concepts  
- Alternative implementation approaches
- Development utilities and scripts

## Success Criteria

- [ ] Experimental code moved to separate repository or archived
- [ ] Production repository size reduced significantly
- [ ] No broken references to experimental code in production
- [ ] Valuable insights documented in main project
- [ ] Clear separation between production and research code
- [ ] Updated .gitignore if needed to prevent future experimental code commits

## Dependencies

**Depends-On**: Audit phase must confirm no production dependencies exist

## Code Examples

**Current Structure**:
```
hypr-sessions/
├── commands/           # Production code
├── fabric-ui/         # Production code
├── experiments/       # ← This entire directory
│   ├── prototype-1/
│   ├── alternative-approach/
│   ├── research-scripts/
│   └── ...
└── README.md
```

**Target Structure**:
```
hypr-sessions/
├── commands/           # Production code only
├── fabric-ui/         # Production code only
└── README.md

# Separate repository:
hypr-sessions-experiments/
├── prototype-1/
├── alternative-approach/
├── research-scripts/
├── INSIGHTS.md        # Documented learnings
└── README.md          # Links back to main project
```

**Implementation Steps**:

1. **Audit Phase**:
```bash
# Check for any imports or references to experimental code
grep -r "experiments" commands/ fabric-ui/
grep -r "from experiments" .
grep -r "import experiments" .
```

2. **Documentation Extraction**:
```bash
# Create insights document from experimental code
find experiments/ -name "*.md" -exec cat {} \; > EXPERIMENTAL_INSIGHTS.md
find experiments/ -name "*.py" -exec grep -l "TODO\|FIXME\|NOTE" {} \; | xargs grep "TODO\|FIXME\|NOTE"
```

3. **Repository Creation**:
```bash
# Create separate experiments repository
git subtree push --prefix=experiments origin experiments-archive
# Or create entirely separate repo and move files
```

4. **Clean Production Repository**:
```bash
# Remove experimental code from main repository
git rm -r experiments/
git commit -m "Archive experimental code to separate repository"
```

**Documentation Updates**:
- Add link to experiments repository in main README
- Document any valuable patterns discovered during experiments
- Include decision rationale for experimental code separation

**Benefits of Cleanup**:
- **Reduced Repository Size**: Faster clones and smaller disk usage
- **Clearer Code Organization**: Production code clearly separated from research
- **Reduced Maintenance Overhead**: No need to maintain experimental code
- **Better Onboarding**: New developers see only production-ready code
- **Preserved Research**: Experimental work still accessible but archived appropriately

## Reminder

When implementation is finished, update the filename prefix from `[ ]` to `[x]`.