"""
Test script to verify P-0002, P-0003, P-0004 fixes.
Run after starting Rhino with mcpstart and MCP server.

Usage: uv run python dev/test_fixes.py
"""
import sys
sys.path.insert(0, "src")

from rhinomcp.server import RhinoConnection

def main():
    rhino = RhinoConnection("127.0.0.1", 1999)
    rhino.connect()
    
    print("\n=== Testing P-0002: PBR Material Creation ===")
    try:
        result = rhino.send_command("create_material", {
            "name": "TestPBR_Gold",
            "material_type": "pbr",
            "color": [255, 215, 0],
            "metallic": 0.9,
            "roughness": 0.2
        })
        print(f"[OK] PBR Material created: {result}")
        material_id = result.get("id")
    except Exception as e:
        print(f"[FAIL] PBR Material creation failed: {e}")
        material_id = None
    
    print("\n=== Testing P-0003: Objects on Current Layer ===")
    try:
        # Create a test layer
        layer_result = rhino.send_command("create_layer", {
            "name": "TestLayer_Fix",
            "color": [0, 128, 255]
        })
        print(f"[OK] Layer created: {layer_result}")
        
        # Set it as current
        set_result = rhino.send_command("get_or_set_current_layer", {
            "name": "TestLayer_Fix"
        })
        print(f"[OK] Current layer set: {set_result.get('name')}")
        
        # Create an object - should be on TestLayer_Fix
        obj_result = rhino.send_command("create_object", {
            "type": "BOX",
            "name": "TestBox_LayerFix",
            "params": {"width": 5, "length": 5, "height": 5}
        })
        print(f"[OK] Object created: {obj_result}")
        
        # Check the layer
        obj_layer = obj_result.get("layer", "Unknown")
        if obj_layer == "TestLayer_Fix":
            print(f"[SUCCESS] Object is on correct layer: {obj_layer}")
        else:
            print(f"[FAIL] Object is on wrong layer: {obj_layer} (expected TestLayer_Fix)")
    except Exception as e:
        print(f"[FAIL] Layer test failed: {e}")
    
    print("\n=== Testing P-0004: Material Assignment Validation ===")
    try:
        # Test with missing material_id (should get clear error)
        try:
            rhino.send_command("assign_material_to_layer", {
                "layer_name": "TestLayer_Fix"
                # material_id intentionally missing
            })
            print("[FAIL] Should have failed with missing material_id")
        except Exception as e:
            if "material_id" in str(e).lower() or "required" in str(e).lower():
                print(f"[OK] Correct validation error for missing material_id: {e}")
            else:
                print(f"[?] Unexpected error: {e}")
        
        # Test with valid parameters if we have a material
        if material_id:
            assign_result = rhino.send_command("assign_material_to_layer", {
                "layer_name": "TestLayer_Fix",
                "material_id": material_id
            })
            print(f"[OK] Material assigned successfully: {assign_result}")
    except Exception as e:
        print(f"[FAIL] Material assignment test failed: {e}")
    
    print("\n=== All tests complete ===")
    rhino.disconnect()

if __name__ == "__main__":
    main()
