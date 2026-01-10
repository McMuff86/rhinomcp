# MCP Tool Standards and Template

This document defines standards for Python MCP tools and the C# handlers to keep the system consistent and AI-friendly.

## Return Format

- Prefer stable, structured responses. On errors, include a machine-readable `code`.
- Python helper utilities are provided in `rhinomcp/utils/responses.py`.

Shapes:

- Success: `{ "success": true, "message": "...", "data": <any> }`
- Error: `{ "success": false, "message": "...", "code": "SOME_CODE", "data"?: <any> }`

Tools that naturally return strings to be shown to users can still return a plain string. For programmatic chaining, prefer structured dicts.

## Error Codes

All error codes are defined in `rhinomcp/utils/errors.py` as constants in the `ErrorCode` class.

| Category | Code | Description |
|----------|------|-------------|
| **Connection** | `CONNECTION_ERROR` | General connection failure |
| | `CONNECTION_TIMEOUT` | Connection timed out |
| | `CONNECTION_REFUSED` | Connection refused by Rhino plugin |
| **Validation** | `INVALID_PARAMS` | Invalid parameters provided |
| | `MISSING_PARAMS` | Required parameters missing |
| | `INVALID_TYPE` | Invalid object type specified |
| | `INVALID_ID` | Invalid GUID/object ID |
| **Rhino** | `RHINO_ERROR` | General Rhino error |
| | `RHINO_COMMAND_FAILED` | Command execution failed |
| | `RHINO_OBJECT_NOT_FOUND` | Object not found by ID |
| | `RHINO_LAYER_NOT_FOUND` | Layer not found |
| | `RHINO_MATERIAL_NOT_FOUND` | Material not found |
| **Document** | `DOC_INFO_ERROR` | Error retrieving document info |
| | `DOC_NOT_OPEN` | No document open |
| **Script** | `SCRIPT_ERROR` | Script execution error |
| | `SCRIPT_TIMEOUT` | Script execution timed out |
| **Objects** | `CREATE_OBJECT_ERROR` | Error creating object |
| | `MODIFY_OBJECT_ERROR` | Error modifying object |
| | `DELETE_OBJECT_ERROR` | Error deleting object |
| | `SELECT_OBJECT_ERROR` | Error selecting object |
| **Layers** | `CREATE_LAYER_ERROR` | Error creating layer |
| | `DELETE_LAYER_ERROR` | Error deleting layer |
| **Materials** | `CREATE_MATERIAL_ERROR` | Error creating material |
| | `ASSIGN_MATERIAL_ERROR` | Error assigning material |
| **Generic** | `UNKNOWN_ERROR` | Unknown/unclassified error |
| | `INTERNAL_ERROR` | Internal server error |

### Usage Example

```python
from rhinomcp.utils.responses import ok, from_exception
from rhinomcp.utils.errors import ErrorCode

# Success response
return json.dumps(ok(message="Created object", data={"id": "..."}))

# Error with explicit code
return json.dumps(from_exception(e, code=ErrorCode.CREATE_OBJECT_ERROR))

# Error with auto-detection (for connection errors)
return json.dumps(from_exception(e))  # auto_detect=True by default
```

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
