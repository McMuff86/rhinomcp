# Solved Issue: GetPlane 3-Step Problem

**Status:** ✅ SOLVED
**Date Solved:** 2026-01-11
**Solution:** Use `Rahmentuer_UD4.gh` with GetPoint instead of GetPlane

---

## Original Problem

The `Rahmentuer_UD3.gh` script used GetPlane which has 3 steps:
1. Plane type selection (WorldXY/WorldYZ/WorldZX)
2. Origin point
3. Confirmation

After sending all 3 inputs, **no door was created**. Rhino returned to Command prompt without geometry.

## Attempted Solutions (Failed)

| Input for Step 3 | Result |
|------------------|--------|
| `""` (empty) | ❌ Did not complete |
| `"Enter"` | ❌ Did not complete |
| `"_Accept"` | ❌ Did not complete |
| `"0,0,1"` | ❌ Did not complete |

## Working Solution Found

`"_Enter"` - The Rhino command (not just Enter key) completed step 3.

## Better Solution Implemented

**Changed Grasshopper script** to use `GetPoint` instead of `GetPlane`:
- `Rahmentuer_UD4.gh` - Plane fixed to XY, only needs a point
- Only 3 simple prompts: Lichthoehe, Lichtbreite, Get Point
- Much more reliable for automation

## Key Learning

When automating interactive Rhino commands:
1. Prefer simpler input methods (GetPoint over GetPlane)
2. Use Rhino commands (`_Enter`) not keyboard simulation
3. Consider modifying the Grasshopper script for easier automation

## Related Files

- `Rahmentuer_UD4.gh` - Simplified script (recommended)
- `Rahmentuer_UD3.gh` - Original script with GetPlane
- `dev/debug_getplane.py` - Debug script that found the `_Enter` solution
