using System;
using System.Drawing;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Render;
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

        // First, include legacy materials (including PBR-style materials)
        int legacyCount = 0;
        foreach (var docMaterial in doc.Materials)
        {
            if (legacyCount >= LIMIT) break;

            // Check if this is a PBR material by looking for user data
            var isPBR = docMaterial.GetUserString("is_pbr") == "true" ||
                       docMaterial.GetUserString("material_type") == "pbr";

            materialData.Add(new JObject
            {
                ["id"] = legacyCount.ToString(),
                ["name"] = docMaterial.Name,
                ["diffuse_color"] = $"{docMaterial.DiffuseColor.R},{docMaterial.DiffuseColor.G},{docMaterial.DiffuseColor.B}",
                ["shine"] = docMaterial.Shine,
                ["type"] = isPBR ? "pbr" : "legacy",
                ["metallic"] = isPBR ? docMaterial.GetUserString("metallic") ?? "0.0" : "0.0",
                ["roughness"] = isPBR ? docMaterial.GetUserString("roughness") ?? "0.1" : "0.1",
                ["base_color"] = isPBR ? docMaterial.GetUserString("base_color") ?? "Unknown" : "Unknown"
            });
            legacyCount++;
        }

        // Also include render materials (true PBR materials)
        int renderCount = 0;
        foreach (var renderMaterial in doc.RenderMaterials)
        {
            if (renderCount >= LIMIT) break;

            // Check if this is a PBR material by looking for PBR parameters
            var isPBR = renderMaterial.GetParameter("metallic") != null ||
                       renderMaterial.GetParameter("roughness") != null ||
                       renderMaterial.GetParameter("is_pbr") != null ||
                       renderMaterial.Name.Contains("_PBR");

            materialData.Add(new JObject
            {
                ["id"] = $"R{renderCount}",
                ["name"] = renderMaterial.Name,
                ["type"] = isPBR ? "pbr" : "render",
                ["diffuse_color"] = renderMaterial.GetParameter("diffuse")?.ToString() ?? "Unknown",
                ["metallic"] = renderMaterial.GetParameter("metallic")?.ToString() ?? "0.0",
                ["roughness"] = renderMaterial.GetParameter("roughness")?.ToString() ?? "0.1",
                ["opacity"] = renderMaterial.GetParameter("opacity")?.ToString() ?? "1.0",
                ["base_color"] = renderMaterial.GetParameter("base_color_rgb")?.ToString() ?? "Unknown"
            });
            renderCount++;
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
        string materialType = parameters["material_type"]?.ToString() ?? "custom";
        int[] color = castToIntArray(parameters.SelectToken("color"));
        double shine = parameters.SelectToken("shine") != null ? castToDouble(parameters.SelectToken("shine")) : 0.5;
        double metallic = parameters.SelectToken("metallic") != null ? castToDouble(parameters.SelectToken("metallic")) : 0.0;
        double roughness = parameters.SelectToken("roughness") != null ? castToDouble(parameters.SelectToken("roughness")) : 0.1;

        var doc = RhinoDoc.ActiveDoc;

        // Create material based on type
        if (string.Equals(materialType, "pbr", StringComparison.OrdinalIgnoreCase))
        {
            try
            {
                // Create a base Material first, then convert to RenderMaterial
                var baseMaterial = new Material
                {
                    Name = name,
                    DiffuseColor = Color.FromArgb(color[0], color[1], color[2]),
                    SpecularColor = metallic > 0.5 ? Color.FromArgb(255, 255, 255) : Color.FromArgb(128, 128, 128),
                    Shine = metallic > 0.5 ? 0.9 : (1.0 - roughness) * 0.8,
                    Transparency = 0.0
                };

                // Convert to PhysicallyBased and set PBR parameters
                baseMaterial.ToPhysicallyBased();
                var pbr = baseMaterial.PhysicallyBased;
                if (pbr != null)
                {
                    pbr.Metallic = metallic;
                    pbr.Roughness = roughness;
                    pbr.BaseColor = new Rhino.Display.Color4f(Color.FromArgb(color[0], color[1], color[2]));
                }

                baseMaterial.CommitChanges();

                // Create RenderMaterial from the base material and add to RenderMaterials table
                var renderMaterial = Rhino.Render.RenderMaterial.CreateBasicMaterial(baseMaterial, doc);
                doc.RenderMaterials.Add(renderMaterial);

                // Get the index of the just-added render material
                int renderIndex = doc.RenderMaterials.Count - 1;

                RhinoApp.WriteLine($"[PBR MATERIAL CREATED] PBR material '{name}' created with RenderMaterials index {renderIndex} (metallic: {metallic}, roughness: {roughness})");

                return JObject.FromObject(new
                {
                    status = "success",
                    message = $"PBR Material {name} created with render index {renderIndex}",
                    id = renderIndex.ToString(),
                    type = "pbr",
                    metallic = metallic,
                    roughness = roughness
                });
            }
            catch (Exception ex)
            {
                RhinoApp.WriteLine($"[PBR ERROR] Failed to create PBR render material: {ex.Message}");

                // Fallback: create a basic legacy material
                var fallbackMaterial = new Material
                {
                    Name = name,
                    DiffuseColor = Color.FromArgb(color[0], color[1], color[2]),
                    SpecularColor = Color.FromArgb(255, 255, 255),
                    Shine = 0.8,
                    Transparency = 0.0
                };

                fallbackMaterial.CommitChanges();
                var fallbackId = doc.Materials.Add(fallbackMaterial);

                return JObject.FromObject(new
                {
                    status = "success",
                    message = $"PBR Material {name} created as basic fallback (ID: {fallbackId})",
                    id = fallbackId.ToString(),
                    type = "pbr_basic",
                    metallic = metallic,
                    roughness = roughness,
                    note = "Created as basic legacy material - PBR parameters not fully supported"
                });
            }
        }
        else
        {
            // Create legacy custom material (existing implementation)
            var legacyMaterial = new Material
            {
                Name = name,
                DiffuseColor = Color.FromArgb(color[0], color[1], color[2]),
                SpecularColor = Color.FromArgb(255, 255, 255),  // White specular
                Shine = shine
            };

            legacyMaterial.CommitChanges();
            var materialId = doc.Materials.Add(legacyMaterial);

            if (materialId == -1)
            {
                throw new InvalidOperationException("Failed to create material");
            }

            RhinoApp.WriteLine($"[MATERIAL CREATED] Successfully created material: {name} with ID: {materialId}");
            return JObject.FromObject(new
            {
                status = "success",
                message = $"Material {name} created with ID {materialId}",
                id = materialId,
                type = "legacy"
            });
        }
    }

    public JObject AssignMaterialToLayer(JObject parameters)
    {
        string layerName = parameters["layer_name"]?.ToString();
        string materialId = parameters["material_id"]?.ToString();

        // Validate required parameters
        if (string.IsNullOrWhiteSpace(layerName))
            throw new ArgumentException("Parameter 'layer_name' is required.");

        if (string.IsNullOrWhiteSpace(materialId))
            throw new ArgumentException("Parameter 'material_id' is required.");

        var doc = RhinoDoc.ActiveDoc;
        var layer = doc.Layers.FindName(layerName);
        if (layer == null)
        {
            throw new InvalidOperationException($"Layer {layerName} not found");
        }

        // Parse and validate material index
        if (!int.TryParse(materialId, out var materialIndex))
            throw new InvalidOperationException($"Invalid material_id '{materialId}'. Expected an integer index.");

        if (materialIndex < 0 || materialIndex >= doc.RenderMaterials.Count)
            throw new InvalidOperationException($"Material index {materialIndex} is out of range. There are {doc.RenderMaterials.Count} render materials in the document.");

        // Assign material to layer - use RenderMaterialIndex for modern Rhino render materials
        layer.RenderMaterialIndex = materialIndex;
        doc.Layers.Modify(layer, layer.Index, true);

        RhinoApp.WriteLine($"[MATERIAL ASSIGNED] Render material {materialIndex} assigned to layer {layerName}");
        return JObject.FromObject(new { status = "success", message = $"Material assigned to layer {layerName}" });
    }
}