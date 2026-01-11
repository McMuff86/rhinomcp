# Solved Issue: WebSocket Door Automation

**Status:** ✅ SOLVED
**Date Solved:** 2026-01-11
**Solution:** Proper timing + GetPoint script + input flags

---

## Original Problem

When running multiple Grasshopper scripts in sequence:
- Doors 2 and 3 were not created
- Prompts were missed or inputs sent too early
- ScriptCompleted showed success but no geometry

## Root Causes

1. **Timing too fast** - Inputs sent before Rhino processed the prompt
2. **No wait between scripts** - Next script started before previous finished
3. **Duplicate inputs** - Same input sent multiple times without flags

## Solution Implemented

### 1. Input Flags
```python
sent_height = False
sent_width = False
sent_point = False

if "lichthoe" in text and not sent_height:
    send_input(height)
    sent_height = True
```

### 2. Delay Before Input
```python
await asyncio.sleep(0.5)  # Wait before sending input
```

### 3. Wait Between Scripts
```python
await asyncio.sleep(2.0)  # Wait after each door
```

### 4. Wait for Command Prompt
```python
# After ScriptCompleted, wait for Command prompt
await wait_for_command_prompt(ws, timeout=5.0)
```

## Timing Rules

| Action | Delay |
|--------|-------|
| Before each input | 0.5s |
| Between scripts | 2.0s |
| After ScriptCompleted | Wait for "Command" prompt |

## Result

```
DOOR 1: 2200x1200mm at 0,0,0       ✓
DOOR 2: 2200x900mm  at 2000,0,0    ✓
DOOR 3: 2400x1000mm at 4000,0,0    ✓

New objects: 18 (6 per door)
```

## Related Files

- `dev/create_3_doors.py` - Working multi-door script
- `docs/GRASSHOPPER_AUTOMATION.md` - Updated documentation
