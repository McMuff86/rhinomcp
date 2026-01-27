---
name: rhinomcp
description: Control Rhino 3D via RhinoMCP plugin. Use when creating, modifying, or deleting 3D geometry (spheres, boxes, cylinders, lines, curves, meshes), managing layers and materials (including PBR), boolean operations, transforms, file import/export, groups/blocks, or querying document information. Requires Rhino running on Windows with RhinoMCP plugin started (`tcpstart` command for WSL access).
---

# RhinoMCP Skill

Control Rhino 3D directly from Clawdbot via TCP socket connection to the RhinoMCP plugin.

## Prerequisites

1. **Rhino 7/8** running on Windows
2. **RhinoMCP plugin** installed and built
3. **Plugin started**: In Rhino command line, type `tcpstart` (for WSL/remote access)

> **Note:** Use `mcpstart` for local-only access (Cursor, Claude Desktop), `tcpstart` for WSL/Clawdbot.

## Configuration

Edit `config.json`:

```json
{
  "connection": {
    "host": "172.31.96.1",
    "port": 1999,
    "timeout": 15.0
  },
  "screenshots": {
    "linux_dir": "/home/mcmuff/clawd/projects/rhinomcp-dev/captures",
    "windows_dir": "\\\\wsl.localhost\\Ubuntu\\home\\mcmuff\\clawd\\projects\\rhinomcp-dev\\captures"
  }
}
```

## Quick Test

```bash
cd ~/clawd/skills/rhinomcp/scripts
python3 rhino_client.py ping
```

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `rhino_client.py` | Base TCP client, raw commands |
| `geometry.py` | Create primitives (box, sphere, cylinder, curves...) |
| `transforms.py` | Move, rotate, scale, copy, mirror, arrays |
| `booleans.py` | Union, difference, intersection |
| `selection.py` | Select by layer, type, name, IDs |
| `analysis.py` | Object info, properties, bounding box, volume |
| `curves.py` | Offset, fillet, chamfer, join, explode |
| `surfaces.py` | Loft, extrude, revolve, sweep |
| `layers.py` | Create, set, list, delete layers |
| `materials.py` | PBR materials, assign to layers |
| `viewport.py` | Views, camera, screenshots |
| `render.py` | Lights, render settings, render to file |
| `files.py` | Open, save, import, export (STEP, OBJ, STL...) |
| `groups.py` | Groups and block definitions |
| `scene.py` | Document info, batch operations |

---

## 🎯 Geometry Creation

```bash
# Primitives
python3 geometry.py sphere --radius 5 --position 0,0,0 --name "Ball"
python3 geometry.py box --width 10 --length 10 --height 5 --color 255,0,0
python3 geometry.py cylinder --radius 2 --height 8 --layer "Parts"
python3 geometry.py cone --radius 3 --height 6
python3 geometry.py line --start 0,0,0 --end 10,10,0
python3 geometry.py circle --radius 5
python3 geometry.py arc --radius 5 --angle 90
python3 geometry.py polyline --points "0,0,0 10,0,0 10,10,0 0,10,0"
```

### Supported Geometry Types

| Type | Key Parameters |
|------|----------------|
| POINT | location |
| LINE | start, end |
| POLYLINE | points |
| CIRCLE | center, radius |
| ARC | center, radius, angle |
| ELLIPSE | center, radius_x, radius_y |
| CURVE | points, degree |
| BOX | width, length, height |
| SPHERE | radius |
| CONE | radius, height |
| CYLINDER | radius, height |
| MESH | vertices, faces |

---

## 🔄 Transform Operations

```bash
# Move object
python3 transforms.py move <id> --vector 10,0,0

# Rotate object (degrees around axis through point)
python3 transforms.py rotate <id> --angle 45 --axis 0,0,1 --center 0,0,0

# Scale object
python3 transforms.py scale <id> --factor 2.0 --center 0,0,0

# Copy with offset
python3 transforms.py copy <id> --offset 10,0,0

# Mirror across plane
python3 transforms.py mirror <id> --origin 0,0,0 --normal 1,0,0

# Linear array: 5 copies along X
python3 transforms.py linear <id> --direction 1,0,0 --count 5 --distance 10

# Polar array: 8 copies around Z axis
python3 transforms.py polar <id> --center 0,0,0 --axis 0,0,1 --count 8
```

---

## ⚡ Boolean Operations

```bash
# Union multiple solids
python3 booleans.py union <id1> <id2> <id3>

# Difference: subtract cutter(s) from base
python3 booleans.py difference <base_id> <cutter_id>

# Intersection
python3 booleans.py intersection <id1> <id2>

# Keep input objects (don't delete)
python3 booleans.py union <id1> <id2> --keep
```

> **Note:** Objects must be closed solids (Breps).

---

## 🎯 Selection

```bash
# Select all
python3 selection.py all

# Clear selection
python3 selection.py none

# Get info about selected objects
python3 selection.py get

# Select by layer
python3 selection.py layer "MyLayer"

# Select by object type
python3 selection.py type solid    # solid, curve, surface, mesh, point, etc.

# Select by name (partial match)
python3 selection.py name "Box"

# Select specific IDs
python3 selection.py ids <id1> <id2> <id3>

# Combined filters
python3 selection.py filter --layer "Parts" --type solid
```

---

## 📊 Object Analysis

```bash
# Basic object info
python3 analysis.py info <object_id>

# Detailed properties (bounding box, area, volume, centroid)
python3 analysis.py properties <object_id>

# Info about selected objects
python3 analysis.py selected

# Document summary
python3 analysis.py document
```

---

## 〰️ Curve Operations

```bash
# Offset curve
python3 curves.py offset <curve_id> --distance 5

# Fillet two curves
python3 curves.py fillet <curve1_id> <curve2_id> --radius 2

# Chamfer two curves
python3 curves.py chamfer <curve1_id> <curve2_id> --distance 3

# Join curves into polycurve
python3 curves.py join <id1> <id2> <id3>

# Explode polycurve into segments
python3 curves.py explode <polycurve_id>

# Keep input (don't delete)
python3 curves.py join <id1> <id2> --keep
```

---

## 🏔️ Surface Operations

```bash
# Loft through curves
python3 surfaces.py loft <curve1_id> <curve2_id> <curve3_id>

# Extrude curve along vector
python3 surfaces.py extrude <curve_id> --direction 0,0,10

# Revolve curve around axis
python3 surfaces.py revolve <curve_id> --axis-start 0,0,0 --axis-end 0,0,1 --angle 360

# Sweep curve along rail
python3 surfaces.py sweep <profile_id> <rail_id>

# Create planar surface from closed curve
python3 surfaces.py planar <closed_curve_id>
```

---

## 📁 Layers

```bash
python3 layers.py create "MyLayer" --color 255,100,100
python3 layers.py set "MyLayer"
python3 layers.py list
python3 layers.py delete "OldLayer"
```

---

## 🎨 Materials (PBR)

```bash
# Metal presets
python3 materials.py preset gold
python3 materials.py preset silver
python3 materials.py preset copper

# Custom PBR material
python3 materials.py pbr "Chrome" --color 200,200,210 --metallic 0.95 --roughness 0.02

# Assign material to layer
python3 materials.py assign "MyLayer" <material_id>
```

---

## 📷 Viewport & Screenshots

```bash
# Set standard view
python3 viewport.py view Perspective
python3 viewport.py view Top

# Zoom to fit all
python3 viewport.py zoom

# Zoom to selection
python3 viewport.py zoom --selected

# Orbit camera
python3 viewport.py orbit --yaw 45 --pitch 30

# Set camera position
python3 viewport.py camera --position 100,100,50 --target 0,0,0 --lens 35

# Capture screenshot (saves to linux_dir, returns linux_path)
python3 viewport.py screenshot --width 1920 --height 1080
python3 viewport.py screenshot --output myrender.png

# Render with materials
python3 viewport.py render --output render.png
```

> **Screenshots** are saved directly to the Linux filesystem via WSL UNC path. The returned `linux_path` can be read directly.

---

## 💡 Render & Lighting

```bash
# Set render quality
python3 render.py settings --width 1920 --height 1080 --quality high
python3 render.py settings --background 50,50,50

# Add lights
python3 render.py light point --position 50,50,100 --intensity 1.5
python3 render.py light directional --direction -1,-1,-1
python3 render.py light spot --position 0,0,100 --target 0,0,0

# Render to file
python3 render.py render --output scene.png
```

---

## 📦 Files (Import/Export)

```bash
# Open 3DM file
python3 files.py open "/path/to/file.3dm"

# Save current document
python3 files.py save
python3 files.py save --path "/path/to/new.3dm"

# Export to various formats
python3 files.py export output.step
python3 files.py export output.obj --ids <id1> <id2>
python3 files.py export output.stl --format stl

# Import mesh
python3 files.py import model.obj
```

### Supported Export Formats
STEP, IGES, OBJ, STL, DXF, DWG, 3DS, FBX, DAE

---

## 📦 Groups & Blocks

```bash
# Create group
python3 groups.py group <id1> <id2> --name "MyGroup"

# Ungroup
python3 groups.py ungroup --name "MyGroup"

# Create block definition
python3 groups.py block-create "MyBlock" <id1> <id2> --base 0,0,0

# Insert block instance
python3 groups.py block-insert "MyBlock" --position 10,0,0 --scale 2 --rotation 45

# Explode block
python3 groups.py block-explode <instance_id>
```

---

## 📜 RhinoScript Execution

```bash
# Execute inline code
python3 script_exec.py -c "import rhinoscriptsyntax as rs; rs.AddSphere([0,0,0], 10)"

# Execute script file
python3 script_exec.py -f ~/scripts/my_script.py
```

---

## 🔍 Log Monitoring

Check the Rhino log for debugging:

```bash
# View recent log entries
tail -30 "/mnt/c/Users/Adi.Muff/AppData/Local/Temp/rhinomcp.log"

# Continuous monitoring
tail -f "/mnt/c/Users/Adi.Muff/AppData/Local/Temp/rhinomcp.log" &
```

---

## Example: Complete PBR Scene Workflow

```bash
# 1. Create layer with material
python3 layers.py create "Gold_Parts" --color 255,215,0
python3 materials.py preset gold
# → Note material_id

# 2. Assign material to layer
python3 materials.py assign "Gold_Parts" <material_id>
python3 layers.py set "Gold_Parts"

# 3. Create geometry
python3 geometry.py sphere --radius 5 --name "Gold_Ball"
python3 geometry.py box --width 10 --length 10 --height 2 --position 0,0,-3

# 4. Boolean difference (cut hole)
python3 geometry.py cylinder --radius 2 --height 5 --position 0,0,-3
python3 booleans.py difference <box_id> <cylinder_id>

# 5. Set camera and capture
python3 viewport.py camera --position 30,30,20 --target 0,0,0 --lens 35
python3 viewport.py screenshot --width 1920 --height 1080
# → Returns linux_path, read directly with Read tool
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Run `tcpstart` in Rhino |
| Timeout | Increase timeout in config.json |
| Boolean failed | Ensure objects are closed solids |
| Screenshot path issues | Check windows_dir UNC path in config |
| Command not found | Rebuild plugin after C# changes |
