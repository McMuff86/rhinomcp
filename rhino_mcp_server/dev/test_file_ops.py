"""Live test for US-C01 File Operations."""
import sys
sys.path.insert(0, "src")

from rhinomcp.server import RhinoConnection
import json

def test_file_operations():
    rhino = RhinoConnection("127.0.0.1", 1999)
    rhino.connect()
    
    print("=" * 50)
    print("US-C01: File Operations Live Test")
    print("=" * 50)
    
    # Use Windows backslash paths
    test_path = "C:\\temp\\rhinomcp_test.3dm"
    step_path = "C:\\temp\\rhinomcp_test.step"
    obj_path = "C:\\temp\\rhinomcp_test.obj"
    
    # Create a box first so we have something to export
    print("\n0. Creating test geometry...")
    try:
        result = rhino.send_command("create_object", {
            "type": "BOX",
            "params": {"width": 10, "length": 10, "height": 10}
        })
        print(f"   OK create_object: {result.get('id', 'created')}")
    except Exception as e:
        print(f"   FAIL create_object: {e}")
    
    # Test 1: Save file to temp location
    print("\n1. Testing save_file...")
    try:
        result = rhino.send_command("save_file", {
            "file_path": test_path
        })
        print(f"   OK save_file: {result}")
    except Exception as e:
        print(f"   FAIL save_file: {e}")
    
    # Test 2: Export to STEP
    print("\n2. Testing export_file (STEP)...")
    try:
        result = rhino.send_command("export_file", {
            "file_path": step_path,
            "format": "STEP"
        })
        print(f"   OK export_file STEP: {result}")
    except Exception as e:
        print(f"   FAIL export_file STEP: {e}")
    
    # Test 3: Export to OBJ
    print("\n3. Testing export_file (OBJ)...")
    try:
        result = rhino.send_command("export_file", {
            "file_path": obj_path,
            "format": "OBJ"
        })
        print(f"   OK export_file OBJ: {result}")
    except Exception as e:
        print(f"   FAIL export_file OBJ: {e}")
    
    # Test 4: Open the saved file
    print("\n4. Testing open_file...")
    try:
        result = rhino.send_command("open_file", {
            "file_path": test_path
        })
        print(f"   OK open_file: {result}")
    except Exception as e:
        print(f"   FAIL open_file: {e}")
    
    print("\n" + "=" * 50)
    print("File Operations Test Complete!")
    print("=" * 50)
    
    rhino.disconnect()

if __name__ == "__main__":
    test_file_operations()
