# RhinoMCP Future Issues

> Known issues and planned improvements. Check here before starting new work.

---

## Issue: Automatic MCP Plugin Start

**Priority:** Medium
**Status:** Open
**Created:** 2026-01-10
**Related:** US-C02 Viewport Control Implementation

### Description
The MCP plugin currently does not start automatically when Rhino launches, despite implementing `OnLoad` and `OnShutdown` methods in `RhinoMCPPlugin.cs`.

### Current State
- Plugin loads on Rhino startup (confirmed)
- `OnLoad` method is called (confirmed by logs)
- Server creation works (confirmed)
- Server.Start() is called (confirmed)
- But MCP commands still return "Unknown command type" errors

### Root Cause Analysis
The issue appears to be that while the plugin loads and attempts to start the server, the server is not properly registered or accessible through the expected TCP connection.

### Investigation Steps
1. Verify server thread creation and startup
2. Check TCP listener binding and port availability
3. Test server availability immediately after plugin load
4. Check for race conditions between plugin load and server startup

### Workaround
Users must manually run `mcpstart` in Rhino command line after startup.

### Acceptance Criteria
- MCP server starts automatically when Rhino loads
- No manual `mcpstart` command needed
- All MCP tools work immediately after Rhino startup
- Server status shows as "running" in MCPStatus command

### Technical Notes
- Implemented in `rhino_mcp_plugin/rhinomcpPlugin.cs`
- Uses `Task.Run()` for background server startup
- Server configured for `127.0.0.1:1999`
- Related code in `RhinoMCPServerController.cs`

---

## Issue: modify_object Layer Parameter Not Functional

**Priority:** Low
**Status:** Open
**Created:** 2026-01-11
**Related:** Galaxy Scene Creation session

### Description
The `modify_object` tool's layer parameter does not correctly assign objects to layers.

### Workaround
Use RhinoScript for layer assignment:

```python
import rhinoscriptsyntax as rs
rs.ObjectLayer(obj_id, 'LayerName')
```

### Pattern
Create objects with MCP tools, then assign layers with RhinoScript.

### Acceptance Criteria
- `modify_object(object_id="...", layer="LayerName")` correctly moves object to layer
- No RhinoScript workaround needed

---

## Future Enhancements

### Grasshopper API Direct Access
**Priority:** Low
**Status:** Planned

Bypass GrasshopperPlayer prompts entirely by directly accessing Grasshopper API:
- Introspect .gh files to find required inputs
- Set parameters programmatically without prompts
- Bake geometry directly

### Parameter Discovery for GH Files
**Priority:** Low
**Status:** Planned

Analyze .gh files to discover:
- Required input parameters
- Parameter types and ranges
- Output geometry types

### ML-Based Prompt Understanding
**Priority:** Low
**Status:** Planned

Smarter prompt parsing for:
- Automatic prompt type detection
- Intelligent response generation
- Multi-language support