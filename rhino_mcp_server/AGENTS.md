# Python MCP Server - Agent Instructions

> Context-specific guide for AI agents working on the Python MCP server component.
> For the full RhinoMCP guide, see [../AGENTS.md](../AGENTS.md).

## Quick Reference

| Item | Value |
|------|-------|
| **Language** | Python 3.10+ |
| **Framework** | FastMCP |
| **Location** | `rhino_mcp_server/src/rhinomcp/` |
| **Tests** | `rhino_mcp_server/tests/` (155 tests) |
| **Entry Point** | `rhinomcp.server:main` |

---

## Directory Structure

```
rhino_mcp_server/
├── src/rhinomcp/
│   ├── __init__.py          # Package exports
│   ├── server.py            # Main server + RhinoConnection
│   ├── tools/               # MCP tool implementations (45+ files)
│   │   ├── create_object.py
│   │   ├── modify_object.py
│   │   ├── boolean_operation.py
│   │   └── ...
│   ├── utils/
│   │   ├── responses.py     # ok(), from_exception() helpers
│   │   ├── errors.py        # ErrorCode enum
│   │   └── interaction_logger.py  # ML training data logger
│   ├── prompts/             # Prompt templates
│   └── static/              # RhinoScript reference data
├── tests/                   # Pytest test suite
├── dev/                     # Development scripts
└── pyproject.toml           # Package configuration
```

---

## Response Format (SACRED)

**ALL MCP tools MUST return JSON via helper functions:**

```python
from rhinomcp.utils.responses import ok, from_exception
from rhinomcp.utils.errors import ErrorCode
import json

@mcp.tool()
def my_tool(ctx: Context, param: str) -> str:
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("my_command", {"param": param})
        return json.dumps(ok(
            message=f"Success: {param}",
            data=result
        ))
    except Exception as e:
        logger.error(f"Error: {e}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))
```

**Never return plain strings!** Always use `ok()` or `from_exception()`.

---

## Adding New Tools

### 1. Create Tool File

```python
# src/rhinomcp/tools/my_new_tool.py
from mcp.server.fastmcp import Context
import json
from rhinomcp.server import get_rhino_connection, mcp, logger
from rhinomcp.utils.responses import ok, from_exception
from rhinomcp.utils.errors import ErrorCode
from typing import Literal, Optional

ToolType = Literal["option1", "option2"]  # Use Literal for enums

@mcp.tool()
def my_new_tool(
    ctx: Context, 
    required_param: str,
    optional_param: Optional[int] = None
) -> str:
    """
    Tool description for AI agents.
    
    Parameters:
    - required_param: Description of param
    - optional_param: Description (default: None)
    
    Returns:
        {"success": true, "message": "...", "data": {...}}
    """
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("my_command", {
            "required_param": required_param,
            "optional_param": optional_param
        })
        return json.dumps(ok(message="Success", data=result))
    except Exception as e:
        logger.error(f"Error: {e}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))
```

### 2. Export in __init__.py

```python
# Add to src/rhinomcp/__init__.py
from .tools.my_new_tool import my_new_tool
```

### 3. Add Tests

```python
# tests/test_my_new_tool.py
import pytest

class TestMyNewTool:
    def test_basic_functionality(self):
        # Test implementation
        pass
    
    def test_error_handling(self):
        # Test error cases
        pass
```

### 4. Register C# Handler

The Python tool sends commands to C# - make sure the handler exists in `rhino_mcp_plugin/`.

---

## Error Codes

Use appropriate error codes from `rhinomcp.utils.errors`:

| Code | Use Case |
|------|----------|
| `CONNECTION_ERROR` | General connection issues |
| `CONNECTION_TIMEOUT` | Socket timeout |
| `CONNECTION_REFUSED` | Rhino not running |
| `INVALID_PARAMS` | Bad input parameters |
| `RHINO_ERROR` | Error from Rhino |
| `CREATE_OBJECT_ERROR` | Object creation failed |

---

## Testing

```bash
# Run all tests
cd rhino_mcp_server
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_create_object.py -v

# Run with coverage
uv run pytest tests/ --cov=src/rhinomcp
```

---

## Key Patterns

### 1. Use Literal Types for Enums
```python
ObjectType = Literal["POINT", "LINE", "BOX", "SPHERE", ...]
```

### 2. Avoid Mutable Defaults
```python
# ❌ BAD
def tool(params: Dict = {}): ...

# ✅ GOOD
def tool(params: Optional[Dict] = None):
    params = params if params is not None else {}
```

### 3. Log Errors with Context
```python
logger.error(f"Error in {tool_name}: {str(e)}")
```

---

## See Also

- [Root AGENTS.md](../AGENTS.md) - Full agent guide
- [MCP_TOOL_STANDARDS.md](../MCP_TOOL_STANDARDS.md) - Tool standards
- [Ralph/progress.txt](../Ralph/progress.txt) - Session learnings
