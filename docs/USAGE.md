# RhinoMCP Usage Guide

> Quick reference for using RhinoMCP tools.

**Version:** 0.1.3.9

---

## Quick Start

```bash
# 1. Start Rhino
# 2. Run 'mcpstart' in Rhino command line

# 3. Start MCP Server
cd rhino_mcp_server
uv run rhinomcp

# 4. Verify with ping tool
```

**Note:** MCP plugin must be started manually with `mcpstart` command in Rhino command line.

---

## Available Tools

### System
| Tool | Description |
|------|-------------|
| `ping` | Test connection |
| `set_debug_mode` | Toggle logging |
| `get_document_info` | Document metadata |
| `get_logs` | Get recent server logs (debugging) |
| `clear_logs` | Clear server log buffer |
| `get_command_history` | Get Rhino command line history & current prompt |

### Object Creation
| Tool | Description |
|------|-------------|
| `create_object` | Create geometry (BOX, SPHERE, CYLINDER, etc.) |
| `create_objects` | Batch create |
| `create_text` | Text annotation |
| `create_text_dot` | Text dot |
| `create_leader` | Leader annotation |

### Object Manipulation
| Tool | Description |
|------|-------------|
| `modify_object` | Transform single object |
| `modify_objects` | Batch transform |
| `delete_object` | Delete by ID |
| `select_objects` | Select by ID |
| `get_object_info` | Get object details |
| `get_object_properties` | Get bounding box, area, volume, centroid |
| `set_object_properties` | Set name, layer, color, material |
| `get_selected_objects_info` | Selected objects info |

### Boolean Operations
| Tool | Description |
|------|-------------|
| `boolean_operation` | union, difference, intersection |

### Transform Operations
| Tool | Description |
|------|-------------|
| `copy_object` | Copy with optional offset |
| `mirror_object` | Mirror across plane |
| `array_linear` | Linear array |
| `array_polar` | Polar/radial array |

### Curve Operations
| Tool | Description |
|------|-------------|
| `offset_curve` | Offset by distance |
| `fillet_curves` | Fillet arc between curves |
| `chamfer_curves` | Chamfer between curves |

### Surface Operations
| Tool | Description |
|------|-------------|
| `loft_curves` | Loft between curves |
| `extrude_curve` | Extrude along vector |
| `revolve_curve` | Revolve around axis |

### Dimension Tools
| Tool | Description |
|------|-------------|
| `create_linear_dimension` | Linear dimension between points |
| `create_angular_dimension` | Angle dimension at vertex |
| `create_radial_dimension` | Radius/diameter dimension |

### Layer & Material
| Tool | Description |
|------|-------------|
| `create_layer` | Create layer |
| `get_or_set_current_layer` | Layer control |
| `delete_layer` | Delete layer |
| `create_material` | Create material |
| `assign_material_to_layer` | Assign to layer |

### File Operations
| Tool | Description |
|------|-------------|
| `open_file` | Open .3dm file |
| `save_file` | Save current document |
| `export_file` | Export to STEP, IGES, DWG, OBJ, STL, etc. |

### Viewport Control
| Tool | Description |
|------|-------------|
| `set_view` | Set viewport to standard views (Top, Front, Perspective, etc.) |
| `zoom_extents` | Zoom viewport to show all objects |
| `zoom_selected` | Zoom viewport to selected objects |
| `orbit_camera` | Rotate camera around target (orbit around model) |
| `capture_viewport` | Capture viewport as image (auto-saves to screenshots/ by default) |

### Render Settings
| Tool | Description |
|------|-------------|
| `set_render_settings` | Set render resolution and quality |
| `add_light` | Add point, directional, or spot lights |
| `set_camera` | Set camera position, target, and lens |
| `render_view` | Render viewport to image (file or base64) |

### Script Execution
| Tool | Description |
|------|-------------|
| `execute_rhinoscript_python_code` | Run Python in Rhino |
| `get_rhinoscript_python_function_names` | List available functions |
| `get_rhinoscript_python_code_guide` | Get function documentation |

---

## Parameter Conventions

| Type | Format | Example |
|------|--------|---------|
| Colors | `[R, G, B]` (0-255) | `[255, 0, 0]` (red) |
| Points | `[X, Y, Z]` | `[10, 20, 5]` |
| IDs | GUID string | `"ae0b9ce6-..."` |
| Translation | `[X, Y, Z]` offset | `[10, 0, 0]` |
| Rotation | `[X, Y, Z]` radians | `[0, 0, 1.57]` |
| Scale | `[X, Y, Z]` factors | `[1, 1, 2]` |

---

## Supported Object Types

| Type | Key Parameters |
|------|----------------|
| `POINT` | `x`, `y`, `z` |
| `LINE` | `start`, `end` |
| `POLYLINE` | `points` |
| `CIRCLE` | `center`, `radius` |
| `ARC` | `center`, `radius`, `angle` |
| `ELLIPSE` | `center`, `radius_x`, `radius_y` |
| `CURVE` | `points`, `degree` |
| `BOX` | `width`, `length`, `height` |
| `SPHERE` | `radius` |
| `CONE` | `radius`, `height`, `cap` |
| `CYLINDER` | `radius`, `height`, `cap` |
| `SURFACE` | `count`, `points`, `degree` |
| `MESH` | `vertices`, `faces` |

---

## Error Codes

| Code | Description |
|------|-------------|
| `CONNECTION_ERROR` | Cannot connect |
| `CONNECTION_TIMEOUT` | Operation timed out |
| `CONNECTION_REFUSED` | Rhino not running |
| `INVALID_PARAMS` | Invalid parameters |
| `RHINO_ERROR` | Error in Rhino |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Run `mcpstart` in Rhino |
| Timeout | Increase timeout, check Rhino |
| Unknown command | Check spelling, ensure registered |

```bash
# Check status in Rhino
MCPStatus
```

---

## Best Practices

1. Use `ping` to verify connection first
2. Use batch operations for >10 items
3. Set current layer before creating objects
4. Use layer-based materials for PBR (see `docs/learnings/material-assignment.md` for complete guide)

---

## Tool Documentation

Detailed tool documentation is in the Python docstrings:

```
rhino_mcp_server/src/rhinomcp/tools/*.py
```

Each tool file contains full parameter documentation and usage examples.

---

## See Also

- [AGENTS.md](../AGENTS.md) - Agent development guide
- [README.md](../README.md) - Project overview
