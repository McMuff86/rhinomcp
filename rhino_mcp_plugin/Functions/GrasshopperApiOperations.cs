using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Special;
using Grasshopper.Kernel.Types;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Grasshopper SDK API operations for programmatic control of Grasshopper definitions.
/// 
/// These methods provide direct access to the Grasshopper SDK, allowing:
/// - Loading definitions without the GrasshopperPlayer
/// - Setting parameters programmatically
/// - Solving definitions on demand
/// - Baking output geometry
/// - Retrieving computed values
/// 
/// This approach is different from the WebSocket-based interactive approach,
/// which is better suited for scripts that require user input during execution.
/// </summary>
public partial class RhinoMCPFunctions
{
    // Store loaded Grasshopper documents by ID
    private static readonly Dictionary<string, GH_Document> _loadedDefinitions = new Dictionary<string, GH_Document>();
    private static readonly object _definitionLock = new object();

    /// <summary>
    /// Load a Grasshopper definition file and return information about its parameters.
    /// The definition is stored in memory for subsequent operations.
    /// </summary>
    /// <param name="parameters">
    /// - file_path (string, required): Path to the .gh or .ghx file
    /// </param>
    /// <returns>
    /// - definition_id: Unique identifier for subsequent operations
    /// - parameters: List of input parameters with name, nickname, type, current value
    /// - outputs: List of output components with name, nickname
    /// </returns>
    public JObject LoadGrasshopperDefinition(JObject parameters)
    {
        string filePath = parameters["file_path"]?.ToString();
        if (string.IsNullOrEmpty(filePath))
            throw new ArgumentException("file_path is required");

        if (!File.Exists(filePath))
            throw new FileNotFoundException($"Grasshopper file not found: {filePath}");

        string ext = Path.GetExtension(filePath).ToLower();
        if (ext != ".gh" && ext != ".ghx")
            throw new ArgumentException("file_path must be a .gh or .ghx file");

        // Generate a unique ID for this definition
        string definitionId = Guid.NewGuid().ToString("N").Substring(0, 8);

        GH_Document ghDoc = null;
        
        try
        {
            // Create archive and read the file
            var archive = new GH_IO.Serialization.GH_Archive();
            if (!archive.ReadFromFile(filePath))
                throw new InvalidOperationException($"Failed to read Grasshopper file: {filePath}");

            // Create a new document
            ghDoc = new GH_Document();
            if (!archive.ExtractObject(ghDoc, "Definition"))
                throw new InvalidOperationException($"Failed to extract definition from file: {filePath}");

            // Set document properties
            ghDoc.FilePath = filePath;
            ghDoc.IsModified = false;

            // Store the document
            lock (_definitionLock)
            {
                // If there's an existing document with same path, dispose it
                var existingKey = _loadedDefinitions.Keys.FirstOrDefault(k => 
                    _loadedDefinitions[k].FilePath == filePath);
                if (existingKey != null)
                {
                    _loadedDefinitions[existingKey].Dispose();
                    _loadedDefinitions.Remove(existingKey);
                }
                
                _loadedDefinitions[definitionId] = ghDoc;
            }

            // Collect parameter info
            var inputParams = new JArray();
            var outputParams = new JArray();

            foreach (var obj in ghDoc.Objects)
            {
                // Check for input parameters
                if (obj is IGH_Param param && param.Kind == GH_ParamKind.floating)
                {
                    // This is a standalone input parameter
                    if (param.Sources.Count == 0) // No inputs = it's an input
                    {
                        var paramInfo = GetParameterInfo(param);
                        inputParams.Add(paramInfo);
                    }
                }
                
                // Check for sliders (special input type)
                if (obj is GH_NumberSlider slider)
                {
                    inputParams.Add(new JObject
                    {
                        ["name"] = slider.Name,
                        ["nickname"] = slider.NickName,
                        ["type"] = "NumberSlider",
                        ["value"] = slider.CurrentValue,
                        ["min"] = (double)slider.Slider.Minimum,
                        ["max"] = (double)slider.Slider.Maximum,
                        ["component_guid"] = slider.InstanceGuid.ToString()
                    });
                }

                // Check for panels (text input)
                if (obj is GH_Panel panel)
                {
                    inputParams.Add(new JObject
                    {
                        ["name"] = panel.Name,
                        ["nickname"] = panel.NickName,
                        ["type"] = "Panel",
                        ["value"] = panel.UserText,
                        ["component_guid"] = panel.InstanceGuid.ToString()
                    });
                }

                // Check for boolean toggles
                if (obj is GH_BooleanToggle toggle)
                {
                    inputParams.Add(new JObject
                    {
                        ["name"] = toggle.Name,
                        ["nickname"] = toggle.NickName,
                        ["type"] = "BooleanToggle",
                        ["value"] = toggle.Value,
                        ["component_guid"] = toggle.InstanceGuid.ToString()
                    });
                }

                // Check for output components
                if (obj is IGH_Component component)
                {
                    // Check if this component has output parameters that are outputs
                    foreach (var output in component.Params.Output)
                    {
                        if (output.Recipients.Count == 0) // No recipients = it's a final output
                        {
                            outputParams.Add(new JObject
                            {
                                ["name"] = output.Name,
                                ["nickname"] = output.NickName,
                                ["type"] = output.TypeName,
                                ["component_name"] = component.Name,
                                ["component_guid"] = component.InstanceGuid.ToString(),
                                ["param_index"] = component.Params.Output.IndexOf(output)
                            });
                        }
                    }
                }
            }

            RhinoApp.WriteLine($"[GH_API] Loaded definition: {Path.GetFileName(filePath)} (ID: {definitionId})");
            RhinoApp.WriteLine($"[GH_API] Found {inputParams.Count} inputs, {outputParams.Count} outputs");

            return JObject.FromObject(new
            {
                definition_id = definitionId,
                file_path = filePath,
                file_name = Path.GetFileName(filePath),
                parameters = inputParams,
                outputs = outputParams,
                object_count = ghDoc.ObjectCount
            });
        }
        catch (Exception ex)
        {
            // Clean up on error
            ghDoc?.Dispose();
            throw new InvalidOperationException($"Failed to load Grasshopper definition: {ex.Message}", ex);
        }
    }

    /// <summary>
    /// Set a parameter value in a loaded Grasshopper definition.
    /// </summary>
    /// <param name="parameters">
    /// - definition_id (string, required): ID from load_grasshopper_definition
    /// - parameter_name (string, required): Parameter nickname to set
    /// - value (any, required): Value to set (type depends on parameter type)
    /// </param>
    public JObject SetGrasshopperParameter(JObject parameters)
    {
        string definitionId = parameters["definition_id"]?.ToString();
        string paramName = parameters["parameter_name"]?.ToString();
        var value = parameters["value"];

        if (string.IsNullOrEmpty(definitionId))
            throw new ArgumentException("definition_id is required");
        if (string.IsNullOrEmpty(paramName))
            throw new ArgumentException("parameter_name is required");
        if (value == null)
            throw new ArgumentException("value is required");

        GH_Document ghDoc;
        lock (_definitionLock)
        {
            if (!_loadedDefinitions.TryGetValue(definitionId, out ghDoc))
                throw new ArgumentException($"Definition not found: {definitionId}");
        }

        bool found = false;
        string paramType = null;
        object setValue = null;

        foreach (var obj in ghDoc.Objects)
        {
            // Match by nickname (case-insensitive)
            if (obj.NickName.Equals(paramName, StringComparison.OrdinalIgnoreCase) ||
                obj.Name.Equals(paramName, StringComparison.OrdinalIgnoreCase))
            {
                if (obj is GH_NumberSlider slider)
                {
                    double numValue = value.Type == JTokenType.Float || value.Type == JTokenType.Integer
                        ? value.Value<double>()
                        : double.Parse(value.ToString());
                    
                    slider.SetSliderValue((decimal)numValue);
                    slider.ExpireSolution(false);
                    found = true;
                    paramType = "NumberSlider";
                    setValue = numValue;
                    break;
                }
                else if (obj is GH_Panel panel)
                {
                    panel.SetUserText(value.ToString());
                    panel.ExpireSolution(false);
                    found = true;
                    paramType = "Panel";
                    setValue = value.ToString();
                    break;
                }
                else if (obj is GH_BooleanToggle toggle)
                {
                    bool boolValue = value.Type == JTokenType.Boolean
                        ? value.Value<bool>()
                        : bool.Parse(value.ToString());
                    
                    toggle.Value = boolValue;
                    toggle.ExpireSolution(false);
                    found = true;
                    paramType = "BooleanToggle";
                    setValue = boolValue;
                    break;
                }
                else if (obj is Param_Number numParam)
                {
                    double numValue = value.Type == JTokenType.Float || value.Type == JTokenType.Integer
                        ? value.Value<double>()
                        : double.Parse(value.ToString());
                    
                    numParam.PersistentData.Clear();
                    numParam.PersistentData.Append(new GH_Number(numValue));
                    numParam.ExpireSolution(false);
                    found = true;
                    paramType = "Number";
                    setValue = numValue;
                    break;
                }
                else if (obj is Param_Integer intParam)
                {
                    int intValue = value.Type == JTokenType.Integer
                        ? value.Value<int>()
                        : int.Parse(value.ToString());
                    
                    intParam.PersistentData.Clear();
                    intParam.PersistentData.Append(new GH_Integer(intValue));
                    intParam.ExpireSolution(false);
                    found = true;
                    paramType = "Integer";
                    setValue = intValue;
                    break;
                }
                else if (obj is Param_String strParam)
                {
                    strParam.PersistentData.Clear();
                    strParam.PersistentData.Append(new GH_String(value.ToString()));
                    strParam.ExpireSolution(false);
                    found = true;
                    paramType = "String";
                    setValue = value.ToString();
                    break;
                }
                else if (obj is Param_Boolean boolParam)
                {
                    bool boolValue = value.Type == JTokenType.Boolean
                        ? value.Value<bool>()
                        : bool.Parse(value.ToString());
                    
                    boolParam.PersistentData.Clear();
                    boolParam.PersistentData.Append(new GH_Boolean(boolValue));
                    boolParam.ExpireSolution(false);
                    found = true;
                    paramType = "Boolean";
                    setValue = boolValue;
                    break;
                }
                else if (obj is Param_Point ptParam)
                {
                    Point3d pt = ParsePoint3d(value);
                    ptParam.PersistentData.Clear();
                    ptParam.PersistentData.Append(new GH_Point(pt));
                    ptParam.ExpireSolution(false);
                    found = true;
                    paramType = "Point";
                    setValue = $"{pt.X},{pt.Y},{pt.Z}";
                    break;
                }
            }
        }

        if (!found)
            throw new ArgumentException($"Parameter not found: {paramName}");

        RhinoApp.WriteLine($"[GH_API] Set parameter '{paramName}' ({paramType}) = {setValue}");

        return JObject.FromObject(new
        {
            definition_id = definitionId,
            parameter_name = paramName,
            parameter_type = paramType,
            value = setValue,
            status = "set"
        });
    }

    /// <summary>
    /// Solve a loaded Grasshopper definition.
    /// </summary>
    /// <param name="parameters">
    /// - definition_id (string, required): ID from load_grasshopper_definition
    /// - expire_all (bool, optional): Force full recalculation (default: true)
    /// </param>
    public JObject SolveGrasshopper(JObject parameters)
    {
        string definitionId = parameters["definition_id"]?.ToString();
        bool expireAll = parameters["expire_all"]?.Value<bool>() ?? true;

        if (string.IsNullOrEmpty(definitionId))
            throw new ArgumentException("definition_id is required");

        GH_Document ghDoc;
        lock (_definitionLock)
        {
            if (!_loadedDefinitions.TryGetValue(definitionId, out ghDoc))
                throw new ArgumentException($"Definition not found: {definitionId}");
        }

        // Expire all objects if requested
        if (expireAll)
        {
            foreach (var obj in ghDoc.Objects)
            {
                obj.ExpireSolution(false);
            }
        }

        // Solve the definition
        ghDoc.NewSolution(true, GH_SolutionMode.Silent);

        // Check for errors
        var errors = new JArray();
        var warnings = new JArray();
        
        foreach (var obj in ghDoc.Objects)
        {
            if (obj is IGH_ActiveObject activeObj)
            {
                if (activeObj.RuntimeMessageLevel == GH_RuntimeMessageLevel.Error)
                {
                    foreach (var msg in activeObj.RuntimeMessages(GH_RuntimeMessageLevel.Error))
                    {
                        errors.Add(new JObject
                        {
                            ["component"] = obj.NickName,
                            ["message"] = msg
                        });
                    }
                }
                else if (activeObj.RuntimeMessageLevel == GH_RuntimeMessageLevel.Warning)
                {
                    foreach (var msg in activeObj.RuntimeMessages(GH_RuntimeMessageLevel.Warning))
                    {
                        warnings.Add(new JObject
                        {
                            ["component"] = obj.NickName,
                            ["message"] = msg
                        });
                    }
                }
            }
        }

        RhinoApp.WriteLine($"[GH_API] Solved definition {definitionId} (errors: {errors.Count}, warnings: {warnings.Count})");

        return JObject.FromObject(new
        {
            definition_id = definitionId,
            status = errors.Count == 0 ? "solved" : "solved_with_errors",
            errors = errors,
            warnings = warnings
        });
    }

    /// <summary>
    /// Bake output geometry from a solved Grasshopper definition to Rhino.
    /// </summary>
    /// <param name="parameters">
    /// - definition_id (string, required): ID from load_grasshopper_definition
    /// - component_names (array, optional): Specific component nicknames to bake (default: all)
    /// - layer (string, optional): Target layer name for baked geometry
    /// </param>
    public JObject BakeGrasshopper(JObject parameters)
    {
        string definitionId = parameters["definition_id"]?.ToString();
        var componentNames = parameters["component_names"]?.ToObject<List<string>>();
        string layerName = parameters["layer"]?.ToString();

        if (string.IsNullOrEmpty(definitionId))
            throw new ArgumentException("definition_id is required");

        GH_Document ghDoc;
        lock (_definitionLock)
        {
            if (!_loadedDefinitions.TryGetValue(definitionId, out ghDoc))
                throw new ArgumentException($"Definition not found: {definitionId}");
        }

        var doc = RhinoDoc.ActiveDoc;
        var bakedIds = new JArray();

        // Get or create target layer
        int layerIndex = -1;
        if (!string.IsNullOrEmpty(layerName))
        {
            layerIndex = doc.Layers.FindByFullPath(layerName, -1);
            if (layerIndex < 0)
            {
                var layer = new Layer { Name = layerName };
                layerIndex = doc.Layers.Add(layer);
            }
        }

        // Set up bake attributes
        var attributes = new ObjectAttributes();
        if (layerIndex >= 0)
            attributes.LayerIndex = layerIndex;

        // Iterate through components and bake
        foreach (var obj in ghDoc.Objects)
        {
            if (obj is IGH_Component component)
            {
                // Check if we should bake this component
                bool shouldBake = componentNames == null || componentNames.Count == 0 ||
                    componentNames.Any(n => 
                        component.NickName.Equals(n, StringComparison.OrdinalIgnoreCase) ||
                        component.Name.Equals(n, StringComparison.OrdinalIgnoreCase));

                if (!shouldBake)
                    continue;

                // Bake each output parameter
                foreach (var output in component.Params.Output)
                {
                    var data = output.VolatileData;
                    
                    // Iterate over all data items using AllData
                    foreach (var item in data.AllData(true))
                    {
                        if (item == null)
                            continue;

                        // Try to bake geometry
                        Guid? bakedGuid = null;

                        if (item is IGH_BakeAwareData bakeAware)
                        {
                            Guid tempGuid;
                            if (bakeAware.BakeGeometry(doc, attributes, out tempGuid))
                            {
                                bakedGuid = tempGuid;
                            }
                        }
                        else if (item is GH_Brep ghBrep && ghBrep.Value != null)
                        {
                            bakedGuid = doc.Objects.AddBrep(ghBrep.Value, attributes);
                        }
                        else if (item is GH_Surface ghSrf && ghSrf.Value != null)
                        {
                            bakedGuid = doc.Objects.AddBrep(ghSrf.Value, attributes);
                        }
                        else if (item is GH_Mesh ghMesh && ghMesh.Value != null)
                        {
                            bakedGuid = doc.Objects.AddMesh(ghMesh.Value, attributes);
                        }
                        else if (item is GH_Curve ghCrv && ghCrv.Value != null)
                        {
                            bakedGuid = doc.Objects.AddCurve(ghCrv.Value, attributes);
                        }
                        else if (item is GH_Point ghPt)
                        {
                            bakedGuid = doc.Objects.AddPoint(ghPt.Value, attributes);
                        }
                        else if (item is GH_Line ghLine)
                        {
                            bakedGuid = doc.Objects.AddLine(ghLine.Value, attributes);
                        }

                        if (bakedGuid.HasValue && bakedGuid.Value != Guid.Empty)
                        {
                            bakedIds.Add(new JObject
                            {
                                ["id"] = bakedGuid.Value.ToString(),
                                ["component"] = component.NickName,
                                ["output"] = output.NickName
                            });
                        }
                    }
                }
            }
        }

        doc.Views.Redraw();

        RhinoApp.WriteLine($"[GH_API] Baked {bakedIds.Count} objects from definition {definitionId}");

        return JObject.FromObject(new
        {
            definition_id = definitionId,
            baked_count = bakedIds.Count,
            baked_objects = bakedIds,
            layer = layerName
        });
    }

    /// <summary>
    /// Get output values from a solved Grasshopper definition.
    /// </summary>
    /// <param name="parameters">
    /// - definition_id (string, required): ID from load_grasshopper_definition
    /// - output_names (array, optional): Specific output nicknames to retrieve (default: all)
    /// </param>
    public JObject GetGrasshopperOutputs(JObject parameters)
    {
        string definitionId = parameters["definition_id"]?.ToString();
        var outputNames = parameters["output_names"]?.ToObject<List<string>>();

        if (string.IsNullOrEmpty(definitionId))
            throw new ArgumentException("definition_id is required");

        GH_Document ghDoc;
        lock (_definitionLock)
        {
            if (!_loadedDefinitions.TryGetValue(definitionId, out ghDoc))
                throw new ArgumentException($"Definition not found: {definitionId}");
        }

        var outputs = new JObject();

        foreach (var obj in ghDoc.Objects)
        {
            if (obj is IGH_Component component)
            {
                foreach (var output in component.Params.Output)
                {
                    // Check if we should include this output
                    bool shouldInclude = outputNames == null || outputNames.Count == 0 ||
                        outputNames.Any(n => 
                            output.NickName.Equals(n, StringComparison.OrdinalIgnoreCase) ||
                            output.Name.Equals(n, StringComparison.OrdinalIgnoreCase));

                    if (!shouldInclude)
                        continue;

                    // Skip if already processed (same nickname)
                    string key = $"{component.NickName}.{output.NickName}";
                    if (outputs.ContainsKey(key))
                        continue;

                    var values = new JArray();
                    var data = output.VolatileData;
                    
                    // Iterate using PathCount and get_Branch for proper API
                    int pathCount = data.PathCount;
                    for (int pathIndex = 0; pathIndex < pathCount; pathIndex++)
                    {
                        var path = data.Paths[pathIndex];
                        var branch = data.get_Branch(path);
                        
                        var branchValues = new JArray();
                        foreach (var item in branch)
                        {
                            if (item == null)
                            {
                                branchValues.Add(JValue.CreateNull());
                                continue;
                            }

                            // Convert to JSON-serializable value
                            if (item is IGH_Goo gooItem)
                            {
                                object val = ConvertGHTypeToValue(gooItem);
                                branchValues.Add(JToken.FromObject(val ?? "null"));
                            }
                            else
                            {
                                branchValues.Add(item?.ToString() ?? "null");
                            }
                        }
                        
                        if (pathCount == 1)
                        {
                            // Single branch - flatten
                            values = branchValues;
                        }
                        else
                        {
                            values.Add(branchValues);
                        }
                    }

                    outputs[key] = new JObject
                    {
                        ["component"] = component.NickName,
                        ["output"] = output.NickName,
                        ["type"] = output.TypeName,
                        ["values"] = values,
                        ["count"] = data.DataCount
                    };
                }
            }

            // Also check for standalone output parameters (like panels)
            if (obj is GH_Panel panel && panel.Sources.Count > 0)
            {
                bool shouldInclude = outputNames == null || outputNames.Count == 0 ||
                    outputNames.Any(n => 
                        panel.NickName.Equals(n, StringComparison.OrdinalIgnoreCase) ||
                        panel.Name.Equals(n, StringComparison.OrdinalIgnoreCase));

                if (shouldInclude && !outputs.ContainsKey(panel.NickName))
                {
                    var values = new JArray();
                    var panelData = panel.VolatileData;
                    
                    for (int pathIndex = 0; pathIndex < panelData.PathCount; pathIndex++)
                    {
                        var path = panelData.Paths[pathIndex];
                        var branch = panelData.get_Branch(path);
                        
                        foreach (var item in branch)
                        {
                            values.Add(item?.ToString() ?? "null");
                        }
                    }

                    outputs[panel.NickName] = new JObject
                    {
                        ["component"] = "Panel",
                        ["output"] = panel.NickName,
                        ["type"] = "Text",
                        ["values"] = values,
                        ["count"] = panel.VolatileData.DataCount
                    };
                }
            }
        }

        RhinoApp.WriteLine($"[GH_API] Retrieved {outputs.Count} outputs from definition {definitionId}");

        return JObject.FromObject(new
        {
            definition_id = definitionId,
            outputs = outputs
        });
    }

    /// <summary>
    /// Unload a Grasshopper definition from memory.
    /// </summary>
    public JObject UnloadGrasshopperDefinition(JObject parameters)
    {
        string definitionId = parameters["definition_id"]?.ToString();

        if (string.IsNullOrEmpty(definitionId))
            throw new ArgumentException("definition_id is required");

        lock (_definitionLock)
        {
            if (_loadedDefinitions.TryGetValue(definitionId, out var ghDoc))
            {
                ghDoc.Dispose();
                _loadedDefinitions.Remove(definitionId);
                RhinoApp.WriteLine($"[GH_API] Unloaded definition: {definitionId}");
                
                return JObject.FromObject(new
                {
                    definition_id = definitionId,
                    status = "unloaded"
                });
            }
            else
            {
                throw new ArgumentException($"Definition not found: {definitionId}");
            }
        }
    }

    /// <summary>
    /// List all currently loaded Grasshopper definitions.
    /// </summary>
    public JObject ListGrasshopperDefinitions(JObject parameters)
    {
        var definitions = new JArray();

        lock (_definitionLock)
        {
            foreach (var kvp in _loadedDefinitions)
            {
                definitions.Add(new JObject
                {
                    ["definition_id"] = kvp.Key,
                    ["file_path"] = kvp.Value.FilePath,
                    ["file_name"] = Path.GetFileName(kvp.Value.FilePath),
                    ["object_count"] = kvp.Value.ObjectCount
                });
            }
        }

        return JObject.FromObject(new
        {
            definitions = definitions,
            count = definitions.Count
        });
    }

    #region Helper Methods

    private JObject GetParameterInfo(IGH_Param param)
    {
        var info = new JObject
        {
            ["name"] = param.Name,
            ["nickname"] = param.NickName,
            ["type"] = param.TypeName,
            ["component_guid"] = param.InstanceGuid.ToString()
        };

        // Try to get current value
        if (param.VolatileDataCount > 0)
        {
            var data = param.VolatileData;
            if (data.PathCount > 0)
            {
                var firstPath = data.Paths[0];
                var firstBranch = data.get_Branch(firstPath);
                if (firstBranch != null && firstBranch.Count > 0)
                {
                    var firstItem = firstBranch[0];
                    if (firstItem is IGH_Goo gooItem)
                    {
                        info["value"] = JToken.FromObject(ConvertGHTypeToValue(gooItem) ?? "null");
                    }
                    else if (firstItem != null)
                    {
                        info["value"] = firstItem.ToString();
                    }
                }
            }
        }

        return info;
    }

    private object ConvertGHTypeToValue(IGH_Goo item)
    {
        if (item == null)
            return null;

        return item switch
        {
            GH_Number num => num.Value,
            GH_Integer intVal => intVal.Value,
            GH_String str => str.Value,
            GH_Boolean boolVal => boolVal.Value,
            GH_Point pt => new { x = pt.Value.X, y = pt.Value.Y, z = pt.Value.Z },
            GH_Vector vec => new { x = vec.Value.X, y = vec.Value.Y, z = vec.Value.Z },
            GH_Plane plane => new 
            { 
                origin = new { x = plane.Value.OriginX, y = plane.Value.OriginY, z = plane.Value.OriginZ },
                normal = new { x = plane.Value.Normal.X, y = plane.Value.Normal.Y, z = plane.Value.Normal.Z }
            },
            GH_Colour col => new { r = col.Value.R, g = col.Value.G, b = col.Value.B, a = col.Value.A },
            GH_Interval interval => new { min = interval.Value.T0, max = interval.Value.T1 },
            GH_Brep brep => $"Brep (faces: {brep.Value?.Faces.Count ?? 0})",
            GH_Surface srf => $"Surface",
            GH_Mesh mesh => $"Mesh (vertices: {mesh.Value?.Vertices.Count ?? 0}, faces: {mesh.Value?.Faces.Count ?? 0})",
            GH_Curve crv => $"Curve (length: {crv.Value?.GetLength() ?? 0:F2})",
            GH_Line line => $"Line (length: {line.Value.Length:F2})",
            _ => item.ToString()
        };
    }

    private Point3d ParsePoint3d(JToken value)
    {
        if (value is JArray arr && arr.Count >= 3)
        {
            return new Point3d(arr[0].Value<double>(), arr[1].Value<double>(), arr[2].Value<double>());
        }
        else if (value is JObject obj)
        {
            return new Point3d(
                obj["x"]?.Value<double>() ?? 0,
                obj["y"]?.Value<double>() ?? 0,
                obj["z"]?.Value<double>() ?? 0
            );
        }
        else if (value.Type == JTokenType.String)
        {
            var parts = value.ToString().Split(',');
            if (parts.Length >= 3)
            {
                return new Point3d(
                    double.Parse(parts[0].Trim()),
                    double.Parse(parts[1].Trim()),
                    double.Parse(parts[2].Trim())
                );
            }
        }
        throw new ArgumentException($"Cannot parse Point3d from: {value}");
    }

    #endregion
}
