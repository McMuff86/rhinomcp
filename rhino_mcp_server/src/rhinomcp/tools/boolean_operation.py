import json
from typing import List, Literal

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok

BooleanOperationType = Literal["union", "difference", "intersection"]

@mcp.tool()
def boolean_operation(
    ctx: Context,
    operation: BooleanOperationType,
    object_ids: List[str],
    delete_input: bool = True
) -> str:
    """
    Perform a boolean operation on solid objects.
    
    Parameters:
    - operation: The boolean operation type: "union", "difference", or "intersection"
    - object_ids: List of object GUIDs to operate on (minimum 2 objects)
    - delete_input: If True (default), delete the input objects after operation
    
    Returns:
    - For UNION/INTERSECTION: New object ID of the resulting solid
    - For DIFFERENCE: First object is the base, remaining objects are subtracted from it
    
    Notes:
    - All objects must be closed solids (Breps)
    - For DIFFERENCE, the first object_id is the base from which others are subtracted
    """
    try:
        rhino = get_rhino_connection()
        
        operation_upper = operation.upper()
        if operation_upper not in ["UNION", "DIFFERENCE", "INTERSECTION"]:
            return json.dumps(from_exception(
                ValueError(f"Invalid operation '{operation}'. Must be 'union', 'difference', or 'intersection'"),
                code=ErrorCode.INVALID_PARAMS
            ))
        
        if len(object_ids) < 2:
            return json.dumps(from_exception(
                ValueError("At least 2 object IDs are required for boolean operations"),
                code=ErrorCode.INVALID_PARAMS
            ))
        
        result = rhino.send_command("boolean_operation", {
            "operation": operation_upper,
            "object_ids": object_ids,
            "delete_input": delete_input
        })
        
        return json.dumps(ok(
            message=f"Boolean {operation_upper} completed",
            data=result
        ))
    except Exception as e:
        logger.error(f"Error performing boolean operation: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))
