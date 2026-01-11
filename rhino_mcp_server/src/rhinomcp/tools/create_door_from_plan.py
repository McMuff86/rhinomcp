import json
import re

from mcp.server.fastmcp import Context

from rhinomcp.server import get_rhino_connection, logger, mcp
from rhinomcp.utils.errors import ErrorCode
from rhinomcp.utils.responses import from_exception, ok


@mcp.tool()
def create_door_from_plan(
    ctx: Context,
    plan_text: str,
    door_type: str = "standard"
) -> str:
    """
    Analyze building plan text and automatically create appropriate door geometry.

    This tool reads plan specifications and generates doors using Grasshopper automation.

    Parameters:
    - plan_text: Text description of the building plan/requirements
    - door_type: Type of door to create ("standard", "entrance", "interior", "fire")

    Returns:
        {"ok": true, "message": "Door created from plan analysis", "data": {...}}

    Notes:
    - Analyzes plan text for door specifications (dimensions, location, type)
    - Automatically generates appropriate door geometry
    - Future: OCR integration for plan image analysis
    """
    try:
        # Analyze the plan text for door specifications
        door_specs = analyze_plan_for_doors(plan_text, door_type)

        if not door_specs:
            return json.dumps(from_exception(
                ValueError("No door specifications found in plan text"),
                code=ErrorCode.INVALID_PARAMS
            ))

        # Use the automated Grasshopper tool with extracted parameters
        rhino = get_rhino_connection()

        # For now, use the existing grasshopper tool with extracted params
        # Future: Direct Grasshopper API integration
        result = rhino.send_command("run_grasshopper_with_params", {
            "file_path": r"c:\Users\Adi.Muff\repos\rhinomcp\Rahmentuer_UD3.gh",
            "height": door_specs.get("height", 2200),
            "width": door_specs.get("width", 5100),
            "plane": door_specs.get("plane", "WorldXY")
        })

        return json.dumps(ok(
            message=f"Door created from plan analysis: {door_specs.get('description', 'Unknown door')}",
            data={
                "door_specs": door_specs,
                "grasshopper_result": result
            }
        ))

    except Exception as e:
        logger.error(f"Error creating door from plan: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.RHINO_ERROR))


def analyze_plan_for_doors(plan_text: str, door_type: str = "standard") -> dict:
    """
    Extract door specifications from plan text using pattern matching.

    This is a basic implementation - future versions will use AI for better understanding.
    """
    # Convert to lowercase for easier matching
    text = plan_text.lower()

    # Default specifications based on door type
    specs = {
        "standard": {"height": 2200, "width": 910, "description": "Standard interior door 910x2200mm"},
        "entrance": {"height": 2200, "width": 1010, "description": "Entrance door 1010x2200mm"},
        "interior": {"height": 2200, "width": 810, "description": "Interior door 810x2200mm"},
        "fire": {"height": 2200, "width": 1010, "description": "Fire door 1010x2200mm"}
    }

    door_spec = specs.get(door_type, specs["standard"]).copy()

    # Try to extract dimensions from text using regex
    # Look for patterns like "2200mm x 910mm", "2200x910", etc.

    # Height patterns
    height_patterns = [
        r'(\d{3,4})\s*mm?\s*x\s*(\d{3,4})\s*mm?',  # "2200mm x 910mm"
        r'(\d{3,4})\s*x\s*(\d{3,4})',  # "2200x910"
        r'height[:\s]+(\d{3,4})',  # "height: 2200"
        r'hoehe[:\s]+(\d{3,4})',  # German "höhe: 2200"
    ]

    # Width patterns
    width_patterns = [
        r'width[:\s]+(\d{3,4})',  # "width: 910"
        r'breite[:\s]+(\d{3,4})',  # German "breite: 910"
    ]

    # Try to extract height
    for pattern in height_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if len(match.groups()) >= 2:
                    # Pattern with both dimensions
                    h1, h2 = int(match.group(1)), int(match.group(2))
                    # Assume first number is height, second is width
                    door_spec["height"] = max(h1, h2)  # Taller dimension is height
                    door_spec["width"] = min(h1, h2)   # Shorter dimension is width
                else:
                    # Single dimension (assume height)
                    door_spec["height"] = int(match.group(1))
                break
            except ValueError:
                continue

    # Try to extract width separately
    for pattern in width_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                door_spec["width"] = int(match.group(1))
                break
            except ValueError:
                continue

    # Update description with extracted dimensions
    door_spec["description"] = f"{door_type.title()} door {door_spec['width']}x{door_spec['height']}mm"

    # Determine plane based on context
    if "front" in text or "entrance" in text:
        door_spec["plane"] = "WorldXY"  # Front elevation
    elif "side" in text:
        door_spec["plane"] = "WorldYZ"  # Side elevation
    else:
        door_spec["plane"] = "WorldXY"  # Default

    return door_spec


@mcp.tool()
def generate_bill_of_materials(
    ctx: Context,
    objects_info: str
) -> str:
    """
    Generate a bill of materials from created geometry objects.

    Parameters:
    - objects_info: JSON string with object information from Rhino

    Returns:
        {"ok": true, "message": "Bill of materials generated", "data": {...}}
    """
    try:
        # Parse the objects info
        objects = json.loads(objects_info) if isinstance(objects_info, str) else objects_info

        # Simple BOM generation - future: More sophisticated analysis
        materials = analyze_materials(objects)

        return json.dumps(ok(
            message="Bill of materials generated",
            data={
                "materials": materials,
                "total_items": len(materials),
                "summary": f"Generated BOM with {len(materials)} material types"
            }
        ))

    except Exception as e:
        logger.error(f"Error generating BOM: {str(e)}")
        return json.dumps(from_exception(e, code=ErrorCode.INVALID_PARAMS))


def analyze_materials(objects: list) -> dict:
    """
    Analyze objects to determine materials and quantities.

    This is a basic implementation - future versions will use more sophisticated analysis.
    """
    materials = {}

    for obj in objects:
        obj_type = obj.get("type", "unknown")
        dimensions = obj.get("dimensions", {})

        # Simple material inference based on object type
        if "door" in obj_type.lower():
            material_key = "Door Frame"
            materials[material_key] = materials.get(material_key, 0) + 1
        elif "wall" in obj_type.lower():
            material_key = "Wall Panel"
            materials[material_key] = materials.get(material_key, 0) + 1
        elif "window" in obj_type.lower():
            material_key = "Window Frame"
            materials[material_key] = materials.get(material_key, 0) + 1
        else:
            material_key = f"Component ({obj_type})"
            materials[material_key] = materials.get(material_key, 0) + 1

    return materials