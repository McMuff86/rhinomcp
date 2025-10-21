from mcp.server.fastmcp import Context
from typing import List, Optional
from rhinomcp.server import get_rhino_connection, mcp, logger

@mcp.tool()
def create_material(ctx: Context, name: str, color: List[int], shine: Optional[float] = 0.5) -> str:
    """Create a new Rhino render material."""
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("create_material", {"name": name, "color": color, "shine": shine})
        return f"Created material: {result['message']}"
    except Exception as e:
        logger.error(f"Error creating material: {str(e)}")
        return f"Error: {str(e)}"
