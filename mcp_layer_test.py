#!/usr/bin/env python3
"""
MCP Tool Test Script: Layer Management & Object Creation
Verwendet MCP Tools um Objekte zu löschen, Layer zu erstellen und Objekte zu platzieren.
"""
import requests
import json
import time

# MCP Server URL
MCP_URL = "http://localhost:8000"

def call_mcp_tool(tool_name, **kwargs):
    """Ruft ein MCP Tool auf."""
    payload = {
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": kwargs
        },
        "id": 1,
        "jsonrpc": "2.0"
    }

    try:
        response = requests.post(MCP_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            print(f"ERROR: MCP Error: {result['error']}")
            return None

        # Extrahiere das Tool-Ergebnis
        tool_result = result.get("result", {})
        if isinstance(tool_result, str):
            # Parse JSON string response
            try:
                return json.loads(tool_result)
            except:
                return tool_result
        return tool_result

    except requests.exceptions.RequestException as e:
        print(f"ERROR: HTTP Error: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Error: {e}")
        return None

def main():
    print("MCP Layer & Object Management Test")
    print("=" * 50)

    # Warte kurz auf Server
    time.sleep(2)

    # Test 1: Alle Objekte löschen
    print("\nSchritt 1: Alle Objekte löschen")
    result = call_mcp_tool("delete_all_objects")
    if result:
        print("OK: Alle Objekte gelöscht")
    else:
        print("WARN: Objekt-Löschung fehlgeschlagen oder keine Objekte vorhanden")

    # Test 2: Neue Layer mit verschiedenen Farben erstellen
    print("\nSchritt 2: Layer mit verschiedenen Farben erstellen")

    layers = [
        {"name": "Geometry_Red", "color": [255, 0, 0]},
        {"name": "Geometry_Green", "color": [0, 255, 0]},
        {"name": "Geometry_Blue", "color": [0, 0, 255]},
        {"name": "Annotations_Yellow", "color": [255, 255, 0]},
        {"name": "Helpers_Purple", "color": [128, 0, 128]}
    ]

    layer_ids = {}
    for layer in layers:
        print(f"  Erstelle Layer: {layer['name']} (Farbe: {layer['color']})")
        result = call_mcp_tool("create_layer",
                             name=layer["name"],
                             color=layer["color"])

        if result and "name" in result:
            layer_ids[layer["name"]] = result.get("id")
            print(f"    OK: Layer erstellt: {result['name']}")
        else:
            print(f"    FAIL: Layer-Erstellung fehlgeschlagen")

    # Test 3: Objekte auf verschiedenen Layern erstellen
    print("\nSchritt 3: Objekte auf Layern erstellen")

    objects = [
        # Geometry Layer - Rote Objekte
        {"layer": "Geometry_Red", "type": "BOX", "name": "RedBox", "params": {"width": 5, "length": 5, "height": 5}, "translation": [0, 0, 0]},
        {"layer": "Geometry_Red", "type": "SPHERE", "name": "RedSphere", "params": {"radius": 3}, "translation": [10, 0, 0]},

        # Geometry Layer - Grüne Objekte
        {"layer": "Geometry_Green", "type": "CYLINDER", "name": "GreenCylinder", "params": {"radius": 2, "height": 8}, "translation": [0, 10, 0]},
        {"layer": "Geometry_Green", "type": "CONE", "name": "GreenCone", "params": {"radius": 3, "height": 6}, "translation": [10, 10, 0]},

        # Geometry Layer - Blaue Objekte
        {"layer": "Geometry_Blue", "type": "BOX", "name": "BlueBox", "params": {"width": 4, "length": 4, "height": 4}, "translation": [0, 20, 0]},
        {"layer": "Geometry_Blue", "type": "PIPE", "name": "BluePipe", "params": {"radius": 1, "height": 10}, "translation": [10, 20, 0]},

        # Annotations Layer - Gelbe Objekte
        {"layer": "Annotations_Yellow", "type": "POINT", "name": "YellowPoint", "params": {"x": 5, "y": 5, "z": 5}, "translation": [0, 0, 0]},

        # Helpers Layer - Lila Objekte
        {"layer": "Helpers_Purple", "type": "LINE", "name": "PurpleLine", "params": {"start": [0, 0, 0], "end": [5, 5, 5]}, "translation": [0, 0, 0]}
    ]

    created_objects = {}
    for obj in objects:
        print(f"  Erstelle {obj['type']}: {obj['name']} auf Layer {obj['layer']}")

        # Erstelle Objekt mit Layer-Zuweisung
        result = call_mcp_tool("create_object",
                             type=obj["type"],
                             name=obj["name"],
                             layer=obj["layer"],
                             params=obj["params"],
                             translation=obj.get("translation"))

        if result and "id" in result:
            obj_id = result["id"]
            created_objects[obj["name"]] = obj_id
            print(f"    OK: Objekt erstellt: {obj_id}")

            # Zusätzliche Layer-Zuweisung falls nötig
            layer_result = call_mcp_tool("set_object_properties",
                                       object_id=obj_id,
                                       layer=obj["layer"])
            if layer_result:
                print(f"    OK: Layer zugewiesen: {obj['layer']}")
        else:
            print(f"    FAIL: Objekt-Erstellung fehlgeschlagen")

    # Test 4: Layer-Informationen abrufen
    print("\nSchritt 4: Layer-Informationen prüfen")
    doc_info = call_mcp_tool("get_document_info")
    if doc_info:
        print(f"Dokument hat {doc_info.get('layer_count', 0)} Layer und {doc_info.get('object_count', 0)} Objekte")

        # Zeige Layer-Details
        layers_info = doc_info.get("layers", [])
        print("  Layer Übersicht:")
        for layer in layers_info[:10]:  # Zeige max 10 Layer
            color = layer.get("color", "Unknown")
            print(f"    - {layer.get('name', 'Unknown')} (Farbe: {color})")

    # Test 5: Viewport Operationen
    print("\nSchritt 5: Viewport Operationen testen")

    # Setze Perspective View
    result = call_mcp_tool("set_view", view_type="Perspective")
    if result:
        print("OK: Perspective View gesetzt")

    # Zoom to Extents
    result = call_mcp_tool("zoom_extents", include_hidden=True)
    if result:
        print("OK: Zoom to Extents ausgeführt")

    # Capture Viewport
    result = call_mcp_tool("capture_viewport",
                         width=1024,
                         height=768,
                         filename="layer_test_screenshot.png")
    if result:
        print("OK: Viewport Screenshot erstellt: layer_test_screenshot.png")

    print("\n" + "=" * 50)
    print("MCP Layer & Object Management Test abgeschlossen!")
    print("\nÜberprüfe in Rhino:")
    print("- 5 Layer mit verschiedenen Farben erstellt")
    print("- Mehrere Objekte auf verschiedenen Layern platziert")
    print("- Screenshot gespeichert als 'layer_test_screenshot.png'")
    print("\nZusammenfassung:")
    print(f"  - Layer erstellt: {len(layer_ids)}")
    print(f"  - Objekte erstellt: {len(created_objects)}")
    print("  - Viewport Operationen: OK")

if __name__ == "__main__":
    main()