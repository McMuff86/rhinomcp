using System;

namespace RhinoMCPPlugin
{
    /// <summary>
    /// Structured error codes for RhinoMCP C# plugin.
    /// Mirrors the Python ErrorCode class for consistent error handling.
    /// </summary>
    public static class ErrorCode
    {
        // Connection errors
        public const string CONNECTION_ERROR = "CONNECTION_ERROR";
        public const string CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT";
        public const string CONNECTION_REFUSED = "CONNECTION_REFUSED";

        // Validation errors
        public const string INVALID_PARAMS = "INVALID_PARAMS";
        public const string MISSING_PARAMS = "MISSING_PARAMS";
        public const string INVALID_TYPE = "INVALID_TYPE";
        public const string INVALID_ID = "INVALID_ID";

        // Rhino errors
        public const string RHINO_ERROR = "RHINO_ERROR";
        public const string RHINO_COMMAND_FAILED = "RHINO_COMMAND_FAILED";
        public const string RHINO_OBJECT_NOT_FOUND = "RHINO_OBJECT_NOT_FOUND";
        public const string RHINO_LAYER_NOT_FOUND = "RHINO_LAYER_NOT_FOUND";
        public const string RHINO_MATERIAL_NOT_FOUND = "RHINO_MATERIAL_NOT_FOUND";

        // Document errors
        public const string DOC_INFO_ERROR = "DOC_INFO_ERROR";
        public const string DOC_NOT_OPEN = "DOC_NOT_OPEN";

        // Script execution errors
        public const string SCRIPT_ERROR = "SCRIPT_ERROR";
        public const string SCRIPT_TIMEOUT = "SCRIPT_TIMEOUT";

        // Object operation errors
        public const string CREATE_OBJECT_ERROR = "CREATE_OBJECT_ERROR";
        public const string MODIFY_OBJECT_ERROR = "MODIFY_OBJECT_ERROR";
        public const string DELETE_OBJECT_ERROR = "DELETE_OBJECT_ERROR";
        public const string SELECT_OBJECT_ERROR = "SELECT_OBJECT_ERROR";

        // Layer operation errors
        public const string CREATE_LAYER_ERROR = "CREATE_LAYER_ERROR";
        public const string DELETE_LAYER_ERROR = "DELETE_LAYER_ERROR";

        // Material operation errors
        public const string CREATE_MATERIAL_ERROR = "CREATE_MATERIAL_ERROR";
        public const string ASSIGN_MATERIAL_ERROR = "ASSIGN_MATERIAL_ERROR";

        // Boolean operation errors
        public const string BOOLEAN_OPERATION_ERROR = "BOOLEAN_OPERATION_ERROR";

        // Transform operation errors
        public const string TRANSFORM_ERROR = "TRANSFORM_ERROR";

        // Curve operation errors
        public const string CURVE_OPERATION_ERROR = "CURVE_OPERATION_ERROR";

        // Surface operation errors
        public const string SURFACE_OPERATION_ERROR = "SURFACE_OPERATION_ERROR";

        // Dimension operation errors
        public const string DIMENSION_ERROR = "DIMENSION_ERROR";

        // File operation errors
        public const string FILE_OPERATION_ERROR = "FILE_OPERATION_ERROR";

        // Generic errors
        public const string UNKNOWN_ERROR = "UNKNOWN_ERROR";
        public const string INTERNAL_ERROR = "INTERNAL_ERROR";
        public const string UNKNOWN_COMMAND = "UNKNOWN_COMMAND";

        /// <summary>
        /// Determine error code based on exception type and context.
        /// </summary>
        public static string FromException(Exception ex, string context = null)
        {
            var message = ex.Message.ToLower();

            // Check for specific error types
            if (message.Contains("object not found") || message.Contains("could not find object"))
                return RHINO_OBJECT_NOT_FOUND;
            if (message.Contains("layer not found") || message.Contains("could not find layer"))
                return RHINO_LAYER_NOT_FOUND;
            if (message.Contains("material not found"))
                return RHINO_MATERIAL_NOT_FOUND;
            if (message.Contains("invalid parameter") || message.Contains("is required"))
                return INVALID_PARAMS;
            if (message.Contains("timeout"))
                return SCRIPT_TIMEOUT;

            // Use context-based defaults
            if (!string.IsNullOrEmpty(context))
            {
                if (context.Contains("boolean"))
                    return BOOLEAN_OPERATION_ERROR;
                if (context.Contains("transform") || context.Contains("copy") || context.Contains("mirror") || context.Contains("array"))
                    return TRANSFORM_ERROR;
                if (context.Contains("curve") || context.Contains("offset") || context.Contains("fillet") || context.Contains("chamfer"))
                    return CURVE_OPERATION_ERROR;
                if (context.Contains("surface") || context.Contains("loft") || context.Contains("extrude") || context.Contains("revolve"))
                    return SURFACE_OPERATION_ERROR;
                if (context.Contains("dimension"))
                    return DIMENSION_ERROR;
                if (context.Contains("file") || context.Contains("open") || context.Contains("save") || context.Contains("export"))
                    return FILE_OPERATION_ERROR;
                if (context.Contains("create_object"))
                    return CREATE_OBJECT_ERROR;
                if (context.Contains("modify"))
                    return MODIFY_OBJECT_ERROR;
                if (context.Contains("delete"))
                    return DELETE_OBJECT_ERROR;
                if (context.Contains("select"))
                    return SELECT_OBJECT_ERROR;
                if (context.Contains("layer"))
                    return CREATE_LAYER_ERROR;
                if (context.Contains("material"))
                    return CREATE_MATERIAL_ERROR;
            }

            return RHINO_ERROR;
        }
    }
}
