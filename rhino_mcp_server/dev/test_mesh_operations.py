"""Test the new mesh operations: import_mesh, export_mesh, mesh_from_brep."""
import sys
import os
sys.path.insert(0, "src")

from rhinomcp.server import RhinoConnection

def test_mesh_operations():
    rhino = RhinoConnection("127.0.0.1", 1999)
    rhino.connect()

    print("=" * 80)
    print("Testing New Mesh Operations")
    print("=" * 80)

    try:
        # Test 1: Create a simple object to convert to mesh
        print("\n1. Creating a box to test mesh conversion...")
        result = rhino.send_command("create_object", {
            "type": "BOX",
            "params": {"width": 10, "length": 10, "height": 10}
        })
        box_id = result.get("id")
        print(f"Created box with ID: {box_id}")

        # Test 2: Convert Brep to mesh
        print("\n2. Converting Brep to mesh...")
        mesh_result = rhino.send_command("mesh_from_brep", {
            "object_ids": [box_id],
            "density": "normal",
            "quality": "normal"
        })
        print(f"Mesh conversion result: {mesh_result}")

        # Test 3: Export mesh (if we have mesh objects)
        export_path = os.path.join(os.getcwd(), "test_export.obj")
        if mesh_result.get("mesh_object_ids"):
            mesh_id = mesh_result["mesh_object_ids"][0]
            print(f"\n3. Exporting mesh to {export_path}...")
            export_result = rhino.send_command("export_mesh", {
                "file_path": export_path,
                "format": "OBJ",
                "object_ids": [mesh_id]
            })
            print(f"Export result: {export_result}")
        else:
            print(f"\n3. No mesh objects to export (mesh conversion returned {mesh_result.get('mesh_object_count', 0)} objects)")
            # Test export with the original box instead
            print(f"Testing export with original box object...")
            export_result = rhino.send_command("export_mesh", {
                "file_path": export_path,
                "format": "OBJ",
                "object_ids": [box_id]
            })
            print(f"Export result: {export_result}")

        # Test 4: Import mesh (if export was successful)
        if os.path.exists(export_path):
            print(f"\n4. Importing mesh from {export_path}...")
            import_result = rhino.send_command("import_mesh", {
                "file_path": export_path,
                "format": "OBJ",
                "import_mode": "merge"
            })
            print(f"Import result: {import_result}")
        else:
            print(f"\n4. Export file {export_path} does not exist, skipping import test")

        print("\n" + "=" * 80)
        print("Mesh Operations Test Complete!")
        print("=" * 80)

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        rhino.disconnect()

if __name__ == "__main__":
    test_mesh_operations()