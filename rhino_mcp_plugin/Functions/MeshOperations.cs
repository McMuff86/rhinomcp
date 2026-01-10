using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Import mesh geometry from external file formats.
    /// </summary>
    public JObject ImportMesh(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;

        string filePath = parameters["file_path"]?.ToString();
        if (string.IsNullOrEmpty(filePath))
            throw new ArgumentException("file_path is required");

        if (!File.Exists(filePath))
            throw new FileNotFoundException($"File not found: {filePath}");

        string format = parameters["format"]?.ToString()?.ToUpper();
        if (string.IsNullOrEmpty(format))
            throw new ArgumentException("format is required");

        string importMode = parameters["import_mode"]?.ToString()?.ToLower() ?? "merge";

        // Validate format
        string[] supportedFormats = { "OBJ", "STL", "3MF", "PLY", "OFF", "3DS", "FBX" };
        if (!supportedFormats.Contains(format))
            throw new ArgumentException($"Unsupported format: {format}");

        // Build import command
        string importCommand = format switch
        {
            "OBJ" => $"_-Import \"{filePath}\" _Enter",
            "STL" => $"_-Import \"{filePath}\" _Enter",
            "3MF" => $"_-Import \"{filePath}\" _Enter",
            "PLY" => $"_-Import \"{filePath}\" _Enter",
            "OFF" => $"_-Import \"{filePath}\" _Enter",
            "3DS" => $"_-Import \"{filePath}\" _Enter",
            "FBX" => $"_-Import \"{filePath}\" _Enter",
            _ => throw new ArgumentException($"Unsupported format: {format}")
        };

        // Handle import mode
        if (importMode == "replace")
        {
            // For replace mode, close current document and create new one first
            string closeCommand = "_-Close _No _Enter";
            RhinoApp.RunScript(closeCommand, false);
            // Create new document
            string newCommand = "_-New _Enter";
            RhinoApp.RunScript(newCommand, false);
        }

        bool success = RhinoApp.RunScript(importCommand, false);

        if (!success)
            throw new InvalidOperationException($"Failed to import {format} file: {filePath}");

        // Get count of imported objects
        int importedCount = doc.Objects.Count;

        return JObject.FromObject(new
        {
            file_path = filePath,
            format = format,
            import_mode = importMode,
            objects_imported = importedCount,
            status = "imported"
        });
    }

    /// <summary>
    /// Export mesh geometry to external file formats.
    /// </summary>
    public JObject ExportMesh(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;

        string filePath = parameters["file_path"]?.ToString();
        if (string.IsNullOrEmpty(filePath))
            throw new ArgumentException("file_path is required");

        string format = parameters["format"]?.ToString()?.ToUpper();
        if (string.IsNullOrEmpty(format))
            throw new ArgumentException("format is required");

        // Get object IDs if specified
        var objectIdsToken = parameters["object_ids"];
        List<Guid> objectGuids = new List<Guid>();

        if (objectIdsToken != null)
        {
            var objectIdStrings = objectIdsToken.ToObject<string[]>();
            if (objectIdStrings != null)
            {
                foreach (string idStr in objectIdStrings)
                {
                    if (Guid.TryParse(idStr, out Guid guid))
                    {
                        objectGuids.Add(guid);
                    }
                }
            }
        }

        // Ensure directory exists
        string directory = Path.GetDirectoryName(filePath);
        if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
        {
            Directory.CreateDirectory(directory);
        }

        // Select objects for export
        int objectCount;
        if (objectGuids.Count > 0)
        {
            // Select only specified objects
            doc.Objects.UnselectAll();
            foreach (Guid guid in objectGuids)
            {
                RhinoObject obj = doc.Objects.FindId(guid);
                if (obj != null)
                {
                    obj.Select(true);
                }
            }
            objectCount = objectGuids.Count;
        }
        else
        {
            // Select all objects
            doc.Objects.UnselectAll();
            foreach (RhinoObject obj in doc.Objects)
            {
                if (!obj.IsDeleted && obj.IsSelectable())
                {
                    obj.Select(true);
                }
            }
            objectCount = doc.Objects.GetSelectedObjects(false, false).Count();
        }

        // Build export command based on format
        string exportCommand = format switch
        {
            // OBJ: Geometry only, with mesh export options
            "OBJ" => $"_-Export \"{filePath}\" _GeometryOnly=Yes _EndOfLine=LF _ExportMeshes=Yes _ExportNurbsCurves=No _Enter",
            // STL: Binary format with mesh export
            "STL" => $"_-Export \"{filePath}\" _ExportFileType=Binary _ExportMeshes=Yes _Enter",
            // 3MF: Mesh focused format
            "3MF" => $"_-Export \"{filePath}\" _ExportMeshes=Yes _Enter",
            // PLY: Point cloud and mesh format
            "PLY" => $"_-Export \"{filePath}\" _Enter",
            // OFF: Mesh format
            "OFF" => $"_-Export \"{filePath}\" _Enter",
            // 3DS: Legacy 3D format
            "3DS" => $"_-Export \"{filePath}\" _Enter",
            // FBX: Game engine format with mesh options
            "FBX" => $"_-Export \"{filePath}\" _Enter _Enter _Enter",
            _ => throw new ArgumentException($"Unsupported mesh format: {format}")
        };

        bool success = RhinoApp.RunScript(exportCommand, false);

        // Deselect all after export
        doc.Objects.UnselectAll();
        doc.Views.Redraw();

        if (!success)
            throw new InvalidOperationException($"Failed to export to {format}");

        return JObject.FromObject(new
        {
            file_path = filePath,
            format = format,
            object_count = objectCount,
            status = "exported"
        });
    }

    /// <summary>
    /// Convert Brep (solid) geometry to mesh representation.
    /// </summary>
    public JObject MeshFromBrep(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;

        // Get object IDs
        var objectIdsToken = parameters["object_ids"];
        if (objectIdsToken == null)
            throw new ArgumentException("object_ids is required");

        var objectIdStrings = objectIdsToken.ToObject<string[]>();
        if (objectIdStrings == null || objectIdStrings.Length == 0)
            throw new ArgumentException("At least one object_id is required");

        string density = parameters["density"]?.ToString()?.ToLower() ?? "normal";
        string quality = parameters["quality"]?.ToString()?.ToLower() ?? "normal";
        double? maxEdgeLength = parameters["max_edge_length"]?.Value<double>();
        double? minEdgeLength = parameters["min_edge_length"]?.Value<double>();

        List<Guid> sourceGuids = new List<Guid>();
        List<Guid> meshGuids = new List<Guid>();

        // Parse object IDs and validate they exist
        foreach (string idStr in objectIdStrings)
        {
            if (Guid.TryParse(idStr, out Guid guid))
            {
                RhinoObject obj = doc.Objects.FindId(guid);
                if (obj != null && (obj.Geometry is Brep || obj.Geometry is Extrusion))
                {
                    sourceGuids.Add(guid);
                }
            }
        }

        if (sourceGuids.Count == 0)
            throw new ArgumentException("No valid Brep objects found");

        // Select source objects
        doc.Objects.UnselectAll();
        foreach (Guid guid in sourceGuids)
        {
            RhinoObject obj = doc.Objects.FindId(guid);
            if (obj != null)
            {
                obj.Select(true);
            }
        }

        // Set mesh parameters based on density
        string meshCommand = density switch
        {
            "coarse" => "_-Mesh _JaggedSeams=No _Refine=No _SimplePlanes=No _DeleteInput=Yes _Enter",
            "normal" => "_-Mesh _JaggedSeams=No _Refine=Yes _SimplePlanes=No _DeleteInput=Yes _Enter",
            "fine" => "_-Mesh _JaggedSeams=No _Refine=Yes _SimplePlanes=Yes _DeleteInput=Yes _Enter",
            "extra_fine" => "_-Mesh _JaggedSeams=No _Refine=Yes _SimplePlanes=Yes _DeleteInput=Yes _Enter _Enter",
            _ => "_-Mesh _JaggedSeams=No _Refine=Yes _SimplePlanes=No _DeleteInput=Yes _Enter"
        };

        // Apply custom edge length constraints if specified
        if (maxEdgeLength.HasValue || minEdgeLength.HasValue)
        {
            // For custom constraints, use detailed mesh settings
            string customSettings = "";
            if (maxEdgeLength.HasValue)
                customSettings += $"_MaximumEdgeLength={maxEdgeLength.Value} ";
            if (minEdgeLength.HasValue)
                customSettings += $"_MinimumEdgeLength={minEdgeLength.Value} ";

            meshCommand = $"_-Mesh {customSettings}_JaggedSeams=No _Refine=Yes _SimplePlanes=No _DeleteInput=Yes _Enter";
        }

        bool success = RhinoApp.RunScript(meshCommand, false);

        if (!success)
            throw new InvalidOperationException("Failed to convert Brep to mesh");

        // Get the newly created mesh objects (they should be selected after the command)
        var selectedObjects = doc.Objects.GetSelectedObjects(true, false);
        foreach (RhinoObject obj in selectedObjects)
        {
            if (obj.Geometry is Mesh)
            {
                meshGuids.Add(obj.Id);
            }
        }

        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            source_object_count = sourceGuids.Count,
            mesh_object_count = meshGuids.Count,
            mesh_object_ids = meshGuids.Select(g => g.ToString()).ToArray(),
            density = density,
            quality = quality,
            max_edge_length = maxEdgeLength,
            min_edge_length = minEdgeLength,
            status = "converted"
        });
    }
}