# WebSocket Streaming Patterns

> Patterns and learnings for real-time Rhino monitoring via WebSocket.

## Quick Reference

- **Port 2000** for WebSocket (Port 1999 for TCP commands)
- **Fleck library** in C# for WebSocket server
- **Event types:** Connected, Prompt, History, ScriptCompleted, Heartbeat
- **Polling at 100ms** for command line changes
- **Event buffer:** Max 500 events with deque

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent / MCP Client                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│   TCP Port 1999 │              │  WS Port 2000   │
│   (Commands)    │              │   (Events)      │
└────────┬────────┘              └────────┬────────┘
         │                                 │
         └────────────────┬────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    RhinoMCP Plugin                           │
│  - RhinoMCPServer.cs (TCP)                                  │
│  - RhinoMCPWebSocketServer.cs (WebSocket)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Event Types

| Type | Description | When Sent |
|------|-------------|-----------|
| Connected | Initial connection | On WebSocket connect |
| Prompt | Command prompt changed | Rhino asks for input |
| History | New command history | Command executed |
| ScriptStarted | Script execution began | After run_script |
| ScriptCompleted | Script finished | Script done |
| InputResult | Input was sent | After send_input |
| CancelResult | Command cancelled | After cancel |
| Heartbeat | Connection health | Every 30 seconds |
| Pong | Response to ping | After client ping |

---

## Detailed Learnings

### Learning: Polling is More Reliable Than Events
**Date:** 2026-01-11
**Context:** Implementing command line monitoring
**Problem:** `RhinoApp.CommandLineOut` event unreliable
**Solution:** Poll command line state every 100ms

```csharp
// C# polling approach
private void MonitorCommandLine()
{
    while (_isMonitoring)
    {
        Thread.Sleep(100);
        
        string currentPrompt = RhinoApp.CommandPrompt;
        if (currentPrompt != _lastPrompt)
        {
            BroadcastEvent("Prompt", currentPrompt);
            _lastPrompt = currentPrompt;
        }
    }
}
```

---

### Learning: Thread-Safe Client Broadcasting
**Date:** 2026-01-11
**Context:** Multiple clients connected to WebSocket
**Solution:** Use ToList() snapshot to avoid lock during I/O

```csharp
private void BroadcastEvent(string type, string text)
{
    var message = JsonConvert.SerializeObject(new {
        type = type,
        text = text,
        timestamp = DateTime.UtcNow.ToString("o")
    });
    
    // Snapshot to avoid lock during I/O
    var clients = _allSockets.ToList();
    foreach (var socket in clients)
    {
        try { socket.Send(message); }
        catch { /* client disconnected */ }
    }
}
```

---

### Learning: WebSocket Commands from Client
**Date:** 2026-01-11
**Context:** Need to send input and run scripts via WebSocket
**Solution:** Handle commands in OnMessage

```csharp
socket.OnMessage = message =>
{
    var cmd = JsonConvert.DeserializeObject<JObject>(message);
    string command = cmd["command"]?.ToString();
    
    switch (command)
    {
        case "send_input":
            string input = cmd["input"]?.ToString();
            RhinoApp.SendKeystrokes(input + "\n", true);
            BroadcastEvent("InputResult", "ok");
            break;
            
        case "run_script":
            string script = cmd["script"]?.ToString();
            RhinoApp.RunScript(script, false);
            BroadcastEvent("ScriptStarted", script);
            break;
            
        case "cancel":
            RhinoApp.SendKeystrokes("\x1b", true);  // ESC
            BroadcastEvent("CancelResult", "cancelled");
            break;
    }
};
```

---

### Learning: Python Async WebSocket Client
**Date:** 2026-01-11
**Context:** MCP tools need to connect to WebSocket
**Solution:** Singleton async client with event buffering

```python
class RhinoWebSocketClient:
    _instance = None
    
    def __init__(self):
        self._ws = None
        self._events = deque(maxlen=500)
        self._connected = False
    
    async def connect(self, uri="ws://127.0.0.1:2000"):
        import websockets
        self._ws = await websockets.connect(uri)
        self._connected = True
        asyncio.create_task(self._receive_loop())
    
    async def _receive_loop(self):
        async for message in self._ws:
            event = json.loads(message)
            self._events.append(event)
    
    async def wait_for_prompt(self, pattern, timeout=10.0):
        start = time.time()
        while time.time() - start < timeout:
            for event in reversed(self._events):
                if event["type"] == "Prompt":
                    if pattern.lower() in event["text"].lower():
                        return event
            await asyncio.sleep(0.1)
        return None
```

---

### Learning: Request-Response Pattern with UUID
**Date:** 2026-01-11
**Context:** Need to track async operations
**Solution:** Include request_id in commands

```python
async def run_script(self, script: str) -> dict:
    request_id = str(uuid.uuid4())
    await self._ws.send(json.dumps({
        "command": "run_script",
        "script": script,
        "request_id": request_id
    }))
    
    # Wait for response with matching ID
    response = await self._wait_for_response(request_id)
    return response
```

---

## MCP Tools for WebSocket

| Tool | Description |
|------|-------------|
| `connect_rhino_stream()` | Connect to WebSocket (Port 2000) |
| `disconnect_rhino_stream()` | Disconnect from stream |
| `send_rhino_input(value)` | Send input to Rhino command line |
| `wait_for_prompt(pattern, timeout)` | Wait for specific prompt |
| `run_script_async(script)` | Run script without blocking |
| `cancel_rhino_command()` | Cancel current command (ESC) |
| `get_stream_status()` | Check connection status |
| `get_stream_events()` | Get buffered events |
| `clear_stream_buffer()` | Clear event buffer |

---

## Best Practices

1. **Use WebSocket for events, TCP for commands** - Separation of concerns
2. **Buffer events** - Use deque with maxlen for memory management
3. **Snapshot before broadcast** - Avoid lock during network I/O
4. **Background thread for monitoring** - Don't block UI thread
5. **Graceful shutdown** - Stop monitoring before disposing server
6. **Heartbeat for health** - 30 second ping keeps connection alive
7. **Request IDs for async** - Track which response matches which request
