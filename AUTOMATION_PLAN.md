# 🏗️ RhinoMCP Vollautomatisierung Plan
## Automatische Grasshopper Eingaben für AI Coding Agent

**Ziel:** Vollständige Automatisierung der Grasshopper Script Ausführung ohne manuelle Eingaben

---

## 📊 **Aktuelle Situation**

### ✅ **Was funktioniert:**
- Grasshopper Scripts werden erfolgreich gestartet
- Plan-Analyse und Parameter-Extraktion arbeitet
- Stücklisten-Generierung ist implementiert
- MCP Kommunikation läuft stabil

### ❌ **Problem:**
- Interaktive Eingaben müssen manuell erfolgen:
  - Lichthoehe: [manuell]
  - Lichtbreite: [manuell]
  - Plane: [manuell]

---

## 🎯 **Lösungsstrategien**

### **Strategie 1: Rhino Command Automation (Empfohlen)**
**Ansatz:** Mehrere sequentielle RunScript Aufrufe mit präzisen Timings

#### **Implementierung:**
```csharp
// Pseudo-Code für automatisierte Eingaben
public JObject RunGrasshopperAutomated(JObject parameters)
{
    // 1. Grasshopper Script starten
    RhinoApp.RunScript("_-GrasshopperPlayer \"path/to/script.gh\"", false);

    // 2. Mit Timing warten und Eingaben senden
    System.Threading.Thread.Sleep(2000); // Warten bis Dialog erscheint

    // 3. Eingaben automatisch senden
    var inputs = parameters["inputs"]?.ToObject<List<string>>();
    foreach (var input in inputs)
    {
        RhinoApp.RunScript(input, false);
        System.Threading.Thread.Sleep(500); // Zwischen Eingaben warten
    }

    return JObject.FromObject(new { status = "completed", automated = true });
}
```

#### **Vorteile:**
- ✅ Nutzt vorhandene Rhino API
- ✅ Keine Script-Modifikation nötig
- ✅ Funktioniert mit bestehenden .gh Dateien

#### **Herausforderungen:**
- ⏳ Timing-abhängig (race conditions)
- 🔧 Debugging schwierig
- 📊 Nicht 100% zuverlässig

---

### **Strategie 2: Grasshopper Script Modifikation (Alternative)**
**Ansatz:** Scripts so ändern, dass sie Parameter aus Dateien lesen

#### **Implementierung:**
```csharp
// Script lädt Parameter aus temporärer JSON Datei
string paramFile = Path.GetTempFileName() + ".json";
File.WriteAllText(paramFile, JsonConvert.SerializeObject(parameters));

// Script starten
RhinoApp.RunScript($"_-GrasshopperPlayer \"script.gh\" -params:\"{paramFile}\"", false);
```

#### **Script Modifikation:**
```python
# Innerhalb Grasshopper Script:
import json
import os

# Parameter aus Datei laden
param_file = os.environ.get('GRASSHOPPER_PARAMS')
if param_file and os.path.exists(param_file):
    with open(param_file, 'r') as f:
        params = json.load(f)
        height = params.get('height', 2200)
        width = params.get('width', 910)
else:
    # Fallback auf interaktive Eingaben
    height = rs.GetReal("Lichthoehe", 2200)
    width = rs.GetReal("Lichtbreite", 910)
```

#### **Vorteile:**
- ✅ Zuverlässig und deterministisch
- ✅ Keine Timing-Probleme
- 📊 Einfach zu debuggen

#### **Herausforderungen:**
- 🔧 Erfordert Script-Modifikation
- 📝 Nicht kompatibel mit bestehenden Scripts
- 🏗️ Zusätzliche Datei-I/O

---

### **Strategie 3: Direkte Grasshopper API Integration (Zukunft)**
**Ansatz:** Grasshopper.dll direkt verwenden

#### **Implementierung:**
```csharp
// Referenz zu Grasshopper.dll hinzufügen
using Grasshopper;
using Grasshopper.Kernel;

// Script direkt laden und ausführen
var doc = new GH_Document();
doc.Open("path/to/script.gh");

// Parameter setzen
foreach (var obj in doc.Objects)
{
    if (obj is IGH_Param param)
    {
        // Parameter direkt setzen
        param.ClearData();
        param.AddVolatileData(new GH_Path(0), 0, new GH_Number(height));
    }
}

// Ausführen
doc.NewSolution(true);
```

#### **Vorteile:**
- ✅ Vollständige Kontrolle
- ⚡ Sehr schnell
- 🔧 Keine UI-Interaktion

#### **Herausforderungen:**
- 📚 Komplexe Grasshopper API
- 🏗️ Zusätzliche Dependencies
- 🧪 Mehr Testing nötig

---

## 📋 **Implementierungsplan**

### **Phase 1: Rhino Command Automation (1-2 Tage)**
**Ziel:** Schnelle Lösung mit minimalen Änderungen

#### **Aufgaben:**
1. **Timing-Analyse** - Wie lange dauert es bis Eingabeaufforderungen erscheinen?
2. **Sequenz-Implementierung** - Mehrere RunScript Aufrufe implementieren
3. **Error Handling** - Timeouts und Wiederholungen handhaben
4. **Testing** - Verschiedene Szenarien testen

#### **Code-Struktur:**
```csharp
public class AutomatedGrasshopperRunner
{
    public async Task<JObject> RunWithAutomation(JObject parameters)
    {
        // 1. Script starten
        // 2. Auf Eingabe warten
        // 3. Eingaben automatisch senden
        // 4. Erfolg prüfen
    }
}
```

### **Phase 2: Parameter-File Integration (2-3 Tage)**
**Ansatz:** Kombination aus beiden Strategien

#### **Implementierung:**
1. **Parameter-Datei erstellen** vor Script-Start
2. **Script modifizieren** um Datei zu lesen (Fallback auf manuelle Eingaben)
3. **Cleanup** - Temporäre Dateien entfernen

### **Phase 3: Grasshopper API Integration (1-2 Wochen)**
**Ziel:** Langfristige, robuste Lösung

#### **Meilensteine:**
1. **Grasshopper.dll Integration** in C# Plugin
2. **Parameter Mapping** implementieren
3. **Error Handling** für API-Aufrufe
4. **Performance Testing**

---

## 🔧 **Technische Details**

### **Erforderliche Änderungen:**

#### **C# Plugin (RhinoMCPPlugin):**
```csharp
// Neue Klasse für automatisierte Ausführung
public class GrasshopperAutomation
{
    private static readonly SemaphoreSlim _semaphore = new SemaphoreSlim(1, 1);

    public async Task<JObject> ExecuteAutomated(string scriptPath, JObject inputs)
    {
        await _semaphore.WaitAsync(); // Thread-Sicherheit
        try
        {
            // Automatisierte Ausführung
            return await RunWithInputs(scriptPath, inputs);
        }
        finally
        {
            _semaphore.Release();
        }
    }
}
```

#### **Python Tool:**
```python
@mcp.tool()
async def run_grasshopper_automated(
    ctx: Context,
    file_path: str,
    height: int = 2200,
    width: int = 910,
    plane: str = "WorldXY"
) -> str:
    """Run Grasshopper with fully automated inputs."""
    rhino = get_rhino_connection()

    inputs = {
        "height": height,
        "width": width,
        "plane": plane
    }

    result = await rhino.send_command_async("run_grasshopper_automated", {
        "file_path": file_path,
        "inputs": inputs
    })

    return json.dumps(ok(
        message=f"Grasshopper executed with automated inputs: {height}x{width}mm",
        data=result
    ))
```

### **Test-Strategie:**
```python
# Unit Tests für verschiedene Szenarien
def test_automated_execution():
    # Test mit verschiedenen Timings
    # Test mit verschiedenen Eingabe-Sequenzen
    # Test mit Fehlerfällen
    pass
```

---

## ⚠️ **Risiken & Herausforderungen**

### **Timing-Abhängigkeiten:**
- Race Conditions zwischen Script-Start und Eingabe-Senden
- Variable System-Performance
- UI-Responsiveness

### **Kompatibilität:**
- Unterschiedliche Rhino-Versionen
- Verschiedene Grasshopper-Script Typen
- Netzwerk-Latenz bei MCP

### **Debugging:**
- Schwierig zu diagnostizieren warum Automatisierung fehlschlägt
- Keine direkte Sichtbarkeit der Eingabe-Sequenzen

---

## 📊 **Zeitplan**

### **Sprint 1: Grundlegende Automation (3-5 Tage)**
- ✅ Rhino Command Automation implementieren
- ✅ Basic Timing-Tests
- ✅ Error Handling
- ✅ Dokumentation

### **Sprint 2: Robuste Lösung (1-2 Wochen)**
- ✅ Parameter-File Integration
- ✅ Erweiterte Testfälle
- ✅ Performance-Optimierung
- ✅ User Feedback Integration

### **Sprint 3: API Integration (2-3 Wochen)**
- ✅ Grasshopper.dll Integration
- ✅ Vollständige Parameter-Kontrolle
- ✅ Legacy-Support für alte Scripts

---

## 🎯 **Erfolgskriterien**

### **Funktional:**
- ✅ 95% Erfolgsrate bei automatisierten Ausführungen
- ✅ Keine manuellen Eingaben mehr nötig
- ✅ Kompatibel mit bestehenden Scripts

### **Zuverlässig:**
- ✅ Thread-sicher
- ✅ Error-resistent
- ✅ Wiederholbare Ergebnisse

### **Performant:**
- ✅ < 5 Sekunden für vollständige Ausführung
- ✅ Minimale System-Belastung
- ✅ Skalierbar für multiple Scripts

---

## 🚀 **Sofortige nächste Schritte**

### **Für AI Coding Agent:**

1. **Implementiere Strategie 1** (Rhino Command Automation)
2. **Füge detailliertes Logging hinzu** für Debugging
3. **Implementiere Retry-Mechanismen** für Timeouts
4. **Teste mit verschiedenen Script-Typen**

### **Code-Snippet für sofortige Implementierung:**
```csharp
public async Task<JObject> RunGrasshopperAutomated(JObject parameters)
{
    var scriptPath = parameters["file_path"]?.ToString();
    var inputs = parameters["inputs"] as JArray;

    // Script starten
    RhinoApp.RunScript($"_-GrasshopperPlayer \"{scriptPath}\"", false);

    // Mit präzisem Timing Eingaben senden
    await Task.Delay(1500); // Optimierte Wartezeit

    foreach (var input in inputs)
    {
        RhinoApp.RunScript(input.ToString(), false);
        await Task.Delay(300); // Optimierte Pause zwischen Eingaben
    }

    return JObject.FromObject(new { status = "success", automated = true });
}
```

---

## 📈 **Metriken & Monitoring**

### **Zu tracken:**
- Erfolgsrate automatischer Ausführungen
- Durchschnittliche Ausführungszeit
- Häufigste Fehlerursachen
- User Satisfaction (weniger manuelle Eingaben)

### **Logging:**
```csharp
_logger.LogInformation("Grasshopper automation started: {ScriptPath}", scriptPath);
_logger.LogInformation("Input sequence: {Inputs}", string.Join(" -> ", inputs));
_logger.LogInformation("Execution completed in {Duration}ms", stopwatch.ElapsedMilliseconds);
```

---

## 🎊 **Vision erreicht: Vollautomatisierung**

Dieser Plan führt zu einem System, wo AI Agents:

- **📖 Baupläne lesen** können
- **🏗️ Geometrie automatisch generieren**
- **📋 Stücklisten selbst erstellen**
- **🚫 Keine manuellen Eingaben mehr brauchen**

**Deine Vision von KI-gestützter Architektur-Automatisierung wird Realität!** 🏗️🤖

---

*Plan erstellt für AI Coding Agent zur Implementierung der vollautomatischen Grasshopper Integration.*