# Grasshopper Automation Guide

**Last Updated:** 2026-01-11
**Status:** Refactored - Clean WebSocket Implementation

---

## Overview

This guide explains how to run interactive Grasshopper scripts that require user input using the WebSocket-based automation approach.

---

## Architecture

The automation uses a two-channel approach:

```
Port 1999 (TCP)              Port 2000 (WebSocket)
┌─────────────────┐          ┌─────────────────┐
│  Commands       │          │  Events         │
│  - run_script   │          │  - Prompt       │
│  - send_input   │          │  - History      │
└────────┬────────┘          └────────┬────────┘
         └────────────┬───────────────┘
                      │
            ┌─────────┴─────────┐
            │  RhinoMCP Plugin  │
            └───────────────────┘
```

---

## Available Tools

### Connection Management

| Tool | Description |
|------|-------------|
| `connect_rhino_stream()` | Connect to WebSocket for real-time events |
| `disconnect_rhino_stream()` | Disconnect from WebSocket |
| `get_stream_status()` | Check connection status |

### Command Execution

| Tool | Description |
|------|-------------|
| `run_script_async(script)` | Start a script asynchronously |
| `send_rhino_input(value)` | Send input to Rhino command line |
| `cancel_rhino_command()` | Cancel current command |

### Prompt Monitoring

| Tool | Description |
|------|-------------|
| `wait_for_prompt(pattern, timeout)` | Wait for specific prompt |
| `get_stream_events()` | Get buffered events |
| `clear_stream_buffer()` | Clear event buffer |

### Grasshopper Helpers

| Tool | Description |
|------|-------------|
| `run_grasshopper_interactive(file, inputs)` | Run GH with auto-inputs |
| `run_door_script(file, height, width, origin)` | Run door script |

---

## Usage Patterns

### Pattern 1: Manual Control

```python
# 1. Connect to stream
connect_rhino_stream()

# 2. Start interactive script
run_script_async('_-GrasshopperPlayer "path/to/script.gh"')

# 3. Wait for prompts and respond
prompt = wait_for_prompt("lichthoehe", timeout=10)
if prompt:
    send_rhino_input("2200")

prompt = wait_for_prompt("lichtbreite", timeout=5)
if prompt:
    send_rhino_input("910")

# 4. Cleanup
disconnect_rhino_stream()
```

### Pattern 2: Automatic Input Mapping

```python
# Use pattern-based auto-input
run_grasshopper_interactive(
    file_path="C:/path/to/door.gh",
    inputs={
        "lichthoehe": "2200",
        "lichtbreite": "910",
        "getplane.*worldxy": "WorldXY",
        "getplane.*parallel": "0,0,0",
    }
)
```

### Pattern 3: Door Script Wrapper

```python
# Specific helper for door creation
run_door_script(
    file_path="C:/path/to/Rahmentuer_UD3.gh",
    height=2200,
    width=910,
    origin="0,0,0",
    plane="WorldXY"
)
```

---

## Recommended: Simplified Script with GetPoint ✅

The **best solution** is to use a simplified Grasshopper script that uses **GetPoint instead of GetPlane**.

### Rahmentuer_UD4.gh (Simplified)

Only 3 inputs required:
```
1. Lichthoehe: → 2200
2. Lichtbreite ( Undo ): → 1200
3. Get Point ( Undo ): → 0,1200,0
```

**Result:** `1 closed polysurface added to selection.`

### Test Script

```python
async with websockets.connect("ws://127.0.0.1:2000") as ws:
    await ws.send(json.dumps({
        "command": "run_script",
        "script": f'_-GrasshopperPlayer "C:/path/Rahmentuer_UD4.gh"'
    }))
    
    # React to prompts
    if "lichthoe" in prompt:  # Match partial for robustness
        await ws.send(json.dumps({"command": "send_input", "input": "2200"}))
    elif "lichtbreite" in prompt:
        await ws.send(json.dumps({"command": "send_input", "input": "1200"}))
    elif "get point" in prompt:
        await ws.send(json.dumps({"command": "send_input", "input": "0,1200,0"}))
```

**Test file:** `dev/test_door_ud4.py`

---

## Creating Multiple Objects

To create multiple objects in sequence, proper timing is critical.

### Pattern: Multi-Door Creation

```python
DOORS = [
    {"height": 2200, "width": 1200, "point": "0,0,0"},
    {"height": 2200, "width": 900, "point": "2000,0,0"},
    {"height": 2400, "width": 1000, "point": "4000,0,0"},
]

async def create_door(ws, height, width, point):
    # 1. Wait before starting
    await asyncio.sleep(0.5)
    
    # 2. Start script
    await ws.send(json.dumps({
        "command": "run_script",
        "script": f'_-GrasshopperPlayer "{GH_FILE}"'
    }))
    
    # 3. Track sent inputs with flags
    sent_height = sent_width = sent_point = False
    
    # 4. React to prompts
    for _ in range(40):
        event = json.loads(await ws.recv())
        
        if event["type"] == "Prompt":
            text = event["text"].lower()
            await asyncio.sleep(0.5)  # Important delay!
            
            if "lichthoe" in text and not sent_height:
                await ws.send(json.dumps({"command": "send_input", "input": str(height)}))
                sent_height = True
            elif "lichtbreite" in text and not sent_width:
                await ws.send(json.dumps({"command": "send_input", "input": str(width)}))
                sent_width = True
            elif "get point" in text and not sent_point:
                await ws.send(json.dumps({"command": "send_input", "input": point}))
                sent_point = True
            elif text.strip() == "command":
                return True  # Done!
                
        elif event["type"] == "ScriptCompleted":
            return True

# Main loop
for door in DOORS:
    await create_door(ws, door["height"], door["width"], door["point"])
    await asyncio.sleep(2.0)  # Wait between doors!
```

### Critical Timing Rules

| Rule | Value | Reason |
|------|-------|--------|
| Delay before input | 0.5s | Let Rhino process prompt |
| Wait between scripts | 2.0s | Let Rhino create geometry |
| Max iterations | 40 | Timeout safety |

### Test File

**Multi-door test:** `dev/create_3_doors.py`

```
Result:
DOOR 1: 2200x1200mm at 0,0,0       ✓
DOOR 2: 2200x900mm  at 2000,0,0    ✓
DOOR 3: 2400x1000mm at 4000,0,0    ✓

New objects: 18 (6 per door)
```

---

## Alternative: GetPlane with _Enter

If you must use GetPlane (Rahmentuer_UD3.gh), the 3 steps are:

```
1. GetPlane ( WorldXY  WorldYZ  WorldZX  Undo )  → Send "WorldXY"
2. GetPlane ( ParallelGrid  ParallelXY ... )     → Send origin "0,0,0"
3. GetPlane ( Undo )                             → Send "_Enter" ✅
```

**Important:** Step 3 requires the Rhino command `_Enter`, not an empty string!

```python
# WRONG - Does NOT work:
send_input("")

# CORRECT - Works!
send_input("_Enter")
```

---

## Event Types

Events received via WebSocket:

| Type | Description |
|------|-------------|
| `Connected` | Initial connection with current prompt |
| `Prompt` | Command prompt changed (Rhino asking for input) |
| `History` | New command history entry |
| `ScriptStarted` | Script execution began |
| `ScriptCompleted` | Script execution finished |
| `InputResult` | Result of send_input command |
| `Heartbeat` | Connection health check (every 30s) |

---

## Files

### Python Tools
- `rhino_mcp_server/src/rhinomcp/tools/stream_commands.py` - Stream tools
- `rhino_mcp_server/src/rhinomcp/tools/grasshopper_interactive.py` - GH helpers
- `rhino_mcp_server/src/rhinomcp/websocket_client.py` - WebSocket client

### C# Plugin
- `rhino_mcp_plugin/RhinoMCPWebSocketServer.cs` - WebSocket server
- `rhino_mcp_plugin/Functions/GrasshopperOperations.cs` - GH handlers

### Debug/Test
- `rhino_mcp_server/dev/test_door_ud4.py` - Single door test with GetPoint
- `rhino_mcp_server/dev/create_3_doors.py` - **Multi-door test (recommended)**
- `rhino_mcp_server/dev/debug_getplane.py` - GetPlane debugging
- `rhino_mcp_server/dev/check_objects.py` - Check object count in Rhino

---

## Troubleshooting

### Connection Issues
```
Error: Cannot connect to WebSocket
```
**Solution:** Make sure Rhino is running and `mcpstart` was executed.

### Prompts Not Detected
```
Timeout waiting for prompt
```
**Solution:** Check that the script actually prompts for input. Use `get_stream_events()` to see all events.

### Script Doesn't Complete
**Solution:** The script might be waiting for additional input. Use `debug_getplane.py` to investigate.

---

## See Also

- [AI_AGENT_RHINO_VISIBILITY.md](AI_AGENT_RHINO_VISIBILITY.md) - Real-time monitoring
- [AGENTS.md](../AGENTS.md) - Agent quick start
- [Ralph/progress.txt](../Ralph/progress.txt) - Session learnings
