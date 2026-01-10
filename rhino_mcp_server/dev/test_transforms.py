#!/usr/bin/env python
"""
Live test for transform operations (US-B02).

Prerequisites:
1. Rhino must be running with mcpstart executed
2. Run with: uv run python dev/test_transforms.py

This script tests:
- copy_object: Copy with translation
- mirror_object: Mirror across YZ plane  
- array_linear: Linear array along X axis
- array_polar: Polar array around Z axis
"""

import socket
import json
import time


def send_command(cmd_type: str, params: dict) -> dict:
    """Send a command to the Rhino MCP plugin."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 1999))
    sock.settimeout(30)
    
    command = {"type": cmd_type, "params": params}
    sock.send(json.dumps(command).encode())
    
    response = sock.recv(65536).decode()
    sock.close()
    
    return json.loads(response)


def test_copy_object():
    """Test copy_object with translation."""
    print("\n=== Test: copy_object ===")
    
    # Create a box to copy
    result = send_command("create_object", {
        "type": "BOX",
        "name": "OriginalBox",
        "params": {"width": 5, "length": 5, "height": 5},
        "translation": [0, 0, 2.5]
    })
    print(f"Created box: {result}")
    
    if result.get("status") != "success":
        print("FAIL: Could not create box")
        return False
    
    obj_id = result["result"]["id"]
    
    # Copy with translation
    result = send_command("copy_object", {
        "object_id": obj_id,
        "translation": [10, 0, 0],
        "count": 3
    })
    print(f"Copy result: {result}")
    
    if result.get("status") != "success":
        print("FAIL: copy_object failed")
        return False
    
    copy_ids = result["result"]["copy_ids"]
    print(f"Created {len(copy_ids)} copies: {copy_ids}")
    
    print("PASS: copy_object")
    return True


def test_mirror_object():
    """Test mirror_object across YZ plane."""
    print("\n=== Test: mirror_object ===")
    
    # Create a sphere to mirror
    result = send_command("create_object", {
        "type": "SPHERE",
        "name": "OriginalSphere",
        "params": {"radius": 3},
        "translation": [15, 0, 5]
    })
    print(f"Created sphere: {result}")
    
    if result.get("status") != "success":
        print("FAIL: Could not create sphere")
        return False
    
    obj_id = result["result"]["id"]
    
    # Mirror across YZ plane at X=10
    result = send_command("mirror_object", {
        "object_id": obj_id,
        "plane_origin": [10, 0, 0],
        "plane_normal": [1, 0, 0],
        "delete_input": False
    })
    print(f"Mirror result: {result}")
    
    if result.get("status") != "success":
        print("FAIL: mirror_object failed")
        return False
    
    mirror_id = result["result"]["mirror_id"]
    print(f"Mirrored object ID: {mirror_id}")
    
    print("PASS: mirror_object")
    return True


def test_array_linear():
    """Test array_linear along X axis."""
    print("\n=== Test: array_linear ===")
    
    # Create a cylinder to array
    result = send_command("create_object", {
        "type": "CYLINDER",
        "name": "ArrayCylinder",
        "params": {"radius": 2, "height": 8, "cap": True},
        "translation": [0, 20, 4]
    })
    print(f"Created cylinder: {result}")
    
    if result.get("status") != "success":
        print("FAIL: Could not create cylinder")
        return False
    
    obj_id = result["result"]["id"]
    
    # Create linear array
    result = send_command("array_linear", {
        "object_id": obj_id,
        "direction": [1, 0, 0],
        "count": 5,
        "spacing": 8.0
    })
    print(f"Array result: {result}")
    
    if result.get("status") != "success":
        print("FAIL: array_linear failed")
        return False
    
    array_ids = result["result"]["array_ids"]
    print(f"Created {len(array_ids)} array copies")
    
    print("PASS: array_linear")
    return True


def test_array_polar():
    """Test array_polar around Z axis."""
    print("\n=== Test: array_polar ===")
    
    # Create a box to array
    result = send_command("create_object", {
        "type": "BOX",
        "name": "PolarBox",
        "params": {"width": 3, "length": 3, "height": 3},
        "translation": [50, 0, 1.5]
    })
    print(f"Created box: {result}")
    
    if result.get("status") != "success":
        print("FAIL: Could not create box")
        return False
    
    obj_id = result["result"]["id"]
    
    # Create polar array (6 objects in full circle)
    result = send_command("array_polar", {
        "object_id": obj_id,
        "center": [50, 0, 0],
        "axis": [0, 0, 1],
        "count": 6,
        "angle": 360.0
    })
    print(f"Polar array result: {result}")
    
    if result.get("status") != "success":
        print("FAIL: array_polar failed")
        return False
    
    array_ids = result["result"]["array_ids"]
    print(f"Created {len(array_ids)} polar array copies")
    
    print("PASS: array_polar")
    return True


def main():
    """Run all transform tests."""
    print("=" * 50)
    print("RhinoMCP Transform Operations Live Test")
    print("=" * 50)
    
    try:
        # Test connection first
        result = send_command("ping", {})
        print(f"Ping: {result}")
        if result.get("status") != "success":
            print("ERROR: Cannot connect to Rhino. Run 'mcpstart' in Rhino.")
            return
    except Exception as e:
        print(f"ERROR: Cannot connect to Rhino: {e}")
        print("Make sure Rhino is running and 'mcpstart' has been executed.")
        return
    
    results = []
    results.append(("copy_object", test_copy_object()))
    time.sleep(0.5)
    results.append(("mirror_object", test_mirror_object()))
    time.sleep(0.5)
    results.append(("array_linear", test_array_linear()))
    time.sleep(0.5)
    results.append(("array_polar", test_array_polar()))
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll transform tests passed!")
    else:
        print("\nSome tests failed. Check output above.")


if __name__ == "__main__":
    main()
