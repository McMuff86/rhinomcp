# Next Session Plan: US-C02 Viewport Control

> Plan für die nächste Agent-Session. Kopiere diesen Plan in ein neues Kontext-Fenster.

**US-C01 File Operations - COMPLETED 2026-01-10**
**Phase B - COMPLETED 2026-01-10**

---

## Ziel

Implementiere **US-C02: Viewport Control** für View-Steuerung und Viewport-Capture.

---

## Acceptance Criteria (aus prd_phase_c.json)

1. `set_view` tool sets named views (Top, Front, Perspective, etc.)
2. `zoom_extents` tool fits all objects
3. `zoom_selected` tool zooms to selection
4. `capture_viewport` tool captures viewport as image
5. Tests pass
6. Documentation updated

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
uv run python dev/test_viewport.py
```

### 4. Dokumentation aktualisieren

Nach erfolgreichen Tests:
1. `USAGE.md` - Neue Tools dokumentieren
2. `AGENTS.md` - Tool-Tabellen aktualisieren, Testzahl aktualisieren
3. `Ralph/prd_phase_c.json` - `passes: true` setzen
4. `Ralph/progress.txt` - Learnings dokumentieren

---

## Zu implementierende Tools

### 1. set_view
- Python: `rhino_mcp_server/src/rhinomcp/tools/set_view.py`
- C# API: `RhinoDoc.Views.ActiveView.SetNamedView()`
- Parameter: `view_name` (Top, Front, Right, Perspective, etc.)
- Returns: `{ success: true, view: "Perspective" }`

### 2. zoom_extents
- Python: `rhino_mcp_server/src/rhinomcp/tools/zoom_extents.py`
- C# API: `RhinoDoc.Views.ActiveView.ActiveViewport.ZoomExtents()`
- Returns: `{ success: true }`

### 3. zoom_selected
- Python: `rhino_mcp_server/src/rhinomcp/tools/zoom_selected.py`
- C# API: `RhinoDoc.Views.ActiveView.ActiveViewport.ZoomBoundingBox()`
- Returns: `{ success: true }`

### 4. capture_viewport
- Python: `rhino_mcp_server/src/rhinomcp/tools/capture_viewport.py`
- C# API: `RhinoDoc.Views.ActiveView.CaptureToBitmap()`
- Parameter: `width`, `height`, `file_path` (optional)
- Returns: `{ success: true, path: "...", base64: "..." }`

---

## RhinoCommon API Referenz

Für Viewport Control:
- https://developer.rhino3d.com/api/rhinocommon/rhino.display.rhinoview
- https://developer.rhino3d.com/api/rhinocommon/rhino.display.rhinoviewport

Key Methods:
- `view.SetNamedView(name)` - Set named view
- `viewport.ZoomExtents()` - Zoom to all objects
- `viewport.ZoomBoundingBox(bbox)` - Zoom to bounding box
- `view.CaptureToBitmap(size)` - Capture viewport as bitmap

---

## Prompt für neues Fenster

```
Lies @Ralph/NEXT_SESSION_PLAN.md und führe den Plan für US-C02: Viewport Control aus.

Workflow:
1. Implementiere die 4 Viewport Tools (set_view, zoom_extents, zoom_selected, capture_viewport)
2. Prüfe RhinoCommon API Dokumentation für korrekte Implementierung
3. Schließe Rhino automatisch wenn nötig (Stop-Process)
4. Baue das C# Plugin neu
5. Starte Rhino automatisch
6. Führe Tests aus
7. Aktualisiere alle Dokumentation inkl. AGENTS.md
```
