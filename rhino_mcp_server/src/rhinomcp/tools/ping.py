from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger

@mcp.tool()
def ping(ctx: Context) -> str:
    """Send a ping to the Rhino plugin to check connectivity."""
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("ping", {})
        return f"Pong from Rhino at {result['timestamp']}"
    except Exception as e:
        logger.error(f"Error in ping: {str(e)}")
        return f"Error: {str(e)}"
