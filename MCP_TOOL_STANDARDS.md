# MCP Tool Standards and Template

This document defines standards for Python MCP tools and the C# handlers to keep the system consistent and AI-friendly.

## Return Format

- Prefer stable, structured responses. On errors, include a machine-readable `code`.
- Python helper utilities are provided in `rhinomcp/utils/responses.py`.

Shapes:

- Success: `{ "success": true, "message": "...", "data": <any> }`
- Error: `{ "success": false, "message": "...", "code": "SOME_CODE", "data"?: <any> }`

Tools that naturally return strings to be shown to users can still return a plain string. For programmatic chaining, prefer structured dicts.

## Logging

- Use `logger` from `rhinomcp.server`.
- Log the high-level operation and parameters (sanitized). Log concise error summaries.

## Exceptions

- Validate inputs. Raise meaningful errors in C# for invalid geometry or states; Python should convert exceptions to error responses using `from_exception`.

## Naming

- Modules and command names: lower_snake_case verbs first: `create_object`, `modify_objects`.
- Parameters: explicit and typed. Colors `[r, g, b]` (0–255). Points `[x, y, z]`. IDs are GUID strings.

## Template (Python)

```python
from mcp.server.fastmcp import Context
from typing import Any, Dict, List, Optional
from rhinomcp import get_rhino_connection, mcp, logger
from rhinomcp.utils.responses import ok, from_exception

@mcp.tool()
def my_tool(ctx: Context, name: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Describe what this tool does and how to use it."""
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("my_tool", {"name": name, "options": options or {}})
        return ok(message=f"Did thing for {name}", data=result)
    except Exception as e:
        logger.error(f"Error in my_tool: {str(e)}")
        return from_exception(e, code="MY_TOOL_ERROR")
```

## C# Handlers

- Run operations within an UndoRecord. Update views after geometry changes.
- Return compact, stable JSON via `JObject` and `Serializer` helpers.
- Map handlers in `RhinoMCPServer.ExecuteCommandInternal` with the same command name.

## Testing

- Add minimal smoke tests for tools that serialize/deserialize, and for failure paths.
- Prefer idempotent operations for tests where possible.
