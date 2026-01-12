# Scripts Directory

> **Purpose:** Utility scripts, examples, and temporary development scripts.

## Structure

```
scripts/
├── README.md              # This file
├── cleanup_temp.py        # Cleanup script for temp folder
│
├── temp/                  # Temporary scripts (auto-cleanup)
│   ├── README.md          # Temp scripts documentation
│   ├── .gitkeep           # Keep directory in git
│   └── *.py               # Temporary scripts (gitignored)
│
├── examples/              # Reusable example scripts
│   ├── README.md          # Examples documentation
│   └── *.py               # Example scripts
│
└── [utility scripts]      # Permanent utility scripts
    ├── check_rhino_connection.py
    └── sync_version.py
```

## Quick Reference

| Directory | Purpose | Lifecycle | Git Status |
|-----------|---------|-----------|------------|
| `scripts/` (root) | Utility scripts | Permanent | Tracked |
| `scripts/temp/` | Temporary scripts | Auto-cleanup (7 days) | Ignored |
| `scripts/examples/` | Example scripts | Permanent | Tracked |
| `rhino_mcp_server/dev/` | MCP server dev scripts | Permanent | Tracked |

## Usage

### Temporary Scripts

**Create:**
```bash
# Save temporary scripts to scripts/temp/
# Example: scripts/temp/test_feature.py
```

**Run:**
```bash
# From project root
python scripts/temp/test_feature.py

# Or from temp directory
cd scripts/temp
python test_feature.py
```

**Cleanup:**
```bash
# Remove scripts older than 7 days
python scripts/cleanup_temp.py

# Remove scripts older than 3 days
python scripts/cleanup_temp.py --days 3

# Remove all scripts (with confirmation)
python scripts/cleanup_temp.py --all

# Preview what would be deleted
python scripts/cleanup_temp.py --dry-run
```

### Example Scripts

**Run examples:**
```bash
python scripts/examples/complete_door_example.py
```

**Create new examples:**
1. Add to `scripts/examples/`
2. Include clear docstrings
3. Document usage in README.md

## Best Practices

1. **Temporary scripts** → `scripts/temp/`
   - One-time testing/debugging
- Auto-cleanup after 7 days
- Not committed to git

2. **Reusable examples** → `scripts/examples/`
   - Demonstrates patterns
   - Can be referenced/modified
   - Committed to git

3. **Utility scripts** → `scripts/` (root)
   - Project maintenance
   - Version sync, checks, etc.
   - Committed to git

4. **MCP server dev scripts** → `rhino_mcp_server/dev/`
   - MCP-specific development
   - Testing MCP functionality
   - Committed to git

## Cleanup Policy

- **Automatic:** Scripts in `temp/` older than 7 days
- **Manual:** Run `cleanup_temp.py` anytime
- **Before commit:** Review temp scripts, move useful ones to examples

## Related Documentation

- `docs/learnings/grasshopper-automation.md` - Grasshopper automation patterns
- `docs/learnings/getting-unstuck.md` - Handling stuck situations
- `AGENTS.md` - Agent guidelines
