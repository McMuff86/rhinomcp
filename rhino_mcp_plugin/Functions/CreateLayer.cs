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
        // Set RenderMaterialIndex on the layer object before Add()
        if (parameters.ContainsKey("material_id"))
        {
            string materialIdStr = parameters["material_id"]?.ToString();
            if (!string.IsNullOrWhiteSpace(materialIdStr) && int.TryParse(materialIdStr, out int materialIndex))
            {
                if (materialIndex >= 0 && materialIndex < doc.RenderMaterials.Count)
                {
                    // Set RenderMaterialIndex BEFORE adding to document (like RhinoScript does)
                    layer.RenderMaterialIndex = materialIndex;
                    RhinoApp.WriteLine($"[LAYER PREP] Setting RenderMaterialIndex {materialIndex} on layer '{name}' before Add()");
                }
                else
                {
                    RhinoApp.WriteLine($"[WARNING] Material index {materialIndex} is out of range. RenderMaterials count: {doc.RenderMaterials.Count}");
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
                if (materialIndex >= 0 && materialIndex < doc.RenderMaterials.Count)
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
                        RhinoApp.WriteLine($"[LAYER CREATED] Layer '{name}' created with material index {materialIndex} (preserved from pre-Add assignment)");
                    }
                }
            }
        }

        // Update views
        doc.Views.Redraw();

        return Serializer.SerializeLayer(layer);
    }
}