# Ralph Agent Instructions (RhinoMCP Edition)

## Overview

Ralph is a structured development workflow for RhinoMCP. Instead of autonomous loops, Ralph provides a systematic approach to iterative development with small, context-window-friendly tasks.

## Quick Start

```bash
# 1. Read the patterns first
cat Ralph/progress.txt

# 2. Check story status
cat Ralph/prd.json

# 3. Work on highest priority story (passes: false)
# 4. Test, commit, update progress.txt
# 5. Mark story passes: true
```

## Key Files

| File | Purpose |
|------|---------|
| `prd.json` | User stories with `passes` status |
| `progress.txt` | Codebase patterns + learnings (READ FIRST!) |
| `scripts/ralph/prompt.md` | Full AI agent instructions |

## Patterns (SACRED - always follow)

- **Python Server**: `rhino_mcp_server/src/rhinomcp/`
- **C# Plugin**: `rhino_mcp_plugin/`
- **Commands**: lower_snake_case verbs first (`create_object`)
- **Colors**: `[r, g, b]` (0-255)
- **Points**: `[x, y, z]`
- **Returns**: `{ success, message, data }` JSON objects

## After Each Story

1. Update `progress.txt` with learnings
2. Update relevant `AGENTS.md` files with patterns
3. Commit with clear message: `feat/story/US-XXX: description`
