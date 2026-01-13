# AGENTS.md

> Agent-focused guide for working with RhinoMCP. Single source of truth for AI coding agents.

**Last Updated:** 2026-01-13
**Version:** 0.1.4.3
**Phase:** C Complete + Grasshopper Automation (Multi-door creation working!)

---

## 🚀 Agent Quick Start

**ALWAYS do this first when starting a new session (Both Cursor and Amp!):**

1. **Read progress:** `Ralph/progress.txt` - Current status, quick commands, recent sessions
2. **Check learnings:** `docs/learnings/*.md` - Technical patterns from previous work
3. **Check current phase:** `docs/ROADMAP.md` - What's the current focus?
4. **Find next task:** `Ralph/prd_phase_c.json` - Pick highest priority story with `passes: false`

### Tool Selection: Cursor vs Amp (Ralph)

Before starting, determine which workflow to use:

| Scenario | Tool | Reason |
|----------|------|--------|
| Autonomous iteration loops | **Amp (Ralph)** | Auto-handoff, fresh context per iteration |
| Interactive development | **Cursor** | Real-time feedback, debugging |
| Large refactoring | **Amp (Ralph)** | Context persistence via progress.txt |
| Quick fixes | **Cursor** | Direct, no overhead |

> **IMPORTANT:** Both tools MUST use `Ralph/progress.txt` for consistency!
> - **Before work:** Read progress.txt for learnings
> - **After work:** Append new learnings to progress.txt

### Behavioral Guidelines

| Do | Don't |
|----|-------|
| Read `progress.txt` before making changes | Jump straight into coding |
| Use structured JSON responses (`ok()`, `from_exception()`) | Return plain strings from tools |
| Test with `uv run pytest tests/ -v` | Skip testing |
| Update `progress.txt` after each story | Forget to document learnings |
| Follow existing patterns in the codebase | Invent new conventions |
| Use same progress.txt for Cursor AND Amp | Create separate progress logs |
| **Keep documentation clean** | Leave solved problems in active docs |
| **Archive solved issues** to `docs/archive/solved_issues/` | Delete problem history entirely |
| **Use plain text markers** (`[OK]`, `[ERROR]`) in console output | **Use emojis in code** (causes UnicodeEncodeError on Windows) |

### Documentation Hygiene (IMPORTANT!)

**Keep all documentation clean and current:**

1. **Remove solved problems** from `progress.txt` and other active docs
2. **Archive valuable learnings** to `docs/archive/solved_issues/ISSUE_NAME.md`
3. **Each archived issue should contain:**
   - Problem description
   - Failed attempts (brief)
   - Working solution
   - Key learnings
4. **Never leave** "TODO", "INCOMPLETE", or "PROBLEM" entries in active docs after resolution
5. **Check archives** before debugging - the problem may already be solved!

**Archive location:** `docs/archive/solved_issues/`

### Learning Documentation System

**CRITICAL: Document in Ralph first, use .md files sparingly!**

**Documentation Hierarchy:**

1. **Ralph (`Ralph/progress.txt`)** - PRIMARY location for learnings
   - Quick learnings (5-10 lines)
   - Gotchas and patterns
   - Session notes
   - Codebase patterns
   - **Use this for 90% of learnings**

2. **Learning Files (`docs/learnings/*.md`)** - Only for complex topics
   - Multi-step workflows requiring detailed guides
   - Complex API patterns with examples
   - Troubleshooting guides with multiple solutions
   - Reference documentation for tools/features
   - **Use sparingly - only when topic is too complex for progress.txt**

3. **Archive (`docs/archive/solved_issues/`)** - Solved problems
   - Complete problem descriptions
   - Failed attempts
   - Working solutions
   - **Move from progress.txt after resolution**

**Decision Tree:**
- Simple learning/gotcha? → `Ralph/progress.txt`
- Complex topic needing detailed guide? → `docs/learnings/*.md`
- Solved problem to archive? → `docs/archive/solved_issues/`

**Where to Document:**

| Content Type | Location | When to Update |
|--------------|----------|----------------|
| Session logs | `Ralph/progress.txt` | Each session (brief, 5-10 lines) |
| Quick learnings | `Ralph/progress.txt` | After solving problems (brief) |
| Complex technical guides | `docs/learnings/*.md` | Only for complex topics requiring detailed guides |
| Solved issues | `docs/archive/solved_issues/` | After issue resolved |
| Future work | `FUTURE_ISSUES.md` | When deferring work |
| Codebase patterns | `AGENTS.md` | When patterns stabilize |

**Progress.txt Rules:**
- Keep entries brief (5-10 lines per session)
- **Primary location for learnings** - use this for 90% of documentation
- Reference learning files only when topic is complex: "See: docs/learnings/TOPIC.md"
- Archive completed phases to `progress_archive_phase_X.txt`
- Remove detailed learnings after moving to archive (not to .md files)
- Max ~100-150 lines in active progress.txt
- **Don't create new .md files** unless topic is too complex for progress.txt

**Available Learning Files (use sparingly - prefer Ralph/progress.txt):**
- `docs/learnings/rhinocommon-api.md` - Complex RhinoCommon API patterns
- `docs/learnings/grasshopper-automation.md` - Multi-step GH automation workflows
- `docs/learnings/websocket-patterns.md` - Complex WebSocket streaming patterns
- `docs/learnings/boolean-operations.md` - Boolean operations API patterns
- `docs/learnings/viewport-camera-operations.md` - Viewport control reference guide
- `docs/learnings/material-assignment.md` - **Complex material assignment troubleshooting guide**
- `docs/learnings/getting-unstuck.md` - **Troubleshooting guide for stuck situations**

**Quick Learnings (in Ralph/progress.txt):**
- No emojis in Rhino code (Windows encoding issue) - see "Recent Learnings" section
- Display mode must be set to "Rendered" to show materials
- Screenshots directory must be created explicitly (it's in .gitignore)

### Response Format (SACRED)

All MCP tools MUST return JSON via helper functions:

```python
from rhinomcp.utils.responses import ok, from_exception
from rhinomcp.utils.errors import ErrorCode

# Success
return json.dumps(ok(message="Created object", data={"id": guid}))

# Error  
return json.dumps(from_exception(e, code=ErrorCode.CREATE_OBJECT_ERROR))
```

---

## 🚀 Real-Time Rhino Monitoring (WebSocket)

**Since Version 0.1.4.0 - Refactored in 0.1.4.1**

AI agents can now "see" what's happening in Rhino in real-time using **WebSocket streaming** (Port 2000).

### Quick Start

```python
# 1. Connect to WebSocket stream
connect_rhino_stream()

# 2. Run interactive Grasshopper script
run_script_async('_-GrasshopperPlayer "path/to/script.gh"')

# 3. Wait for prompts and respond -> this is just an example, it could be anything, 
prompt = wait_for_prompt("lichthoehe", timeout=10)
if prompt:
    send_rhino_input("2200")

# 4. Or use the automated helper
run_grasshopper_interactive(
    file_path="script.gh",
    inputs={"lichthoehe": "2200", "lichtbreite": "910"}
)
```

### Recommended: Use GetPoint Scripts

For reliable automation, use Grasshopper scripts with **GetPoint** instead of **GetPlane**:

```python
# Rahmentuer_UD4.gh - simplified with GetPoint
# Only 3 prompts: Lichthoehe, Lichtbreite, Get Point

# Single door (relativer Pfad vom Projekt-Root)
await ws.send({"command": "run_script", "script": '_-GrasshopperPlayer "Rahmentuer_UD4.gh"'})
# React to: Lichthoehe -> 2200, Lichtbreite -> 1200, Get Point -> 0,0,0

# Multi-door: See dev/create_3_doors.py for pattern (verwendet automatische Pfad-Erkennung)
```

**Key timing rules:**
- 0.5s delay before each input
- 2.0s wait between scripts

### WebSocket Tools

| Tool | Description |
|------|-------------|
| `connect_rhino_stream()` | Connect to WebSocket (Port 2000) |
| `disconnect_rhino_stream()` | Disconnect from stream |
| `send_rhino_input(value)` | Send input to Rhino command line |
| `wait_for_prompt(pattern)` | Wait for specific prompt |
| `run_script_async(script)` | Run script without blocking |
| `cancel_rhino_command()` | Cancel current command (LAST RESORT - only if timeout >60s) |
| `run_grasshopper_interactive()` | Run GH with auto-input |

### Documentation

- **Full Guide:** <a>docs/AI_AGENT_RHINO_VISIBILITY.md</a>
- **Grasshopper-Specific:** <a>docs/GRASSHOPPER_AUTOMATION.md</a>
- **Getting Unstuck:** <a>docs/learnings/getting-unstuck.md</a> - **When Rhino hangs or asks for unknown input**

---

## Project Overview

RhinoMCP enables AI agents to control Rhino 3D via the Model Context Protocol (MCP).

| Component | Location | Technology |
|-----------|----------|------------|
| **MCP Server** | `rhino_mcp_server/src/rhinomcp/` | Python, FastMCP |
| **Rhino Plugin** | `rhino_mcp_plugin/` | C#, RhinoCommon |
| **Transport** | TCP `127.0.0.1:1999` | JSON messages |

---

## Quick Commands

### Setup
```bash
# Install UV (required)
# macOS: brew install uv
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies
cd rhino_mcp_server
uv pip install -e .
```

### Run
```bash
# 1. Start MCP server
cd rhino_mcp_server
uv run rhinomcp
```

### Script Organization
```bash
# Temporary scripts (auto-cleanup after 7 days)
python scripts/temp/test_feature.py

# Example scripts (reusable)
python scripts/examples/complete_door_example.py

# Cleanup temp scripts
python scripts/cleanup_temp.py --days 7
python scripts/cleanup_temp.py --all  # Remove all
python scripts/cleanup_temp.py --dry-run  # Preview
```

See `scripts/README.md` for script organization guidelines.

### Test
```bash
# Run pytest suite (283+ tests)
cd rhino_mcp_server
uv run pytest tests/ -v

# Live test with Rhino
uv run python dev/test_fixes.py
```

### Build
```bash
# Python package
cd rhino_mcp_server
uv build

# C# plugin (Release)
cd rhino_mcp_plugin
dotnet build --configuration Release
```

---

## Project Structure

```
rhinomcp/                          # Project root
├── rhino_mcp_server/             # Python MCP server
│   ├── src/rhinomcp/
│   │   ├── tools/                # MCP tool implementations
│   │   ├── utils/                # Helpers (responses.py, errors.py)
│   │   └── server.py             # Main server + RhinoConnection
│   ├── tests/                    # Pytest test suite (30 files, 265 tests)
│   ├── dev/                      # Development scripts
│   └── pyproject.toml
│
├── rhino_mcp_plugin/             # C# Rhino plugin
│   ├── Functions/                # Command handlers
│   ├── Serializers/              # JSON serialization
│   ├── Commands/                 # Rhino command definitions
│   ├── RhinoMCPServer.cs         # TCP server + command dispatch
│   └── rhinomcp.csproj
│
├── Ralph/                        # Structured development workflow
│   ├── prd.json                  # Phase A user stories (complete)
│   ├── prd_phase_b.json          # Phase B user stories (complete)
│   ├── prd_phase_c.json          # Phase C user stories (in progress)
│   ├── progress.txt              # Codebase patterns & learnings
│   ├── archive/                  # Archived session plans
│   └── scripts/ralph/            # Ralph automation scripts
│
├── docs/                         # Documentation
│   ├── USAGE.md                  # Tool reference & examples
│   ├── ROADMAP.md                # Project phases & roadmap
│   ├── FUNCTIONAL_STATUS.md      # Current status & known issues
│   ├── MCP_TOOL_STANDARDS.md     # Tool development standards
│   └── archive/                  # Archived documentation
│       ├── PHASE_B_CONTEXT.md
│       ├── REPOSITORY_ANALYSIS.md
│       └── development_guide.md
│
├── assets/                       # Images, icons, demo files
├── demo_chats/                   # Demo conversation examples
├── learning/                     # ML training data
├── scripts/                      # Utility scripts
├── testdata/                     # Test data files (.3dm)
│
├── .github/workflows/            # CI/CD pipelines
│   ├── ci.yml                    # Pytest + ruff on Python 3.10-3.12
│   └── mcp-server-publish.yml    # Automated publishing
│
├── AGENTS.md                     # This file - agent guide
├── README.md                     # Project overview
├── README_MCP.md                 # MCP-specific documentation
├── FUTURE_ISSUES.md              # Planned improvements
└── LICENSE
```

---

## Code Conventions

### Naming
- **Commands:** `lower_snake_case`, verb first: `create_object`, `get_document_info`
- **Colors:** `[r, g, b]` (0-255)
- **Points:** `[x, y, z]`
- **IDs:** GUID strings

### Type Hints (MCP Schema Best Practices)
```python
from typing import Literal, Optional, List, Dict, Any

# Use Literal types for enum-like parameters (helps MCP clients)
ObjectType = Literal["POINT", "LINE", "POLYLINE", "CIRCLE", "BOX", "SPHERE", ...]
BooleanOperationType = Literal["union", "difference", "intersection"]

# Use Optional with None default (avoid mutable defaults!)
def my_tool(
    params: Optional[Dict[str, Any]] = None,  # NOT: Dict = {}
    filters: Optional[List[str]] = None,      # NOT: List = []
) -> str:
    params = params if params is not None else {}  # Runtime fallback
```

### Python Response Format
```python
from rhinomcp.utils.responses import ok, from_exception
from rhinomcp.utils.errors import ErrorCode

# Success
return json.dumps(ok(message="Created object", data={"id": obj_id}))

# Error
return json.dumps(from_exception(e, code=ErrorCode.CREATE_OBJECT_ERROR))
```

### C# Command Handler
```csharp
public JObject CreateObject(JObject parameters)
{
    var doc = RhinoDoc.ActiveDoc;
    
    // Parse parameters
    string type = parameters["type"]?.ToString();
    
    // Create geometry
    // ...
    
    // Update views
    doc.Views.Redraw();
    
    return JObject.FromObject(new { status = "success", id = objectId });
}
```

### Error Codes
| Code | Use Case |
|------|----------|
| `CONNECTION_ERROR` | General connection issues |
| `CONNECTION_TIMEOUT` | Socket timeout |
| `CONNECTION_REFUSED` | Rhino not running |
| `INVALID_PARAMS` | Bad input parameters |
| `RHINO_ERROR` | Error from Rhino |
| `CREATE_OBJECT_ERROR` | Object creation failed |

---

## Available Tools

For the complete tool list with parameters and examples, see **[docs/USAGE.md](docs/USAGE.md)**.

### Handler Mapping (for developers)

When adding new tools, register them in `RhinoMCPServer.cs`:

| Category | C# Handler File |
|----------|-----------------|
| Core (create, modify, delete) | `CreateObject.cs`, `ModifyObject.cs`, `DeleteObject.cs` |
| Layer & Material | `CreateLayer.cs`, `GetOrSetCurrentLayer.cs`, `GetDocumentInfo.cs` |
| **Material Assignment** | **See `docs/learnings/material-assignment.md` for complete guide** |
| Boolean Operations | `BooleanOperations.cs` |
| Transform Tools | `TransformOperations.cs` |
| Curve Tools | `CurveOperations.cs` |
| Surface Tools | `SurfaceOperations.cs` |
| Dimension Tools | `DimensionOperations.cs` |
| Object Properties | `ObjectProperties.cs` |
| Viewport Operations | `ViewportOperations.cs` |
| Render Operations | `RenderOperations.cs` |
| Mesh Operations | `MeshOperations.cs` |
| Grasshopper Operations | `GrasshopperOperations.cs` (run_grasshopper, run_grasshopper_automated, run_door_script) |
| Script Execution | `ExecuteCode.cs` |

---

## Adding New Tools

### 1. Python Tool
```python
# rhino_mcp_server/src/rhinomcp/tools/my_new_tool.py
from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger
from rhinomcp.utils.responses import ok, from_exception
import json

@mcp.tool()
def my_new_tool(ctx: Context, param1: str, param2: int = 10) -> str:
    """Tool description for AI agents."""
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("my_new_command", {
            "param1": param1,
            "param2": param2
        })
        return json.dumps(ok(message="Success", data=result))
    except Exception as e:
        logger.error(f"Error: {e}")
        return json.dumps(from_exception(e))
```

### 2. C# Handler
```csharp
// rhino_mcp_plugin/Functions/MyNewCommand.cs
public JObject MyNewCommand(JObject parameters)
{
    string param1 = parameters["param1"]?.ToString();
    int param2 = parameters["param2"]?.Value<int>() ?? 10;
    
    // Validate
    if (string.IsNullOrEmpty(param1))
        throw new ArgumentException("param1 is required");
    
    // Execute
    var doc = RhinoDoc.ActiveDoc;
    // ... do work ...
    
    doc.Views.Redraw();
    return JObject.FromObject(new { status = "success" });
}
```

### 3. Register in Server
```csharp
// RhinoMCPServer.cs in ExecuteCommandInternal
["my_new_command"] = this.handler.MyNewCommand,
```

### 4. Add Test
```python
# rhino_mcp_server/tests/test_my_new_tool.py
def test_my_new_tool():
    # Test implementation
    pass
```

---

## Development Workflow (Ralph)

Ralph is our structured development workflow for iterative improvements.

### Start New Feature
1. Read `Ralph/progress.txt` for patterns
2. Check `Ralph/prd_phase_c.json` for current stories
3. Pick highest priority story with `passes: false`
4. Implement in small steps
5. Build & Test (see below)
6. Update `progress.txt` with learnings
7. Mark story as `passes: true`
8. Update `AGENTS.md` (tool tables, test count, status)

### Build & Restart Workflow
After implementing features, **always** run:
```powershell
# 1. Close Rhino (if blocking build)
Stop-Process -Name "Rhino" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 2. Build C# plugin
cd rhino_mcp_plugin
dotnet build --configuration Release

# 3. Start Rhino
Start-Process "C:\Program Files\Rhino 8\System\Rhino.exe"
Start-Sleep -Seconds 15

# 4. Run tests (ensure MCP plugin is started with mcpstart first by the User)
cd c:\Users\Adi.Muff\repos\rhinomcp\rhino_mcp_server
uv run pytest tests/ -v
```

### Current Phase: C (Advanced Features) - Complete ✅
| Story | Title | Status |
|-------|-------|--------|
| US-C01 | File Operations | ✅ |
| US-C02 | Viewport Control | ✅ |
| US-C03 | Groups & Blocks | ✅ |
| US-C04 | Mesh Import/Export | ✅ |
| US-C05 | Render Settings | ✅ |
| US-C06 | Grasshopper Integration | ⚠️ Teilweise (Plane manuell) |

---

## Troubleshooting

### Connection Issues
```bash
# Check Rhino plugin status (use mcpstart to start manually)
MCPStatus  # in Rhino command line

# Manual restart if needed
mcpstop
mcpstart
```

**Note:** MCP plugin must be started manually with `mcpstart` command in Rhino command line.

### Build Errors (C#)
- Ensure Rhino SDK is installed
- Check `rhinomcp.csproj` for correct RhinoCommon version
- Build in Release mode: `dotnet build -c Release`

### Test Failures
```bash
# Run with verbose output
uv run pytest tests/ -v --tb=long

# Run specific test
uv run pytest tests/test_connection.py -v
```

---

## Agent Integration

### Claude Desktop
```json
// claude_desktop_config.json
{
  "mcpServers": {
    "rhino": {
      "command": "uvx",
      "args": ["rhinomcp"]
    }
  }
}
```

### Cursor
```json
// .cursor/mcp.json
{
  "mcpServers": {
    "rhino": {
      "command": "uvx",
      "args": ["rhinomcp"]
    }
  }
}
```

---

## Documentation Index

| File | Purpose |
|------|---------|
| `README.md` | Project overview & quick start |
| `AGENTS.md` | This file - AI agent guide |
| `FUTURE_ISSUES.md` | Planned improvements & feature requests |
| `README_MCP.md` | MCP-specific documentation |
| `docs/USAGE.md` | Tool reference, examples & conventions |
| `docs/ROADMAP.md` | Project phases & development roadmap |
| `docs/FUNCTIONAL_STATUS.md` | Current status, known issues & solutions |
| `docs/MCP_TOOL_STANDARDS.md` | Tool development standards & patterns |
| `docs/AI_AGENT_RHINO_VISIBILITY.md` | Guide for monitoring Rhino state in real-time |
| `docs/GRASSHOPPER_AUTOMATION.md` | Grasshopper Automation with command monitoring |
| **`docs/learnings/`** | **Technical learnings by topic** |
| `docs/learnings/rhinocommon-api.md` | RhinoCommon API patterns |
| `docs/learnings/grasshopper-automation.md` | Grasshopper automation learnings |
| `docs/learnings/websocket-patterns.md` | WebSocket streaming patterns |
| `docs/learnings/boolean-operations.md` | Boolean operations learnings |
| `docs/archive/PHASE_B_CONTEXT.md` | Phase B implementation details (archived) |
| `docs/archive/REPOSITORY_ANALYSIS.md` | Codebase analysis & insights (archived) |
| `docs/archive/development_guide.md` | Development workflow (deprecated) |
| `docs/archive/solved_issues/` | Solved issues archive - check before debugging! |
| `Ralph/README.md` | Ralph workflow documentation |
| `Ralph/progress.txt` | Session logs & quick commands (keep brief!) |
| `Ralph/progress_archive_phase_a.txt` | Archived Phase A sessions |
| `Ralph/progress_archive_phase_b.txt` | Archived Phase B+C sessions

### Tool Documentation

Detailed tool documentation is in the **Python docstrings**:

```
rhino_mcp_server/src/rhinomcp/tools/*.py
```

Each tool file contains:
- Full parameter documentation
- Return value descriptions
- Usage examples and notes

---

## Using Native Rhino Commands

For complex operations, you can use native Rhino commands instead of manual implementations:

### RhinoApp.RunScript() - Execute Native Commands
```csharp
// Execute native Rhino command from C# handler
string script = "_Loft _Pause _Pause _Enter";
bool echo = false;
RhinoApp.RunScript(script, echo);
```

### Built-in Alternatives
| Manual Implementation | Native Alternative |
|-----------------------|-------------------|
| Complex chamfer | `Curve.CreateFilletCurves(radius=0)` |
| Loft surfaces | `RhinoApp.RunScript("_Loft")` |
| Sweep surfaces | `RhinoApp.RunScript("_Sweep1")` |

### When to Use Native Commands
- Complex surface operations (Loft, Sweep, Revolve)
- Operations with many edge cases
- Features already perfected in Rhino

### Caveats
- Object references may become invalid after RunScript
- Re-fetch objects by GUID after native command execution
- Some commands require object selection first

---

## External Resources (Rhino Developer Docs)

When unsure how to implement a feature or which RhinoCommon/RhinoScript API to use, **always consult the official Rhino Developer Documentation**:

| Resource | URL | Use Case |
|----------|-----|----------|
| **Developer Portal** | https://developer.rhino3d.com/ | Main entry point, guides, tutorials |
| **RhinoCommon API** | https://developer.rhino3d.com/api/rhinocommon/ | C# API reference for Rhino plugins |
| **C++ API** | https://mcneel.github.io/rhino-cpp-api-docs/api/cpp/ | C++ SDK reference |
| **RhinoScript Guide** | https://developer.rhino3d.com/guides/rhinoscript/ | VBScript scripting reference |
| **Rhino.Python** | https://developer.rhino3d.com/guides/rhinopython/ | Python scripting in Rhino |

### When to Use External Docs

1. **Implementing new geometry types** - Check `Rhino.Geometry` namespace
2. **Working with materials/rendering** - Check `Rhino.Render` namespace
3. **Document operations** - Check `Rhino.DocObjects` namespace
4. **Unknown RhinoScript functions** - Use `get_rhinoscript_python_function_names` tool first, then docs
5. **Boolean operations, surfaces, curves** - Check `Rhino.Geometry.Brep`, `Rhino.Geometry.Curve`

> **IMPORTANT:** Don't guess RhinoCommon API calls. Always verify against the official docs to avoid runtime errors.

---

## See Also

- [docs/USAGE.md](docs/USAGE.md) - Quick reference (tool list, conventions)
- [docs/ROADMAP.md](docs/ROADMAP.md) - Project roadmap
- [Ralph/progress.txt](Ralph/progress.txt) - Session logs & quick commands
- [docs/learnings/](docs/learnings/) - Technical learnings by topic
- [Rhino Developer Docs](https://developer.rhino3d.com/) - Official API documentation
- Tool docstrings: `rhino_mcp_server/src/rhinomcp/tools/*.py` - Detailed tool documentation
