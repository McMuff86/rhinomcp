# Next Session Plan: US-B04 Surface from Curves

> Plan für die nächste Agent-Session. Kopiere diesen Plan in ein neues Kontext-Fenster.

---

## Ziel

Implementiere **US-B04: Surface from Curves (Loft, Extrude, Revolve)** mit automatischem Build & Test Workflow.

---

## Acceptance Criteria (aus prd_phase_b.json)

1. Add `loft_curves` tool (loft between multiple curves)
2. Add `extrude_curve` tool (extrude along vector or path)
3. Add `revolve_curve` tool (revolve around axis)
4. Support closed surfaces where applicable
5. Return new surface/brep IDs

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
# Versuche zuerst graceful, dann forciert
Stop-Process -Name "Rhino" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Schritt 2: C# Plugin builden
cd c:\Users\Adi.Muff\repos\rhinomcp\rhino_mcp_plugin
dotnet build --configuration Release

# Schritt 3: Rhino starten
Start-Process "C:\Program Files\Rhino 8\System\Rhino.exe"
Start-Sleep -Seconds 10  # Warte bis Rhino geladen ist

# Schritt 4: MCP Server starten (in separatem Terminal)
# Der User muss manuell "mcpstart" in Rhino eingeben
```

### 3. Test Workflow

```powershell
# Unit Tests ausführen
cd c:\Users\Adi.Muff\repos\rhinomcp\rhino_mcp_server
uv run pytest tests/ -v

# Live Tests ausführen (nach mcpstart in Rhino)
uv run python dev/test_surface_operations.py
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

## Hilfreiche Shell-Befehle

### Rhino schließen (wenn Build blockiert)
```powershell
# Graceful
Stop-Process -Name "Rhino" -ErrorAction SilentlyContinue

# Forciert (falls nötig)
Stop-Process -Name "Rhino" -Force -ErrorAction SilentlyContinue
```

### Rhino starten
```powershell
Start-Process "C:\Program Files\Rhino 8\System\Rhino.exe"
```

### Prüfen ob Rhino läuft
```powershell
Get-Process -Name "Rhino" -ErrorAction SilentlyContinue
```

### Build mit Fehlerbehandlung
```powershell
cd c:\Users\Adi.Muff\repos\rhinomcp\rhino_mcp_plugin

# Wenn Build fehlschlägt wegen gesperrter Datei:
Stop-Process -Name "Rhino" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
dotnet build --configuration Release
```

---

## Zu implementierende Tools

### 1. loft_curves
- Python: `rhino_mcp_server/src/rhinomcp/tools/loft_curves.py`
- C# API: `Brep.CreateFromLoft()` oder `Brep.CreateFromLoftRebuild()`
- Parameter: `curve_ids`, `closed` (bool), `loft_type` (normal, loose, tight, straight)

### 2. extrude_curve
- Python: `rhino_mcp_server/src/rhinomcp/tools/extrude_curve.py`
- C# API: `Extrusion.Create()` oder `Surface.CreateExtrusion()`
- Parameter: `curve_id`, `direction` (vector), `distance`, `cap` (bool)

### 3. revolve_curve
- Python: `rhino_mcp_server/src/rhinomcp/tools/revolve_curve.py`
- C# API: `RevSurface.Create()` oder `Brep.CreateFromRevSurface()`
- Parameter: `curve_id`, `axis_start`, `axis_end`, `angle` (degrees)

---

## RhinoCommon API Referenz

Für Surface Operations:
- https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.brep
- https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.extrusion
- https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.revsurface

Key Methods:
- `Brep.CreateFromLoft(curves, start, end, loftType, closed)`
- `Surface.CreateExtrusion(profile, direction)`
- `Extrusion.Create(profile, height, cap)`
- `RevSurface.Create(profile, axis, startAngle, endAngle)`

---

## Checkliste für den Agenten

- [ ] `loft_curves` implementieren
- [ ] `extrude_curve` implementieren  
- [ ] `revolve_curve` implementieren
- [ ] C# Handler in `SurfaceOperations.cs` erstellen
- [ ] Handler in `RhinoMCPServer.cs` registrieren
- [ ] Unit Tests erstellen
- [ ] Rhino schließen & neu builden
- [ ] Rhino starten
- [ ] Live Tests ausführen
- [ ] `USAGE.md` aktualisieren
- [ ] `AGENTS.md` aktualisieren (Tool-Tabellen, Testzahl, US-B04 Status)
- [ ] `Ralph/prd_phase_b.json` - US-B04 als passes: true markieren
- [ ] `Ralph/progress.txt` - Learnings dokumentieren

---

## Wichtige Learnings aus US-B03

1. **Parameter-Validierung VOR get_rhino_connection()** - Tests schlagen fehl wenn Validierung nach Connection-Versuch kommt
2. **Curve Operations können mehrere Ergebnisse liefern** - Immer Liste von IDs zurückgeben
3. **Immer LayerIndex auf neue Objekte setzen**

---

## Prompt für neues Fenster

```
Lies @Ralph/NEXT_SESSION_PLAN.md und führe den Plan für US-B04: Surface from Curves aus.

Workflow:
1. Implementiere die 3 Surface Tools (loft_curves, extrude_curve, revolve_curve)
2. Schließe Rhino automatisch wenn nötig (Stop-Process)
3. Baue das C# Plugin neu
4. Starte Rhino automatisch
5. Führe Tests aus
6. Aktualisiere alle Dokumentation inkl. AGENTS.md
```
