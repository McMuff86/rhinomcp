# RhinoMCP MCP Tools Guide

This document explains how MCP tools in this workspace are structured, how they talk to Rhino, and how to add new tools following best practices. It targets AI coding agents and developers who want to extend RhinoMCP.

## Architecture Overview

- **Python MCP server** (`rhino_mcp_server/src/rhinomcp`): Built on FastMCP. Registers tools with `@mcp.tool()` and sends JSON commands over TCP to the Rhino plugin.
- **Rhino plugin (C#)** (`rhino_mcp_plugin`): Hosts a TCP server, receives JSON commands, dispatches to functions (geometry ops via RhinoCommon), and returns JSON responses.
- **Transport**: TCP localhost (`127.0.0.1:1999`). Python keeps a persistent socket managed by `get_rhino_connection()`.

### Python Side

- Server init: `rhinomcp.server` creates a `FastMCP` instance and manages a persistent `RhinoConnection`.
- Connection helper: `get_rhino_connection()` returns a cached connection, creating and connecting as needed.
- Send command: `RhinoConnection.send_command(command_type, params)` assembles `{ type, params }`, sends over socket, waits for full JSON response, and returns `result` or raises on error status.

#### Tool pattern

Each tool:

- Imports `Context`, `get_rhino_connection`, `mcp`, `logger`.
- Is registered with `@mcp.tool()`.
- Defines explicit parameters with type hints for MCP schemas.
- Calls `rhino.send_command("<command>", params)` inside try/except and returns a concise string or structured result.

Example: create multiple objects

```python
from mcp.server.fastmcp import Context
from typing import Any, List, Dict
from rhinomcp.server import get_rhino_connection, mcp, logger

@mcp.tool()
def create_objects(ctx: Context, objects: List[Dict[str, Any]]) -> str:
    """Create multiple objects in Rhino."""
    try:
        rhino = get_rhino_connection()
        command_params = {obj["name"]: obj for obj in objects}
        result = rhino.send_command("create_objects", command_params)
        return f"Created {len(result)} objects"
    except Exception as e:
        logger.error(f"Error creating object: {str(e)}")
        return f"Error creating object: {str(e)}"
```

Other examples in repo:

- `execute_rhinoscript_python_code.py` executes Python code in Rhino.
- `modify_object.py` and `modify_objects.py` change attributes (name, color, transforms, visibility).
- Query tools: `get_document_info.py`, `get_object_info.py`, `get_selected_objects_info.py`.
- Layer/Annotation tools: `create_layer.py`, `get_or_set_current_layer.py`, `delete_layer.py`, `create_leader.py`.

### C# Side

- TCP server: `RhinoMCPServer` listens and handles client data on a background thread. JSON is parsed and dispatched on Rhino UI thread.
- Command dispatch: `ExecuteCommandInternal` maps `type` to methods of `RhinoMCPFunctions`.
- Undo safety: Each command runs within an UndoRecord so user can undo changes.
- Serialization: `rhinomcp.Serializers.Serializer` provides helpers to serialize objects, colors, layers, geometry, and attributes.

Handler mapping snippet (abridged):

```280:362:rhino_mcp_plugin/RhinoMCPServer.cs
// ... existing code ...
Dictionary<string, Func<JObject, JObject>> handlers = new Dictionary<string, Func<JObject, JObject>>
{
    ["get_document_info"] = this.handler.GetDocumentInfo,
    ["create_object"] = this.handler.CreateObject,
    ["create_objects"] = this.handler.CreateObjects,
    ["get_object_info"] = this.handler.GetObjectInfo,
    ["get_selected_objects_info"] = this.handler.GetSelectedObjectsInfo,
    ["delete_object"] = this.handler.DeleteObject,
    ["modify_object"] = this.handler.ModifyObject,
    ["modify_objects"] = this.handler.ModifyObjects,
    ["execute_rhinoscript_python_code"] = this.handler.ExecuteRhinoscript,
    ["select_objects"] = this.handler.SelectObjects,
    ["create_layer"] = this.handler.CreateLayer,
    ["get_or_set_current_layer"] = this.handler.GetOrSetCurrentLayer,
    ["delete_layer"] = this.handler.DeleteLayer
};
```

### Request/Response Contract

- Client (Python) sends:
  - **type**: string, one of the mapped command names.
  - **params**: object, command-specific parameters.
- Server (C#) responds:
  - On success: `{ "status": "success", "result": <JObject> }`
  - On error: `{ "status": "error", "message": <string> }`

Tools should surface either a clear string summary or raw structured result suitable for chaining.

See also: `MCP_TOOL_STANDARDS.md` for the preferred tool-level return shape and Python helpers in `rhinomcp/utils/responses.py`.

### Adding a New Tool (Checklist)

1. C# implementation

- Add a method in `RhinoMCPPlugin.Functions.RhinoMCPFunctions` returning a `JObject`.
- Use `Serializer` helpers for any output. Modify document on `RhinoDoc.ActiveDoc`, update views, and return a small, stable shape.

1. Wire on C# server

- Register the new command in `handlers` dictionary in `RhinoMCPServer.ExecuteCommandInternal`.

1. Python tool stub

- Create `src/rhinomcp/tools/<tool_name>.py` with `@mcp.tool()`, typed parameters, and error handling.
- Call `rhino.send_command("<command>", params)`.

1. Optional: expose in `src/rhinomcp/__init__.py` for convenience imports.

1. Document and test

- Update this file with a short section and example.
- Test round-trip: start Rhino plugin (`mcpstart`), run MCP server (`python -m rhinomcp`), call the tool.

### Best Practices

- Keep tool parameter names stable; prefer explicit parameters with type hints over untyped blobs.
- Validate inputs on C# side and return clear error messages. Avoid throwing without context.
- Keep responses compact but consistent; for lists, return arrays of stable objects; for actions, return counts and identifiers.
- Maintain undo safety (`BeginUndoRecord`/`EndUndoRecord`).
- Log actionable errors; Python logs via `logger`, C# via `RhinoApp.WriteLine`.
- Prefer batch endpoints for N>10 objects (see `create_objects`, `modify_objects`).

### Example: Add a simple annotation tool (sketch)

Steps:

- C#: implement `CreateLeader` in `RhinoMCPFunctions`, map to `create_leader` in `RhinoMCPServer`.
- Python: add `tools/create_leader.py` calling `send_command("create_leader", {...})`.
- Return `{ id, name }` and a concise string: `"Created leader: <name>"`.

### Startup

- In Rhino, run command `mcpstart` to start the C# TCP server.
- In Python, run MCP server:

```bash
cd rhino_mcp_server
uv run python -m rhinomcp
```

- On startup the Python server attempts to connect and logs status. Ensure the Rhino add-on is running before invoking tools.

### Troubleshooting

- Timeout waiting for response: Simplify request or verify the plugin is running; Python resets socket on timeout.
- Unknown command type: Ensure C# handler is registered and names match on both sides.
- Serialization gaps: Extend `Serializer` to cover new geometry types consistently.

### Conventions

- Python tool module names: snake_case matching command name where possible.
- Command names: lower_snake_case, verbs first (e.g., `create_object`, `modify_objects`).
- Colors: `[r, g, b]` 0–255. Points: `[x, y, z]`. IDs: string GUIDs.
