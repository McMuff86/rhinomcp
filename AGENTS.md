# AGENTS.md

An agent-focused guide for working with RhinoMCP. This complements human-facing docs and gives coding agents a single source of truth for setup, commands, conventions, and troubleshooting. Inspired by the open format described at [agents.md](https://agents.md/).

## Project overview

- Python MCP server: `rhino_mcp_server/src/rhinomcp` (FastMCP-based). Exposes tools to AI agents and bridges to the Rhino plugin via TCP.
- Rhino plugin (C#): `rhino_mcp_plugin`. Hosts a TCP server inside Rhino and executes geometry/annotation commands.
- Transport: TCP localhost `127.0.0.1:1999`. The Python side maintains a persistent socket.

## Setup commands

- Install UV (required)
  - macOS: `brew install uv`
  - Windows (PowerShell): `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

- Install Python deps (local dev)
  - From repo root: `cd rhino_mcp_server`
  - Optional: create venv with UV: `uv venv`
  - Install: `uv pip install -e .`

- Start Rhino plugin
  - In Rhino command line: `mcpstart`

- Start MCP server (development)
  - From `rhino_mcp_server`: `uv run python -m rhinomcp`

- Start MCP server (installed entrypoint)
  - Anywhere: `uvx rhinomcp`

## Agent integrations

- Claude Desktop (example)
  - Add to `claude_desktop_config.json`:
    ```json
    {
      "mcpServers": {
        "rhino": {
          "command": "uvx",
          "args": ["rhinomcp"]
        }
      }
    }
    ```

- Cursor
  - Create `.cursor/mcp.json` with the same config as above.
  - Ensure Rhino plugin is running (see "Start Rhino plugin").

## Build and publish

- Python package (server)
  - `cd rhino_mcp_server`
  - Build: `uv build`
  - Publish: `uv publish`

- Rhino plugin (Yak)
  - Build in Release mode
  - Copy `rhino_mcp_plugin/manifest.yml` into `rhino_mcp_plugin/bin/Release`
  - From that folder: `yak build`
  - Publish: `yak push rhino_mcp_plugin_XXXX.yak`

## Testing instructions

- Smoke/dev script:
  - Start Rhino plugin (`mcpstart`) and MCP server (`uv run python -m rhinomcp`).
  - From `rhino_mcp_server`: `uv run python dev_test.py`
  - This exercises a few tools (document info, text, text dot, leader). No full test suite yet.

## Tooling and commands

RhinoMCP tools are registered on Python and dispatched to C#. Common commands include:

- `get_document_info`
- `create_object`, `create_objects` (supports POINT, LINE, POLYLINE, CIRCLE, ARC, ELLIPSE, CURVE, BOX, SPHERE, CONE, CYLINDER, SURFACE, MESH)
- `get_object_info`, `get_selected_objects_info` (enhanced with geometry details)
- `delete_object`
- `modify_object`, `modify_objects`
- `execute_rhinoscript_python_code`
- `select_objects`
- `create_layer`, `get_or_set_current_layer`, `delete_layer`
- `create_material` (supports both legacy custom and PBR materials), `assign_material_to_layer` (render material management)
- `ping` (health check)
- `set_debug_mode` (enable/disable enhanced logging)
- `log_thought` (log AI thought processes)

Parameters follow these conventions:
- Colors: `[r, g, b]` in range 0–255
- Points: `[x, y, z]`
- IDs: GUID strings

**Material parameters:**
- **Legacy Custom:** `shine` (0.0–1.0, controls specular reflection)
- **PBR Materials:** `material_type='pbr'`, `metallic` (0.0–1.0), `roughness` (0.0–1.0)
  - `metallic`: 0.0 = dielectric/non-metal, 1.0 = pure metal
  - `roughness`: 0.0 = mirror smooth, 1.0 = completely rough

**Status:** ✅ Layer-based PBR implementation is now working correctly, creating materials with proper metallic and roughness parameters. Objects automatically inherit PBR materials from their layers, rendering with realistic metallic appearance in Rendered viewport. The system successfully handles both legacy custom materials and Layer-based PBR materials. See W-0004 in FUNCTIONAL_STATUS.md for implementation details.

**Best Practice:** Use Layer-based material assignment for PBR materials - create dedicated material layers, assign PBR materials to layers, then create objects on those layers for automatic material inheritance.

## Code style and MCP standards

Follow the standards described in `MCP_TOOL_STANDARDS.md`:
- Return shape prefers stable JSON objects with `{ success, message, data }` for Python-side helpers when appropriate.
- Log concise, actionable details; Python via `rhinomcp.server.logger`, C# via `RhinoApp.WriteLine`.
- Validate inputs and surface clear error messages.
- Command names use lower_snake_case verbs first (e.g., `create_object`).
- Keep operations undo-safe in C# (Begin/End undo record) and update views.

## Dev environment tips

- Use `uv run` to ensure local package resolution from `src/` during development.
- If the MCP server fails to connect, confirm Rhino plugin is running and listening on `127.0.0.1:1999`.
- Prefer batch endpoints (e.g., `create_objects`, `modify_objects`) for N > 10 items.

## Troubleshooting

- Timeout waiting for response: Verify plugin is running (`mcpstart`) and restart the Python server. Reduce payload size.
- "Unknown command type": Ensure the command is registered on both sides and names match exactly.
- Serialization gaps: Extend `rhinomcp_plugin.Serializers.Serializer` consistently before adding new geometry types.

## Security considerations

- Experimental script execution (`execute_rhinoscript_python_code`) can fail or run arbitrary code inside Rhino. Ensure you trust the source before executing.
- Document queries limit counts (e.g., 30 items) to avoid overwhelming agents.

## Documentation index (keep updated)

- Root docs
  - `README.md`
  - `README_MCP.md`
  - `MCP_TOOL_STANDARDS.md`
  - `FUNCTIONAL_STATUS.md`
  - `ANALYSIS_LOG.md`
  - `USAGE.md` (user guide for tool operation)
  - `AGENTS.md` (this file)

- Server docs
  - `rhino_mcp_server/README.md`

When adding any new `*.md` file, list it here under the appropriate section.

## Project Structure

```
rhinomcp/
├── rhino_mcp_plugin/          # C# Rhino plugin
│   ├── Functions/             # Command handlers
│   ├── Serializers/           # JSON serialization helpers
│   ├── Commands/              # Rhino command definitions
│   └── *.cs files             # Plugin core files
├── rhino_mcp_server/          # Python MCP server
│   ├── src/rhinomcp/          # Server code
│   │   ├── tools/             # MCP tool implementations
│   │   └── server.py          # Main server
│   ├── dev/                   # Development and example scripts
│   │   ├── dev_artwork.py     # Artwork generation example
│   │   ├── dev_castle.py      # Castle building example
│   │   └── dev_test.py        # Basic testing script
│   └── *.py files             # Server utilities
├── learning/                  # AI learning data
│   └── learning_data.json     # Structured object data
├── assets/                    # Images and demos
├── demo_chats/                # Example conversations
└── *.md files                 # Documentation
```

## Pull request checklist

- Run local checks before committing:
  - Start plugin (`mcpstart`) and MCP server (`uv run python -m rhinomcp`)
  - Exercise critical tools (e.g., `get_document_info`, create/modify/delete)
- Keep tool parameter names stable and documented.
- Update this `AGENTS.md` and `README_MCP.md` for any new tools or parameters.

## Functional status log

- See `FUNCTIONAL_STATUS.md` for a running log of what works, known problems, and solutions.
- How to use:
  - When adding or validating features, add a WORKS entry (ID `W-####`).
  - When observing failures or flaky behavior, add a PROBLEM entry (ID `P-####`) with repro steps.
  - When implementing fixes, add a SOLUTION entry (ID `S-####`) and link it to the problem.
  - Keep the Status board sections up to date (Works well / Flaky / Broken) for quick triage.

## Analysis log

- See `ANALYSIS_LOG.md` for the DWG/DXF 2D analysis workflow, property schema, heuristics, and append template.
- How to use:
  - For each analyzed drawing, append a new case study using the provided template.
  - Export properties JSON and optional preview image; record paths in the log.
  - Capture learnings (rules/regex/layer maps) and uncertainties for future iterations.

## Ralph workflow

Ralph is a structured development workflow for systematic, iterative improvements. It breaks large features into small user stories that fit within a single AI context window.

- See `Ralph/README.md` for the full workflow documentation.
- See `Ralph/progress.txt` for codebase patterns, learnings, and gotchas.

### How to use Ralph

1. **Create a PRD**: Define user stories in `Ralph/prd.json` (see `prd.json.example`)
2. **Work iteratively**: Pick highest priority story where `passes: false`
3. **Implement in small steps**: One story per iteration
4. **Document learnings**: Update `Ralph/progress.txt` after each story
5. **Mark complete**: Set `passes: true` in `prd.json`

### Key principles

- **Small tasks**: Each story should complete in one context window
- **Read progress.txt first**: Contains SACRED codebase patterns
- **Update AGENTS.md**: Add discovered patterns for future iterations
- **Commit often**: Atomic commits with clear messages

### Ralph files

| File | Purpose |
|------|---------|
| `Ralph/prd.json` | User stories with status |
| `Ralph/progress.txt` | Learnings and patterns |
| `Ralph/scripts/ralph/prompt.md` | AI agent instructions |

