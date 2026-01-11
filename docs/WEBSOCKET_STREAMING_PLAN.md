# WebSocket Real-Time Event Streaming - Implementation Plan

**Date:** 2026-01-11  
**Status:** PLANNED  
**Priority:** HIGH  
**Estimated Effort:** 8-12 hours

---

## Overview

Extend the current polling-based command line monitoring with real-time WebSocket streaming for immediate event notifications to AI agents.

### Current State (Polling)
- ✅ Agent polls `get_command_output()` to check for events
- ✅ Events captured on-demand via `CaptureCommandLineState()`
- ⚠️ Latency: 1-5 seconds depending on polling frequency
- ⚠️ Overhead: Repeated polling even when no events

### Target State (WebSocket Streaming)
- ✅ Events pushed to connected clients immediately
- ✅ Sub-second latency (<100ms)
- ✅ No polling overhead
- ✅ Multiple clients can subscribe
- ✅ Backwards compatible with polling API

---

## Architecture

### High-Level Design

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Rhino 3D      │         │  C# Plugin       │         │  Python MCP     │
│                 │         │  RhinoMCPServer  │         │  Server         │
│  CommandPrompt  │────────▶│                  │────────▶│                 │
│  CommandHistory │  Event  │  WebSocket       │  Stream │  WebSocket      │
│                 │  Capture│  Server (WS)     │  Events │  Client         │
│                 │         │  Port: 2000      │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │                            │
                                     │                            │
                                     ▼                            ▼
                            ┌─────────────────┐         ┌─────────────────┐
                            │ WebSocket       │◀────────│ AI Agent        │
                            │ Clients         │  WSS    │                 │
                            │ (Multiple)      │  Stream │ (Claude/GPT)    │
                            └─────────────────┘         └─────────────────┘
```

### Components

1. **C# WebSocket Server** (Rhino Plugin)
   - Runs alongside existing TCP server (port 1999)
   - WebSocket endpoint on port 2000
   - Background thread monitors command line changes
   - Broadcasts events to all connected clients

2. **Python WebSocket Client** (MCP Server)
   - Connects to C# WebSocket server
   - Maintains persistent connection
   - Provides async event stream to tools

3. **MCP Tools** (New)
   - `subscribe_command_stream()` - Start receiving events
   - `unsubscribe_command_stream()` - Stop receiving events
   - Polling tools remain for backwards compatibility

---

## Implementation Details

### Phase 1: C# WebSocket Server (4-5 hours)

#### Dependencies
```xml
<!-- Add to rhinomcp.csproj -->
<ItemGroup>
  <PackageReference Include="WebSocketSharp" Version="1.0.3-rc11" />
  <!-- or -->
  <PackageReference Include="Fleck" Version="1.2.0" />
</ItemGroup>
```

**Recommendation:** Use **Fleck** - simpler, more reliable, better maintained.

#### Implementation

**File:** `rhino_mcp_plugin/RhinoMCPWebSocketServer.cs` (NEW)

```csharp
using System;
using System.Collections.Generic;
using System.Threading;
using Fleck;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin
{
    /// <summary>
    /// WebSocket server for real-time command line event streaming.
    /// </summary>
    public class RhinoMCPWebSocketServer
    {
        private WebSocketServer server;
        private Thread monitorThread;
        private bool isRunning = false;
        private List<IWebSocketConnection> clients = new List<IWebSocketConnection>();
        private readonly object clientsLock = new object();
        
        private string lastCommandPrompt = "";
        private string lastCommandHistory = "";
        private const int MonitorIntervalMs = 100; // Check every 100ms
        
        public void Start(string host = "127.0.0.1", int port = 2000)
        {
            if (isRunning)
            {
                RhinoApp.WriteLine("WebSocket server already running");
                return;
            }
            
            // Start WebSocket server
            server = new WebSocketServer($"ws://{host}:{port}");
            
            server.Start(socket =>
            {
                socket.OnOpen = () =>
                {
                    lock (clientsLock)
                    {
                        clients.Add(socket);
                    }
                    RhinoApp.WriteLine($"WebSocket client connected: {socket.ConnectionInfo.ClientIpAddress}");
                };
                
                socket.OnClose = () =>
                {
                    lock (clientsLock)
                    {
                        clients.Remove(socket);
                    }
                    RhinoApp.WriteLine($"WebSocket client disconnected");
                };
                
                socket.OnMessage = message =>
                {
                    // Handle client messages (e.g., subscribe/unsubscribe)
                    HandleClientMessage(socket, message);
                };
            });
            
            // Start monitoring thread
            isRunning = true;
            monitorThread = new Thread(MonitorCommandLine);
            monitorThread.IsBackground = true;
            monitorThread.Start();
            
            RhinoApp.WriteLine($"WebSocket server started on ws://{host}:{port}");
        }
        
        public void Stop()
        {
            isRunning = false;
            
            if (monitorThread != null)
            {
                monitorThread.Join(1000);
            }
            
            if (server != null)
            {
                server.Dispose();
            }
            
            RhinoApp.WriteLine("WebSocket server stopped");
        }
        
        private void MonitorCommandLine()
        {
            while (isRunning)
            {
                try
                {
                    // Check for command prompt changes
                    string currentPrompt = RhinoApp.CommandPrompt ?? "";
                    if (currentPrompt != lastCommandPrompt && !string.IsNullOrEmpty(currentPrompt))
                    {
                        BroadcastEvent(new
                        {
                            type = "Prompt",
                            timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                            text = currentPrompt
                        });
                        lastCommandPrompt = currentPrompt;
                    }
                    
                    // Check for command history changes
                    string historyText = RhinoApp.CommandHistoryWindowText ?? "";
                    if (historyText != lastCommandHistory && !string.IsNullOrEmpty(historyText))
                    {
                        if (historyText.StartsWith(lastCommandHistory))
                        {
                            string newText = historyText.Substring(lastCommandHistory.Length);
                            if (!string.IsNullOrWhiteSpace(newText))
                            {
                                var newLines = newText.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                                foreach (var line in newLines)
                                {
                                    if (!string.IsNullOrWhiteSpace(line))
                                    {
                                        BroadcastEvent(new
                                        {
                                            type = "History",
                                            timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                                            text = line
                                        });
                                    }
                                }
                            }
                        }
                        lastCommandHistory = historyText;
                    }
                }
                catch (Exception ex)
                {
                    RhinoApp.WriteLine($"Error in WebSocket monitor: {ex.Message}");
                }
                
                Thread.Sleep(MonitorIntervalMs);
            }
        }
        
        private void BroadcastEvent(object eventData)
        {
            string json = JObject.FromObject(eventData).ToString();
            
            lock (clientsLock)
            {
                foreach (var client in clients)
                {
                    try
                    {
                        client.Send(json);
                    }
                    catch (Exception ex)
                    {
                        RhinoApp.WriteLine($"Error sending to WebSocket client: {ex.Message}");
                    }
                }
            }
        }
        
        private void HandleClientMessage(IWebSocketConnection socket, string message)
        {
            try
            {
                var msg = JObject.Parse(message);
                string command = msg["command"]?.ToString();
                
                switch (command)
                {
                    case "subscribe":
                        // Client wants to receive events (default)
                        socket.Send(JObject.FromObject(new { status = "subscribed" }).ToString());
                        break;
                        
                    case "unsubscribe":
                        // Client wants to stop receiving events
                        socket.Send(JObject.FromObject(new { status = "unsubscribed" }).ToString());
                        break;
                        
                    case "ping":
                        // Health check
                        socket.Send(JObject.FromObject(new { status = "pong" }).ToString());
                        break;
                }
            }
            catch (Exception ex)
            {
                RhinoApp.WriteLine($"Error handling WebSocket message: {ex.Message}");
            }
        }
    }
}
```

**Integration into RhinoMCPServer.cs:**

```csharp
public class RhinoMCPServer
{
    private RhinoMCPWebSocketServer wsServer;
    
    public void Start()
    {
        // ... existing TCP server startup ...
        
        // Start WebSocket server
        wsServer = new RhinoMCPWebSocketServer();
        wsServer.Start("127.0.0.1", 2000);
    }
    
    public void Stop()
    {
        // ... existing TCP server shutdown ...
        
        // Stop WebSocket server
        if (wsServer != null)
        {
            wsServer.Stop();
        }
    }
}
```

---

### Phase 2: Python WebSocket Client (3-4 hours)

#### Dependencies
```toml
# Add to rhino_mcp_server/pyproject.toml
[project]
dependencies = [
    "websockets>=12.0",  # For async WebSocket client
    # ... existing dependencies ...
]
```

#### Implementation

**File:** `rhino_mcp_server/src/rhinomcp/websocket_client.py` (NEW)

```python
"""
WebSocket client for real-time Rhino command line event streaming.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncIterator, Callable, Optional
from queue import Queue
import websockets

logger = logging.getLogger("RhinoWebSocketClient")


class RhinoWebSocketClient:
    """
    WebSocket client for receiving real-time command line events from Rhino.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 2000):
        self.url = f"ws://{host}:{port}"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.event_queue: Queue = Queue()
        self.event_callbacks: list[Callable] = []
        self._running = False
        self._task = None
    
    async def connect(self) -> bool:
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.url)
            logger.info(f"Connected to Rhino WebSocket at {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        self._running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("Disconnected from WebSocket")
    
    async def start_listening(self):
        """Start listening for events in the background."""
        if not self.websocket:
            if not await self.connect():
                return
        
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
    
    async def stop_listening(self):
        """Stop listening for events."""
        self._running = False
        if self._task:
            await self._task
    
    async def _listen_loop(self):
        """Main event listening loop."""
        try:
            while self._running and self.websocket:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=1.0
                    )
                    event = json.loads(message)
                    
                    # Add to queue
                    self.event_queue.put(event)
                    
                    # Notify callbacks
                    for callback in self.event_callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            logger.error(f"Error in event callback: {e}")
                
                except asyncio.TimeoutError:
                    # No message received, continue
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error receiving WebSocket message: {e}")
                    break
        
        finally:
            await self.disconnect()
    
    def add_callback(self, callback: Callable):
        """Add a callback function to be called on each event."""
        self.event_callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a callback function."""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    async def get_events_stream(self) -> AsyncIterator[dict]:
        """
        Async iterator that yields events as they arrive.
        
        Usage:
            async for event in client.get_events_stream():
                print(f"Event: {event}")
        """
        if not self._running:
            await self.start_listening()
        
        while self._running:
            try:
                # Check queue for events
                if not self.event_queue.empty():
                    event = self.event_queue.get_nowait()
                    yield event
                else:
                    # Brief sleep to avoid busy-waiting
                    await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error in event stream: {e}")
                break
    
    def get_events_blocking(self, timeout: float = 1.0) -> list[dict]:
        """
        Get all events from the queue (blocking).
        
        Args:
            timeout: Maximum time to wait for events
        
        Returns:
            List of events received
        """
        events = []
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if not self.event_queue.empty():
                events.append(self.event_queue.get_nowait())
            else:
                break
        
        return events


# Global WebSocket client instance
_ws_client: Optional[RhinoWebSocketClient] = None


def get_websocket_client() -> RhinoWebSocketClient:
    """Get or create the global WebSocket client."""
    global _ws_client
    if _ws_client is None:
        _ws_client = RhinoWebSocketClient()
    return _ws_client
```

#### MCP Tools Integration

**File:** `rhino_mcp_server/src/rhinomcp/tools/subscribe_command_stream.py` (NEW)

```python
"""
Real-time command stream subscription tools.
"""

import json
from typing import Optional

from mcp.server.fastmcp import Context

from rhinomcp.server import logger, mcp
from rhinomcp.websocket_client import get_websocket_client
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok


@mcp.tool()
async def subscribe_command_stream(ctx: Context) -> str:
    """
    Subscribe to real-time command line event stream from Rhino.
    
    This tool enables push-based event notifications instead of polling.
    Events are delivered immediately as they occur in Rhino.
    
    Returns:
        JSON string with subscription status
    
    Example:
        # Start receiving real-time events
        subscribe_command_stream()
        
        # Events will be pushed to your client automatically
        # No need to poll with get_command_output()
    
    Notes:
        - Requires WebSocket server running in Rhino plugin
        - Events include: Prompt (input requests), History (command output)
        - Connection is persistent until unsubscribe or disconnect
    """
    try:
        ws_client = get_websocket_client()
        
        # Start listening for events
        await ws_client.start_listening()
        
        logger.info("Subscribed to command stream")
        return json.dumps(ok(
            message="Subscribed to real-time command stream",
            data={
                "status": "subscribed",
                "url": ws_client.url
            }
        ))
        
    except Exception as e:
        logger.error(f"Failed to subscribe to command stream: {e}")
        return json.dumps(from_exception(e, code=ErrorCode.CONNECTION_ERROR))


@mcp.tool()
async def unsubscribe_command_stream(ctx: Context) -> str:
    """
    Unsubscribe from real-time command line event stream.
    
    Stops receiving push notifications. You can still use get_command_output()
    for polling-based access.
    
    Returns:
        JSON string with unsubscription status
    """
    try:
        ws_client = get_websocket_client()
        
        # Stop listening
        await ws_client.stop_listening()
        
        logger.info("Unsubscribed from command stream")
        return json.dumps(ok(
            message="Unsubscribed from command stream",
            data={"status": "unsubscribed"}
        ))
        
    except Exception as e:
        logger.error(f"Failed to unsubscribe: {e}")
        return json.dumps(from_exception(e, code=ErrorCode.CONNECTION_ERROR))


@mcp.tool()
async def get_stream_events(
    ctx: Context,
    timeout: float = 1.0
) -> str:
    """
    Get events from the WebSocket stream (non-blocking).
    
    Retrieves all events that have been received since the last call.
    
    Args:
        ctx: MCP context
        timeout: Maximum time to wait for events (default: 1.0 second)
    
    Returns:
        JSON string with events
    
    Example:
        # Subscribe first
        subscribe_command_stream()
        
        # Then periodically get new events
        events = get_stream_events(timeout=0.5)
    """
    try:
        ws_client = get_websocket_client()
        
        # Get events from queue
        events = ws_client.get_events_blocking(timeout=timeout)
        
        return json.dumps(ok(
            message=f"Retrieved {len(events)} events from stream",
            data={
                "events": events,
                "count": len(events)
            }
        ))
        
    except Exception as e:
        logger.error(f"Failed to get stream events: {e}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))
```

---

### Phase 3: Testing & Documentation (2-3 hours)

#### Unit Tests

**File:** `rhino_mcp_server/tests/test_websocket_client.py` (NEW)

```python
"""Tests for WebSocket client."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from rhinomcp.websocket_client import RhinoWebSocketClient


@pytest.fixture
def ws_client():
    """Create WebSocket client for testing."""
    return RhinoWebSocketClient(host="127.0.0.1", port=2000)


@pytest.mark.asyncio
async def test_connect_success(ws_client):
    """Test successful WebSocket connection."""
    with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        
        result = await ws_client.connect()
        
        assert result is True
        assert ws_client.websocket is not None


@pytest.mark.asyncio
async def test_connect_failure(ws_client):
    """Test failed WebSocket connection."""
    with patch('websockets.connect', side_effect=Exception("Connection failed")):
        result = await ws_client.connect()
        
        assert result is False
        assert ws_client.websocket is None


@pytest.mark.asyncio
async def test_event_callback(ws_client):
    """Test event callback functionality."""
    received_events = []
    
    def callback(event):
        received_events.append(event)
    
    ws_client.add_callback(callback)
    
    # Simulate event
    test_event = {"type": "Prompt", "text": "Test prompt"}
    ws_client.event_queue.put(test_event)
    
    # Process event
    for cb in ws_client.event_callbacks:
        cb(test_event)
    
    assert len(received_events) == 1
    assert received_events[0] == test_event
```

#### Integration Tests

**File:** `rhino_mcp_server/tests/integration/test_websocket_streaming.py` (NEW)

```python
"""Integration tests for WebSocket streaming."""

import asyncio
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_time_event_streaming():
    """
    Test real-time event streaming with actual Rhino connection.
    
    Requirements:
    - Rhino must be running
    - MCP plugin must be loaded
    - WebSocket server must be started
    """
    from rhinomcp.websocket_client import get_websocket_client
    
    ws_client = get_websocket_client()
    
    # Connect
    connected = await ws_client.connect()
    assert connected, "Failed to connect to Rhino WebSocket"
    
    # Start listening
    await ws_client.start_listening()
    
    # Wait for some events (or timeout)
    await asyncio.sleep(2)
    
    # Check if we received any events
    events = ws_client.get_events_blocking(timeout=0.1)
    print(f"Received {len(events)} events")
    
    # Cleanup
    await ws_client.stop_listening()
```

#### Documentation Updates

Update the following files:

1. **`docs/AI_AGENT_RHINO_VISIBILITY.md`**
   - Add section on WebSocket streaming
   - Compare polling vs streaming
   - Usage examples

2. **`docs/WEBSOCKET_STREAMING.md`** (NEW)
   - Detailed WebSocket guide
   - Architecture diagrams
   - Troubleshooting

3. **`AGENTS.md`**
   - Update quick start with WebSocket option
   - Add WebSocket tools to tool list

4. **`README.md`**
   - Mention real-time streaming capability

---

## Deployment Strategy

### Rollout Phases

1. **Phase 1: Beta (Optional WebSocket)**
   - WebSocket server runs alongside TCP server
   - Polling API remains default
   - WebSocket is opt-in via `subscribe_command_stream()`
   - Monitor stability and performance

2. **Phase 2: Production (Recommended)**
   - WebSocket becomes recommended approach
   - Polling API kept for backwards compatibility
   - Documentation updated to promote WebSocket

3. **Phase 3: Optimization (Future)**
   - Consider deprecating polling API
   - WebSocket-only mode for maximum efficiency

### Backwards Compatibility

- ✅ All existing tools (`get_command_output`, `clear_command_output`) remain functional
- ✅ No breaking changes to existing workflows
- ✅ WebSocket is additive functionality
- ✅ Clients can choose polling or streaming

---

## Performance Considerations

### Latency Comparison

| Method | Typical Latency | Best Case | Worst Case |
|--------|----------------|-----------|------------|
| **Polling** | 1-5 seconds | 100ms | 10+ seconds |
| **WebSocket** | <100ms | <50ms | 500ms |

### Resource Usage

**Polling:**
- Network: ~1KB per poll * frequency
- CPU: Low (on-demand only)
- Memory: ~100KB buffer

**WebSocket:**
- Network: ~100 bytes per event (only when events occur)
- CPU: Low (background monitoring thread)
- Memory: ~200KB (persistent connection + monitoring)

**Verdict:** WebSocket is more efficient for real-time monitoring.

---

## Security Considerations

### Current Implementation (localhost only)
- ✅ WebSocket server bound to 127.0.0.1
- ✅ No authentication needed (localhost trust)
- ✅ No encryption needed (local machine)

### Future: Remote Access (If Needed)
- 🔐 WSS (WebSocket Secure) with TLS
- 🔐 Token-based authentication
- 🔐 Rate limiting per client
- 🔐 IP whitelist

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| WebSocket library bugs | Medium | Use well-tested Fleck library |
| Thread safety issues | High | Use locks for all shared state |
| Memory leaks (long connections) | Medium | Monitor and test extensively |
| Client reconnection logic | Medium | Implement exponential backoff |
| Backward compatibility | Low | Keep polling API unchanged |

---

## Success Metrics

### Functional
- ✅ Events delivered within 100ms
- ✅ Multiple clients can connect simultaneously
- ✅ No events lost during normal operation
- ✅ Graceful degradation on connection loss

### Non-Functional
- ✅ Memory usage <500KB total
- ✅ CPU usage <1% on idle
- ✅ No impact on Rhino UI responsiveness
- ✅ 99.9% uptime (excludes Rhino restarts)

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1: C# Server** | 4-5 hours | WebSocket server, monitoring thread, testing |
| **Phase 2: Python Client** | 3-4 hours | Client implementation, MCP tools, integration |
| **Phase 3: Testing & Docs** | 2-3 hours | Unit tests, integration tests, documentation |
| **Total** | **9-12 hours** | Full implementation |

---

## Alternative Approaches Considered

### 1. Server-Sent Events (SSE)
- ❌ One-way only (server to client)
- ❌ Less efficient than WebSocket
- ✅ Simpler protocol
- **Verdict:** WebSocket preferred for flexibility

### 2. gRPC Streaming
- ✅ Type-safe, efficient
- ❌ More complex setup
- ❌ Additional dependencies
- **Verdict:** Overkill for this use case

### 3. Polling with Long-Polling
- ✅ No new server required
- ❌ Still has latency
- ❌ More network overhead
- **Verdict:** WebSocket is cleaner solution

---

## Next Steps

To implement this plan:

1. **Review & Approve Plan**
   - Stakeholder review
   - Technical feasibility confirmation

2. **Setup Development Environment**
   - Install Fleck NuGet package
   - Install websockets Python package

3. **Implement Phase 1 (C# Server)**
   - Create RhinoMCPWebSocketServer.cs
   - Integrate into existing server
   - Test locally

4. **Implement Phase 2 (Python Client)**
   - Create websocket_client.py
   - Implement MCP tools
   - Test integration

5. **Implement Phase 3 (Testing & Docs)**
   - Write unit tests
   - Write integration tests
   - Update all documentation

6. **Deploy & Monitor**
   - Beta release
   - Gather feedback
   - Production release

---

## References

- **Fleck Documentation:** https://github.com/statianzo/Fleck
- **Python websockets:** https://websockets.readthedocs.io/
- **WebSocket Protocol:** RFC 6455
- **Current Polling Implementation:** `rhino_mcp_plugin/RhinoMCPServer.cs`

---

**Status:** PLANNED - Ready for Implementation  
**Author:** GitHub Copilot (Claude Opus 4.5)  
**Date:** 2026-01-11
