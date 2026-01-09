# RhinoMCP Server

Python MCP server that connects AI agents to Rhino 3D via the Model Context Protocol.

## Overview

This server bridges AI agents (Claude, Cursor, etc.) to Rhino through:
- **FastMCP**: Python MCP implementation
- **TCP Socket**: Communication with Rhino plugin on `localhost:1999`

## Installation

```bash
# Install uv (if not already installed)
# macOS: brew install uv
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies
cd rhino_mcp_server
uv pip install -e .
```

## Usage

```bash
# Development mode
uv run python -m rhinomcp

# Or via uvx (installed)
uvx rhinomcp
```

**Note:** Start the Rhino plugin first (`mcpstart` in Rhino command line).

## Project Structure

```
rhino_mcp_server/
├── src/rhinomcp/
│   ├── server.py          # Main server, FastMCP setup
│   ├── tools/             # MCP tool implementations
│   │   ├── create_object.py
│   │   ├── modify_object.py
│   │   ├── get_document_info.py
│   │   └── ...
│   ├── utils/             # Helper utilities
│   └── prompts/           # AI prompts
├── dev/                   # Development scripts
│   ├── dev_test.py        # Basic testing
│   └── dev_castle.py      # Example: castle generation
└── pyproject.toml         # Package configuration
```

## Available Tools

| Tool | Description |
|------|-------------|
| `create_object` | Create geometry (BOX, SPHERE, CYLINDER, etc.) |
| `create_objects` | Batch create multiple objects |
| `modify_object` | Change object properties |
| `get_document_info` | Query document state |
| `get_object_info` | Get object details |
| `execute_rhinoscript_python_code` | Run Python scripts in Rhino |
| `create_layer` | Create new layers |
| `create_material` | Create render materials (PBR supported) |
| `ping` | Health check |

## Development

```bash
# Run tests
uv run python dev/dev_test.py

# Build package
uv build

# Publish to PyPI
uv publish
```

## Documentation

- [Main README](../README.md) - Installation and usage
- [AGENTS.md](../AGENTS.md) - Agent-focused guide
- [README_MCP.md](../README_MCP.md) - MCP tools guide
- [USAGE.md](../USAGE.md) - Detailed usage examples
