# RhinoMCP Usage Guide

> Complete guide for using RhinoMCP tools to control Rhino via AI agents.

**Last Updated:** 2026-01-10  
**Version:** 0.1.3.6

---

## Quick Start

### 1. Start Rhino Plugin
```
# In Rhino Command Line
mcpstart
```

### 2. Start MCP Server
```bash
cd rhino_mcp_server
uv run rhinomcp
```

### 3. Verify Connection
Use the `ping` tool to test connectivity.

---

## Available Tools

### System Tools

| Tool | Description |
|------|-------------|
| `ping` | Test server connection |
| `set_debug_mode` | Enable/disable enhanced logging |
| `log_thought` | Log AI thought processes |
| `get_document_info` | Get current document information |

### Object Creation

| Tool | Description |
|------|-------------|
| `create_object` | Create geometry (BOX, SPHERE, CYLINDER, etc.) |
| `create_objects` | Batch create multiple objects |
| `create_text` | Create text annotation |
| `create_text_dot` | Create text dot annotation |
| `create_leader` | Create leader annotation |

#### Supported Object Types

| Type | Parameters |
|------|------------|
| `POINT` | `x`, `y`, `z` |
| `LINE` | `start: [x,y,z]`, `end: [x,y,z]` |
| `POLYLINE` | `points: [[x,y,z], ...]` |
| `CIRCLE` | `center: [x,y,z]`, `radius` |
| `ARC` | `center`, `radius`, `angle` (degrees) |
| `ELLIPSE` | `center`, `radius_x`, `radius_y` |
| `CURVE` | `points`, `degree` |
| `BOX` | `width`, `length`, `height` |
| `SPHERE` | `radius` |
| `CONE` | `radius`, `height`, `cap` |
| `CYLINDER` | `radius`, `height`, `cap` |
| `SURFACE` | `count`, `points`, `degree`, `closed` |
| `MESH` | `vertices`, `faces` |
| `TEXT` | `text`, `location`, `height` |
| `TEXT_DOT` | `text`, `location` |
| `LEADER` | `text`, `points` |

#### Example: Create a Box
```python
create_object(
    type="BOX",
    name="MyCube",
    params={"width": 10, "length": 10, "height": 10},
    translation=[0, 0, 5],
    color=[255, 0, 0]
)
```

### Object Manipulation

| Tool | Description |
|------|-------------|
| `modify_object` | Transform a single object |
| `modify_objects` | Batch transform objects |
| `delete_object` | Delete an object by ID |
| `select_objects` | Select objects by ID |
| `get_object_info` | Get object properties |
| `get_selected_objects_info` | Get selected objects info |

### Boolean Operations

| Tool | Description |
|------|-------------|
| `boolean_operation` | Perform boolean operations on solids |

#### Supported Operations

| Operation | Description |
|-----------|-------------|
| `union` | Combine multiple solids into one |
| `difference` | Subtract solids from a base solid |
| `intersection` | Keep only the overlapping volume |

#### Example: Boolean Union
```python
# Create two overlapping boxes
box1 = create_object(type="BOX", params={"width": 10, "length": 10, "height": 10})
box2 = create_object(
    type="BOX", 
    params={"width": 10, "length": 10, "height": 10},
    translation=[5, 5, 0]
)

# Combine into one solid
boolean_operation(
    operation="union",
    object_ids=[box1["id"], box2["id"]],
    delete_input=True  # Remove original objects
)
```

#### Example: Boolean Difference
```python
# Create base box and cutting cylinder
base = create_object(type="BOX", params={"width": 20, "length": 20, "height": 10})
cutter = create_object(
    type="CYLINDER", 
    params={"radius": 5, "height": 15, "cap": True},
    translation=[10, 10, -2]
)

# Subtract cylinder from box (creates a hole)
boolean_operation(
    operation="difference",
    object_ids=[base["id"], cutter["id"]]  # First ID is base
)
```

#### Example: Boolean Intersection
```python
# Create two overlapping spheres
sphere1 = create_object(type="SPHERE", params={"radius": 10})
sphere2 = create_object(
    type="SPHERE", 
    params={"radius": 10},
    translation=[8, 0, 0]
)

# Keep only overlapping volume
boolean_operation(
    operation="intersection",
    object_ids=[sphere1["id"], sphere2["id"]]
)
```

#### Notes
- All input objects must be closed solids (Breps)
- For `difference`, the first object_id is the base from which others are subtracted
- Returns the new object ID(s) of the resulting solid(s)
- Set `delete_input=False` to keep original objects

### Layer Management

| Tool | Description |
|------|-------------|
| `create_layer` | Create a new layer |
| `get_or_set_current_layer` | Get or set current layer |
| `delete_layer` | Delete a layer |

#### Example: Layer Workflow
```python
# Create layer
create_layer(name="MyLayer", color=[0, 128, 255])

# Set as current
get_or_set_current_layer(name="MyLayer")

# Objects now created on MyLayer
create_object(type="SPHERE", params={"radius": 5})
```

### Material System

| Tool | Description |
|------|-------------|
| `create_material` | Create legacy or PBR material |
| `assign_material_to_layer` | Assign material to layer |

#### Legacy Materials
```python
create_material(
    name="Gold",
    color=[255, 215, 0],
    shine=0.9  # 0.0 = matte, 1.0 = glossy
)
```

#### PBR Materials (Recommended)
```python
create_material(
    name="GoldPBR",
    material_type="pbr",
    color=[255, 215, 0],
    metallic=0.95,   # 0.0 = dielectric, 1.0 = metal
    roughness=0.05   # 0.0 = mirror, 1.0 = rough
)
```

#### Layer-Based Material Workflow (Best Practice)
```python
# 1. Create material layer
create_layer(name="Gold_Layer", color=[255, 215, 0])

# 2. Create PBR material
result = create_material(
    name="GoldPBR",
    material_type="pbr",
    color=[255, 215, 0],
    metallic=0.95,
    roughness=0.05
)
material_id = result["id"]

# 3. Assign material to layer
assign_material_to_layer(
    layer_name="Gold_Layer",
    material_id=material_id
)

# 4. Create objects on layer (auto-inherit material)
get_or_set_current_layer(name="Gold_Layer")
create_object(type="SPHERE", params={"radius": 5})
```

### RhinoScript Execution

| Tool | Description |
|------|-------------|
| `execute_rhinoscript_python_code` | Run Python code in Rhino |

#### Example with Timeout
```python
execute_rhinoscript_python_code(
    code='''
import rhinoscriptsyntax as rs
rs.AddSphere([0,0,0], 10)
''',
    timeout=30  # seconds (default: 15, max: 120)
)
```

---

## Parameter Conventions

### Colors
- Format: `[R, G, B]` (0-255)
- Examples:
  - Red: `[255, 0, 0]`
  - Gold: `[255, 215, 0]`
  - Silver: `[192, 192, 192]`

### Points / Coordinates
- Format: `[X, Y, Z]`
- Units: Model units (typically mm)

### IDs
- Format: GUID string (e.g., `"ae0b9ce6-1d6a-43cf-856f-12f2351eab27"`)

### Transforms
- `translation`: `[X, Y, Z]` offset
- `rotation`: `[X, Y, Z]` radians
- `scale`: `[X, Y, Z]` factors

---

## Error Handling

RhinoMCP uses structured error codes:

| Code | Description |
|------|-------------|
| `CONNECTION_ERROR` | Cannot connect to Rhino |
| `CONNECTION_TIMEOUT` | Operation timed out |
| `CONNECTION_REFUSED` | Rhino not running |
| `INVALID_PARAMS` | Invalid parameters |
| `RHINO_ERROR` | Error in Rhino |
| `CREATE_OBJECT_ERROR` | Object creation failed |

---

## Troubleshooting

### "Connection refused"
1. Start Rhino
2. Run `mcpstart` in Rhino command line
3. Restart MCP server

### "Timeout waiting for response"
- Increase timeout for long operations
- Check if Rhino is responding
- Reduce batch size

### "Unknown command"
- Ensure command is registered on both Python and C# sides
- Check command name spelling

### Check Connection Status
```
# In Rhino command line
MCPStatus
```

---

## Best Practices

1. **Use layer-based materials** for PBR workflows
2. **Set current layer** before creating objects
3. **Use batch operations** (`create_objects`, `modify_objects`) for >10 items
4. **Enable debug mode** for troubleshooting
5. **Use meaningful names** for objects and layers
6. **Use `ping`** to verify connection before complex operations

---

## Examples

### Create PBR Metal Spheres
```python
# Gold sphere
create_layer(name="Gold", color=[255, 215, 0])
create_material(name="GoldPBR", material_type="pbr", 
                color=[255, 215, 0], metallic=0.95, roughness=0.05)
assign_material_to_layer(layer_name="Gold", material_id="0")
get_or_set_current_layer(name="Gold")
create_object(type="SPHERE", params={"radius": 5}, translation=[-10, 0, 0])

# Silver sphere
create_layer(name="Silver", color=[192, 192, 192])
create_material(name="SilverPBR", material_type="pbr",
                color=[192, 192, 192], metallic=0.90, roughness=0.10)
assign_material_to_layer(layer_name="Silver", material_id="1")
get_or_set_current_layer(name="Silver")
create_object(type="SPHERE", params={"radius": 5}, translation=[0, 0, 0])
```

### Create Annotation
```python
# Text
create_object(
    type="TEXT",
    params={"text": "Hello World", "location": [0, 0, 0], "height": 5}
)

# Leader
create_object(
    type="LEADER",
    params={"text": "Note", "points": [[0, 0, 0], [10, 10, 0], [20, 10, 0]]}
)
```

---

## See Also

- [AGENTS.md](AGENTS.md) - Agent development guide
- [MCP_TOOL_STANDARDS.md](MCP_TOOL_STANDARDS.md) - Tool development standards
- [FUNCTIONAL_STATUS.md](FUNCTIONAL_STATUS.md) - Feature status and known issues
- [ROADMAP.md](ROADMAP.md) - Project roadmap
