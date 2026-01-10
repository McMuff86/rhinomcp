# Phase B Context for New Thread

> Use this file to provide context when starting a new Amp thread for Phase B.

**Created:** 2026-01-10  
**Thread:** https://ampcode.com/threads/T-019ba51e-18ff-75b3-8584-55649245f3d9

---

## Project Summary

**RhinoMCP** enables AI agents to control Rhino 3D via the Model Context Protocol (MCP).

| Component | Location | Technology |
|-----------|----------|------------|
| MCP Server | `rhino_mcp_server/src/rhinomcp/` | Python, FastMCP |
| Rhino Plugin | `rhino_mcp_plugin/` | C#, RhinoCommon |
| Transport | TCP `127.0.0.1:1999` | JSON messages |

---

## Phase A: Complete ✅

All 6 user stories completed:

| ID | Title |
|----|-------|
| US-001 | Structured error codes |
| US-002 | Auto-reconnect on connection drop |
| US-003 | Complete C# handlers for annotations |
| US-004 | Pytest test suite (34 tests) |
| US-005 | GitHub Actions CI |
| US-006 | Configurable script timeout |

Bug fixes:
- P-0002: PBR materials now visible in Rhino (use `RenderMaterials` table)
- P-0003: Objects created on correct current layer
- P-0004: `assign_material_to_layer` parameter validation

---

## Phase B: Ready to Start

### User Stories (in `Ralph/prd_phase_b.json`)

| Priority | ID | Title |
|----------|----|-------|
| 1 | US-B01 | Boolean Operations (Union, Difference, Intersection) |
| 2 | US-B02 | Transform Tools (Copy, Mirror, Array) |
| 3 | US-B03 | Curve Operations (Offset, Fillet, Chamfer) |
| 4 | US-B04 | Surface from Curves (Loft, Extrude, Revolve) |
| 5 | US-B05 | Dimension Tools |
| 6 | US-B06 | Get/Set Object Properties |

---

## Key Files to Read First

1. `Ralph/progress.txt` - Codebase patterns and learnings (SACRED conventions)
2. `Ralph/prd_phase_b.json` - User stories with acceptance criteria
3. `AGENTS.md` - Agent guide with code conventions
4. `MCP_TOOL_STANDARDS.md` - How to add new tools

---

## Adding a New Tool (Quick Reference)

### 1. Python Tool
```python
# rhino_mcp_server/src/rhinomcp/tools/my_tool.py
@mcp.tool()
def my_tool(ctx: Context, param: str) -> str:
    rhino = get_rhino_connection()
    result = rhino.send_command("my_command", {"param": param})
    return json.dumps(ok(message="Success", data=result))
```

### 2. C# Handler
```csharp
// rhino_mcp_plugin/Functions/MyCommand.cs
public JObject MyCommand(JObject parameters) {
    var doc = RhinoDoc.ActiveDoc;
    // ... implementation ...
    doc.Views.Redraw();
    return JObject.FromObject(new { status = "success" });
}
```

### 3. Register in `RhinoMCPServer.cs`
```csharp
["my_command"] = this.handler.MyCommand,
```

---

## Commands

```bash
# Build plugin
cd rhino_mcp_plugin && dotnet build -c Release

# Run tests
cd rhino_mcp_server && uv run pytest tests/ -v

# Start server
cd rhino_mcp_server && uv run rhinomcp
```

---

## Starting Prompt for New Thread

```
Continue Phase B of RhinoMCP development.

Context:
- Phase A is complete (all 6 stories, bug fixes done)
- Read Ralph/prd_phase_b.json for Phase B user stories
- Start with US-B01: Boolean Operations

Key references:
- Ralph/progress.txt (codebase patterns)
- AGENTS.md (code conventions)
- MCP_TOOL_STANDARDS.md (tool development)

First task: Implement boolean_operation tool supporting Union, Difference, Intersection.
```

---

## Notes from Phase A

### Learnings (from `Ralph/progress.txt`)
- PBR materials must use `doc.RenderMaterials` not `doc.Materials`
- Always set `LayerIndex` explicitly when creating objects
- Use `int.TryParse()` not `int.Parse()` for user input
- `RenderMaterial.CreateBasicMaterial()` takes (Material, RhinoDoc)
- `Material.ToPhysicallyBased()` returns void

### Project Structure Notes
- `static/` folder outside `src/` contains reference files (not critical)
- Consider moving to `docs/` folder in future
- Tests follow `test_*.py` pattern in `tests/` folder
