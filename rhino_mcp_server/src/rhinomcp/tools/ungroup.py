import json
from typing import List

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok

@mcp.tool()
def ungroup(
    ctx: Context,
    group_ids: List[str] = None,
    group_id: str = None
) -> str:
    """
    Explode groups, converting grouped objects back to individual objects.

    Parameters:
    - group_ids: List of group IDs to ungroup (takes precedence if provided)
    - group_id: Single group ID to ungroup (alternative to group_ids)

    Returns:
        {"ok": true, "message": "Ungrouped 2 groups, released 6 objects", "data": {"groups_ungrouped": 2, "objects_released": 6}}

    Note:
    - Either group_ids or group_id must be provided
    - Group IDs must exist in the document
    - Objects will retain their original properties and layers
    """
    try:
        if not group_ids and not group_id:
            raise ValueError("Either group_ids or group_id must be provided")

        target_group_ids = group_ids if group_ids else [group_id]

        rhino = get_rhino_connection()
        result = rhino.send_command("ungroup", {
            "group_ids": target_group_ids
        })

        groups_count = len(target_group_ids)
        objects_count = result["objects_released"]
        message = f"Ungrouped {groups_count} groups, released {objects_count} objects"

        return json.dumps(ok(
            message=message,
            data={
                "groups_ungrouped": groups_count,
                "objects_released": objects_count
            }
        ))
    except Exception as e:
        logger.error(f"Error ungrouping: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))