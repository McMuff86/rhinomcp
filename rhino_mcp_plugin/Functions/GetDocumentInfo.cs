using System;
using System.Drawing;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject GetDocumentInfo(JObject parameters)
    {
        const int LIMIT = 50;
                
        RhinoApp.WriteLine("Getting document info...");

        var doc = RhinoDoc.ActiveDoc;

        var metaData = new JObject
        {
            ["name"] = doc.Name,
            ["date_created"] = doc.DateCreated,
            ["date_modified"] = doc.DateLastEdited,
            ["tolerance"] = doc.ModelAbsoluteTolerance,
            ["angle_tolerance"] = doc.ModelAngleToleranceDegrees,
            ["path"] = doc.Path,
            ["units"] = doc.ModelUnitSystem.ToString(),
        };

        var objectData = new JArray();

        // Collect minimal object information (limit to first 10 objects)
        int count = 0;
        foreach (var docObject in doc.Objects)
        {
            if (count >= LIMIT) break;
            
            objectData.Add(Serializer.RhinoObject(docObject));
            count++;
        }

        var layerData = new JArray();

        count = 0;
        foreach (var docLayer in doc.Layers)
        {
            if (count >= LIMIT) break;
            layerData.Add(new JObject
            {
                ["id"] = docLayer.Id.ToString(),
                ["name"] = docLayer.Name,
                ["color"] = docLayer.Color.ToString(),
                ["visible"] = docLayer.IsVisible,
                ["locked"] = docLayer.IsLocked
            });
            count++;
        }


        var materialData = new JArray();
        count = 0;
        foreach (var docMaterial in doc.Materials)
        {
            if (count >= LIMIT) break;
            materialData.Add(new JObject
            {
                ["id"] = count.ToString(),
                ["name"] = docMaterial.Name,
                ["diffuse_color"] = $"{docMaterial.DiffuseColor.R},{docMaterial.DiffuseColor.G},{docMaterial.DiffuseColor.B}",
                ["shine"] = docMaterial.Shine
            });
            count++;
        }

        var result = new JObject
        {
            ["meta_data"] = metaData,
            ["object_count"] = doc.Objects.Count,
            ["objects"] = objectData,
            ["layer_count"] = doc.Layers.Count,
            ["layers"] = layerData,
            ["material_count"] = doc.Materials.Count,
            ["materials"] = materialData
        };

        RhinoApp.WriteLine($"Document info collected: {count} objects");
        return result;
    }

    public JObject Ping(JObject parameters)
    {
        RhinoApp.WriteLine("Ping received");
        return JObject.FromObject(new { status = "success", message = "Pong", timestamp = DateTime.UtcNow.ToString("o") });
    }

    public JObject SetDebugMode(JObject parameters)
    {
        bool enable = parameters["enable"]?.ToObject<bool>() ?? false;
        // Access the server instance - this is a bit hacky, but for demo purposes
        var plugin = RhinoMCPPlugin.Instance;
        if (plugin?.Server != null)
        {
            plugin.Server.SetDebugMode(enable);
        }
        return JObject.FromObject(new { status = "success", message = $"Debug mode {(enable ? "enabled" : "disabled")}" });
    }

    public JObject LogThought(JObject parameters)
    {
        string thought = parameters["thought"]?.ToString() ?? "No thought provided";
        RhinoApp.WriteLine($"[AI THOUGHT] {thought}");
        return JObject.FromObject(new { status = "success", message = "Thought logged" });
    }

    public JObject CreateMaterial(JObject parameters)
    {
        string name = parameters["name"]?.ToString() ?? "NewMaterial";
        int[] color = castToIntArray(parameters.SelectToken("color"));
        double shine = castToDouble(parameters.SelectToken("shine"));

        var doc = RhinoDoc.ActiveDoc;
        var material = new Material
        {
            Name = name,
            DiffuseColor = Color.FromArgb(color[0], color[1], color[2]),
            SpecularColor = Color.FromArgb(255, 255, 255),  // White specular
            Shine = shine
        };

        // Ensure material is added to document table
        material.CommitChanges();
        var materialId = doc.Materials.Add(material);
        if (materialId == -1)
        {
            throw new InvalidOperationException("Failed to create material");
        }

        RhinoApp.WriteLine($"[MATERIAL CREATED] Successfully created material: {name} with ID: {materialId}");
        return JObject.FromObject(new { status = "success", message = $"Material {name} created with ID {materialId}", id = materialId });
    }

    public JObject AssignMaterialToLayer(JObject parameters)
    {
        string layerName = parameters["layer_name"]?.ToString();
        string materialId = parameters["material_id"]?.ToString();

        var doc = RhinoDoc.ActiveDoc;
        var layer = doc.Layers.FindName(layerName);
        if (layer == null)
        {
            throw new InvalidOperationException($"Layer {layerName} not found");
        }

        layer.RenderMaterialIndex = int.Parse(materialId);
        doc.Layers.Modify(layer, layer.Index, true);

        RhinoApp.WriteLine($"[MATERIAL ASSIGNED] Material {materialId} assigned to layer {layerName}");
        return JObject.FromObject(new { status = "success", message = $"Material assigned to layer {layerName}" });
    }
}