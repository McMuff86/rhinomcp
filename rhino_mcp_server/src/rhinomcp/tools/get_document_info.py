from mcp.server.fastmcp import Context
import json
from rhinomcp import get_rhino_connection, mcp, logger
from rhinomcp.utils.responses import ok, from_exception

@mcp.tool()
def get_document_info(ctx: Context) -> str:
    """Get detailed information about the current Rhino document"""
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("get_document_info")
        
        # Return the JSON representation of what Rhino sent us
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting document info from Rhino: {str(e)}")
        return json.dumps(from_exception(e, code="DOC_INFO_ERROR"))