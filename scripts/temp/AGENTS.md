# Temporary Scripts - Agent Instructions

> **Quick reference for AI agents:** Where to put temporary scripts and how to clean them up.

## Quick Rules

1. **Always save temporary scripts to `scripts/temp/`**
   - One-time testing/debugging scripts
   - Analysis scripts
   - Helper scripts for specific issues

2. **Run from project root:**
   ```bash
   python scripts/temp/your_script.py
   ```

3. **After session:**
   - Review scripts in `scripts/temp/`
   - Move useful patterns to `scripts/examples/`
   - Run cleanup: `python scripts/cleanup_temp.py`

## When Creating Temporary Scripts

```python
# Save as: scripts/temp/test_feature.py
# Example temporary script for testing
```

## Cleanup

- **Automatic:** Scripts older than 7 days
- **Manual:** `python scripts/cleanup_temp.py`
- **Before commit:** Review and move useful ones to `examples/`

## See Also

- `scripts/README.md` - Full documentation
- `scripts/temp/README.md` - Detailed usage guide
- `AGENTS.md` (root) - Main agent guide
