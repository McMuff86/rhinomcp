# RhinoMCP MCP Tools Guide

> **Note:** This file is partially deprecated. For current development practices, see `AGENTS.md` and `MCP_TOOL_STANDARDS.md`.

This document explains how MCP tools in this workspace are structured, how they talk to Rhino, and how to add new tools following best practices. It targets AI coding agents and developers who want to extend RhinoMCP.

## Architecture Overview

- **Python MCP server** (`rhino_mcp_server/src/rhinomcp`): Built on FastMCP. Registers tools with `@mcp.tool()` and sends JSON commands over TCP to the Rhino plugin.
- **Rhino plugin (C#)** (`rhino_mcp_plugin`): Hosts a TCP server, receives JSON commands, dispatches to functions (geometry ops via RhinoCommon), and returns JSON responses.
- **Transport**: TCP localhost (`127.0.0.1:1999`). Python keeps a persistent socket managed by `get_rhino_connection()`.

### Python Side

- Server init: `rhinomcp.server` creates a `FastMCP` instance and manages a persistent `RhinoConnection`.
- Connection helper: `get_rhino_connection()` returns a cached connection, creating and connecting as needed.
- Send command: `RhinoConnection.send_command(command_type, params)` assembles `{ type, params }`, sends over socket, waits for full JSON response, and returns `result` or raises on error status.

#### Tool pattern (Current Standard)

Each tool:

- Imports `Context`, `get_rhino_connection`, `mcp`, `logger`, and response helpers.
- Is registered with `@mcp.tool()`.
- Defines explicit parameters with type hints (use `Literal` for enums).
- Returns JSON via `ok()` or `from_exception()` helpers.

Example: Create object with structured response

```python
from mcp.server.fastmcp import Context
import json
from rhinomcp.server import get_rhino_connection, mcp, logger
from rhinomcp.utils.responses import ok, from_exception
from rhinomcp.utils.errors import ErrorCode
from typing import Literal, Optional, List

ObjectType = Literal["BOX", "SPHERE", "CYLINDER"]

@mcp.tool()
def create_object(
    ctx: Context,
    type: ObjectType = "BOX",
    name: Optional[str] = None
) -> str:
    """
    Create a new object in Rhino.
    
    Parameters:
    - type: Object type (BOX, SPHERE, CYLINDER)
    - name: Optional name for the object
    
    Returns:
        {"ok": true, "message": "Created BOX", "data": {"id": "guid", "name": "Box_1"}}
    """
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("create_object", {"type": type, "name": name})
        return json.dumps(ok(
            message=f"Created {type}",
            data=result
        ))
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.CREATE_OBJECT_ERROR))
```

### C# Side

- TCP server: `RhinoMCPServer` listens and handles client data on a background thread. JSON is parsed and dispatched on Rhino UI thread.
- Command dispatch: `ExecuteCommandInternal` maps `type` to methods of `RhinoMCPFunctions`.
- Undo safety: Each command runs within an UndoRecord so user can undo changes.
- Serialization: `rhinomcp.Serializers.Serializer` provides helpers to serialize objects, colors, layers, geometry, and attributes.

Handler mapping (see `RhinoMCPServer.cs` for complete list - 48 tools as of v0.1.3.8):

```csharp
// Document & System
["get_document_info"], ["ping"], ["set_debug_mode"], ["log_thought"],
["get_logs"], ["clear_logs"], ["get_command_history"],

// Objects
["create_object"], ["create_objects"], ["get_object_info"], 
["get_selected_objects_info"], ["delete_object"], ["modify_object"],
["modify_objects"], ["select_objects"], ["get_object_properties"],
["set_object_properties"],

// Boolean & Transform
["boolean_operation"], ["copy_object"], ["mirror_object"],
["array_linear"], ["array_polar"],

// Curve Operations
["offset_curve"], ["fillet_curves"], ["chamfer_curves"],

// Surface Operations
["loft_curves"], ["extrude_curve"], ["revolve_curve"],

// Dimensions
["create_linear_dimension"], ["create_angular_dimension"],
["create_radial_dimension"],

// Layers & Materials
["create_layer"], ["get_or_set_current_layer"], ["delete_layer"],
["create_material"], ["assign_material_to_layer"],

// File Operations
["open_file"], ["save_file"], ["export_file"],

// Scripting
["execute_rhinoscript_python_code"]
```

### Request/Response Contract

- Client (Python) sends:
  - **type**: string, one of the mapped command names.
  - **params**: object, command-specific parameters.
- Server (C#) responds:
  - On success: `{ "status": "success", "result": <JObject> }`
  - On error: `{ "status": "error", "message": <string> }`

Tools should return structured JSON via `ok()` / `from_exception()` helpers.

See also: `MCP_TOOL_STANDARDS.md` for the preferred tool-level return shape and Python helpers in `rhinomcp/utils/responses.py`.

### Adding a New Tool (Checklist)

1. **C# implementation**
   - Add a method in `RhinoMCPPlugin.Functions.RhinoMCPFunctions` returning a `JObject`.
   - Use `Serializer` helpers for any output.

2. **Wire on C# server**
   - Register in `handlers` dictionary in `RhinoMCPServer.ExecuteCommandInternal`.
   - **Also** add to `GetAvailableTools()` list.

3. **Python tool stub**
   - Create `src/rhinomcp/tools/<tool_name>.py` with `@mcp.tool()`.
   - Use `Literal` types for enum parameters.
   - Return JSON via `ok()` / `from_exception()`.

4. **Export in `__init__.py`** for convenience imports.

5. **Add tests** in `tests/test_<tool_name>.py`.

6. **Document** - Update AGENTS.md tool tables if needed.

### Best Practices

- Use `Literal` types for enum-like parameters.
- Always return structured JSON via `ok()` / `from_exception()`.
- Validate inputs early and return `from_exception()` with `INVALID_PARAMS`.
- Keep responses compact but consistent.
- Maintain undo safety (`BeginUndoRecord`/`EndUndoRecord`).
- Log errors via `logger`.

### Startup

- In Rhino, run command `mcpstart` to start the C# TCP server.
- In Python, run MCP server:

```bash
cd rhino_mcp_server
uv run python -m rhinomcp
```

### Troubleshooting

- **Timeout**: Simplify request or verify plugin is running.
- **Unknown command**: Ensure C# handler is registered in BOTH `handlers` dict AND `GetAvailableTools()`.
- **Serialization gaps**: Extend `Serializer` to cover new geometry types.
