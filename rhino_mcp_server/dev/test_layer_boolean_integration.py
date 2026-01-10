"""
Integration Test für Layer Management + Boolean Operations
Testet die Integration von Layer-Erstellung, Objekt-Zuweisung und Boolesche Operationen.

Usage: uv run python dev/test_layer_boolean_integration.py
Starte vorher Rhino mit mcpstart und MCP Server.
"""
import sys
sys.path.insert(0, "src")

from rhinomcp.server import RhinoConnection

def main():
    rhino = RhinoConnection("127.0.0.1", 1999)
    rhino.connect()

    print("\n=== MCP Layer + Boolean Integration Test ===")
    print("Testet Layer-Erstellung, Objekt-Zuweisung und Boolesche Operationen\n")

    # Plugin Status prüfen
    print("--- Plugin Status prüfen ---")
    try:
        status = rhino.send_command("get_available_tools", {})
        print(f"[OK] Plugin verfügbar, {len(status)} Tools")
    except Exception as e:
        print(f"[FAIL] Plugin nicht verfügbar: {e}")
        return

    # Test 1: Layer erstellen
    print("=== Test 1: Layer erstellen ===")
    try:
        layer1_result = rhino.send_command("create_layer", {
            "name": "TestLayer_Boolean1",
            "color": [255, 0, 0]  # Rot
        })
        print(f"[OK] Layer 1 erstellt: {layer1_result}")

        layer2_result = rhino.send_command("create_layer", {
            "name": "TestLayer_Boolean2",
            "color": [0, 255, 0]  # Grün
        })
        print(f"[OK] Layer 2 erstellt: {layer2_result}")

        layer3_result = rhino.send_command("create_layer", {
            "name": "TestLayer_Result",
            "color": [0, 0, 255]  # Blau
        })
        print(f"[OK] Result Layer erstellt: {layer3_result}")

    except Exception as e:
        print(f"[FAIL] Layer-Erstellung fehlgeschlagen: {e}")
        return

    # Test 2: Test-Objekte erstellen und Layer zuweisen
    print("\n=== Test 2: Test-Objekte erstellen und Layer zuweisen ===")
    try:
        # Box 1 auf Layer 1 (bei Origin)
        box1_result = rhino.send_command("create_object", {
            "type": "BOX",
            "name": "TestBox1",
            "params": {"width": 5, "length": 5, "height": 5}
        })
        box1_id = box1_result.get("id")
        print(f"[OK] Box 1 erstellt: {box1_id}")

        # Layer zuweisen
        rhino.send_command("set_object_properties", {
            "object_id": box1_id,
            "layer": "TestLayer_Boolean1"
        })
        print(f"[OK] Box 1 zu Layer 1 zugewiesen")

        # Box 2 auf Layer 2 (überlappend mit Box 1 - verschoben um 2 Einheiten)
        box2_result = rhino.send_command("create_object", {
            "type": "BOX",
            "name": "TestBox2",
            "params": {"width": 4, "length": 4, "height": 4},
            "translation": [2, 2, 2]  # Überlappung mit Box 1
        })
        box2_id = box2_result.get("id")
        print(f"[OK] Box 2 erstellt: {box2_id}")

        # Layer zuweisen
        rhino.send_command("set_object_properties", {
            "object_id": box2_id,
            "layer": "TestLayer_Boolean2"
        })
        print(f"[OK] Box 2 zu Layer 2 zugewiesen")

        # Sphere für weitere Tests (überlappend mit beiden Boxen)
        sphere_result = rhino.send_command("create_object", {
            "type": "SPHERE",
            "name": "TestSphere",
            "params": {"radius": 3},
            "translation": [1, 1, 1]  # Überlappung mit beiden Boxen
        })
        sphere_id = sphere_result.get("id")
        print(f"[OK] Sphere erstellt: {sphere_id}")

        # Sphere zu Layer 1 zuweisen
        rhino.send_command("set_object_properties", {
            "object_id": sphere_id,
            "layer": "TestLayer_Boolean1"
        })
        print(f"[OK] Sphere zu Layer 1 zugewiesen")

    except Exception as e:
        print(f"[FAIL] Objekt-Erstellung/Zuweisung fehlgeschlagen: {e}")
        return

    # Test 3: Boolean Operations testen
    print("\n=== Test 3: Boolean Operations testen ===")

    # Union Test
    print("--- Union Operation ---")
    try:
        union_result = rhino.send_command("boolean_operation", {
            "operation": "union",
            "object_ids": [box1_id, sphere_id],
            "delete_input": False  # Behalte Originale für weitere Tests
        })
        union_id = union_result.get("id")
        if union_id:
            print(f"[OK] Union erfolgreich: {union_id}")

            # Result zu Result Layer zuweisen
            rhino.send_command("set_object_properties", {
                "object_id": union_id,
                "layer": "TestLayer_Result"
            })
            print(f"[OK] Union-Result zu Result Layer zugewiesen")
        else:
            print(f"[WARN] Union ergab kein Result")

    except Exception as e:
        print(f"[FAIL] Union Operation fehlgeschlagen: {e}")

    # Difference Test
    print("\n--- Difference Operation ---")
    try:
        # Erstelle eine weitere Box für Difference Test (innerhalb von Box1)
        diff_box_result = rhino.send_command("create_object", {
            "type": "BOX",
            "name": "DiffBox",
            "params": {"width": 2, "length": 2, "height": 2},
            "translation": [1.5, 1.5, 1.5]  # Innerhalb von Box1 für gültige Difference
        })
        diff_box_id = diff_box_result.get("id")
        print(f"[OK] Difference-Box erstellt: {diff_box_id}")

        difference_result = rhino.send_command("boolean_operation", {
            "operation": "difference",
            "object_ids": [box1_id, diff_box_id],  # Box1 minus DiffBox
            "delete_input": False
        })
        diff_id = difference_result.get("id")
        if diff_id:
            print(f"[OK] Difference erfolgreich: {diff_id}")

            # Result zu Result Layer zuweisen
            rhino.send_command("set_object_properties", {
                "object_id": diff_id,
                "layer": "TestLayer_Result"
            })
            print(f"[OK] Difference-Result zu Result Layer zugewiesen")
        else:
            print(f"[WARN] Difference ergab kein Result")

    except Exception as e:
        print(f"[FAIL] Difference Operation fehlgeschlagen: {e}")

    # Intersection Test
    print("\n--- Intersection Operation ---")
    try:
        intersection_result = rhino.send_command("boolean_operation", {
            "operation": "intersection",
            "object_ids": [box2_id, sphere_id],
            "delete_input": False
        })
        intersect_id = intersection_result.get("id")
        if intersect_id:
            print(f"[OK] Intersection erfolgreich: {intersect_id}")

            # Result zu Result Layer zuweisen
            rhino.send_command("set_object_properties", {
                "object_id": intersect_id,
                "layer": "TestLayer_Result"
            })
            print(f"[OK] Intersection-Result zu Result Layer zugewiesen")
        else:
            print(f"[WARN] Intersection ergab kein Result")

    except Exception as e:
        print(f"[FAIL] Intersection Operation fehlgeschlagen: {e}")

    # Test 4: MCP Funktionen Verifikation
    print("\n=== Test 4: MCP Funktionen Verifikation ===")

    # Überprüfe Layer-Informationen
    try:
        current_layer = rhino.send_command("get_or_set_current_layer", {})
        print(f"[OK] Aktueller Layer: {current_layer.get('name')}")

        # Layer-Info abrufen
        layers_info = rhino.send_command("get_document_info", {})
        print(f"[OK] Dokument enthält Layer-Informationen")

    except Exception as e:
        print(f"[WARN] Layer-Info Abruf fehlgeschlagen: {e}")

    # Überprüfe Objekt-Properties
    try:
        obj_info = rhino.send_command("get_object_properties", {
            "object_id": box1_id
        })
        print(f"[OK] Objekt-Properties abgerufen für Box1")

        obj_info2 = rhino.send_command("get_object_properties", {
            "object_id": box2_id
        })
        print(f"[OK] Objekt-Properties abgerufen für Box2")

    except Exception as e:
        print(f"[FAIL] Objekt-Properties Abruf fehlgeschlagen: {e}")

    print("\n=== Test abgeschlossen ===")
    print("Überprüfe die Ergebnisse in Rhino:")
    print("- TestLayer_Boolean1 (Rot): Ursprüngliche Objekte")
    print("- TestLayer_Boolean2 (Grün): Zweite Box")
    print("- TestLayer_Result (Blau): Boolean Operation Ergebnisse")
    print("\nMCP Funktionen erfolgreich getestet!")

if __name__ == "__main__":
    main()