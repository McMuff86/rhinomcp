import json
from typing import List

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok

@mcp.tool()
def explode_block(
    ctx: Context,
    instance_ids: List[str] = None,
    block_instance_id: str = None
) -> str:
    """
    Explode block instances, converting them back to individual objects.

    Parameters:
    - instance_ids: List of block instance IDs to explode (takes precedence if provided)
    - instance_id: Single block instance ID to explode (alternative to instance_ids)

    Returns:
        {"ok": true, "message": "Exploded 2 block instances, created 6 objects", "data": {"instances_exploded": 2, "objects_created": 6}}

    Note:
    - Either instance_ids or instance_id must be provided
    - Block instances must exist in the document
    - Block definition remains in the document for future use
    - Objects will be positioned according to the instance's transform
    """
    try:
        if not instance_ids and not block_instance_id:
            raise ValueError("Either instance_ids or block_instance_id must be provided")

        target_instance_ids = instance_ids if instance_ids else [block_instance_id]

        rhino = get_rhino_connection()
        result = rhino.send_command("explode_block", {
            "instance_ids": target_instance_ids
        })

        instances_count = len(target_instance_ids)
        objects_count = result["objects_created"]
        message = f"Exploded {instances_count} block instances, created {objects_count} objects"

        return json.dumps(ok(
            message=message,
            data={
                "instances_exploded": instances_count,
                "objects_created": objects_count
            }
        ))
    except Exception as e:
        logger.error(f"Error exploding block: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))