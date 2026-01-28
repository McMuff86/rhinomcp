using System;
using System.Collections.Generic;
using System.Drawing;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject CreateLayer(JObject parameters)
    {
        // parse meta data
        bool hasName = parameters.ContainsKey("name");
        bool hasColor = parameters.ContainsKey("color");
        bool hasParent = parameters.ContainsKey("parent");

        string name = hasName ? castToString(parameters.SelectToken("name")) : null;
        int[] color = hasColor ? castToIntArray(parameters.SelectToken("color")) : null;
        string parent = hasParent ? castToString(parameters.SelectToken("parent")) : null;

        var doc = RhinoDoc.ActiveDoc;

        var layer = new Layer();
        if (hasName) layer.Name = name;
        if (hasColor) layer.Color = Color.FromArgb(color[0], color[1], color[2]);

        if (hasParent)
        {
            var parentLayer = doc.Layers.FindName(parent);
            if (parentLayer != null)
                layer.ParentLayerId = parentLayer.Id;

        }
        
        // Handle material assignment BEFORE adding layer to document
        // IMPORTANT: layer.RenderMaterialIndex expects doc.Materials index, NOT doc.RenderMaterials index!
        if (parameters.ContainsKey("material_id"))
        {
            string materialIdStr = parameters["material_id"]?.ToString();
            if (!string.IsNullOrWhiteSpace(materialIdStr) && int.TryParse(materialIdStr, out int materialIndex))
            {
                // Validate against doc.Materials (not doc.RenderMaterials!)
                if (materialIndex >= 0 && materialIndex < doc.Materials.Count)
                {
                    // Set RenderMaterialIndex BEFORE adding to document
                    // Despite the name, this expects doc.Materials index
                    layer.RenderMaterialIndex = materialIndex;
                    RhinoApp.WriteLine($"[LAYER PREP] Setting RenderMaterialIndex {materialIndex} on layer '{name}' (doc.Materials index)");
                }
                else
                {
                    RhinoApp.WriteLine($"[WARNING] Material index {materialIndex} is out of range. doc.Materials count: {doc.Materials.Count}. Note: Use doc.Materials index, not doc.RenderMaterials index.");
                }
            }
        }
        
        // Add the layer to the document
        var layerId = doc.Layers.Add(layer);
        
        // Get fresh reference after Add() to verify
        layer = doc.Layers.FindIndex(layerId);
        
        // Verify material assignment after Add()
        if (parameters.ContainsKey("material_id"))
        {
            string materialIdStr = parameters["material_id"]?.ToString();
            if (!string.IsNullOrWhiteSpace(materialIdStr) && int.TryParse(materialIdStr, out int materialIndex))
            {
                // Validate against doc.Materials (not doc.RenderMaterials!)
                if (materialIndex >= 0 && materialIndex < doc.Materials.Count)
                {
                    var layerIndex = layer.Index;

                    // Check if material was preserved after Add()
                    if (layer.RenderMaterialIndex != materialIndex)
                    {
                        RhinoApp.WriteLine($"[WARNING] Material index lost after Add(). Expected {materialIndex}, got {layer.RenderMaterialIndex}. Re-assigning...");
                        // Re-assign using Modify() as fallback
                        layer.RenderMaterialIndex = materialIndex;
                        bool modifySuccess = doc.Layers.Modify(layer, layerIndex, true);
                        if (!modifySuccess)
                        {
                            // Last resort: get fresh layer and try again
                            var freshLayer = doc.Layers[layerIndex];
                            if (freshLayer != null)
                            {
                                freshLayer.RenderMaterialIndex = materialIndex;
                                doc.Layers.Modify(freshLayer, layerIndex, true);
                            }
                        }
                    }
                    else
                    {
                        RhinoApp.WriteLine($"[LAYER CREATED] Layer '{name}' created with doc.Materials index {materialIndex}");
                    }
                }
            }
        }

        // Update views
        doc.Views.Redraw();

        return Serializer.SerializeLayer(layer);
    }
}