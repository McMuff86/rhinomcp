# AGENTS.md

> Agent-focused guide for working with RhinoMCP. Single source of truth for AI coding agents.

**Last Updated:** 2026-01-10  
**Version:** 0.1.3.7  
**Phase:** B Complete (see ROADMAP.md for Phase C)

---

## Project Overview

RhinoMCP enables AI agents to control Rhino 3D via the Model Context Protocol (MCP).

| Component | Location | Technology |
|-----------|----------|------------|
| **MCP Server** | `rhino_mcp_server/src/rhinomcp/` | Python, FastMCP |
| **Rhino Plugin** | `rhino_mcp_plugin/` | C#, RhinoCommon |
| **Transport** | TCP `127.0.0.1:1999` | JSON messages |

---

## Quick Commands

### Setup
```bash
# Install UV (required)
# macOS: brew install uv
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies
cd rhino_mcp_server
uv pip install -e .
```

### Run
```bash
# 1. Start Rhino plugin (in Rhino command line)
mcpstart

# 2. Start MCP server
cd rhino_mcp_server
uv run rhinomcp
```

### Test
```bash
# Run pytest suite (138 tests)
cd rhino_mcp_server
uv run pytest tests/ -v

# Live test with Rhino
uv run python dev/test_fixes.py
```

### Build
```bash
# Python package
cd rhino_mcp_server
uv build

# C# plugin (Release)
cd rhino_mcp_plugin
dotnet build --configuration Release
```

---

## Project Structure

```
rhinomcp/
├── rhino_mcp_server/           # Python MCP server
│   ├── src/rhinomcp/
│   │   ├── tools/              # MCP tool implementations
│   │   ├── utils/              # Helpers (responses.py, errors.py)
│   │   └── server.py           # Main server + RhinoConnection
│   ├── tests/                  # Pytest test suite
│   ├── dev/                    # Development scripts
│   └── pyproject.toml
│
├── rhino_mcp_plugin/           # C# Rhino plugin
│   ├── Functions/              # Command handlers
│   ├── Serializers/            # JSON serialization
│   ├── Commands/               # Rhino command definitions
│   ├── RhinoMCPServer.cs       # TCP server + command dispatch
│   └── rhinomcp.csproj
│
├── Ralph/                      # Structured development workflow
│   ├── prd.json                # Phase A user stories (complete)
│   ├── prd_phase_b.json        # Phase B user stories (complete)
│   └── progress.txt            # Codebase patterns & learnings
│
├── .github/workflows/          # CI/CD
│   └── ci.yml                  # Pytest + ruff on Python 3.10-3.12
│
└── Documentation
    ├── AGENTS.md               # This file
    ├── USAGE.md                # User guide
    ├── ROADMAP.md              # Project phases
    ├── FUNCTIONAL_STATUS.md    # What works / problems / solutions
    ├── MCP_TOOL_STANDARDS.md   # Tool development standards
    └── README.md               # Project overview
```

---

## Code Conventions

### Naming
- **Commands:** `lower_snake_case`, verb first: `create_object`, `get_document_info`
- **Colors:** `[r, g, b]` (0-255)
- **Points:** `[x, y, z]`
- **IDs:** GUID strings

### Python Response Format
```python
from rhinomcp.utils.responses import ok, from_exception
from rhinomcp.utils.errors import ErrorCode

# Success
return json.dumps(ok(message="Created object", data={"id": obj_id}))

# Error
return json.dumps(from_exception(e, code=ErrorCode.CREATE_OBJECT_ERROR))
```

### C# Command Handler
```csharp
public JObject CreateObject(JObject parameters)
{
    var doc = RhinoDoc.ActiveDoc;
    
    // Parse parameters
    string type = parameters["type"]?.ToString();
    
    // Create geometry
    // ...
    
    // Update views
    doc.Views.Redraw();
    
    return JObject.FromObject(new { status = "success", id = objectId });
}
```

### Error Codes
| Code | Use Case |
|------|----------|
| `CONNECTION_ERROR` | General connection issues |
| `CONNECTION_TIMEOUT` | Socket timeout |
| `CONNECTION_REFUSED` | Rhino not running |
| `INVALID_PARAMS` | Bad input parameters |
| `RHINO_ERROR` | Error from Rhino |
| `CREATE_OBJECT_ERROR` | Object creation failed |

---

## Available Tools

### Core Tools
| Tool | Handler | Description |
|------|---------|-------------|
| `ping` | Inline | Health check |
| `get_logs` | Inline | Get recent server logs |
| `clear_logs` | Inline | Clear log buffer |
| `get_document_info` | `GetDocumentInfo.cs` | Document metadata |
| `create_object` | `CreateObject.cs` | Create geometry |
| `create_objects` | `CreateObjects.cs` | Batch create |
| `modify_object` | `ModifyObject.cs` | Transform object |
| `delete_object` | `DeleteObject.cs` | Delete by ID |
| `select_objects` | `SelectObjects.cs` | Select by ID |

### Layer & Material
| Tool | Handler | Description |
|------|---------|-------------|
| `create_layer` | `CreateLayer.cs` | Create layer |
| `get_or_set_current_layer` | `GetOrSetCurrentLayer.cs` | Layer control |
| `delete_layer` | `DeleteLayer.cs` | Delete layer |
| `create_material` | `GetDocumentInfo.cs` | Create material |
| `assign_material_to_layer` | `GetDocumentInfo.cs` | Assign to layer |

### Boolean Operations
| Tool | Handler | Description |
|------|---------|-------------|
| `boolean_operation` | `BooleanOperations.cs` | Union, difference, intersection |

### Transform Tools
| Tool | Handler | Description |
|------|---------|-------------|
| `copy_object` | `TransformOperations.cs` | Copy with optional translation |
| `mirror_object` | `TransformOperations.cs` | Mirror across plane |
| `array_linear` | `TransformOperations.cs` | Linear array with spacing |
| `array_polar` | `TransformOperations.cs` | Polar array around center |

### Curve Tools
| Tool | Handler | Description |
|------|---------|-------------|
| `offset_curve` | `CurveOperations.cs` | Offset curve by distance |
| `fillet_curves` | `CurveOperations.cs` | Create fillet arc between curves |
| `chamfer_curves` | `CurveOperations.cs` | Create chamfer line between curves |

### Surface Tools
| Tool | Handler | Description |
|------|---------|-------------|
| `loft_curves` | `SurfaceOperations.cs` | Loft surface between curves |
| `extrude_curve` | `SurfaceOperations.cs` | Extrude curve along vector |
| `revolve_curve` | `SurfaceOperations.cs` | Revolve curve around axis |

### Dimension Tools
| Tool | Handler | Description |
|------|---------|-------------|
| `create_linear_dimension` | `DimensionOperations.cs` | Linear dimension between points |
| `create_angular_dimension` | `DimensionOperations.cs` | Angle dimension at vertex |
| `create_radial_dimension` | `DimensionOperations.cs` | Radius/diameter dimension |

### Object Properties
| Tool | Handler | Description |
|------|---------|-------------|
| `get_object_properties` | `ObjectProperties.cs` | Get bounding box, area, volume, centroid |
| `set_object_properties` | `ObjectProperties.cs` | Set name, layer, color, material |

### Script Execution
| Tool | Handler | Description |
|------|---------|-------------|
| `execute_rhinoscript_python_code` | `ExecuteCode.cs` | Run Python in Rhino |

---

## Adding New Tools

### 1. Python Tool
```python
# rhino_mcp_server/src/rhinomcp/tools/my_new_tool.py
from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger
from rhinomcp.utils.responses import ok, from_exception
import json

@mcp.tool()
def my_new_tool(ctx: Context, param1: str, param2: int = 10) -> str:
    """Tool description for AI agents."""
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("my_new_command", {
            "param1": param1,
            "param2": param2
        })
        return json.dumps(ok(message="Success", data=result))
    except Exception as e:
        logger.error(f"Error: {e}")
        return json.dumps(from_exception(e))
```

### 2. C# Handler
```csharp
// rhino_mcp_plugin/Functions/MyNewCommand.cs
public JObject MyNewCommand(JObject parameters)
{
    string param1 = parameters["param1"]?.ToString();
    int param2 = parameters["param2"]?.Value<int>() ?? 10;
    
    // Validate
    if (string.IsNullOrEmpty(param1))
        throw new ArgumentException("param1 is required");
    
    // Execute
    var doc = RhinoDoc.ActiveDoc;
    // ... do work ...
    
    doc.Views.Redraw();
    return JObject.FromObject(new { status = "success" });
}
```

### 3. Register in Server
```csharp
// RhinoMCPServer.cs in ExecuteCommandInternal
["my_new_command"] = this.handler.MyNewCommand,
```

### 4. Add Test
```python
# rhino_mcp_server/tests/test_my_new_tool.py
def test_my_new_tool():
    # Test implementation
    pass
```

---

## Development Workflow (Ralph)

Ralph is our structured development workflow for iterative improvements.

### Start New Feature
1. Read `Ralph/progress.txt` for patterns
2. Check `Ralph/prd_phase_b.json` for current stories
3. Pick highest priority story with `passes: false`
4. Read `Ralph/NEXT_SESSION_PLAN.md` for detailed workflow
5. Implement in small steps
6. Build & Test (see below)
7. Update `progress.txt` with learnings
8. Mark story as `passes: true`
9. Update `AGENTS.md` (tool tables, test count, status)

### Build & Restart Workflow
After implementing features, **always** run:
```powershell
# 1. Close Rhino (if blocking build)
Stop-Process -Name "Rhino" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 2. Build C# plugin
cd c:\Users\Adi.Muff\repos\rhinomcp\rhino_mcp_plugin
dotnet build --configuration Release

# 3. Start Rhino
Start-Process "C:\Program Files\Rhino 8\System\Rhino.exe"
Start-Sleep -Seconds 10

# 4. User runs 'mcpstart' in Rhino, then run tests
cd c:\Users\Adi.Muff\repos\rhinomcp\rhino_mcp_server
uv run pytest tests/ -v
```

### Current Phase: B (Core Features)
| Story | Title | Status |
|-------|-------|--------|
| US-B01 | Boolean Operations | ✅ |
| US-B02 | Transform Tools | ✅ |
| US-B03 | Curve Operations | ✅ |
| US-B04 | Surface from Curves | ✅ |
| US-B05 | Dimension Tools | ✅ |
| US-B06 | Object Properties | ✅ |

---

## Troubleshooting

### Connection Issues
```bash
# Check Rhino plugin status
MCPStatus  # in Rhino command line

# Restart plugin
mcpstop
mcpstart
```

### Build Errors (C#)
- Ensure Rhino SDK is installed
- Check `rhinomcp.csproj` for correct RhinoCommon version
- Build in Release mode: `dotnet build -c Release`

### Test Failures
```bash
# Run with verbose output
uv run pytest tests/ -v --tb=long

# Run specific test
uv run pytest tests/test_connection.py -v
```

---

## Agent Integration

### Claude Desktop
```json
// claude_desktop_config.json
{
  "mcpServers": {
    "rhino": {
      "command": "uvx",
      "args": ["rhinomcp"]
    }
  }
}
```

### Cursor
```json
// .cursor/mcp.json
{
  "mcpServers": {
    "rhino": {
      "command": "uvx",
      "args": ["rhinomcp"]
    }
  }
}
```

---

## Documentation Index

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `USAGE.md` | Quick reference (tool list, conventions) |
| `AGENTS.md` | This file - agent guide |
| `ROADMAP.md` | Project phases |
| `MCP_TOOL_STANDARDS.md` | Tool development standards |
| `Ralph/progress.txt` | Patterns & learnings |

### Tool Documentation

Detailed tool documentation is in the **Python docstrings**:

```
rhino_mcp_server/src/rhinomcp/tools/*.py
```

Each tool file contains:
- Full parameter documentation
- Return value descriptions
- Usage examples and notes

---

## Using Native Rhino Commands

For complex operations, you can use native Rhino commands instead of manual implementations:

### RhinoApp.RunScript() - Execute Native Commands
```csharp
// Execute native Rhino command from C# handler
string script = "_Loft _Pause _Pause _Enter";
bool echo = false;
RhinoApp.RunScript(script, echo);
```

### Built-in Alternatives
| Manual Implementation | Native Alternative |
|-----------------------|-------------------|
| Complex chamfer | `Curve.CreateFilletCurves(radius=0)` |
| Loft surfaces | `RhinoApp.RunScript("_Loft")` |
| Sweep surfaces | `RhinoApp.RunScript("_Sweep1")` |

### When to Use Native Commands
- Complex surface operations (Loft, Sweep, Revolve)
- Operations with many edge cases
- Features already perfected in Rhino

### Caveats
- Object references may become invalid after RunScript
- Re-fetch objects by GUID after native command execution
- Some commands require object selection first

---

## External Resources (Rhino Developer Docs)

When unsure how to implement a feature or which RhinoCommon/RhinoScript API to use, **always consult the official Rhino Developer Documentation**:

| Resource | URL | Use Case |
|----------|-----|----------|
| **Developer Portal** | https://developer.rhino3d.com/ | Main entry point, guides, tutorials |
| **RhinoCommon API** | https://developer.rhino3d.com/api/rhinocommon/ | C# API reference for Rhino plugins |
| **C++ API** | https://mcneel.github.io/rhino-cpp-api-docs/api/cpp/ | C++ SDK reference |
| **RhinoScript Guide** | https://developer.rhino3d.com/guides/rhinoscript/ | VBScript scripting reference |
| **Rhino.Python** | https://developer.rhino3d.com/guides/rhinopython/ | Python scripting in Rhino |

### When to Use External Docs

1. **Implementing new geometry types** - Check `Rhino.Geometry` namespace
2. **Working with materials/rendering** - Check `Rhino.Render` namespace
3. **Document operations** - Check `Rhino.DocObjects` namespace
4. **Unknown RhinoScript functions** - Use `get_rhinoscript_python_function_names` tool first, then docs
5. **Boolean operations, surfaces, curves** - Check `Rhino.Geometry.Brep`, `Rhino.Geometry.Curve`

> **IMPORTANT:** Don't guess RhinoCommon API calls. Always verify against the official docs to avoid runtime errors.

---

## See Also

- [USAGE.md](USAGE.md) - Quick reference (tool list, conventions)
- [ROADMAP.md](ROADMAP.md) - Project roadmap
- [Ralph/progress.txt](Ralph/progress.txt) - Codebase patterns
- [Rhino Developer Docs](https://developer.rhino3d.com/) - Official API documentation
- Tool docstrings: `rhino_mcp_server/src/rhinomcp/tools/*.py` - Detailed tool documentation
