#!/usr/bin/env python3
"""
Einfacher MCP Test: Layer und Objekte verwalten
"""
import sys
import os
sys.path.insert(0, "rhino_mcp_server/src")

from rhinomcp.server import RhinoConnection

def main():
    print("MCP Layer & Object Test")
    print("=" * 40)

    # Verbinde mit Rhino
    rhino = RhinoConnection("127.0.0.1", 1999)
    rhino.connect()

    # Schritt 1: Alle vorhandenen Objekte löschen
    print("\n1. Lösche vorhandene Objekte...")

    # Hole Dokument-Info um Objekte zu finden
    doc_info = rhino.send_command("get_document_info", {})
    if doc_info and doc_info.get("objects"):
        for obj in doc_info["objects"]:
            obj_id = obj.get("id")
            if obj_id:
                print(f"   Lösche Objekt: {obj_id}")
                result = rhino.send_command("delete_object", {"id": obj_id})
                print(f"   Ergebnis: {result}")
    else:
        print("   Keine Objekte zum Löschen gefunden")

    # Schritt 2: Layer mit Farben erstellen
    print("\n2. Erstelle Layer mit verschiedenen Farben...")

    layers = [
        ("Geometry_Red", [255, 0, 0]),
        ("Geometry_Green", [0, 255, 0]),
        ("Geometry_Blue", [0, 0, 255]),
        ("Annotations_Yellow", [255, 255, 0]),
        ("Helpers_Purple", [128, 0, 128])
    ]

    for name, color in layers:
        print(f"   Erstelle Layer: {name} (Farbe: {color})")
        try:
            result = rhino.send_command("create_layer", {
                "name": name,
                "color": color
            })
            print(f"   Ergebnis: {result}")
        except Exception as e:
            print(f"   Layer möglicherweise bereits vorhanden oder Fehler: {e}")
            # Fortfahren trotz Fehler

    # Schritt 3: Objekte auf Layern erstellen
    print("\n3. Erstelle Objekte auf verschiedenen Layern...")

    objects = [
        # Rote Objekte
        ("Geometry_Red", "BOX", "RedBox", {"width": 5, "length": 5, "height": 5}, [0, 0, 0]),
        ("Geometry_Red", "SPHERE", "RedSphere", {"radius": 3}, [10, 0, 0]),

        # Grüne Objekte
        ("Geometry_Green", "CYLINDER", "GreenCylinder", {"radius": 2, "height": 8}, [0, 10, 0]),
        ("Geometry_Green", "CONE", "GreenCone", {"radius": 3, "height": 6}, [10, 10, 0]),

        # Blaue Objekte
        ("Geometry_Blue", "BOX", "BlueBox", {"width": 4, "length": 4, "height": 4}, [0, 20, 0]),
        ("Geometry_Blue", "SPHERE", "BlueSphere", {"radius": 2}, [10, 20, 0]),

        # Gelbe Objekte
        ("Annotations_Yellow", "POINT", "YellowPoint", {"x": 5, "y": 5, "z": 5}, [0, 0, 0]),

        # Lila Objekte
        ("Helpers_Purple", "LINE", "PurpleLine", {"start": [0, 0, 0], "end": [5, 5, 5]}, [0, 0, 0])
    ]

    for layer, obj_type, name, params, translation in objects:
        print(f"   Erstelle {obj_type}: {name} auf Layer {layer}")

        try:
            result = rhino.send_command("create_object", {
                "type": obj_type,
                "name": name,
                "layer": layer,
                "params": params,
                "translation": translation
            })
            print(f"   Ergebnis: {result}")

            # Zusätzliche Layer-Zuweisung
            if result and "id" in result:
                obj_id = result["id"]
                try:
                    layer_result = rhino.send_command("set_object_properties", {
                        "object_id": obj_id,
                        "layer": layer
                    })
                    print(f"   Layer zugewiesen: {layer_result}")
                except Exception as e:
                    print(f"   Layer-Zuweisung Fehler: {e}")
        except Exception as e:
            print(f"   Objekt-Erstellung Fehler: {e}")
            # Fortfahren mit nächsten Objekt

    # Schritt 4: Dokument-Info abrufen
    print("\n4. Dokument-Informationen abrufen...")
    doc_info = rhino.send_command("get_document_info", {})
    print(f"   Layer: {doc_info.get('layer_count', 0)}")
    print(f"   Objekte: {doc_info.get('object_count', 0)}")

    # Schritt 5: Viewport Operationen
    print("\n5. Viewport Operationen...")

    # Perspective View setzen
    result = rhino.send_command("set_view", {"view_type": "Perspective"})
    print(f"   Perspective View: {result}")

    # Zoom to Extents
    result = rhino.send_command("zoom_extents", {"include_hidden": True})
    print(f"   Zoom Extents: {result}")

    # Screenshot erstellen
    result = rhino.send_command("capture_viewport", {
        "width": 1024,
        "height": 768,
        "filename": "layer_demo.png"
    })
    print(f"   Screenshot: {result}")

    print("\n" + "=" * 40)
    print("Test abgeschlossen!")
    print("\nÜberprüfe in Rhino:")
    print("- 5 farbige Layer erstellt")
    print("- 9 Objekte auf verschiedenen Layern")
    print("- Screenshot: layer_demo.png")

if __name__ == "__main__":
    main()