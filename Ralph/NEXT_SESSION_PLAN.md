# Next Session Plan: US-C03 Groups & Blocks

> Plan für die nächste Agent-Session. Kopiere diesen Plan in ein neues Kontext-Fenster.

**US-C01 File Operations - COMPLETED 2026-01-10**
**US-C02 Viewport Control - COMPLETED 2026-01-10**
**Phase B - COMPLETED 2026-01-10**

---

## Ziel

Implementiere **US-C03: Groups & Blocks** für geometrische Organisation und Wiederverwendung.

---

## Acceptance Criteria (aus prd_phase_c.json)

1. `create_group` tool groups objects by ID
2. `ungroup` tool explodes groups
3. `create_block` tool creates block definition
4. `insert_block` tool inserts block instance
5. `explode_block` tool converts block to geometry
6. Tests pass
7. Documentation updated

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
Start-Sleep -Seconds 15

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

### 1. create_group
- Python: `rhino_mcp_server/src/rhinomcp/tools/create_group.py`
- C# API: `RhinoDoc.Groups.Add()`
- Parameter: `object_ids` (list of object IDs to group)
- Returns: `{ success: true, group_id: "guid", group_name: "Group 01" }`

### 2. ungroup
- Python: `rhino_mcp_server/src/rhinomcp/tools/ungroup.py`
- C# API: `RhinoDoc.Groups.Ungroup()`
- Parameter: `group_id` (ID of group to ungroup)
- Returns: `{ success: true, object_ids: ["id1", "id2"] }`

### 3. create_block
- Python: `rhino_mcp_server/src/rhinomcp/tools/create_block.py`
- C# API: `RhinoDoc.InstanceDefinitions.Add()`
- Parameter: `name`, `object_ids`, `base_point` (insertion point)
- Returns: `{ success: true, block_id: "guid" }`

### 4. insert_block
- Python: `rhino_mcp_server/src/rhinomcp/tools/insert_block.py`
- C# API: `RhinoDoc.Objects.AddInstanceObject()`
- Parameter: `block_name`, `position` (insertion point)
- Returns: `{ success: true, instance_id: "guid" }`

### 5. explode_block
- Python: `rhino_mcp_server/src/rhinomcp/tools/explode_block.py`
- C# API: `RhinoDoc.Objects.Explode()`
- Parameter: `instance_id` (block instance to explode)
- Returns: `{ success: true, object_ids: ["id1", "id2"] }`

---

## RhinoCommon API Referenz

Für Groups & Blocks:
- https://developer.rhino3d.com/api/rhinocommon/rhino.docobjects.groups
- https://developer.rhino3d.com/api/rhinocommon/rhino.docobjects.instancedefinition

Key Methods für Groups:
- `RhinoDoc.Groups.Add(objects)` - Create new group
- `RhinoDoc.Groups.Ungroup(groupIndex)` - Ungroup objects

Key Methods für Blocks:
- `RhinoDoc.InstanceDefinitions.Add(name, description, basePoint, geometry, attributes)` - Create block definition
- `RhinoDoc.Objects.AddInstanceObject(instanceDefinitionIndex, xform)` - Insert block instance
- `RhinoDoc.Objects.Explode(objRef, pieces)` - Explode block to geometry

---

## Prompt für neues Fenster

```
Lies @Ralph/NEXT_SESSION_PLAN.md und führe den Plan für US-C03: Groups & Blocks aus.

Workflow:
1. Implementiere die 5 Group/Block Tools (create_group, ungroup, create_block, insert_block, explode_block)
2. Prüfe RhinoCommon API Dokumentation für korrekte Implementierung
3. Schließe Rhino automatisch wenn nötig (Stop-Process)
4. Baue das C# Plugin neu
5. Starte Rhino automatisch
6. Führe Tests aus
7. Aktualisiere alle Dokumentation inkl. AGENTS.md
```
