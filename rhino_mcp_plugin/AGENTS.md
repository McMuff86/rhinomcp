# C# Rhino Plugin - Agent Instructions

> Context-specific guide for AI agents working on the C# Rhino plugin component.
> For the full RhinoMCP guide, see [../AGENTS.md](../AGENTS.md).

## Quick Reference

| Item | Value |
|------|-------|
| **Language** | C# (.NET Framework) |
| **Framework** | RhinoCommon SDK |
| **Location** | `rhino_mcp_plugin/` |
| **Build** | `dotnet build --configuration Release` |
| **Transport** | TCP server on `localhost:1999` |

---

## Directory Structure

```
rhino_mcp_plugin/
├── RhinoMCPPlugin.cs         # Plugin entry point
├── RhinoMCPServer.cs         # TCP server + command dispatch
├── RhinoMCPServerController.cs # Server lifecycle management
├── Functions/                # Command handlers (21+ files)
│   ├── CreateObject.cs
│   ├── ModifyObject.cs
│   ├── BooleanOperations.cs
│   ├── TransformOperations.cs
│   ├── CurveOperations.cs
│   ├── SurfaceOperations.cs
│   ├── DimensionOperations.cs
│   ├── ObjectProperties.cs
│   ├── FileOperations.cs
│   └── _utils.cs             # Helper methods
├── Serializers/
│   └── Serializer.cs         # JSON serialization helpers
├── Commands/                 # Rhino command definitions
└── rhinomcp.csproj           # Project configuration
```

---

## Handler Registration

**CRITICAL:** When adding a new handler, register it in TWO places:

### 1. Handler Dictionary (ExecuteCommandInternal)

```csharp
// RhinoMCPServer.cs - ExecuteCommandInternal method
Dictionary<string, Func<JObject, JObject>> handlers = new Dictionary<string, Func<JObject, JObject>>
{
    // ... existing handlers ...
    ["my_new_command"] = this.handler.MyNewCommand,
};
```

### 2. Tool Registry (GetAvailableTools)

```csharp
// RhinoMCPServer.cs - GetAvailableTools method
public List<string> GetAvailableTools()
{
    return new List<string>
    {
        // ... existing tools ...
        "my_new_command",
    };
}
```

---

## Creating New Handlers

### 1. Create Handler File

```csharp
// Functions/MyNewOperation.cs
using System;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject MyNewCommand(JObject parameters)
    {
        // 1. Parse parameters
        string param1 = parameters["param1"]?.ToString();
        int param2 = parameters["param2"]?.Value<int>() ?? 10;
        
        // 2. Validate
        if (string.IsNullOrEmpty(param1))
            throw new ArgumentException("param1 is required");
        
        // 3. Get document
        var doc = RhinoDoc.ActiveDoc;
        
        // 4. Perform operation
        // ... your code here ...
        
        // 5. Update views
        doc.Views.Redraw();
        
        // 6. Return result
        return JObject.FromObject(new { 
            status = "success",
            result = "..."
        });
    }
}
```

### 2. Key Patterns

#### Undo-Safe Operations
All operations are automatically wrapped in undo records by the server:
```csharp
var record = doc.BeginUndoRecord("Run MCP command");
// ... operation ...
doc.EndUndoRecord(record);
```

#### UI Thread Dispatch
For operations that must run on the UI thread:
```csharp
RhinoApp.InvokeOnUiThread(new Action(() => {
    // UI-sensitive code here
}));
```

#### Error Handling
Throw exceptions with descriptive messages:
```csharp
throw new InvalidOperationException("Failed to create object: reason");
```

---

## Parameter Parsing Helpers

Use helper methods from `_utils.cs`:

```csharp
// Parse to Point3d
Point3d point = castToPoint3d(parameters.SelectToken("center"));

// Parse to double array
double[] values = castToDoubleArray(parameters.SelectToken("values"));

// Parse to int
int count = castToInt(parameters.SelectToken("count"));

// Parse to bool
bool flag = castToBool(parameters.SelectToken("enabled"));
```

---

## Build & Test Workflow

```powershell
# 1. Close Rhino (if running)
Stop-Process -Name "Rhino" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 2. Build plugin
cd rhino_mcp_plugin
dotnet build --configuration Release

# 3. Start Rhino
Start-Process "C:\Program Files\Rhino 8\System\Rhino.exe"
Start-Sleep -Seconds 10

# 4. In Rhino command line:
mcpstart

# 5. Run Python tests
cd ../rhino_mcp_server
uv run pytest tests/ -v
```

---

## RhinoCommon API Reference

- **Developer Portal**: https://developer.rhino3d.com/
- **RhinoCommon API**: https://developer.rhino3d.com/api/rhinocommon/
- **C++ API**: https://mcneel.github.io/rhino-cpp-api-docs/api/cpp/

### Common Namespaces

```csharp
using Rhino;                  // RhinoDoc, RhinoApp
using Rhino.Geometry;         // Point3d, Curve, Brep, Mesh, etc.
using Rhino.DocObjects;       // RhinoObject, ObjectAttributes
using Rhino.Display;          // RhinoView, RhinoViewport
using Rhino.Render;           // Materials
```

---

## Native Commands via RunScript

For complex operations, use native Rhino commands:

```csharp
// Execute native Rhino command
string script = "_Loft _Pause _Pause _Enter";
bool echo = false;
RhinoApp.RunScript(script, echo);
```

**Caveat:** Object references may become invalid after RunScript.

---

## Debugging

### Enable Debug Mode
```
MCPDebug  # Toggle in Rhino command line
```

### Check Logs
```csharp
// Logs are stored in server buffer
var logs = GetRecentLogs(50);
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Build fails | Close Rhino before building |
| Handler not found | Register in BOTH ExecuteCommandInternal AND GetAvailableTools |
| Object not created | Check if geometry is valid before adding to doc |
| Views not updating | Call `doc.Views.Redraw()` after changes |

---

## See Also

- [Root AGENTS.md](../AGENTS.md) - Full agent guide
- [MCP_TOOL_STANDARDS.md](../MCP_TOOL_STANDARDS.md) - Tool standards
- [Ralph/progress.txt](../Ralph/progress.txt) - Session learnings
- [Rhino Developer Docs](https://developer.rhino3d.com/) - Official API docs
