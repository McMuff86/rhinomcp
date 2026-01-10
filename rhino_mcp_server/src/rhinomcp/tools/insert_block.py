import json
from typing import List

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok

@mcp.tool()
def insert_block(
    ctx: Context,
    block_name: str,
    position: List[float],
    scale: List[float] = None,
    rotation: List[float] = None
) -> str:
    """
    Insert an instance of a block at the specified position.

    Parameters:
    - block_name: Name of the block definition to insert
    - position: Position [x, y, z] where to insert the block
    - scale: Optional scale factors [x, y, z] (default: [1, 1, 1])
    - rotation: Optional rotation angles [x, y, z] in radians (default: [0, 0, 0])

    Returns:
        {"ok": true, "message": "Inserted block 'MyBlock' at [10, 0, 0]", "data": {"instance_id": "instance_guid", "block_name": "MyBlock", "position": [10,0,0]}}

    Note:
    - Block definition must exist (created with create_block)
    - Position is the insertion point of the block instance
    - Scale and rotation are applied relative to the block's base point
    - Each insertion creates a new instance that references the same block definition
    """
    try:
        if not block_name or block_name.strip() == "":
            raise ValueError("block_name cannot be empty")

        if len(position) != 3:
            raise ValueError("position must be [x, y, z]")

        if scale is None:
            scale = [1.0, 1.0, 1.0]
        elif len(scale) != 3:
            raise ValueError("scale must be [x, y, z]")

        if rotation is None:
            rotation = [0.0, 0.0, 0.0]
        elif len(rotation) != 3:
            raise ValueError("rotation must be [x, y, z] in radians")

        rhino = get_rhino_connection()
        result = rhino.send_command("insert_block", {
            "block_name": block_name,
            "position": position,
            "scale": scale,
            "rotation": rotation
        })

        message = f"Inserted block '{block_name}' at [{position[0]}, {position[1]}, {position[2]}]"

        return json.dumps(ok(
            message=message,
            data={
                "instance_id": result["instance_id"],
                "block_name": block_name,
                "position": position,
                "scale": scale,
                "rotation": rotation
            }
        ))
    except Exception as e:
        logger.error(f"Error inserting block: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))