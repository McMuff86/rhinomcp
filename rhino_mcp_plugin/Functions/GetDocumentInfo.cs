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

                // CRITICAL: Add base material to doc.Materials first so it appears in UI
                int materialIndex = doc.Materials.Add(baseMaterial);
                if (materialIndex < 0)
                {
                    throw new InvalidOperationException("Failed to add material to doc.Materials");
                }

                // Create RenderMaterial from the base material and add to RenderMaterials table
                var renderMaterial = Rhino.Render.RenderMaterial.CreateBasicMaterial(baseMaterial, doc);
                if (renderMaterial == null)
                {
                    throw new InvalidOperationException("Failed to create RenderMaterial from base material");
                }
                
                // Set the name on the RenderMaterial
                renderMaterial.Name = name;
                
                bool addSuccess = doc.RenderMaterials.Add(renderMaterial);
                if (!addSuccess)
                {
                    throw new InvalidOperationException("Failed to add RenderMaterial to doc.RenderMaterials");
                }
                
                // Get the index of the just-added render material
                int renderIndex = doc.RenderMaterials.Count - 1;

                // Force UI update
                doc.Views.Redraw();

                RhinoApp.WriteLine($"[PBR MATERIAL CREATED] PBR material '{name}' created: Material index {materialIndex}, RenderMaterial index {renderIndex} (metallic: {metallic}, roughness: {roughness})");

                return JObject.FromObject(new
                {
                    status = "success",
                    message = $"PBR Material {name} created with material index {materialIndex}",
                    id = materialIndex.ToString(),  // Return Materials index for layer assignment
                    material_index = materialIndex,  // doc.Materials index - use this for layers!
                    render_material_index = renderIndex,  // doc.RenderMaterials index
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

        // IMPORTANT: layer.RenderMaterialIndex expects doc.Materials index, NOT doc.RenderMaterials index!
        // Validate against doc.Materials
        if (materialIndex < 0 || materialIndex >= doc.Materials.Count)
            throw new InvalidOperationException($"Material index {materialIndex} is out of range. There are {doc.Materials.Count} materials in the document. Note: Use doc.Materials index, not doc.RenderMaterials index.");

        // Assign material to layer using doc.Materials index
        var layerIndex = layer.Index;

        // Set the RenderMaterialIndex - this expects doc.Materials index despite the confusing name
        layer.RenderMaterialIndex = materialIndex;
        RhinoApp.WriteLine($"[LAYER MATERIAL] Setting layer '{layerName}' RenderMaterialIndex to {materialIndex} (doc.Materials index)");
        
        // CRITICAL: Use Modify to persist the change - but we need to pass the layer object itself
        // The Modify method needs the modified layer object and the index
        bool modifySuccess = doc.Layers.Modify(layer, layerIndex, true);
        
        if (!modifySuccess)
        {
            // If Modify fails, try alternative approach: get fresh layer and modify again
            var freshLayer = doc.Layers[layerIndex];
            if (freshLayer != null)
            {
                freshLayer.RenderMaterialIndex = materialIndex;
                modifySuccess = doc.Layers.Modify(freshLayer, layerIndex, true);
            }
            
            if (!modifySuccess)
            {
                throw new InvalidOperationException($"Failed to modify layer {layerName} - Modify() returned false. Material index: {materialIndex}, Layer index: {layerIndex}");
            }
        }
        
        // Verify the assignment was successful by reading it back
        var verifyLayer = doc.Layers[layerIndex];
        if (verifyLayer != null && verifyLayer.RenderMaterialIndex != materialIndex)
        {
            RhinoApp.WriteLine($"[WARNING] Material assignment verification failed. Expected {materialIndex}, got {verifyLayer.RenderMaterialIndex}");
            // Try one more time with direct assignment
            verifyLayer.RenderMaterialIndex = materialIndex;
            doc.Layers.Modify(verifyLayer, layerIndex, true);
        }
        
        // Force viewport redraw to show the changes immediately
        doc.Views.Redraw();

        RhinoApp.WriteLine($"[MATERIAL ASSIGNED] Render material {materialIndex} assigned to layer {layerName} (layer index: {layerIndex}, modify success: {modifySuccess}, verified: {verifyLayer?.RenderMaterialIndex == materialIndex})");
        return JObject.FromObject(new { status = "success", message = $"Material assigned to layer {layerName}" });
    }
}