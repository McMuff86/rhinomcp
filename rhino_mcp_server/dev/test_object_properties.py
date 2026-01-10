"""
Live test for get_object_properties and set_object_properties tools.
Run with: uv run python dev/test_object_properties.py
"""
import sys
sys.path.insert(0, "src")

from rhinomcp.server import RhinoConnection

def main():
    print("=" * 60)
    print("Testing Object Properties Tools")
    print("=" * 60)
    
    rhino = RhinoConnection("127.0.0.1", 1999)
    rhino.connect()
    
    # Step 1: Create a test box
    print("\n1. Creating test box...")
    result = rhino.send_command("create_object", {
        "type": "BOX",
        "params": {
            "width": 10,
            "length": 20,
            "height": 5
        }
    })
    box_id = result.get("id")
    print(f"   Created box: {box_id}")
    
    # Step 2: Get object properties
    print("\n2. Getting object properties...")
    props = rhino.send_command("get_object_properties", {
        "object_id": box_id
    })
    print(f"   Bounding Box: {props.get('bounding_box')}")
    print(f"   Volume: {props.get('volume')}")
    print(f"   Area: {props.get('area')}")
    print(f"   Centroid: {props.get('centroid')}")
    print(f"   Is Solid: {props.get('is_solid')}")
    
    # Step 3: Set object properties
    print("\n3. Setting object properties (name, color)...")
    set_result = rhino.send_command("set_object_properties", {
        "object_id": box_id,
        "name": "TestBox_Modified",
        "color": [255, 100, 50]  # Orange
    })
    print(f"   Modified: {set_result.get('modified_count')} object(s)")
    
    # Step 4: Create a sphere and test batch
    print("\n4. Creating sphere for batch test...")
    sphere_result = rhino.send_command("create_object", {
        "type": "SPHERE",
        "params": {"radius": 3},
        "translation": [15, 0, 0]
    })
    sphere_id = sphere_result.get("id")
    print(f"   Created sphere: {sphere_id}")
    
    # Step 5: Batch get properties
    print("\n5. Batch getting properties...")
    batch_props = rhino.send_command("get_object_properties", {
        "object_ids": [box_id, sphere_id]
    })
    print(f"   Got properties for {batch_props.get('count')} objects")
    for obj in batch_props.get("objects", []):
        print(f"   - {obj.get('type')}: volume={obj.get('volume')}, area={obj.get('area')}")
    
    # Step 6: Batch set properties
    print("\n6. Batch setting color to red...")
    batch_set = rhino.send_command("set_object_properties", {
        "object_ids": [box_id, sphere_id],
        "color": [255, 0, 0]
    })
    print(f"   Modified: {batch_set.get('modified_count')} object(s)")
    
    # Step 7: Test with a curve (no volume)
    print("\n7. Creating circle to test curve properties...")
    circle_result = rhino.send_command("create_object", {
        "type": "CIRCLE",
        "params": {"center": [0, 0, 0], "radius": 5},
        "translation": [0, 15, 0]
    })
    circle_id = circle_result.get("id")
    
    curve_props = rhino.send_command("get_object_properties", {
        "object_id": circle_id
    })
    print(f"   Curve length: {curve_props.get('curve_length')}")
    print(f"   Is closed: {curve_props.get('is_closed')}")
    print(f"   Centroid: {curve_props.get('centroid')}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
    
    rhino.disconnect()

if __name__ == "__main__":
    main()
