# Getting Unstuck - Best Practices for RhinoMCP Agents

> **When Rhino is waiting for input and you don't know what to do, or when commands hang.**

**Last Updated:** 2026-01-12  
**Context:** Grasshopper automation, interactive command handling  
**Principle:** Try to understand prompts first, cancel only as last resort when timeout exceeded

---

## 🚨 Quick Reference

| Situation | Solution | Tool |
|-----------|----------|------|
| Rhino waiting for input (unknown prompt) | **Try to understand first** → Analyze prompt, check context | `get_stream_status()` + prompt analysis |
| Script hangs/timeout (>60s) | **Last resort:** Cancel command | `cancel_rhino_command()` |
| WebSocket disconnected | Reconnect | Auto-reconnect in `websocket_client.py` |
| Multiple prompts, unsure which | Check current prompt, analyze pattern | `get_stream_status()` + pattern matching |

---

## Common "Stuck" Scenarios

### 1. **Unknown Prompt / Unexpected Input Request**

**Symptom:**
- Rhino shows a prompt you don't recognize
- You don't have a matching input pattern
- Script is waiting for input

**⚠️ IMPORTANT: Don't cancel immediately! Try to understand first.**

**Solution - Step by Step:**

```python
# Step 1: Get current state and analyze the prompt
from rhinomcp.tools.stream_commands import get_stream_status

status = await get_stream_status(ctx)
current_prompt = status.get("current_prompt", "")

# Step 2: Analyze the prompt intelligently
# Look for keywords, numbers, patterns, context clues

# Example analysis:
if "height" in current_prompt.lower() or "hoehe" in current_prompt.lower():
    # It's asking for height - try a reasonable default (e.g., 2200mm)
    await send_input("2200")
elif "width" in current_prompt.lower() or "breite" in current_prompt.lower():
    # It's asking for width - try a reasonable default (e.g., 1200mm)
    await send_input("1200")
elif "point" in current_prompt.lower() or "punkt" in current_prompt.lower():
    # It's asking for a point - use origin or reasonable default
    await send_input("0,0,0")
elif "<" in current_prompt and ">" in current_prompt:
    # Prompt shows default value in brackets - try accepting default
    await send_input("_Enter")
elif "yes" in current_prompt.lower() or "no" in current_prompt.lower():
    # Boolean question - try "yes" or accept default
    await send_input("_Enter")  # or "yes"
else:
    # Step 3: If truly unknown after analysis, wait a bit
    # Maybe the script is still processing
    await asyncio.sleep(2.0)
    
    # Step 4: Check again - maybe prompt changed
    status = await get_stream_status(ctx)
    new_prompt = status.get("current_prompt", "")
    
    if new_prompt != current_prompt:
        # Prompt changed - try again with new prompt
        # (recursive call or retry logic)
        pass
    else:
        # Step 5: LAST RESORT - Only cancel if timeout exceeded (>60s)
        # or if we've tried multiple times
        if timeout_exceeded or retry_count > 3:
            from rhinomcp.tools.stream_commands import cancel_rhino_command
            await cancel_rhino_command(ctx)
```

**Best Practice:**
1. ✅ **First:** Analyze prompt for keywords, numbers, context
2. ✅ **Second:** Try reasonable defaults based on prompt analysis
3. ✅ **Third:** Wait and check if prompt changes
4. ❌ **Last Resort:** Cancel only if timeout exceeded or multiple retries failed

**What Cancel does (when used):**
- Sends `_Esc` (Escape key) to Rhino
- Also sends `_Cancel` as fallback
- Cancels current operation
- Returns to Command prompt

---

### 2. **Script Timeout / Hanging**

**Symptom:**
- Script started but no completion event
- WebSocket timeout after 60+ seconds
- No new prompts appearing

**⚠️ IMPORTANT: Only cancel if timeout really exceeded (>60s). Scripts may take time to process.**

**Solution:**
```python
import asyncio
from rhinomcp.tools.stream_commands import get_stream_status, cancel_rhino_command

# Step 1: Check current state first
status = await get_stream_status(ctx)
current_prompt = status.get("current_prompt", "")

# Step 2: If waiting for input, try to understand it
if current_prompt and current_prompt.lower() != "command":
    # Script is waiting - analyze prompt (see Scenario 1)
    # Try to provide input based on prompt analysis
    # ...
    pass

# Step 3: Only cancel if timeout exceeded (>60s) AND no progress
timeout_seconds = 60
if timeout_exceeded and current_prompt == last_prompt:
    # No progress for 60+ seconds - cancel as last resort
    await cancel_rhino_command(ctx)
    
    # Step 4: Check state after cancel
    status = await get_stream_status(ctx)
    # Check status["current_prompt"] to see where we are
```

**Best Practice:**
- Set reasonable timeouts (30-60s for interactive scripts)
- **Wait for script to process** - geometry creation takes time
- **Only cancel if:** Timeout exceeded (>60s) AND no prompt changes
- Check state before and after cancel

---

### 3. **WebSocket Connection Issues**

**Symptom:**
- "WebSocket client disconnected" in logs
- Connection errors
- Can't send inputs

**Understanding:**
- **WebSocket connections are short-lived by design**
- Each script execution may create a new connection
- Disconnections are normal after script completion
- The client auto-reconnects when needed

**Why disconnections happen (NORMAL behavior):**
- ✅ Script completes → connection closes (normal)
- ✅ Timeout → connection closes (normal)
- ✅ Multiple scripts → each may use separate connection
- ✅ Client closes connection after receiving all events
- ⚠️ Error → connection closes (reconnect needed)

**Solution:**
```python
# The websocket_client handles reconnection automatically
from rhinomcp.websocket_client import get_websocket_client

ws_client = get_websocket_client()
if not ws_client.is_connected:
    await ws_client.start_listening()  # Auto-reconnects
```

**Important:** Seeing "WebSocket client disconnected" in logs is **normal** and **expected**. It doesn't mean there's a problem - it just means:
1. The script finished executing
2. All events were received
3. The connection was closed cleanly
4. Next script will create a new connection

**Pattern:** Each interactive script typically:
1. Opens WebSocket connection
2. Sends script command
3. Receives events (prompts, history, etc.)
4. Sends inputs as needed
5. Closes connection when done

This is **by design** - not a bug!

---

### 4. **Multiple Prompts / Complex Flow**

**Symptom:**
- Script asks for many inputs
- You're not sure which input comes next
- Pattern matching fails

**Solution:**
```python
# Use get_stream_status to check current state
status = await get_stream_status(ctx)
current_prompt = status.get("current_prompt", "")

# Match against known patterns
if "lichthoe" in current_prompt.lower():
    # Send height
    await send_input("2200")
elif "lichtbreite" in current_prompt.lower():
    # Send width
    await send_input("1200")
elif "get point" in current_prompt.lower():
    # Send point
    await send_input("0,0,0")
else:
    # Unknown prompt - TRY TO UNDERSTAND FIRST
    # Analyze prompt for keywords, numbers, context
    
    # Look for common patterns:
    if "<" in current_prompt and ">" in current_prompt:
        # Has default value - try accepting it
        await send_input("_Enter")
    elif any(keyword in current_prompt.lower() for keyword in ["yes", "no", "ok", "continue"]):
        # Boolean/confirmation - try yes or Enter
        await send_input("_Enter")
    elif any(keyword in current_prompt.lower() for keyword in ["number", "value", "input"]):
        # Asking for numeric input - try reasonable default
        await send_input("0")
    else:
        # Wait a bit - maybe script is still processing
        await asyncio.sleep(2.0)
        
        # Check again
        status = await get_stream_status(ctx)
        new_prompt = status.get("current_prompt", "")
        
        # Only cancel if still stuck after timeout
        if timeout_exceeded or (new_prompt == current_prompt and retry_count > 2):
            await cancel_rhino_command(ctx)
```

**Best Practice:**
- Always check `current_prompt` before sending input
- Use partial string matching (case-insensitive)
- **Try to understand unknown prompts** - look for keywords, defaults, context
- **Only cancel if:** Multiple retries failed AND timeout exceeded

---

## Cancel Command Details

### How It Works

The `cancel_rhino_command()` tool sends `_Cancel` to Rhino, which:
1. Cancels the current command
2. Returns to Command prompt
3. Clears any pending input requests

### When to Use

✅ **DO cancel when (LAST RESORT ONLY):**
- Script timeout exceeded (>60s) AND no progress
- Multiple retry attempts failed (>3 attempts)
- Wrong input was sent AND can't recover
- Need to abort current operation AND no other option

❌ **DON'T cancel when:**
- Unknown prompt appears → **Try to understand it first!**
- Script is progressing normally
- Just waiting for next prompt (normal delay)
- Script is creating geometry (may take time)
- Prompt shows default value → Try accepting default first
- Prompt contains recognizable keywords → Analyze and try reasonable input

---

## Esc Key Implementation

**Implementation:** The `cancel_rhino_command()` tool sends both `_Esc` and `_Cancel`:
1. `_Esc` - Simulates pressing Escape key (immediate cancel)
2. `_Cancel` - Rhino's native cancel command (fallback)

This dual approach ensures maximum reliability, just like a human pressing Esc in Rhino.

**You don't need to send Esc manually** - `cancel_rhino_command()` handles it automatically.

---

## Pattern: "Unstuck" Workflow (Intelligent Approach)

```python
async def handle_stuck_situation(ctx, timeout_seconds=60, max_retries=3):
    """
    Standard workflow when stuck or unsure what to do.
    Tries to understand prompts before canceling.
    """
    retry_count = 0
    start_time = time.time()
    
    while retry_count < max_retries:
        # 1. Check current state
        status = await get_stream_status(ctx)
        current_prompt = status.get("current_prompt", "")
        
        # 2. If at command prompt - safe to continue
        if not current_prompt or current_prompt.lower() == "command":
            return True
        
        # 3. Try to understand the prompt
        input_sent = await try_understand_and_respond(current_prompt)
        
        if input_sent:
            # Successfully sent input - wait for next prompt
            await asyncio.sleep(1.0)
            retry_count = 0  # Reset retry counter
            continue
        
        # 4. Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            # Timeout exceeded - cancel as last resort
            result = await cancel_rhino_command(ctx)
            return result.get("cancelled", False)
        
        # 5. Wait and retry
        retry_count += 1
        await asyncio.sleep(2.0)
    
    # Max retries exceeded - cancel
    result = await cancel_rhino_command(ctx)
    return result.get("cancelled", False)


async def try_understand_and_respond(prompt: str) -> bool:
    """
    Try to understand a prompt and send appropriate input.
    Returns True if input was sent, False if prompt is truly unknown.
    """
    prompt_lower = prompt.lower()
    
    # Pattern 1: Has default value in brackets
    if "<" in prompt and ">" in prompt:
        await send_input("_Enter")  # Accept default
        return True
    
    # Pattern 2: Height-related keywords
    if any(kw in prompt_lower for kw in ["height", "hoehe", "hoch", "tall"]):
        await send_input("2200")  # Reasonable default height
        return True
    
    # Pattern 3: Width-related keywords
    if any(kw in prompt_lower for kw in ["width", "breite", "wide"]):
        await send_input("1200")  # Reasonable default width
        return True
    
    # Pattern 4: Point-related keywords
    if any(kw in prompt_lower for kw in ["point", "punkt", "position", "location"]):
        await send_input("0,0,0")  # Origin point
        return True
    
    # Pattern 5: Boolean/confirmation
    if any(kw in prompt_lower for kw in ["yes", "no", "ok", "continue", "confirm"]):
        await send_input("_Enter")  # Accept/confirm
        return True
    
    # Pattern 6: Numeric input
    if any(kw in prompt_lower for kw in ["number", "value", "input", "enter"]):
        await send_input("0")  # Default numeric value
        return True
    
    # Pattern 7: Side/direction (like "Bandseite")
    if any(kw in prompt_lower for kw in ["side", "seite", "left", "right", "links", "rechts"]):
        await send_input("_Enter")  # Accept default
        return True
    
    # Unknown - couldn't understand
    return False
```

---

## Real-World Example: Rahmentuer_UD5.gh

**Problem:** Script asks for 4 inputs, but you only know 3 patterns.

**Solution:**
```python
inputs_sent = 0
max_inputs = 4

for iteration in range(100):
    event = await ws.recv()
    
    if event["type"] == "Prompt":
        prompt = event["text"].lower()
        
        # Known patterns
        if "lichthoe" in prompt and inputs_sent == 0:
            await send_input("2200")
            inputs_sent += 1
        elif "lichtbreite" in prompt and inputs_sent == 1:
            await send_input("1200")
            inputs_sent += 1
        elif "get point" in prompt and inputs_sent == 2:
            await send_input("0,0,0")
            inputs_sent += 1
        elif "bandseite" in prompt and inputs_sent == 3:
            await send_input("_Enter")  # Accept default
            inputs_sent += 1
        else:
            # Unknown prompt - TRY TO UNDERSTAND FIRST
            # Analyze prompt for keywords, defaults, context
            if "<" in prompt and ">" in prompt:
                # Has default - try accepting it
                await send_input("_Enter")
            elif any(kw in prompt.lower() for kw in ["height", "hoehe", "width", "breite", "point", "punkt"]):
                # Recognizable keyword - try reasonable default
                if "height" in prompt.lower() or "hoehe" in prompt.lower():
                    await send_input("2200")
                elif "width" in prompt.lower() or "breite" in prompt.lower():
                    await send_input("1200")
                elif "point" in prompt.lower() or "punkt" in prompt.lower():
                    await send_input("0,0,0")
            else:
                # Wait a bit - maybe script is processing
                await asyncio.sleep(2.0)
                
                # Check if prompt changed
                new_event = await ws.recv()
                if new_event.get("type") == "Prompt" and new_event.get("text") != prompt:
                    # Prompt changed - continue
                    continue
                elif timeout_exceeded:
                    # Only cancel if timeout exceeded
                    await cancel_rhino_command(ctx)
                    break
```

---

## Key Learnings

1. **Try to understand first** - Analyze prompts for keywords, defaults, context before canceling
2. **Cancel is last resort** - Only cancel if timeout exceeded (>60s) or multiple retries failed
3. **Check state first** - Always check `current_prompt` before acting
4. **WebSocket disconnections are normal** - They happen after script completion
5. **Use timeouts** - Set reasonable timeouts (30-60s) for interactive scripts
6. **Pattern matching** - Use partial, case-insensitive matching for robustness
7. **Intelligent defaults** - Try reasonable defaults based on prompt analysis (height=2200, width=1200, point=0,0,0)
8. **Wait for processing** - Scripts may take time to create geometry - don't cancel too quickly

---

## Related Documentation

- `docs/learnings/grasshopper-automation.md` - Grasshopper automation patterns
- `docs/learnings/websocket-patterns.md` - WebSocket usage patterns
- `rhino_mcp_server/src/rhinomcp/tools/stream_commands.py` - Cancel implementation
