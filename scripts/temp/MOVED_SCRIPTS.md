# Moved Temporary Scripts

The following temporary scripts from the 2026-01-12 session have been organized:

## Scripts Moved to `scripts/temp/`

These scripts were created during the Rahmentuer_UD5 analysis session and are temporary:

- `test_door_ud5.py` - Analysis script for understanding Rahmentuer_UD5.gh prompts
- `complete_ud5_door.py` - Complete door creation attempt
- `complete_full_ud5.py` - Full door creation with all inputs
- `check_rhino_state.py` - Check current Rhino state
- `analyze_ud5_manual.py` - Manual analysis script
- `send_height_input.py` - Send height input helper
- `send_width_input.py` - Send width input helper
- `send_point_input.py` - Send point input helper
- `send_hinge_side.py` - Send hinge side input helper

## Cleanup

These scripts will be automatically cleaned up after 7 days, or manually via:
```bash
python scripts/cleanup_temp.py
```

## Useful Patterns Extracted

The learnings from these scripts have been documented in:
- `docs/learnings/getting-unstuck.md` - Best practices for handling unknown prompts
- `scripts/examples/complete_door_example.py` - Reusable example pattern
