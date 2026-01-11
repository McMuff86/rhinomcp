"""
Get command line output from Rhino in real-time.

This tool enables AI agents to "see" what's happening in Rhino by capturing
command line output, prompts, and interactive requests.
"""

import json
from datetime import datetime
from typing import Optional

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok


@mcp.tool()
def get_command_output(
    ctx: Context,
    count: int = 50,
    since: Optional[str] = None
) -> str:
    """
    Get recent command line output from Rhino.
    
    This tool captures Rhino's command line output, allowing AI agents to:
    - See when Rhino prompts for user input
    - Monitor script execution progress
    - Detect interactive requests (e.g., "GetPlane ( WorldXY WorldYZ WorldZX )")
    - Track what's happening during long-running operations
    
    Args:
        ctx: MCP context
        count: Number of recent events to return (default: 50, max: 200)
        since: Optional ISO timestamp - only return events after this time
               Format: "2026-01-11 12:34:56.789"
    
    Returns:
        JSON string with command line events:
        {
            "status": "success",
            "data": {
                "events": [
                    {
                        "timestamp": "2026-01-11 12:34:56.789",
                        "text": "GetPlane ( WorldXY WorldYZ WorldZX Undo )",
                        "type": "Prompt"  # or "History"
                    },
                    ...
                ],
                "count": 5,
                "current_prompt": "Command: "
            }
        }
    
    Example:
        # Get last 20 events
        get_command_output(count=20)
        
        # Get events since specific time
        get_command_output(since="2026-01-11 12:30:00.000")
    
    Notes:
        - Uses polling to capture command line state changes
        - Look for event.type == "Prompt" to detect interactive requests
        - The current_prompt field shows what Rhino is currently asking for
    """
    try:
        # Validate count
        count = max(1, min(count, 200))
        
        rhino = get_rhino_connection()
        result = rhino.send_command("get_command_output", {
            "count": count,
            "since": since
        })
        
        logger.info(f"Retrieved {result.get('count', 0)} command output events")
        return json.dumps(ok(
            message=f"Retrieved {result.get('count', 0)} command line events",
            data=result
        ))
        
    except Exception as e:
        logger.error(f"Failed to get command output: {e}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))


@mcp.tool()
def clear_command_output(ctx: Context) -> str:
    """
    Clear the command line output buffer.
    
    Useful to start fresh before running a specific operation.
    
    Returns:
        JSON string with status
    
    Example:
        # Clear buffer before starting operation
        clear_command_output()
        
        # Run operation
        run_grasshopper(file_path="script.gh")
        
        # Check what happened
        events = get_command_output(count=50)
    """
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("clear_command_output", {})
        
        logger.info("Command output buffer cleared")
        return json.dumps(ok(
            message="Command output buffer cleared",
            data=result
        ))
        
    except Exception as e:
        logger.error(f"Failed to clear command output: {e}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))

