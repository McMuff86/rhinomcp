"""
Grasshopper Automated Execution Tool.

Runs Grasshopper definitions with fully automated parameter input,
eliminating the need for manual user interaction.
"""
import json
from typing import List, Optional

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok


@mcp.tool()
def run_grasshopper_automated(
    ctx: Context,
    file_path: str,
    inputs: List[str],
    initial_delay_ms: int = 1500,
    input_delay_ms: int = 300,
    timeout_ms: int = 15000
) -> str:
    """
    Run a Grasshopper definition with fully automated parameter input.

    This tool executes a Grasshopper script and automatically sends
    parameter values in sequence, eliminating manual user input.

    Parameters:
    - file_path: Full path to the .gh Grasshopper definition file
    - inputs: List of input values to send in sequence (e.g., ["2200", "910", "0"])
    - initial_delay_ms: Delay before first input (default: 1500ms)
    - input_delay_ms: Delay between inputs (default: 300ms)
    - timeout_ms: Maximum execution time (default: 15000ms)

    Returns:
        {"ok": true, "message": "Grasshopper executed with automated inputs",
         "data": {"file_path": "...", "status": "success", "inputs_sent": [...]}}

    Example - Door Generation:
        run_grasshopper_automated(
            file_path="C:/scripts/Rahmentuer_UD3.gh",
            inputs=["2200", "910", "0"],  # height, width, plane
            initial_delay_ms=1500,
            input_delay_ms=300
        )

    Example - Custom Script:
        run_grasshopper_automated(
            file_path="C:/scripts/custom.gh",
            inputs=["100", "200", "hello", "1,0,0"],
            timeout_ms=30000  # longer timeout for complex scripts
        )

    Notes:
    - The script must be designed to accept command-line inputs via GrasshopperPlayer
    - Inputs are sent in the order specified in the inputs array
    - Timing can be adjusted if script requires longer processing between inputs
    - Use 'run_grasshopper' for scripts that don't require input parameters
    """
    # Validate file_path
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

    # Validate inputs
    if not inputs or len(inputs) == 0:
        return json.dumps(from_exception(
            ValueError("inputs array is required with at least one value"),
            code=ErrorCode.INVALID_PARAMS
        ))

    # Validate timing parameters
    if initial_delay_ms < 0:
        return json.dumps(from_exception(
            ValueError("initial_delay_ms must be non-negative"),
            code=ErrorCode.INVALID_PARAMS
        ))

    if input_delay_ms < 0:
        return json.dumps(from_exception(
            ValueError("input_delay_ms must be non-negative"),
            code=ErrorCode.INVALID_PARAMS
        ))

    if timeout_ms < 1000:
        return json.dumps(from_exception(
            ValueError("timeout_ms must be at least 1000ms"),
            code=ErrorCode.INVALID_PARAMS
        ))

    try:
        rhino = get_rhino_connection()

        result = rhino.send_command("run_grasshopper_automated", {
            "file_path": file_path,
            "inputs": inputs,
            "initial_delay_ms": initial_delay_ms,
            "input_delay_ms": input_delay_ms,
            "timeout_ms": timeout_ms
        })

        status = result.get("status", "unknown")
        if status == "success":
            return json.dumps(ok(
                message=f"Grasshopper executed with {len(inputs)} automated inputs",
                data=result
            ))
        elif status == "timeout":
            return json.dumps(ok(
                message="Grasshopper automation timed out - some inputs may not have been processed",
                data=result
            ))
        else:
            return json.dumps(ok(
                message=f"Grasshopper execution completed with status: {status}",
                data=result
            ))

    except Exception as e:
        logger.error(f"Error running Grasshopper automated: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))


@mcp.tool()
def run_door_script(
    ctx: Context,
    file_path: str,
    height: int = 2200,
    width: int = 910,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    origin_z: float = 0.0
) -> str:
    """
    Run a door generation Grasshopper script with FULL automation.

    Uses GrasshopperPlayer with inline parameters for height, width, and plane origin.
    No manual input required - the door is created completely automatically.

    Parameters:
    - file_path: Full path to the door generation .gh file
    - height: Door height in mm (Lichthoehe, default: 2200)
    - width: Door width in mm (Lichtbreite, default: 910)
    - origin_x: X coordinate of plane origin (default: 0.0)
    - origin_y: Y coordinate of plane origin (default: 0.0)
    - origin_z: Z coordinate of plane origin (default: 0.0)

    Returns:
        {"success": true, "message": "Door created",
         "data": {"height": 2200, "width": 910, "origin": [0, 0, 0]}}

    Example - Door at origin:
        run_door_script(
            file_path="C:/Users/Adi.Muff/repos/rhinomcp/Rahmentuer_UD3.gh",
            height=2200,
            width=910
        )

    Example - Door at specific position:
        run_door_script(
            file_path="C:/Users/Adi.Muff/repos/rhinomcp/Rahmentuer_UD3.gh",
            height=2100,
            width=1000,
            origin_x=5000,
            origin_y=0,
            origin_z=0
        )

    Notes:
    - 100% automated - no manual input required
    - The plane origin defines where the door is placed (WorldXY at given point)
    - Command format: _-GrasshopperPlayer "path.gh" height width x y z
    """
    # Validate file_path
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

        # Format: _-GrasshopperPlayer "path" height width x y z
        # The x y z defines the plane origin (WorldXY at that point)
        code = f'''import Rhino
script = '_-GrasshopperPlayer "{file_path}" {height} {width} {origin_x} {origin_y} {origin_z}'
result = Rhino.RhinoApp.RunScript(script, False)
print("Door created: " + str(result))
'''
        
        result = rhino.send_command("execute_rhinoscript_python_code", {
            "code": code
        })

        return json.dumps(ok(
            message=f"Door created: {height}mm x {width}mm at ({origin_x}, {origin_y}, {origin_z})",
            data={
                "file_path": file_path,
                "height": height,
                "width": width,
                "origin": [origin_x, origin_y, origin_z],
                "status": "created",
                "fully_automated": True,
                "rhino_result": result
            }
        ))

    except Exception as e:
        logger.error(f"Error running door script: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))
