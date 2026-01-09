"""Test script: Clear viewport and create a gold PBR cube."""
from rhinomcp.server import get_rhino_connection
import json


def main():
    rhino = get_rhino_connection()

    # 1. Get all objects and delete them
    print("-- Clearing viewport --")
    doc_info = rhino.send_command("get_document_info")
    obj_count = doc_info.get("object_count", 0)
    print(f"Found {obj_count} objects")

    for obj in doc_info.get("objects", []):
        obj_id = obj.get("id")
        if obj_id:
            try:
                rhino.send_command("delete_object", {"id": obj_id})
                print(f"  Deleted: {obj.get('name', obj_id)}")
            except Exception as e:
                print(f"  Could not delete {obj.get('name', obj_id)}: {e}")

    print("Viewport cleared!\n")

    # 2. Create Gold layer (may already exist)
    print("-- Creating Gold layer --")
    try:
        layer_result = rhino.send_command(
            "create_layer", {"name": "GoldPBR", "color": [255, 215, 0]}
        )
        print(f"Layer: {json.dumps(layer_result)}")
    except Exception as e:
        print(f"Layer may already exist: {e}")

    # 3. Create PBR Gold material
    print("\n-- Creating PBR Gold material --")
    try:
        material_result = rhino.send_command(
            "create_material",
            {
                "name": "GoldMaterial",
                "color": [255, 215, 0],
                "material_type": "pbr",
                "metallic": 1.0,
                "roughness": 0.2,
            },
        )
        print(f"Material: {json.dumps(material_result)}")
    except Exception as e:
        print(f"Material creation note: {e}")

    # 4. Set current layer
    print("\n-- Setting current layer --")
    try:
        rhino.send_command("get_or_set_current_layer", {"layer_name": "GoldPBR"})
        print("Current layer set to GoldPBR")
    except Exception as e:
        print(f"Layer switch note: {e}")

    # 5. Create cube with gold color
    print("\n-- Creating Gold Cube --")
    cube_result = rhino.send_command(
        "create_object",
        {
            "type": "BOX",
            "name": "Gold_Cube",
            "color": [255, 215, 0],
            "params": {"width": 10, "length": 10, "height": 10},
        },
    )
    print(f"Cube: {json.dumps(cube_result)}")

    print("\n[OK] Gold Cube created successfully!")
    print("Switch to Rendered viewport in Rhino to see the result.")


if __name__ == "__main__":
    main()
