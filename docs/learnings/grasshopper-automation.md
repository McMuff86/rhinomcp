# Grasshopper Automation Learnings

> Patterns and learnings for automating Grasshopper script execution.

## Quick Reference

- **Use GetPoint instead of GetPlane** - simpler and more reliable
- **Timing is critical:** 0.5s delay before inputs, 2.0s between scripts
- **Use `_Enter` not `""`** to confirm plane origin
- **Prompt matching:** Use partial strings like "lichthoe" for robustness
- **Track sent inputs with flags** to avoid duplicate sends

---

## Detailed Learnings

### Learning: GetPoint is Simpler than GetPlane
**Date:** 2026-01-11
**Context:** Automating door generation with Grasshopper
**Problem:** GetPlane requires 3 inputs (type, origin, confirm)
**Solution:** Modify GH script to use GetPoint with fixed XY plane

```python
# GetPlane (complex - 3 steps):
# 1. Plane type: "WorldXY"
# 2. Origin: "0,0,0"
# 3. Confirm: "_Enter"

# GetPoint (simple - 1 step):
# 1. Point: "0,0,0"
```

**Files:**
- `Rahmentuer_UD3.gh` - Original with GetPlane (complex)
- `Rahmentuer_UD4.gh` - Simplified with GetPoint (recommended)

---

### Learning: Use _Enter for Plane Confirmation
**Date:** 2026-01-11
**Context:** GetPlane step 3 confirmation
**Problem:** Empty string `""` doesn't work for confirmation
**Solution:** Use Rhino command `_Enter`

```python
# WRONG:
send_input("")  # Does NOT work!

# CORRECT:
send_input("_Enter")  # Works! ✅
```

---

### Learning: Timing Between Scripts is Critical
**Date:** 2026-01-11
**Context:** Creating multiple doors in sequence
**Solution:** Proper delays and prompt waiting

```python
async def create_door(ws, height, width, point):
    # 1. Wait before starting
    await asyncio.sleep(0.5)
    
    # 2. Start script
    await ws.send(json.dumps({
        "command": "run_script",
        "script": f'_-GrasshopperPlayer "{GH_FILE}"'
    }))
    
    # 3. React to prompts with delay
    await asyncio.sleep(0.5)  # Delay before EACH input!
    await ws.send({"command": "send_input", "input": str(height)})
    
    # 4. Wait after completion
    await asyncio.sleep(2.0)
```

**Key timing rules:**
- 0.5s delay before each input
- 2.0s wait between scripts
- Wait for "Command" prompt before next script

---

### Learning: Track Sent Inputs with Flags
**Date:** 2026-01-11
**Context:** Prompt events may repeat, causing duplicate inputs
**Solution:** Use flags to track which inputs were already sent

```python
sent_height = False
sent_width = False
sent_point = False

for event in events:
    if event["type"] == "Prompt":
        text = event["text"].lower()
        
        if "lichthoe" in text and not sent_height:
            await send_input(str(height))
            sent_height = True
        elif "lichtbreite" in text and not sent_width:
            await send_input(str(width))
            sent_width = True
        elif "get point" in text and not sent_point:
            await send_input(point)
            sent_point = True
```

---

### Learning: Partial String Matching for Prompts
**Date:** 2026-01-11
**Context:** Prompt text may vary slightly
**Solution:** Match partial strings for robustness

```python
# Robust matching:
if "lichthoe" in text.lower():  # matches "Lichthoehe", "lichthoehe:", etc.
    ...

# Instead of exact matching:
if text == "Lichthoehe":  # May fail with different formatting
    ...
```

---

### Learning: ScriptCompleted Event Pattern
**Date:** 2026-01-11
**Context:** Detecting when GrasshopperPlayer finishes
**Solution:** Wait for ScriptCompleted, then Command prompt

```python
elif event["type"] == "ScriptCompleted":
    # Script finished, wait for Command prompt
    await wait_for_command_prompt(ws)
    return True

async def wait_for_command_prompt(ws, timeout=5):
    """Wait until Rhino returns to Command prompt."""
    for _ in range(int(timeout / 0.2)):
        event = await asyncio.wait_for(ws.recv(), timeout=0.5)
        data = json.loads(event)
        if data["type"] == "Prompt" and data["text"].lower() == "command":
            return True
        await asyncio.sleep(0.2)
    return False
```

---

## Complete Multi-Door Pattern

```python
# dev/create_3_doors.py pattern
async def create_multiple_doors():
    doors = [
        {"height": 2200, "width": 1200, "point": "0,0,0"},
        {"height": 2200, "width": 900, "point": "2000,0,0"},
        {"height": 2400, "width": 1000, "point": "4000,0,0"},
    ]
    
    async with websockets.connect("ws://127.0.0.1:2000") as ws:
        # Wait for initial connection
        await ws.recv()
        
        for door in doors:
            success = await create_door(
                ws, 
                door["height"], 
                door["width"], 
                door["point"]
            )
            if success:
                print(f"Door created at {door['point']} ✓")
            
            # Wait between scripts
            await asyncio.sleep(2.0)
```

---

## Door Object Structure (Rahmentuer_UD4.gh)

| Layer | Count | Type |
|-------|-------|------|
| Intumex_Rahmen | 2 | Brep |
| Tuerrahmen | 3 | Brep |
| Tuerblatt | 1 | Brep |

**Total:** 6 objects per door

---

## Best Practices

1. **Simplify GH scripts** - Use GetPoint instead of GetPlane where possible
2. **Use fixed planes** - Set plane in GH, only get origin from user
3. **Test manually first** - Verify prompt sequence before automation
4. **Use partial matching** - More robust than exact string matching
5. **Track input state** - Prevent duplicate sends with flags
6. **Add delays** - Rhino needs time to process inputs
7. **Wait for completion** - Don't start next script until current finishes
