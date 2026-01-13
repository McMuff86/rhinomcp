# Viewport & Camera Operations

> Learnings for viewport control, camera manipulation, and screenshot capture in RhinoMCP.

**Last Updated:** 2026-01-13

---

## Overview

RhinoMCP provides tools for controlling viewports, rotating cameras, and capturing screenshots. These are essential for:
- Visual verification of geometry creation
- Multimodal model feedback
- Creating documentation images
- Interactive model exploration

---

## Available Tools

### Viewport Control

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `set_view` | Set standard views | `view_type`: "Top", "Front", "Perspective", etc. |
| `zoom_extents` | Zoom to show all objects | `viewport_name`, `include_hidden` |
| `zoom_selected` | Zoom to selected objects | `viewport_name`, `object_ids` |
| `set_camera` | Set camera position | `camera_location`, `target_location`, `lens_length` |
| `orbit_camera` | Rotate camera around target | `direction`: "right", "left", "up", "down", `angle_degrees` |
| `capture_viewport` | Capture screenshot | `viewport_name`, `width`, `height`, `filename`, `auto_save` |

---

## Camera Rotation (Orbit)

### Basic Usage

```python
from rhinomcp.tools.orbit_camera import orbit_camera
from mcp.server.fastmcp import Context

ctx = Context()

# Rotate camera 30° to the right
orbit_camera(ctx, direction="right", angle_degrees=30)

# Rotate camera 15° up
orbit_camera(ctx, direction="up", angle_degrees=15)
```

### Direction Mapping

The `orbit_camera` tool uses RhinoScript's `RotateCamera` function internally:

| Direction | RhinoScript Code | Description |
|-----------|------------------|-------------|
| "right" | 0 | Rotate camera right (clockwise when viewed from above) |
| "left" | 1 | Rotate camera left (counter-clockwise) |
| "down" | 2 | Rotate camera down |
| "up" | 3 | Rotate camera up |

### Implementation Pattern

```python
# Map direction to RhinoScript direction codes
direction_map = {
    "right": 0,
    "left": 1,
    "down": 2,
    "up": 3
}

# Use RhinoScript to rotate camera
code = f"""
import rhinoscriptsyntax as rs
rs.RotateCamera(view="{viewport_name}", direction={direction_code}, angle={angle_degrees})
"""
```

**Key Insight:** Using RhinoScript functions via `execute_rhinoscript_python_code` is often simpler than implementing camera math manually in C#.

---

## Screenshot Capture

### Auto-Save Feature

The `capture_viewport` tool automatically saves screenshots to `screenshots/` directory:

```python
from rhinomcp.tools.capture_viewport import capture_viewport

# Auto-save with timestamp
capture_viewport(ctx)  
# → screenshots/viewport_Perspective_20260113_002315.png

# Custom filename (saved to screenshots/)
capture_viewport(ctx, filename="my_model.png")
# → screenshots/my_model.png

# Absolute path
capture_viewport(ctx, filename="C:/full/path/screenshot.png")
```

### Screenshot Directory

- **Location:** `screenshots/` (project root)
- **Auto-creation:** Directory created automatically on first use
- **Git status:** Ignored (added to `.gitignore`)
- **Purpose:** Multimodal model verification, documentation

### Implementation Details

**Python Side:**
```python
def get_screenshots_dir() -> Path:
    """Get screenshots directory path."""
    server_root = Path(__file__).parent.parent.parent.parent.parent
    screenshots_dir = server_root / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    return screenshots_dir
```

**C# Side:**
```csharp
// Ensure directory exists before saving
var fileInfo = new System.IO.FileInfo(filename);
if (fileInfo.Directory != null && !fileInfo.Directory.Exists)
{
    fileInfo.Directory.Create();
}
```

---

## Common Patterns

### 1. Orbit Around Model

```python
from rhinomcp.tools.set_view import set_view
from rhinomcp.tools.orbit_camera import orbit_camera
from rhinomcp.tools.capture_viewport import capture_viewport
from rhinomcp.tools.zoom_extents import zoom_extents

# Set to perspective view
set_view(ctx, "Perspective")
zoom_extents(ctx)

# Create screenshots at different angles
angles = [0, 45, 90, 135, 180, 225, 270, 315]
for i, angle in enumerate(angles):
    if angle == 0:
        capture_viewport(ctx, filename=f"model_{i:02d}_{angle}deg.png")
    else:
        orbit_camera(ctx, "right", angle)
        zoom_extents(ctx)  # Re-zoom after rotation
        capture_viewport(ctx, filename=f"model_{i:02d}_{angle}deg.png")
```

### 2. Multiple Standard Views

```python
views = ["Top", "Front", "Right", "Left", "Back", "Bottom", "Perspective"]
for view in views:
    set_view(ctx, view)
    zoom_extents(ctx)
    capture_viewport(ctx, filename=f"model_{view.lower()}.png")
```

### 3. Camera Position Calculation

For custom camera positions, calculate positions on a circle:

```python
import math

def get_camera_position(center, radius, angle_degrees, height):
    """Calculate camera position on circle around center."""
    angle_rad = math.radians(angle_degrees)
    x = center[0] + radius * math.cos(angle_rad)
    y = center[1] + radius * math.sin(angle_rad)
    z = center[2] + height
    return [x, y, z]

# Use with set_camera
camera_pos = get_camera_position([0, 0, 0], 50, 45, 10)
set_camera(ctx, camera_location=camera_pos, target_location=[0, 0, 0])
```

---

## Best Practices

1. **Always zoom extents after rotation** - Camera rotation can change the view, re-zoom to ensure model is visible
2. **Use auto-save for quick screenshots** - Let the tool generate filenames with timestamps
3. **Custom filenames for documentation** - Use descriptive names when creating documentation images
4. **Perspective view for orbit** - Orbit works best in perspective projection mode
5. **Batch operations** - Create multiple screenshots in loops for comprehensive documentation

---

## Troubleshooting

### Camera doesn't rotate
- Ensure viewport is in perspective mode (`set_view(ctx, "Perspective")`)
- Check that angle is positive and reasonable (1-360°)

### Screenshots not saving
- Check that `screenshots/` directory exists (auto-created)
- Verify write permissions
- Check file path length (Windows limit: 260 chars)

### Viewport not found
- Default viewport name is "Perspective"
- Use `get_document_info` to list available viewports
- Ensure Rhino is running and viewport exists

---

## Related Documentation

- `docs/USAGE.md` - Complete tool reference
- `docs/learnings/rhinocommon-api.md` - RhinoCommon API patterns
- `scripts/examples/orbit_model_screenshots.py` - Example script

---

## See Also

- RhinoScript Documentation: `RotateCamera`, `ViewCamera`, `ZoomExtents`
- RhinoCommon: `RhinoView`, `Viewport`, `CameraLocation`, `CameraTarget`
