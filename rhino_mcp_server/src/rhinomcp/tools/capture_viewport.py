import json
from typing import Optional

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok

@mcp.tool()
def capture_viewport(
    ctx: Context,
    viewport_name: str = "Perspective",
    width: int = 1920,
    height: int = 1080,
    filename: Optional[str] = None
) -> str:
    """
    Capture the current viewport as an image.

    Parameters:
    - viewport_name: Name of the viewport to capture (default: "Perspective")
    - width: Image width in pixels (default: 1920)
    - height: Image height in pixels (default: 1080)
    - filename: Optional filename to save the image (if not provided, returns base64 data)

    Returns:
    Success message with image data or file path

    Examples:
    - capture_viewport() - Capture perspective view as base64 data
    - capture_viewport(viewport_name="Top", width=1024, height=768) - Capture top view
    - capture_viewport(filename="screenshot.png") - Save to file
    """
    try:
        rhino = get_rhino_connection()

        if width <= 0 or height <= 0:
            return json.dumps(from_exception(
                ValueError("Width and height must be positive"),
                code=ErrorCode.INVALID_PARAMS
            ))

        result = rhino.send_command("capture_viewport", {
            "viewport_name": viewport_name,
            "width": width,
            "height": height,
            "filename": filename
        })

        return json.dumps(ok(
            message=f"Viewport '{viewport_name}' captured ({width}x{height})",
            data=result
        ))
    except Exception as e:
        logger.error(f"Error capturing viewport: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))