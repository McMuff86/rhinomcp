# RhinoMCP Future Issues

## Issue: Automatic MCP Plugin Start

**Priority:** Medium
**Status:** Open
**Created:** 2026-01-10
**Related:** US-C02 Viewport Control Implementation

### Description
The MCP plugin currently does not start automatically when Rhino launches, despite implementing `OnLoad` and `OnShutdown` methods in `RhinoMCPPlugin.cs`.

### Current State
- Plugin loads on Rhino startup (confirmed)
- `OnLoad` method is called (confirmed by logs)
- Server creation works (confirmed)
- Server.Start() is called (confirmed)
- But MCP commands still return "Unknown command type" errors

### Root Cause Analysis
The issue appears to be that while the plugin loads and attempts to start the server, the server is not properly registered or accessible through the expected TCP connection.

### Investigation Steps
1. Verify server thread creation and startup
2. Check TCP listener binding and port availability
3. Test server availability immediately after plugin load
4. Check for race conditions between plugin load and server startup

### Workaround
Users must manually run `mcpstart` in Rhino command line after startup.

### Acceptance Criteria
- MCP server starts automatically when Rhino loads
- No manual `mcpstart` command needed
- All MCP tools work immediately after Rhino startup
- Server status shows as "running" in MCPStatus command

### Technical Notes
- Implemented in `rhino_mcp_plugin/rhinomcpPlugin.cs`
- Uses `Task.Run()` for background server startup
- Server configured for `127.0.0.1:1999`
- Related code in `RhinoMCPServerController.cs`