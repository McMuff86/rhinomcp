"""Rhino integration through the Model Context Protocol."""

__version__ = "0.1.0"

# Expose key classes and functions for easier imports
from .static.rhinoscriptsyntax import rhinoscriptsyntax_json
from .server import RhinoConnection, get_rhino_connection, mcp, logger

from .prompts.assert_general_strategy import asset_general_strategy

from .tools.create_object import create_object
from .tools.create_objects import create_objects
from .tools.delete_object import delete_object
from .tools.get_document_info import get_document_info
from .tools.get_object_info import get_object_info
from .tools.get_selected_objects_info import get_selected_objects_info
from .tools.modify_object import modify_object
from .tools.modify_objects import modify_objects
from .tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code
from .tools.get_rhinoscript_python_function_names import get_rhinoscript_python_function_names
from .tools.get_rhinoscript_python_code_guide import get_rhinoscript_python_code_guide
from .tools.select_objects import select_objects
from .tools.create_layer import create_layer
from .tools.get_or_set_current_layer import get_or_set_current_layer
from .tools.delete_layer import delete_layer
from .tools.create_leader import create_leader
from .tools.create_text import create_text
from .tools.create_text_dot import create_text_dot
from .tools.boolean_operation import boolean_operation
from .tools.create_material import create_material
from .tools.assign_material_to_layer import assign_material_to_layer
from .tools.ping import ping
from .tools.set_debug_mode import set_debug_mode
from .tools.log_thought import log_thought
from .tools.copy_object import copy_object
from .tools.mirror_object import mirror_object
from .tools.array_linear import array_linear
from .tools.array_polar import array_polar
from .tools.offset_curve import offset_curve
from .tools.fillet_curves import fillet_curves
from .tools.chamfer_curves import chamfer_curves
from .tools.loft_curves import loft_curves
from .tools.extrude_curve import extrude_curve
from .tools.revolve_curve import revolve_curve
from .tools.create_linear_dimension import create_linear_dimension
from .tools.create_angular_dimension import create_angular_dimension
from .tools.create_radial_dimension import create_radial_dimension