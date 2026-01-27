using System;
using System.Drawing;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject ModifyObject(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var obj = getObjectByIdOrName(parameters);
        var geometry = obj.Geometry;
        var xform = Transform.Identity;

        // Handle different modifications based on parameters
        bool attributesModified = false;
        bool geometryModified = false;

        // IMPORTANT: Duplicate attributes to avoid losing existing data (user strings, groups, etc.)
        // See: https://discourse.mcneel.com/t/modifyattributes-delete-all-attributes/202870
        var newAttributes = obj.Attributes.Duplicate();

        // Change name if provided
        if (parameters["new_name"] != null)
        {
            string name = parameters["new_name"].ToString();
            newAttributes.Name = name;
            attributesModified = true;
        }

        // Change color if provided
        if (parameters["new_color"] != null)
        {
            int[] color = parameters["new_color"]?.ToObject<int[]>() ?? new[] { 0, 0, 0 };
            newAttributes.ObjectColor = Color.FromArgb(color[0], color[1], color[2]);
            newAttributes.ColorSource = ObjectColorSource.ColorFromObject;
            attributesModified = true;
        }

        // Change layer if provided
        if (parameters["layer"] != null)
        {
            string layerName = parameters["layer"].ToString();
            int layerIndex = doc.Layers.FindByFullPath(layerName, -1);
            if (layerIndex < 0)
            {
                // Try finding by name only (not full path)
                layerIndex = doc.Layers.FindName(layerName)?.Index ?? -1;
            }
            if (layerIndex < 0)
            {
                throw new ArgumentException($"Layer not found: {layerName}");
            }
            newAttributes.LayerIndex = layerIndex;
            attributesModified = true;
        }

        // Change visibility if provided
        if (parameters["visible"] != null)
        {
            bool visible = parameters["visible"].Value<bool>();
            newAttributes.Visible = visible;
            attributesModified = true;
        }

        // Change layer if provided
        if (parameters["layer"] != null)
        {
            string layerName = parameters["layer"].ToString();
            int layerIndex = doc.Layers.FindByFullPath(layerName, -1);
            if (layerIndex < 0)
            {
                // Try finding by name only (not full path)
                layerIndex = doc.Layers.FindName(layerName)?.Index ?? -1;
            }
            if (layerIndex < 0)
            {
                throw new ArgumentException($"Layer not found: {layerName}");
            }
            obj.Attributes.LayerIndex = layerIndex;
            attributesModified = true;
        }

        // Change translation if provided
        if (parameters["translation"] != null)
        {
            xform *= applyTranslation(parameters);
            geometryModified = true;
        }

        // Apply scale if provided
        if (parameters["scale"] != null)
        {
            xform *= applyScale(parameters, geometry);
            geometryModified = true;
        }

        // Apply rotation if provided
        if (parameters["rotation"] != null)
        {
            xform *= applyRotation(parameters, geometry);
            geometryModified = true;
        }

        if (attributesModified)
        {
            // Use duplicated attributes and object ID for reliable modification
            doc.Objects.ModifyAttributes(obj.Id, newAttributes, true);
        }

        if (geometryModified)
        {
            // Update the object geometry if needed
            doc.Objects.Transform(obj, xform, true);
        }

        // Update views
        doc.Views.Redraw();

        return Serializer.RhinoObject(getObjectByIdOrName(new JObject { ["id"] = obj.Id }));

    }
}