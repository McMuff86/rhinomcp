using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.FileIO;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Get Rhino command history and current prompt.
    /// </summary>
    public JObject GetCommandHistory(JObject parameters)
    {
        int lines = parameters["lines"]?.Value<int>() ?? 20;
        lines = Math.Max(1, Math.Min(lines, 100));
        
        // Get command history text
        string historyText = RhinoApp.CommandHistoryWindowText ?? "";
        
        // Split into lines and take last N
        string[] allLines = historyText.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
        int startIndex = Math.Max(0, allLines.Length - lines);
        string[] recentLines = allLines.Skip(startIndex).ToArray();
        
        // Get current command prompt
        string currentPrompt = RhinoApp.CommandPrompt ?? "";
        
        return JObject.FromObject(new
        {
            command_prompt = currentPrompt,
            history = recentLines,
            history_count = recentLines.Length,
            total_lines = allLines.Length
        });
    }
    
    /// <summary>
    /// Open a Rhino 3DM file.
    /// </summary>
    public JObject OpenFile(JObject parameters)
    {
        string filePath = parameters["file_path"]?.ToString();
        if (string.IsNullOrEmpty(filePath))
            throw new ArgumentException("file_path is required");
        
        if (!File.Exists(filePath))
            throw new FileNotFoundException($"File not found: {filePath}");
        
        if (!filePath.ToLower().EndsWith(".3dm"))
            throw new ArgumentException("file_path must be a .3dm file");
        
        // Open the file using Rhino command
        string script = $"_-Open \"{filePath}\" _Enter";
        bool result = RhinoApp.RunScript(script, false);
        
        if (!result)
            throw new InvalidOperationException($"Failed to open file: {filePath}");
        
        return JObject.FromObject(new
        {
            file_path = filePath,
            status = "opened"
        });
    }
    
    /// <summary>
    /// Save the current Rhino document.
    /// </summary>
    public JObject SaveFile(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string filePath = parameters["file_path"]?.ToString();
        
        bool success;
        string savedPath;
        
        if (!string.IsNullOrEmpty(filePath))
        {
            // Save As to new location
            if (!filePath.ToLower().EndsWith(".3dm"))
                throw new ArgumentException("file_path must be a .3dm file");
            
            // Ensure directory exists
            string directory = Path.GetDirectoryName(filePath);
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }
            
            // Use Rhino command for Save As
            string script = $"_-SaveAs \"{filePath}\" _Enter";
            success = RhinoApp.RunScript(script, false);
            savedPath = filePath;
        }
        else
        {
            // Save to current location
            if (string.IsNullOrEmpty(doc.Path))
                throw new InvalidOperationException("Document has not been saved before. Provide a file_path.");
            
            string script = "_-Save _Enter";
            success = RhinoApp.RunScript(script, false);
            savedPath = doc.Path;
        }
        
        if (!success)
            throw new InvalidOperationException($"Failed to save file");
        
        return JObject.FromObject(new
        {
            file_path = savedPath,
            status = "saved"
        });
    }
    
    /// <summary>
    /// Export Rhino geometry to various file formats.
    /// </summary>
    public JObject ExportFile(JObject parameters)
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
        
        // Select specific objects or all objects
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
        
        // Ensure directory exists
        string directory = Path.GetDirectoryName(filePath);
        if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
        {
            Directory.CreateDirectory(directory);
        }
        
        // Build export command based on format
        // Use _Enter repeatedly to accept all default options and avoid dialogs
        string exportCommand = format switch
        {
            // STEP: Schema version prompt
            "STEP" => $"_-Export \"{filePath}\" _Schema=AP214AutomotiveDesign _Enter",
            // IGES: Usually no extra prompts
            "IGES" => $"_-Export \"{filePath}\" _Enter _Enter",
            // DWG/DXF: Version prompts
            "DWG" => $"_-Export \"{filePath}\" _Enter _Enter _Enter",
            "DXF" => $"_-Export \"{filePath}\" _Enter _Enter _Enter",
            // OBJ: Geometry only, no prompts needed with defaults
            "OBJ" => $"_-Export \"{filePath}\" _GeometryOnly=Yes _Enter _Enter _Enter",
            // STL: Binary/ASCII, tolerance prompts
            "STL" => $"_-Export \"{filePath}\" _ExportFileType=Binary _Enter _Enter _Enter",
            // 3MF: Usually no extra prompts
            "3MF" => $"_-Export \"{filePath}\" _Enter _Enter",
            // FBX: Various options
            "FBX" => $"_-Export \"{filePath}\" _Enter _Enter _Enter _Enter",
            // DAE (Collada): Usually no extra prompts
            "DAE" => $"_-Export \"{filePath}\" _Enter _Enter",
            _ => throw new ArgumentException($"Unsupported format: {format}")
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
}
