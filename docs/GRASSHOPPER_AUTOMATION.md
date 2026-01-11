# Grasshopper Automation - Status & Next Steps

**Erstellt:** 2026-01-11
**Status:** ✅ ENHANCED - Command Line Monitoring Implemented!
**Priorität:** HIGH

---

## 🎉 BREAKTHROUGH: Agent Can Now "See" Rhino!

**Update 2026-01-11:** Implemented command line monitoring system that allows AI agents to:
- ✅ Detect when Rhino prompts for user input
- ✅ See what Rhino is asking for (e.g., "GetPlane ( WorldXY WorldYZ WorldZX )")
- ✅ Monitor Grasshopper Player execution state
- ✅ Make intelligent decisions based on Rhino's state

**New Tools:**
- `get_command_output(count=50, since=None)` - Retrieve command line events
- `clear_command_output()` - Reset monitoring buffer

**Documentation:** See `AI_AGENT_RHINO_VISIBILITY.md` for complete guide!

---

## Problem Summary (SOLVED!)

Der AI Agent kann Rhino/GrasshopperPlayer Prompts **nicht sehen**.

### Was der Agent bekommt:
```python
result = Rhino.RhinoApp.RunScript(script, False)
# result = True/False - MEHR NICHT!
```

### Was der Agent NICHT bekommt:
```
Lichthoehe: ___
Lichtbreite ( Undo ): ___
GetPlane ( WorldXY  WorldYZ  WorldZX  Undo )
```

---

## Getestete Ansätze (alle gescheitert)

| Ansatz | Befehl | Ergebnis |
|--------|--------|----------|
| Basis | `_-GrasshopperPlayer "script.gh"` | Alle 3 Eingaben manuell |
| Inline H/W | `... 2200 910` | H/W ok, Plane manuell |
| Inline Point | `... 2200 910 0 0 0` | Inkonsistent! |
| WorldXY Text | `... 2200 910 _WorldXY` | Nicht erkannt |
| w Key | `... 2200 910 w` | `w` → `_SelWindow` |
| Timer C# | `Task.Run` + `Sleep` + `RunScript` | UI Deadlock |
| SendKeys | `System.Windows.Forms.SendKeys` | Timing-Probleme |
| Thread Python | `System.Threading.Thread` | Manchmal ok, inkonsistent |

### Inkonsistenz-Problem:
- Tür 1 am Origin (0,0,0): Manchmal automatisch
- Tür 2/3 an anderen Positionen: Immer manuell
- `Result: True` kommt auch bei manueller Eingabe!

---

## Lösungsansätze für nächste Session

### 1. Rhino CommandLine Output Listener (Empfohlen)

```csharp
// In RhinoMCPServer.cs oder neuer Handler
public void EnableCommandListener()
{
    Rhino.RhinoApp.CommandLineOut += OnCommandLineOut;
}

private void OnCommandLineOut(object sender, Rhino.Commands.CommandLineOutputEventArgs e)
{
    // e.Text enthält: "GetPlane ( WorldXY WorldYZ WorldZX Undo )"
    // An Python MCP Server senden oder in Queue speichern
    commandOutputQueue.Enqueue(e.Text);
}
```

**Vorteil:** Agent sieht was Rhino fragt
**Implementierung:** ~1-2 Stunden

### 2. Grasshopper API Direkt (Langfristig besser)

```csharp
using Grasshopper;
using Grasshopper.Kernel;

public JObject RunGrasshopperDirect(JObject parameters)
{
    string filePath = parameters["file_path"].ToString();
    var inputs = parameters["inputs"] as JObject;
    
    // Definition laden
    var archive = new GH_Archive();
    if (!archive.ReadFromFile(filePath))
        throw new Exception("Cannot read .gh file");
    
    var doc = new GH_Document();
    if (!archive.ExtractObject(doc, "Definition"))
        throw new Exception("Cannot extract definition");
    
    // Inputs finden und setzen
    foreach (var input in doc.Objects.OfType<IGH_Param>())
    {
        if (inputs.ContainsKey(input.NickName))
        {
            var value = inputs[input.NickName];
            // Wert setzen basierend auf Typ
            SetParameterValue(input, value);
        }
    }
    
    // Lösung berechnen
    doc.NewSolution(true);
    
    // Geometrie baken
    foreach (var obj in doc.Objects.OfType<IGH_BakeAwareObject>())
    {
        obj.BakeGeometry(RhinoDoc.ActiveDoc, new ObjectAttributes(), new List<Guid>());
    }
    
    return JObject.FromObject(new { status = "success" });
}
```

**Vorteil:** Keine Prompts, volle Kontrolle
**Nachteil:** Komplexer, Grasshopper.dll nötig
**Implementierung:** ~4-8 Stunden

### 3. Parameter File (Script-Modifikation)

```json
// C:\temp\door_params.json
{
    "Lichthoehe": 2200,
    "Lichtbreite": 910,
    "Plane": "WorldXY",
    "Origin": [0, 0, 0]
}
```

Grasshopper Script modifizieren:
- File Path Input → JSON Datei lesen
- Cluster/C# Component für Parsing

**Vorteil:** Einfach, keine API-Änderungen
**Nachteil:** Jedes Script muss angepasst werden
**Implementierung:** ~30 min pro Script

---

## Test-Script: Rahmentuer_UD3.gh

**Inputs:**
1. `Lichthoehe` (Number) - Default: 2200mm
2. `Lichtbreite` (Number) - Default: 910mm  
3. `Plane` (GetPlane) - Options: WorldXY, WorldYZ, WorldZX

**Outputs:**
- Tuerblatt (1 Objekt pro Tür)
- Tuerrahmen (3 Objekte pro Tür)
- Intumex_Rahmen (2 Objekte pro Tür)
- Total: 6 Objekte pro Tür

**Layers erstellt:**
- `Tuerblatt`
- `Tuerrahmen`
- `Intumex_Rahmen`

---

## Dateien zum Aufräumen

Diese Dateien wurden erstellt, funktionieren aber nicht zuverlässig:

```
rhino_mcp_server/src/rhinomcp/tools/run_grasshopper_automated.py
rhino_mcp_server/tests/test_run_grasshopper_automated.py
rhino_mcp_plugin/Functions/GrasshopperOperations.cs (RunGrasshopperAutomated Methode)
```

Die Basis `run_grasshopper` Funktion funktioniert, aber erfordert manuelle Eingabe.

---

## Empfehlung für nächste Session

1. **Starte mit Ansatz 1** (CommandLine Listener)
   - Schnell zu implementieren
   - Ermöglicht dem Agent zu "sehen" was passiert
   - Kann dann intelligent reagieren

2. **Falls Ansatz 1 nicht reicht** → Ansatz 2 (Grasshopper API)
   - Komplett ohne Prompts
   - Maximale Kontrolle

3. **Nicht mehr probieren:**
   - Inline Parameters mit verschiedenen Formaten
   - Timer-basierte Eingaben
   - SendKeys

---

## Referenzen

- [Rhino Developer Docs](https://developer.rhino3d.com/)
- [Grasshopper SDK](https://developer.rhino3d.com/api/grasshopper/)
- `Ralph/progress.txt` - Vollständige Session-Dokumentation
