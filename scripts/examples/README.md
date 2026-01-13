# Example Scripts

> **Purpose:** Reusable example scripts demonstrating RhinoMCP patterns and workflows.

## Structure

These scripts are kept in the repository as examples and can be referenced or modified for new workflows.

## Examples

### Grasshopper Automation
- `complete_door_example.py` - Example of automating door creation with Grasshopper
- `websocket_interactive_example.py` - Example of WebSocket-based interactive script execution

### Viewport & Camera Operations
- `orbit_model_screenshots.py` - Example of creating orbit screenshots around a model

### Testing & Debugging
- `test_connection_example.py` - Example of testing MCP connection
- `check_rhino_state_example.py` - Example of checking Rhino state

## Usage

Run examples from project root:
```bash
python scripts/examples/complete_door_example.py
```

Or from examples directory:
```bash
cd scripts/examples
python complete_door_example.py
```

## Contributing

When creating reusable examples:
1. Add clear docstrings explaining the purpose
2. Include usage examples in comments
3. Document any prerequisites
4. Keep examples simple and focused
