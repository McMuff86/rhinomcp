# Ralph Agent Instructions

> This file provides Ralph-specific workflow guidance. For the full RhinoMCP agent guide, see [../AGENTS.md](../AGENTS.md).

## Ralph Workflow

Ralph is a structured development workflow for RhinoMCP that uses small, context-window-friendly tasks.

### Quick Start

```bash
# 1. Read the patterns first
cat Ralph/progress.txt

# 2. Check story status (Phase B complete, Phase C next)
cat Ralph/prd_phase_b.json

# 3. Work on highest priority story with passes: false
# 4. Test, commit, update progress.txt
# 5. Mark story passes: true
```

### Key Files

| File | Purpose |
|------|---------|
| `prd.json` | Phase A user stories (complete) |
| `prd_phase_b.json` | Phase B user stories (complete) |
| `progress.txt` | Codebase patterns + learnings (**READ FIRST!**) |
| `NEXT_SESSION_PLAN.md` | Detailed next steps |

### After Each Story

1. Update `progress.txt` with learnings
2. Update root `AGENTS.md` with new patterns
3. Commit with message: `feat/story/US-XXX: description`

## See Also

- [Root AGENTS.md](../AGENTS.md) - Full agent guide with all tools, conventions, and examples
- [ROADMAP.md](../ROADMAP.md) - Project phases
- [progress.txt](progress.txt) - Session learnings
