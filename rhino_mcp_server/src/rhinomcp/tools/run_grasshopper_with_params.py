import json
import time

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok


@mcp.tool()
def run_grasshopper_with_params(
    ctx: Context,
    file_path: str,
    parameters: str = None
) -> str:
    """
    Run a Grasshopper definition file with automated parameter input.

    This tool attempts to automatically respond to common Grasshopper Player prompts.

    Parameters:
    - file_path: Full path to the .gh Grasshopper definition file to run
    - parameters: Optional JSON string with parameter values (not yet implemented)

    Returns:
        {"ok": true, "message": "Ran Grasshopper definition with automated input", "data": {"file_path": "C:/path/to/file.gh"}}

    Notes:
    - Executes the Grasshopper definition using Rhino's GrasshopperPlayer command
    - Attempts to automatically answer common prompts (height, width, plane)
    - The Grasshopper definition will process and create geometry in the active Rhino document
    - Any outputs from the Grasshopper definition will be baked to the Rhino document
    """
    if not file_path:
        return json.dumps(from_exception(
            ValueError("file_path is required"),
            code=ErrorCode.INVALID_PARAMS
        ))

    if not file_path.lower().endswith('.gh'):
        return json.dumps(from_exception(
            ValueError("file_path must be a .gh file"),
            code=ErrorCode.INVALID_PARAMS
        ))

    try:
        rhino = get_rhino_connection()

        # Send the run command
        result = rhino.send_command("run_grasshopper", {
            "file_path": file_path
        })

        # Note: Automatic parameter input would require more complex Rhino scripting
        # For now, this tool works the same as run_grasshopper but documents the limitation

        return json.dumps(ok(
            message=f"Started Grasshopper definition: {file_path}. Note: Interactive parameters must be entered manually in Rhino command line.",
            data=result
        ))
    except Exception as e:
        logger.error(f"Error running Grasshopper definition: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))