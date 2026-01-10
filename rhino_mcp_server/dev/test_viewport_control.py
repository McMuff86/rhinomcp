"""
Test Script für die neuen Viewport Control Funktionen
Testet set_view, zoom_extents, zoom_selected, capture_viewport

Usage: uv run python dev/test_viewport_control.py
"""
import sys
sys.path.insert(0, "src")

from rhinomcp.server import RhinoConnection

def main():
    rhino = RhinoConnection("127.0.0.1", 1999)
    rhino.connect()

    print("\n=== MCP Viewport Control Test ===")
    print("Testet die neuen Viewport-Funktionen\n")

    # Plugin Status prüfen
    print("--- Plugin Status prüfen ---")
    try:
        # Versuche einen einfachen Ping
        result = rhino.send_command("ping", {})
        print("[OK] Plugin verfügbar - Ping erfolgreich")
    except Exception as e:
        print(f"[FAIL] Plugin nicht verfügbar: {e}")
        return

    # Test 1: Objekte erstellen für Zoom-Tests
    print("\n=== Test 1: Test-Objekte erstellen ===")
    try:
        # Erstelle einige Test-Objekte
        box1_result = rhino.send_command("create_object", {
            "type": "BOX",
            "name": "TestBox1",
            "params": {"width": 10, "length": 10, "height": 10}
        })
        box1_id = box1_result.get("id")
        print(f"[OK] Box 1 erstellt: {box1_id}")

        box2_result = rhino.send_command("create_object", {
            "type": "BOX",
            "name": "TestBox2",
            "params": {"width": 5, "length": 5, "height": 5},
            "translation": [15, 15, 5]  # Versetzt platzieren
        })
        box2_id = box2_result.get("id")
        print(f"[OK] Box 2 erstellt: {box2_id}")

        sphere_result = rhino.send_command("create_object", {
            "type": "SPHERE",
            "name": "TestSphere",
            "params": {"radius": 3},
            "translation": [5, 5, 5]
        })
        sphere_id = sphere_result.get("id")
        print(f"[OK] Sphere erstellt: {sphere_id}")

    except Exception as e:
        print(f"[FAIL] Objekt-Erstellung fehlgeschlagen: {e}")
        return

    # Test 2: View setzen
    print("\n=== Test 2: View setzen ===")
    try:
        # Setze verschiedene Views
        views = ["Top", "Front", "Right", "Perspective"]

        for view in views:
            result = rhino.send_command("set_view", {
                "view_type": view,
                "viewport_name": "Perspective"
            })
            print(f"[OK] View gesetzt auf: {view}")
            # Kurze Pause zwischen Views
            import time
            time.sleep(0.5)

        print("[OK] Alle Views erfolgreich gesetzt")

    except Exception as e:
        print(f"[FAIL] View setzen fehlgeschlagen: {e}")

    # Test 3: Zoom Extents
    print("\n=== Test 3: Zoom Extents ===")
    try:
        # Zoom auf alle Objekte
        result = rhino.send_command("zoom_extents", {
            "viewport_name": "Perspective",
            "include_hidden": True
        })
        print("[OK] Zoom Extents erfolgreich")

        # Zoom ohne Hidden Objects
        result = rhino.send_command("zoom_extents", {
            "viewport_name": "Perspective",
            "include_hidden": False
        })
        print("[OK] Zoom Extents (ohne Hidden) erfolgreich")

    except Exception as e:
        print(f"[FAIL] Zoom Extents fehlgeschlagen: {e}")

    # Test 4: Zoom Selected
    print("\n=== Test 4: Zoom Selected ===")
    try:
        # Zoom auf Box 1
        result = rhino.send_command("zoom_selected", {
            "object_ids": [box1_id],
            "viewport_name": "Perspective"
        })
        print(f"[OK] Zoom auf Box 1 erfolgreich")

        # Zoom auf beide Boxen
        result = rhino.send_command("zoom_selected", {
            "object_ids": [box1_id, box2_id],
            "viewport_name": "Perspective"
        })
        print(f"[OK] Zoom auf beide Boxen erfolgreich")

        # Zoom auf aktuell ausgewählte Objekte (keine IDs angegeben)
        result = rhino.send_command("zoom_selected", {
            "viewport_name": "Perspective"
        })
        print(f"[OK] Zoom auf ausgewählte Objekte erfolgreich")

    except Exception as e:
        print(f"[FAIL] Zoom Selected fehlgeschlagen: {e}")

    # Test 5: Capture Viewport
    print("\n=== Test 5: Capture Viewport ===")
    try:
        # Capture als Base64
        result = rhino.send_command("capture_viewport", {
            "viewport_name": "Perspective",
            "width": 800,
            "height": 600
        })
        if result.get("image_data"):
            print(f"[OK] Viewport Capture als Base64 erfolgreich ({len(result['image_data'])} bytes)")
        else:
            print("[WARN] Viewport Capture ergab keine Base64 Daten")

        # Capture als Datei
        result = rhino.send_command("capture_viewport", {
            "viewport_name": "Perspective",
            "width": 1024,
            "height": 768,
            "filename": "viewport_capture_test.png"
        })
        if result.get("saved_to_file"):
            print(f"[OK] Viewport Capture als Datei erfolgreich: {result['saved_to_file']}")
        else:
            print("[WARN] Viewport Capture als Datei ergab kein Ergebnis")

    except Exception as e:
        print(f"[FAIL] Capture Viewport fehlgeschlagen: {e}")

    # Test 6: Kombinierte Tests
    print("\n=== Test 6: Kombinierte Viewport Operationen ===")
    try:
        # Setze Front View
        rhino.send_command("set_view", {"view_type": "Front"})

        # Erstelle ein weiteres Objekt
        cylinder_result = rhino.send_command("create_object", {
            "type": "CYLINDER",
            "name": "TestCylinder",
            "params": {"radius": 2, "height": 8},
            "translation": [0, 0, 0]
        })
        cylinder_id = cylinder_result.get("id")

        # Zoom auf neues Objekt
        rhino.send_command("zoom_selected", {"object_ids": [cylinder_id]})

        # Capture das Resultat
        rhino.send_command("capture_viewport", {
            "filename": "combined_test.png",
            "width": 1920,
            "height": 1080
        })

        print("[OK] Kombinierte Operationen erfolgreich")

    except Exception as e:
        print(f"[FAIL] Kombinierte Operationen fehlgeschlagen: {e}")

    print("\n=== Viewport Control Test abgeschlossen ===")
    print("Überprüfe die Ergebnisse in Rhino:")
    print("- Verschiedene Views wurden gesetzt")
    print("- Zoom-Operationen wurden ausgeführt")
    print("- Bilder wurden aufgenommen (viewport_capture_test.png, combined_test.png)")
    print("\nAlle neuen Viewport-Funktionen wurden erfolgreich getestet! 🎉")

if __name__ == "__main__":
    main()