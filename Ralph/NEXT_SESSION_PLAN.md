# Next Session Plan: US-B05 Dimension Tools

> Plan für die nächste Agent-Session. Kopiere diesen Plan in ein neues Kontext-Fenster.

---

## Ziel

Implementiere **US-B05: Dimension Tools** für lineare, angulare und radiale Bemaßungen.

---

## Acceptance Criteria (aus prd_phase_b.json)

1. Add `create_linear_dimension` tool
2. Add `create_angular_dimension` tool
3. Add `create_radial_dimension` tool
4. Dimensions update correctly with object changes
5. Support dimension style parameters

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
uv run python dev/test_dimension_operations.py
```

### 4. Dokumentation aktualisieren

Nach erfolgreichen Tests:
1. `USAGE.md` - Neue Tools dokumentieren
2. `AGENTS.md` - Tool-Tabellen aktualisieren, Testzahl aktualisieren
3. `Ralph/prd_phase_b.json` - `passes: true` setzen
4. `Ralph/progress.txt` - Learnings dokumentieren

---

## Rhino Pfade (Windows)

```
Rhino 8: C:\Program Files\Rhino 8\System\Rhino.exe
Plugin: C:\Users\Adi.Muff\repos\rhinomcp\rhino_mcp_plugin\bin\Release\net7.0\rhinomcp.rhp
```

---

## Zu implementierende Tools

### 1. create_linear_dimension
- Python: `rhino_mcp_server/src/rhinomcp/tools/create_linear_dimension.py`
- C# API: `LinearDimension.Create()` oder `doc.Objects.AddLinearDimension()`
- Parameter: `start_point`, `end_point`, `text_point`, `dimension_style` (optional)

### 2. create_angular_dimension
- Python: `rhino_mcp_server/src/rhinomcp/tools/create_angular_dimension.py`
- C# API: `AngularDimension.Create()` oder `doc.Objects.AddAngularDimension()`
- Parameter: `vertex`, `start_point`, `end_point`, `text_point`

### 3. create_radial_dimension
- Python: `rhino_mcp_server/src/rhinomcp/tools/create_radial_dimension.py`
- C# API: `RadialDimension.Create()` oder `doc.Objects.AddRadialDimension()`
- Parameter: `center`, `radius_point`, `text_point`, `is_diameter` (bool)

---

## RhinoCommon API Referenz

Für Dimension Operations:
- https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.lineardimension
- https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.angulardimension
- https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.radialdimension

Key Methods:
- `LinearDimension.Create(plane, extensionLine1, extensionLine2, direction, textLocation)`
- `AngularDimension.Create(plane, vertex, startDir, endDir, textPoint)`
- `RadialDimension.Create(circle, point, text)`

---

## Wichtige Learnings aus US-B04

1. **Parameter-Validierung VOR get_rhino_connection()** - Auch für optionale Parameter!
2. **Surface zu Brep konvertieren** - RevSurface muss vor dem Hinzufügen zum Dokument konvertiert werden
3. **Immer LayerIndex auf neue Objekte setzen**

---

## Prompt für neues Fenster

```
Lies @Ralph/NEXT_SESSION_PLAN.md und führe den Plan für US-B05: Dimension Tools aus.

Workflow:
1. Implementiere die 3 Dimension Tools (create_linear_dimension, create_angular_dimension, create_radial_dimension)
2. Prüfe RhinoCommon API Dokumentation für korrekte Implementierung
3. Schließe Rhino automatisch wenn nötig (Stop-Process)
4. Baue das C# Plugin neu
5. Starte Rhino automatisch
6. Führe Tests aus
7. Aktualisiere alle Dokumentation inkl. AGENTS.md
```
