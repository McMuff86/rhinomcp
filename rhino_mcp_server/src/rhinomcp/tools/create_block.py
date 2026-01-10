import json
from typing import List

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok

@mcp.tool()
def create_block(
    ctx: Context,
    object_ids: List[str],
    name: str,
    base_point: List[float] = None
) -> str:
    """
    Create a block definition from the specified objects.

    Parameters:
    - object_ids: List of object IDs to include in the block
    - name: Name for the block definition
    - base_point: Optional base point [x, y, z] for the block (default: [0, 0, 0])

    Returns:
        {"ok": true, "message": "Created block 'MyBlock' with 3 objects", "data": {"block_id": "block_guid", "name": "MyBlock", "object_count": 3, "base_point": [0,0,0]}}

    Note:
    - Objects must exist in the document
    - Block definitions are stored in the document and can be reused
    - Objects in the block will be removed from the document and stored in the block definition
    - Use insert_block to place instances of the block
    """
    try:
        if not object_ids or len(object_ids) == 0:
            raise ValueError("object_ids cannot be empty")

        if not name or name.strip() == "":
            raise ValueError("name cannot be empty")

        if base_point is None:
            base_point = [0.0, 0.0, 0.0]

        if len(base_point) != 3:
            raise ValueError("base_point must be [x, y, z]")

        rhino = get_rhino_connection()
        result = rhino.send_command("create_block", {
            "object_ids": object_ids,
            "name": name,
            "base_point": base_point
        })

        object_count = len(object_ids)
        message = f"Created block '{name}' with {object_count} objects"

        return json.dumps(ok(
            message=message,
            data={
                "block_id": result["block_id"],
                "name": name,
                "object_count": object_count,
                "base_point": base_point
            }
        ))
    except Exception as e:
        logger.error(f"Error creating block: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))