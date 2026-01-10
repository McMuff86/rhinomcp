"""Live test for curve operations (offset, fillet, chamfer)."""

import sys
sys.path.insert(0, "src")

from rhinomcp.server import RhinoConnection
import json


def test_curve_operations():
    """Test all curve operations with live Rhino connection."""
    
    print("=" * 60)
    print("Testing Curve Operations")
    print("=" * 60)
    
    rhino = RhinoConnection("127.0.0.1", 1999)
    rhino.connect()
    
    try:
        # Clean up - delete all objects first
        print("\n1. Cleaning up document...")
        doc_info = rhino.send_command("get_document_info", {})
        for obj in doc_info.get("objects", []):
            rhino.send_command("delete_object", {"id": obj["id"]})
        print("   [OK] Document cleaned")
        
        # Create two intersecting lines for fillet/chamfer tests
        print("\n2. Creating test curves...")
        
        # Line 1: horizontal line along X axis
        line1 = rhino.send_command("create_object", {
            "type": "LINE",
            "params": {
                "start": [0, 0, 0],
                "end": [20, 0, 0]
            },
            "name": "TestLine1"
        })
        line1_id = line1["id"]
        print(f"   [OK] Created Line 1: {line1_id}")
        
        # Line 2: vertical line along Y axis (intersects at origin)
        line2 = rhino.send_command("create_object", {
            "type": "LINE",
            "params": {
                "start": [0, 0, 0],
                "end": [0, 20, 0]
            },
            "name": "TestLine2"
        })
        line2_id = line2["id"]
        print(f"   [OK] Created Line 2: {line2_id}")
        
        # Create a circle for offset test
        circle = rhino.send_command("create_object", {
            "type": "CIRCLE",
            "params": {
                "center": [30, 10, 0],
                "radius": 5
            },
            "name": "TestCircle"
        })
        circle_id = circle["id"]
        print(f"   [OK] Created Circle: {circle_id}")
        
        # Create a polyline for offset test
        polyline = rhino.send_command("create_object", {
            "type": "POLYLINE",
            "params": {
                "points": [[50, 0, 0], [60, 0, 0], [60, 10, 0], [50, 10, 0]]
            },
            "name": "TestPolyline"
        })
        polyline_id = polyline["id"]
        print(f"   [OK] Created Polyline: {polyline_id}")
        
        # Test 1: Offset Curve
        print("\n3. Testing offset_curve...")
        
        # Offset circle outward
        offset_result = rhino.send_command("offset_curve", {
            "curve_id": circle_id,
            "distance": 2.0,
            "plane_normal": [0, 0, 1],
            "corner_style": "sharp"
        })
        print(f"   [OK] Offset circle (outward): {offset_result.get('offset_ids', [])}")
        
        # Offset circle inward
        offset_result2 = rhino.send_command("offset_curve", {
            "curve_id": circle_id,
            "distance": -2.0,
            "plane_normal": [0, 0, 1],
            "corner_style": "sharp"
        })
        print(f"   [OK] Offset circle (inward): {offset_result2.get('offset_ids', [])}")
        
        # Offset polyline with round corners
        offset_result3 = rhino.send_command("offset_curve", {
            "curve_id": polyline_id,
            "distance": 1.5,
            "plane_normal": [0, 0, 1],
            "corner_style": "round"
        })
        print(f"   [OK] Offset polyline (round): {offset_result3.get('offset_ids', [])}")
        
        # Test 2: Fillet Curves
        print("\n4. Testing fillet_curves...")
        
        # Create new lines for fillet (since we need fresh ones)
        line3 = rhino.send_command("create_object", {
            "type": "LINE",
            "params": {"start": [-20, 0, 0], "end": [0, 0, 0]},
            "name": "FilletLine1"
        })
        line3_id = line3["id"]
        
        line4 = rhino.send_command("create_object", {
            "type": "LINE",
            "params": {"start": [0, 0, 0], "end": [0, -20, 0]},
            "name": "FilletLine2"
        })
        line4_id = line4["id"]
        
        fillet_result = rhino.send_command("fillet_curves", {
            "curve_id_1": line3_id,
            "curve_id_2": line4_id,
            "radius": 3.0,
            "join": False
        })
        print(f"   [OK] Fillet created (radius=3): {fillet_result.get('fillet_ids', [])}")
        
        # Test 3: Chamfer Curves
        print("\n5. Testing chamfer_curves...")
        
        # Create new lines for chamfer
        line5 = rhino.send_command("create_object", {
            "type": "LINE",
            "params": {"start": [-20, -30, 0], "end": [0, -30, 0]},
            "name": "ChamferLine1"
        })
        line5_id = line5["id"]
        
        line6 = rhino.send_command("create_object", {
            "type": "LINE",
            "params": {"start": [0, -30, 0], "end": [0, -50, 0]},
            "name": "ChamferLine2"
        })
        line6_id = line6["id"]
        
        chamfer_result = rhino.send_command("chamfer_curves", {
            "curve_id_1": line5_id,
            "curve_id_2": line6_id,
            "distance_1": 4.0,
            "distance_2": 4.0,
            "join": False
        })
        print(f"   [OK] Chamfer created (4x4): {chamfer_result.get('chamfer_ids', [])}")
        
        # Asymmetric chamfer
        line7 = rhino.send_command("create_object", {
            "type": "LINE",
            "params": {"start": [20, -30, 0], "end": [40, -30, 0]},
            "name": "ChamferLine3"
        })
        line7_id = line7["id"]
        
        line8 = rhino.send_command("create_object", {
            "type": "LINE",
            "params": {"start": [40, -30, 0], "end": [40, -50, 0]},
            "name": "ChamferLine4"
        })
        line8_id = line8["id"]
        
        chamfer_result2 = rhino.send_command("chamfer_curves", {
            "curve_id_1": line7_id,
            "curve_id_2": line8_id,
            "distance_1": 3.0,
            "distance_2": 6.0,
            "join": False
        })
        print(f"   [OK] Asymmetric chamfer (3x6): {chamfer_result2.get('chamfer_ids', [])}")
        
        # Summary
        print("\n" + "=" * 60)
        print("All curve operation tests completed successfully!")
        print("=" * 60)
        print("\nCheck Rhino viewport to see:")
        print("  - Original circle with offset curves (outward and inward)")
        print("  - Polyline with rounded offset")
        print("  - Two lines with fillet arc")
        print("  - Two pairs of lines with symmetric and asymmetric chamfers")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        rhino.disconnect()


if __name__ == "__main__":
    success = test_curve_operations()
    sys.exit(0 if success else 1)
