using System;
using Newtonsoft.Json.Linq;
using Rhino;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject GetDocumentInfo(JObject parameters)
    {
        const int LIMIT = 30;
                
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


        var result = new JObject
        {
            ["meta_data"] = metaData,
            ["object_count"] = doc.Objects.Count,
            ["objects"] = objectData,
            ["layer_count"] = doc.Layers.Count,
            ["layers"] = layerData
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
}