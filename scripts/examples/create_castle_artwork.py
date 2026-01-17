"""
Create a castle artwork with cubes, materials, rendering, and screenshots.

This script creates a detailed castle structure using cubes with different
building materials (stone, wood, metal, roof tiles) and renders it with
proper lighting and camera angles.
"""

import json
import sys
import time
from pathlib import Path

# Add parent directory to path to import rhinomcp
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "rhino_mcp_server" / "src"))

from rhinomcp.server import get_rhino_connection


def wait_for_rhino(delay=0.1):
    """Small delay to ensure Rhino operations complete."""
    time.sleep(delay)


def create_castle():
    """Create a detailed castle structure."""
    rhino = get_rhino_connection()
    
    print("Creating Castle Artwork...")
    print("=" * 60)
    
    # ============================================================
    # 1. CREATE MATERIALS
    # ============================================================
    print("\n[1/6] Creating materials...")
    
    materials = {}
    
    # Stone material (walls)
    result = rhino.send_command("create_material", {
        "name": "CastleStone",
        "color": [120, 120, 130],  # Gray stone
        "material_type": "pbr",
        "metallic": 0.0,
        "roughness": 0.8
    })
    materials["stone"] = result["id"]
    wait_for_rhino(0.3)
    
    # Wood material (doors, gates)
    result = rhino.send_command("create_material", {
        "name": "CastleWood",
        "color": [80, 50, 30],  # Brown wood
        "material_type": "pbr",
        "metallic": 0.0,
        "roughness": 0.6
    })
    materials["wood"] = result["id"]
    wait_for_rhino(0.3)
    
    # Metal material (gates, decorations)
    result = rhino.send_command("create_material", {
        "name": "CastleMetal",
        "color": [180, 180, 190],  # Silver metal
        "material_type": "pbr",
        "metallic": 0.9,
        "roughness": 0.2
    })
    materials["metal"] = result["id"]
    wait_for_rhino(0.3)
    
    # Roof tiles material
    result = rhino.send_command("create_material", {
        "name": "RoofTiles",
        "color": [150, 40, 30],  # Red tiles
        "material_type": "pbr",
        "metallic": 0.0,
        "roughness": 0.7
    })
    materials["roof"] = result["id"]
    wait_for_rhino(0.3)
    
    print("[OK] Materials created")
    
    # ============================================================
    # 2. CREATE LAYERS
    # ============================================================
    print("\n[2/6] Creating layers...")
    
    layers = {}
    layer_configs = {
        "Walls": {"color": [120, 120, 130], "material": materials["stone"]},
        "Towers": {"color": [110, 110, 120], "material": materials["stone"]},
        "Gates": {"color": [80, 50, 30], "material": materials["wood"]},
        "Metal": {"color": [180, 180, 190], "material": materials["metal"]},
        "Roofs": {"color": [150, 40, 30], "material": materials["roof"]},
    }
    
    for layer_name, config in layer_configs.items():
        result = rhino.send_command("create_layer", {
            "name": layer_name,
            "color": config["color"]
        })
        layers[layer_name] = result.get("name", layer_name)
        wait_for_rhino(0.1)
        
        # Assign material to layer
        result = rhino.send_command("assign_material_to_layer", {
            "layer_name": layer_name,
            "material_id": config["material"]
        })
        wait_for_rhino(0.1)
    
    print("[OK] Layers created and materials assigned")
    
    # ============================================================
    # 3. CREATE CASTLE STRUCTURE
    # ============================================================
    print("\n[3/6] Building castle structure...")
    
    cube_size = 2.0  # Size of each cube
    base_x = 0.0
    base_y = 0.0
    base_z = 0.0
    
    # Castle dimensions
    wall_length = 20  # cubes
    wall_width = 16  # cubes
    wall_height = 4  # cubes
    tower_height = 8  # cubes (above wall)
    gate_width = 4  # cubes
    
    created_count = 0
    
    # Main walls (stone)
    print("  Building walls...")
    for x in range(wall_length):
        for z in range(wall_height):
            # Front wall (with gate opening)
            if not (wall_length // 2 - gate_width // 2 <= x < wall_length // 2 + gate_width // 2 and z < 3):
                result = rhino.send_command("create_object", {
                    "type": "BOX",
                    "name": f"Wall_Front_{x}_{z}",
                    "layer": "Walls",
                    "params": {
                        "width": cube_size,
                        "length": cube_size,
                        "height": cube_size
                    },
                    "translation": [
                        base_x + x * cube_size,
                        base_y,
                        base_z + z * cube_size
                    ]
                })
                created_count += 1
            
            # Back wall
            result = rhino.send_command("create_object", {
                "type": "BOX",
                "name": f"Wall_Back_{x}_{z}",
                "layer": "Walls",
                "params": {
                    "width": cube_size,
                    "length": cube_size,
                    "height": cube_size
                },
                "translation": [
                    base_x + x * cube_size,
                    base_y + (wall_width - 1) * cube_size,
                    base_z + z * cube_size
                ]
            })
            created_count += 1
            
            wait_for_rhino(0.01)
    
    # Side walls
    for y in range(1, wall_width - 1):
        for z in range(wall_height):
            # Left wall
            result = rhino.send_command("create_object", {
                "type": "BOX",
                "name": f"Wall_Left_{y}_{z}",
                "layer": "Walls",
                "params": {
                    "width": cube_size,
                    "length": cube_size,
                    "height": cube_size
                },
                "translation": [
                    base_x,
                    base_y + y * cube_size,
                    base_z + z * cube_size
                ]
            })
            created_count += 1
            
            # Right wall
            result = rhino.send_command("create_object", {
                "type": "BOX",
                "name": f"Wall_Right_{y}_{z}",
                "layer": "Walls",
                "params": {
                    "width": cube_size,
                    "length": cube_size,
                    "height": cube_size
                },
                "translation": [
                    base_x + (wall_length - 1) * cube_size,
                    base_y + y * cube_size,
                    base_z + z * cube_size
                ]
            })
            created_count += 1
            
            wait_for_rhino(0.01)
    
    # Corner towers (taller)
    print("  Building towers...")
    tower_positions = [
        (0, 0),
        (wall_length - 1, 0),
        (0, wall_width - 1),
        (wall_length - 1, wall_width - 1)
    ]
    
    for tx, ty in tower_positions:
        for z in range(wall_height, tower_height):
            result = rhino.send_command("create_object", {
                "type": "BOX",
                "name": f"Tower_{tx}_{ty}_{z}",
                "layer": "Towers",
                "params": {
                    "width": cube_size,
                    "length": cube_size,
                    "height": cube_size
                },
                "translation": [
                    base_x + tx * cube_size,
                    base_y + ty * cube_size,
                    base_z + z * cube_size
                ]
            })
            created_count += 1
            wait_for_rhino(0.01)
    
    # Gate structure (wood)
    print("  Building gate...")
    gate_x = base_x + (wall_length // 2 - gate_width // 2) * cube_size
    gate_y = base_y
    for x_offset in range(gate_width):
        for z in range(3):
            result = rhino.send_command("create_object", {
                "type": "BOX",
                "name": f"Gate_{x_offset}_{z}",
                "layer": "Gates",
                "params": {
                    "width": cube_size,
                    "length": cube_size,
                    "height": cube_size
                },
                "translation": [
                    gate_x + x_offset * cube_size,
                    gate_y,
                    base_z + z * cube_size
                ]
            })
            created_count += 1
            wait_for_rhino(0.01)
    
    # Metal gate decorations
    for x_offset in [0, gate_width - 1]:
        for z in range(3, 5):
            result = rhino.send_command("create_object", {
                "type": "BOX",
                "name": f"GateMetal_{x_offset}_{z}",
                "layer": "Metal",
                "params": {
                    "width": cube_size * 0.8,
                    "length": cube_size * 0.3,
                    "height": cube_size * 0.8
                },
                "translation": [
                    gate_x + x_offset * cube_size + cube_size * 0.1,
                    gate_y - cube_size * 0.35,
                    base_z + z * cube_size
                ]
            })
            created_count += 1
            wait_for_rhino(0.01)
    
    # Roof structures on towers (red tiles)
    print("  Building roofs...")
    for tx, ty in tower_positions:
        # Pyramid roof on each tower
        roof_levels = 3
        for level in range(roof_levels):
            roof_size = cube_size * (roof_levels - level) * 0.8
            roof_z = base_z + tower_height * cube_size + level * cube_size * 0.6
            
            # Create 4 roof pieces per level
            offsets = [
                (-roof_size * 0.25, -roof_size * 0.25),
                (roof_size * 0.25, -roof_size * 0.25),
                (-roof_size * 0.25, roof_size * 0.25),
                (roof_size * 0.25, roof_size * 0.25)
            ]
            
            for ox, oy in offsets:
                result = rhino.send_command("create_object", {
                    "type": "BOX",
                    "name": f"Roof_{tx}_{ty}_L{level}",
                    "layer": "Roofs",
                    "params": {
                        "width": roof_size * 0.4,
                        "length": roof_size * 0.4,
                        "height": cube_size * 0.5
                    },
                    "translation": [
                        base_x + tx * cube_size + ox,
                        base_y + ty * cube_size + oy,
                        roof_z
                    ]
                })
                created_count += 1
                wait_for_rhino(0.01)
    
    print(f"[OK] Castle structure complete: {created_count} cubes created")
    
    # ============================================================
    # 4. SETUP CAMERA AND LIGHTING
    # ============================================================
    print("\n[4/6] Setting up camera and lighting...")
    
    # Calculate castle center
    castle_center_x = base_x + (wall_length / 2) * cube_size
    castle_center_y = base_y + (wall_width / 2) * cube_size
    castle_center_z = base_z + (tower_height / 2) * cube_size
    
    # Set camera position (diagonal view)
    camera_distance = max(wall_length, wall_width) * cube_size * 1.5
    result = rhino.send_command("set_camera", {
        "viewport_name": "Perspective",
        "camera_location": [
            castle_center_x + camera_distance * 0.7,
            castle_center_y - camera_distance * 0.7,
            castle_center_z + camera_distance * 0.3
        ],
        "target_location": [castle_center_x, castle_center_y, castle_center_z],
        "lens_length": 50.0
    })
    print("[OK] Camera positioned")
    
    # Add lights
    # Main directional light (sun)
    result = rhino.send_command("add_light", {
        "light_type": "directional",
        "direction": [-0.5, -0.5, -1.0],
        "color": [255, 255, 240],  # Warm sunlight
        "intensity": 1.2,
        "name": "Sun"
    })
    wait_for_rhino(0.1)
    
    # Fill light (sky)
    result = rhino.send_command("add_light", {
        "light_type": "directional",
        "direction": [0.3, 0.3, -0.8],
        "color": [200, 220, 255],  # Sky blue
        "intensity": 0.4,
        "name": "Sky"
    })
    wait_for_rhino(0.1)
    
    # Point light near gate (torch)
    result = rhino.send_command("add_light", {
        "light_type": "point",
        "location": [
            castle_center_x,
            gate_y - cube_size * 2,
            base_z + cube_size * 2
        ],
        "color": [255, 200, 150],  # Warm torch light
        "intensity": 0.8,
        "name": "Torch"
    })
    wait_for_rhino(0.1)
    
    print("[OK] Lighting setup complete")
    
    # ============================================================
    # 5. SET VIEW, DISPLAY MODE AND ZOOM
    # ============================================================
    print("\n[5/6] Setting view and display mode...")
    
    result = rhino.send_command("set_view", {
        "viewport_name": "Perspective",
        "view_name": "Perspective"
    })
    wait_for_rhino(0.2)
    
    # Set display mode to "Rendered" to show materials properly
    result = rhino.send_command("execute_rhinoscript_python_code", {
        "code": """
import rhinoscriptsyntax as rs
rs.ViewDisplayMode("Perspective", "Rendered")
"""
    })
    wait_for_rhino(0.3)
    
    result = rhino.send_command("zoom_extents", {
        "viewport_name": "Perspective"
    })
    wait_for_rhino(0.5)
    
    print("[OK] View configured and display mode set to Rendered")
    
    # ============================================================
    # 6. RENDER AND CAPTURE SCREENSHOTS
    # ============================================================
    print("\n[6/6] Rendering and capturing screenshots...")
    
    # Ensure screenshots directory exists (it's in .gitignore, so may not exist)
    screenshots_dir = Path(__file__).parent.parent.parent / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    if not screenshots_dir.exists():
        raise RuntimeError(f"Failed to create screenshots directory: {screenshots_dir}")
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Render high-quality image
    render_file = screenshots_dir / f"castle_render_{timestamp}.png"
    result = rhino.send_command("render_view", {
        "viewport_name": "Perspective",
        "width": 2560,
        "height": 1440,
        "filename": str(render_file),
        "display_mode": "rendered"
    })
    print(f"[OK] Rendered image saved: {render_file}")
    wait_for_rhino(1.0)
    
    # Capture viewport screenshot (faster, different angle)
    screenshot_file = screenshots_dir / f"castle_screenshot_{timestamp}.png"
    result = rhino.send_command("capture_viewport", {
        "viewport_name": "Perspective",
        "width": 1920,
        "height": 1080,
        "filename": str(screenshot_file),
        "auto_save": True
    })
    print(f"[OK] Screenshot saved: {screenshot_file}")
    
    # Additional views
    print("\nCapturing additional views...")
    
    # Top view
    result = rhino.send_command("set_view", {
        "viewport_name": "Perspective",
        "view_name": "Top"
    })
    wait_for_rhino(0.3)
    result = rhino.send_command("zoom_extents", {
        "viewport_name": "Perspective"
    })
    wait_for_rhino(0.3)
    
    top_file = screenshots_dir / f"castle_top_{timestamp}.png"
    result = rhino.send_command("capture_viewport", {
        "viewport_name": "Perspective",
        "width": 1920,
        "height": 1080,
        "filename": str(top_file),
        "auto_save": True
    })
    print(f"[OK] Top view saved: {top_file}")
    
    # Front view
    result = rhino.send_command("set_view", {
        "viewport_name": "Perspective",
        "view_name": "Front"
    })
    wait_for_rhino(0.3)
    result = rhino.send_command("zoom_extents", {
        "viewport_name": "Perspective"
    })
    wait_for_rhino(0.3)
    
    front_file = screenshots_dir / f"castle_front_{timestamp}.png"
    result = rhino.send_command("capture_viewport", {
        "viewport_name": "Perspective",
        "width": 1920,
        "height": 1080,
        "filename": str(front_file),
        "auto_save": True
    })
    print(f"[OK] Front view saved: {front_file}")
    
    # Return to perspective
    result = rhino.send_command("set_view", {
        "viewport_name": "Perspective",
        "view_name": "Perspective"
    })
    wait_for_rhino(0.3)
    result = rhino.send_command("zoom_extents", {
        "viewport_name": "Perspective"
    })
    
    print("\n" + "=" * 60)
    print("Castle Artwork Complete!")
    print("=" * 60)
    print(f"\nStatistics:")
    print(f"   - Cubes created: {created_count}")
    print(f"   - Materials: {len(materials)}")
    print(f"   - Layers: {len(layers)}")
    print(f"\nOutput files:")
    print(f"   - Render: {render_file}")
    print(f"   - Screenshot: {screenshot_file}")
    print(f"   - Top view: {top_file}")
    print(f"   - Front view: {front_file}")
    print("\nEnjoy your castle artwork!")


if __name__ == "__main__":
    try:
        create_castle()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
