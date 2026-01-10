import json
from typing import List

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok

@mcp.tool()
def create_group(
    ctx: Context,
    object_ids: List[str],
    name: str = None
) -> str:
    """
    Create a group containing the specified objects.

    Parameters:
    - object_ids: List of object IDs to include in the group
    - name: Optional name for the group

    Returns:
        {"ok": true, "message": "Created group 'MyGroup' with 3 objects", "data": {"group_id": "group_guid", "object_count": 3}}

    Note:
    - Objects must exist in the document
    - Group will be created on the current layer
    - If name is not provided, Rhino will assign a default name
    """
    try:
        if not object_ids or len(object_ids) == 0:
            raise ValueError("object_ids cannot be empty")

        rhino = get_rhino_connection()
        result = rhino.send_command("create_group", {
            "object_ids": object_ids,
            "name": name
        })

        object_count = len(object_ids)
        group_name = result.get("name", "unnamed")
        message = f"Created group '{group_name}' with {object_count} objects"

        return json.dumps(ok(
            message=message,
            data={
                "group_id": result["group_id"],
                "name": group_name,
                "object_count": object_count
            }
        ))
    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))