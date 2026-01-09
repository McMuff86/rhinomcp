# RhinoMCP Usage Guide

## 🚀 Schnellstart

### 1. Rhino Plugin starten
- **In Rhino Command Line eingeben:** `mcpstart`
- **Status prüfen:** `MCPStatus`
- **Stoppen:** `mcpstop`

### 2. MCP Server starten
```bash
# Aus dem rhino_mcp_server Verzeichnis
cd rhino_mcp_server
uv run rhinomcp
```

**ODER** direkt:
```bash
uv run rhinomcp
```

### 3. Verbindung testen
```bash
# Python Test
uv run python -c "
import sys
sys.path.insert(0, 'rhino_mcp_server/src')
from rhinomcp.tools.ping import ping
from mcp.server.fastmcp import Context
ctx = Context()
result = ping(ctx)
print('Status:', result)
"
```

## 📋 Verfügbare Tools

### 🔧 Grundlegende Befehle
- `ping` - Server-Verbindung testen
- `set_debug_mode` - Debug-Modus aktivieren/deaktivieren
- `log_thought` - AI-Gedanken protokollieren

### 🏗️ Objekte erstellen
```bash
# Kugel (SPHERE)
create_object(type='SPHERE', params={'radius': 1.0}, translation=[0,0,0])

# Würfel (BOX)
create_object(type='BOX', params={'width': 1.0, 'length': 1.0, 'height': 1.0})

# Weitere Typen: POINT, LINE, POLYLINE, CIRCLE, ARC, ELLIPSE, CURVE, CONE, CYLINDER, SURFACE
```

### 🎨 Materialien

#### Legacy Custom Materialien
```bash
# Material erstellen
create_material(name='Gold', color=[255,215,0], shine=0.9)

# Material Layer zuweisen
assign_material_to_layer(layer_name='MyLayer', material_id='0')
```

#### PBR Materialien (Physically Based Rendering) ✅ LAYER-BASIERTES SYSTEM
```bash
# 🔥 EMPFOHLENE HERANGEHENSWEISE: Layer-basiertes PBR System

# 1. PBR Material Layer erstellen
create_layer(name='Gold_Material_Layer', color=[255,215,0])

# 2. PBR Material erstellen
create_material(
    name='Gold_PBR',
    color=[255,215,0],     # Base color
    material_type='pbr',   # Wichtig: 'pbr' für echte PBR Materialien
    metallic=0.95,         # 0.0-1.0 (0.0 = nicht-metallisch, 1.0 = metallisch)
    roughness=0.05         # 0.0-1.0 (0.0 = spiegelglatt, 1.0 = rau)
)

# 3. Material dem Layer zuweisen
assign_material_to_layer(layer_name='Gold_Material_Layer', material_id='0')

# 4. Aktueller Layer setzen und Objekt erstellen
get_or_set_current_layer(name='Gold_Material_Layer')
create_object(type='SPHERE', name='Gold_Sphere', params={'radius': 1.0}, translation=[-3,0,0])

# ✅ ERGEBNIS: Die Kugel erbt automatisch das PBR Material des Layers!
# In Rhino Rendered View werden echte PBR Reflexionen angezeigt.

# PBR Material Parameter für realistische Metalle:
# - Gold: metallic=0.9-0.95, roughness=0.05-0.1 (sehr glänzend, spiegelnd)
# - Silber: metallic=0.8-0.9, roughness=0.08-0.15 (glänzend, leicht rau)
# - Platin: metallic=0.9-0.95, roughness=0.06-0.1 (sehr glänzend)
```

### 🗂️ Layer Management
```bash
# Layer erstellen
create_layer(name='MyLayer', color=[255,100,100])

# Aktueller Layer setzen
get_or_set_current_layer(name='MyLayer')

# Layer löschen
delete_layer(name='MyLayer')
```

### 📊 Informationen abrufen
```bash
# Dokument-Info
get_document_info()

# Objekt-Info
get_object_info(id='object-id')

# Ausgewählte Objekte
get_selected_objects_info()
```

## 🔍 Debugging & Logs

### Logs finden
- **Konsolen-Ausgabe:** Logs werden live in der Konsole angezeigt
- **Format:** `YYYY-MM-DD HH:MM:SS - RhinoMCPServer - INFO - Nachricht`
- **Debug-Modus:** `set_debug_mode(enable=True)`

### AI Thoughts protokollieren
```bash
log_thought(thought='Was ich gerade mache...')
```

## ⚠️ Troubleshooting

### "MCP Server is not running"
1. **Rhino Plugin:** `mcpstart` in Rhino Command Line
2. **Python Server:** `uv run rhinomcp` im Terminal
3. **Verbindung testen:** `ping` Tool verwenden

### Verbindung prüfen
```bash
# In Rhino
MCPStatus

# Via Python
uv run python -c "...ping tool..."
```

### Häufige Probleme
- **Port 1999 belegt:** Anderen Port verwenden
- **Firewall:** Port 1999 freigeben
- **Rhino Version:** Kompatibilität prüfen

## 📖 Beispiele

### PBR Metall-Kugeln erstellen ✅ LAYER-BASIERTES PBR SYSTEM
```bash
# 🔥 EMPFOHLENE LAYER-BASIERTE HERANGEHENSWEISE:

# 1. Debug aktivieren
set_debug_mode(enable=True)

# 2. AI Thought loggen
log_thought(thought='Erstelle Layer-basiertes PBR Setup')

# 3. PBR Material Layer erstellen
create_layer(name='Gold_Material_Layer', color=[255,215,0])
create_layer(name='Silver_Material_Layer', color=[192,192,192])
create_layer(name='Platinum_Material_Layer', color=[229,228,226])

# 4. PBR Materialien erstellen
create_material(name='Gold_PBR', color=[255,215,0], material_type='pbr', metallic=0.95, roughness=0.05)
create_material(name='Silver_PBR', color=[192,192,192], material_type='pbr', metallic=0.90, roughness=0.08)
create_material(name='Platinum_PBR', color=[229,228,226], material_type='pbr', metallic=0.92, roughness=0.06)

# 5. Materialien den Layern zuweisen
assign_material_to_layer(layer_name='Gold_Material_Layer', material_id='0')
assign_material_to_layer(layer_name='Silver_Material_Layer', material_id='1')
assign_material_to_layer(layer_name='Platinum_Material_Layer', material_id='2')

# 6. Kugeln auf den Layern erstellen (erben automatisch die Materialien!)
get_or_set_current_layer(name='Gold_Material_Layer')
create_object(type='SPHERE', name='Gold_Sphere', params={'radius': 1.0}, translation=[-3,0,0])

get_or_set_current_layer(name='Silver_Material_Layer')
create_object(type='SPHERE', name='Silver_Sphere', params={'radius': 1.0}, translation=[0,0,0])

get_or_set_current_layer(name='Platinum_Material_Layer')
create_object(type='SPHERE', name='Platinum_Sphere', params={'radius': 1.0}, translation=[3,0,0])

# ✅ ERFOLG: In Rhino Rendered View verwenden für echte PBR Reflexionen!
# Die Kugeln erben automatisch die PBR Materialien ihrer Layer und zeigen realistische Reflexionen!
```

### Legacy Custom Material Szene erstellen
```bash
# 1. Debug aktivieren
set_debug_mode(enable=True)

# 2. AI Thought loggen
log_thought(thought='Erstelle Beispiel-Szene')

# 3. Layer erstellen
create_layer(name='Gold_Layer', color=[255,215,0])
create_layer(name='Silver_Layer', color=[192,192,192])

# 4. Materialien erstellen
create_material(name='Gold', color=[255,215,0], shine=0.9)
create_material(name='Silver', color=[192,192,192], shine=0.8)

# 5. Materialien zuweisen
assign_material_to_layer(layer_name='Gold_Layer', material_id='0')
assign_material_to_layer(layer_name='Silver_Layer', material_id='1')

# 6. Objekte erstellen
create_object(type='BOX', name='Gold_Cube', params={'width': 2.0, 'length': 2.0, 'height': 2.0})
create_object(type='BOX', name='Silver_Cube', params={'width': 1.5, 'length': 1.5, 'height': 1.5}, translation=[3,0,0])
```

## 🔧 Konfiguration

### Farben
- Format: `[R, G, B]` (0-255)
- Beispiele:
  - Rot: `[255, 0, 0]`
  - Grün: `[0, 255, 0]`
  - Blau: `[0, 0, 255]`
  - Gold: `[255, 215, 0]`
  - Silber: `[192, 192, 192]`

### Material-Eigenschaften
- `shine`: 0.0 (matt) bis 1.0 (glänzend)
- `color`: RGB-Werte für diffuse Farbe

### Koordinaten
- Format: `[X, Y, Z]`
- Einheiten: Millimeter (standardmäßig)

## 📚 RhinoScript Integration

Für komplexe Operationen:
```bash
execute_rhinoscript_python_code(code='import rhinoscriptsyntax as rs\n# Dein Code hier')

# Mit erhöhtem Timeout für lange Skripte (max 120 Sekunden):
execute_rhinoscript_python_code(code='import rhinoscriptsyntax as rs\n# Langes Skript...', timeout=60)
```

### Timeout-Parameter

Der `timeout` Parameter ermöglicht es, längere Skripte auszuführen:
- **Default:** 15 Sekunden
- **Maximum:** 120 Sekunden
- **Minimum:** 1 Sekunde

Verwende höhere Timeouts für:
- Komplexe Geometrieoperationen
- Mesh-Generierung
- Große Datenmengen

## 🚨 Wichtige Hinweise

1. **Rhino Plugin zuerst starten** bevor der Python Server
2. **Debug-Modus aktivieren** für detaillierte Logs
3. **AI Thoughts verwenden** um den Prozess zu dokumentieren
4. **Material-IDs merken** nach der Erstellung (0, 1, 2, ...)
5. **Objekt-Namen eindeutig** verwenden für spätere Referenzierung

## 🎯 Best Practices

- **Konsistente Benennung:** `Material_Layer_1`, `Gold_Cube`, etc.
- **Farbcodierung:** Layer-Farben zu Materialien passend
- **Debugging:** Immer Debug-Modus für komplexe Operationen
- **Dokumentation:** AI Thoughts für Nachvollziehbarkeit
- **Backup:** Wichtige Szenen speichern vor Experimenten
