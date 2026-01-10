# Next Session Plan: US-B06 Object Properties

> Plan für die nächste Agent-Session. Kopiere diesen Plan in ein neues Kontext-Fenster.

**US-B05 Dimension Tools - COMPLETED 2026-01-10**

---

## Ziel

Implementiere **US-B06: Get/Set Object Properties** für Bounding Box, Area, Volume, Centroid etc.

---

## Acceptance Criteria (aus prd_phase_b.json)

1. Add `get_object_properties` tool (bounding box, area, volume, centroid)
2. Add `set_object_properties` tool (name, layer, color, material)
3. Support batch operations for multiple objects
4. Return structured property data

---

## Workflow für jede Implementierung

### 1. Implementierung

Für jedes neue Tool:
1. Python Tool erstellen in `rhino_mcp_server/src/rhinomcp/tools/`
2. C# Handler erstellen/erweitern in `rhino_mcp_plugin/Functions/`
3. Handler registrieren in `rhino_mcp_plugin/RhinoMCPServer.cs`
4. Tests erstellen in `rhino_mcp_server/tests/`

### 2. Build & Restart Workflow

Nach jeder Implementierung **IMMER** diesen Workflow ausführen:

```powershell
# Schritt 1: Rhino beenden (falls es den Build blockiert)
Stop-Process -Name "Rhino" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Schritt 2: C# Plugin builden
cd c:\Users\Adi.Muff\repos\rhinomcp\rhino_mcp_plugin
dotnet build --configuration Release

# Schritt 3: Rhino starten
Start-Process "C:\Program Files\Rhino 8\System\Rhino.exe"
Start-Sleep -Seconds 10

# Schritt 4: MCP Server starten (in separatem Terminal)
# Der User muss manuell "mcpstart" in Rhino eingeben
```

### 3. Test Workflow

```powershell
# Unit Tests ausführen
cd c:\Users\Adi.Muff\repos\rhinomcp\rhino_mcp_server
uv run pytest tests/ -v

# Live Tests ausführen (nach mcpstart in Rhino)
uv run python dev/test_object_properties.py
```

### 4. Dokumentation aktualisieren

Nach erfolgreichen Tests:
1. `USAGE.md` - Neue Tools dokumentieren
2. `AGENTS.md` - Tool-Tabellen aktualisieren, Testzahl aktualisieren
3. `Ralph/prd_phase_b.json` - `passes: true` setzen
4. `Ralph/progress.txt` - Learnings dokumentieren

---

## Zu implementierende Tools

### 1. get_object_properties
- Python: `rhino_mcp_server/src/rhinomcp/tools/get_object_properties.py`
- C# API: `RhinoObject.Geometry.GetBoundingBox()`, `AreaMassProperties.Compute()`, `VolumeMassProperties.Compute()`
- Parameter: `object_id` (single) oder `object_ids` (batch)
- Returns: `{ bounding_box, area, volume, centroid, surface_area }`

### 2. set_object_properties
- Python: `rhino_mcp_server/src/rhinomcp/tools/set_object_properties.py`
- C# API: `RhinoObject.Attributes` modifications
- Parameter: `object_id`, `name`, `layer`, `color`, `material_id`
- Supports batch via `object_ids`

---

## RhinoCommon API Referenz

Für Object Properties:
- https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.areamassproperties
- https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.volumemassproperties
- https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.boundingbox

Key Methods:
- `AreaMassProperties.Compute(geometry)` - Area, centroid for surfaces
- `VolumeMassProperties.Compute(geometry)` - Volume, centroid for solids
- `geometry.GetBoundingBox(accurate)` - Bounding box corners

---

## Prompt für neues Fenster

```
Lies @Ralph/NEXT_SESSION_PLAN.md und führe den Plan für US-B06: Object Properties aus.

Workflow:
1. Implementiere die 2 Object Property Tools (get_object_properties, set_object_properties)
2. Prüfe RhinoCommon API Dokumentation für korrekte Implementierung
3. Schließe Rhino automatisch wenn nötig (Stop-Process)
4. Baue das C# Plugin neu
5. Starte Rhino automatisch
6. Führe Tests aus
7. Aktualisiere alle Dokumentation inkl. AGENTS.md
```
