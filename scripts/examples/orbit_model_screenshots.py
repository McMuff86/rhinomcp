#!/usr/bin/env python3
"""
Create orbit screenshots around a model in Rhino.

This script demonstrates how to:
- Set viewport to perspective view
- Rotate camera around the model at different angles
- Capture screenshots at each angle
- Use zoom_extents to ensure model is visible

Usage:
    python scripts/examples/orbit_model_screenshots.py

The screenshots will be saved to screenshots/ directory with names like:
    model_orbit_00_0deg.png
    model_orbit_01_45deg.png
    etc.
"""

import sys
from pathlib import Path

# Add the server path to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "rhino_mcp_server" / "src"))

from rhinomcp.tools.set_view import set_view
from rhinomcp.tools.orbit_camera import orbit_camera
from rhinomcp.tools.capture_viewport import capture_viewport
from rhinomcp.tools.zoom_extents import zoom_extents
from mcp.server.fastmcp import Context

def create_orbit_screenshots(
    base_filename: str = "model_orbit",
    angles: list = None,
    viewport_name: str = "Perspective"
):
    """
    Create orbit screenshots around the current model.
    
    Parameters:
    - base_filename: Base name for screenshot files (default: "model_orbit")
    - angles: List of angles in degrees to rotate (default: [0, 45, 90, 135, 180, 225, 270, 315])
    - viewport_name: Name of viewport to use (default: "Perspective")
    """
    if angles is None:
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
    
    ctx = Context()
    
    # Set to perspective view
    set_view(ctx, viewport_name)
    zoom_extents(ctx)
    
    print(f"Creating orbit screenshots ({len(angles)} angles)...")
    
    # Create screenshots at different angles
    for i, angle in enumerate(angles):
        if angle == 0:
            # Initial position
            capture_viewport(ctx, filename=f"{base_filename}_{i:02d}_{angle}deg.png")
            print(f"Screenshot {i+1}/{len(angles)} created: {angle}°")
        else:
            # Rotate camera
            orbit_camera(ctx, "right", angle, viewport_name=viewport_name)
            zoom_extents(ctx)
            capture_viewport(ctx, filename=f"{base_filename}_{i:02d}_{angle}deg.png", viewport_name=viewport_name)
            print(f"Screenshot {i+1}/{len(angles)} created: {angle}°")
    
    print(f"All {len(angles)} orbit screenshots created!")

if __name__ == "__main__":
    create_orbit_screenshots()
