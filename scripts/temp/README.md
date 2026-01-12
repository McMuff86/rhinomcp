# Temporary Scripts Directory

> **Purpose:** Temporary scripts created during development sessions for testing, debugging, or analysis.
> 
> **For AI Agents:** See `AGENTS.md` in this directory for quick reference.

## Structure

```
scripts/
├── temp/              # Temporary scripts (auto-cleanup after session)
│   ├── README.md      # This file
│   └── *.py           # Temporary scripts
│
├── examples/          # Reusable example scripts
│   └── *.py           # Example scripts that can be reused
│
└── cleanup_temp.py    # Cleanup script for temp folder
```

## Usage

### Creating Temporary Scripts

When creating temporary scripts during a session:

1. **Save to `scripts/temp/`**:
   ```python
   # Save as: scripts/temp/test_feature.py
   ```

2. **Run from project root**:
   ```bash
   python scripts/temp/test_feature.py
   ```

3. **Or run from temp directory**:
   ```bash
   cd scripts/temp
   python test_feature.py
   ```

### After Session

**Option 1: Manual cleanup**
```bash
python scripts/cleanup_temp.py
```

**Option 2: Keep useful scripts**
- Move reusable scripts to `scripts/examples/`
- Delete truly temporary ones

## What Goes Where?

| Location | Purpose | Lifecycle |
|----------|---------|-----------|
| `scripts/temp/` | Temporary testing/debugging scripts | Cleanup after session |
| `scripts/examples/` | Reusable example scripts | Keep in repo |
| `rhino_mcp_server/dev/` | Development scripts for MCP server | Keep in repo |
| `scripts/` (root) | Utility scripts (sync_version, etc.) | Keep in repo |

## Cleanup Policy

- **Auto-cleanup:** Scripts older than 7 days (configurable)
- **Manual cleanup:** Run `cleanup_temp.py` anytime
- **Keep examples:** Move useful scripts to `examples/` before cleanup

## Examples

**Temporary (goes to `temp/`):**
- `test_door_ud5.py` - One-time analysis script
- `send_height_input.py` - Debug script for specific issue
- `check_rhino_state.py` - Temporary state checker

**Reusable (goes to `examples/`):**
- `complete_door_example.py` - Example of door creation workflow
- `websocket_interactive_example.py` - Example of WebSocket usage
