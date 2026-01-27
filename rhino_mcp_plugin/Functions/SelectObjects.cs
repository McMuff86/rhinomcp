using System;
using System.Drawing;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using System.Collections.Generic;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject SelectObjects(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var objects = doc.Objects.ToList();
        var selectedObjects = new List<Guid>();
        
        // Support simple filter parameters directly
        string layerName = parameters["layer"]?.ToString();
        string objectType = parameters["type"]?.ToString()?.ToLowerInvariant();
        string objectName = parameters["name"]?.ToString();
        bool? selectAll = parameters["all"]?.Value<bool>();
        bool? clearSelection = parameters["clear"]?.Value<bool>();
        var objectIds = parameters["ids"]?.ToObject<List<string>>();
        
        // Clear selection if requested
        if (clearSelection == true)
        {
            doc.Objects.UnselectAll();
            doc.Views.Redraw();
            return new JObject { ["count"] = 0, ["action"] = "cleared" };
        }
        
        // Select by IDs directly
        if (objectIds != null && objectIds.Count > 0)
        {
            foreach (string idStr in objectIds)
            {
                if (Guid.TryParse(idStr, out Guid objId))
                {
                    selectedObjects.Add(objId);
                }
            }
            doc.Objects.UnselectAll();
            doc.Objects.Select(selectedObjects);
            doc.Views.Redraw();
            return new JObject { ["count"] = selectedObjects.Count };
        }
        
        // Select all
        if (selectAll == true)
        {
            doc.Objects.UnselectAll();
            doc.Objects.Select(objects.Select(o => o.Id));
            doc.Views.Redraw();
            return new JObject { ["count"] = objects.Count };
        }
        
        // Filter by layer
        if (!string.IsNullOrEmpty(layerName))
        {
            int layerIndex = doc.Layers.FindByFullPath(layerName, -1);
            if (layerIndex < 0)
            {
                // Try partial match
                var layer = doc.Layers.FirstOrDefault(l => l.Name.Equals(layerName, StringComparison.OrdinalIgnoreCase));
                if (layer != null) layerIndex = layer.Index;
            }
            
            if (layerIndex >= 0)
            {
                objects = objects.Where(o => o.Attributes.LayerIndex == layerIndex).ToList();
            }
            else
            {
                // Layer not found, return empty
                doc.Objects.UnselectAll();
                doc.Views.Redraw();
                return new JObject { ["count"] = 0, ["error"] = $"Layer not found: {layerName}" };
            }
        }
        
        // Filter by type
        if (!string.IsNullOrEmpty(objectType))
        {
            objects = objects.Where(o => MatchesObjectType(o, objectType)).ToList();
        }
        
        // Filter by name
        if (!string.IsNullOrEmpty(objectName))
        {
            objects = objects.Where(o => 
                o.Name != null && o.Name.IndexOf(objectName, StringComparison.OrdinalIgnoreCase) >= 0
            ).ToList();
        }
        
        // Legacy filter support
        JObject filters = parameters["filters"] as JObject;
        if (filters != null && filters.Count > 0)
        {
            return SelectObjectsLegacy(parameters, objects);
        }
        
        // Select filtered objects
        selectedObjects = objects.Select(o => o.Id).ToList();
        doc.Objects.UnselectAll();
        doc.Objects.Select(selectedObjects);
        doc.Views.Redraw();
        
        return new JObject { ["count"] = selectedObjects.Count };
    }
    
    private bool MatchesObjectType(RhinoObject obj, string type)
    {
        var geo = obj.Geometry;
        
        return type switch
        {
            "curve" or "curves" => geo is Curve,
            "surface" or "surfaces" => geo is Surface || (geo is Brep b && !b.IsSolid),
            "brep" or "solid" or "solids" => geo is Brep brep && brep.IsSolid,
            "mesh" or "meshes" => geo is Mesh,
            "point" or "points" => geo is Rhino.Geometry.Point,
            "line" or "lines" => geo is LineCurve,
            "circle" or "circles" => geo is ArcCurve ac && ac.IsCircle(),
            "arc" or "arcs" => geo is ArcCurve arc && !arc.IsCircle(),
            "polyline" or "polylines" => geo is PolylineCurve,
            "extrusion" or "extrusions" => geo is Extrusion,
            "text" or "annotation" => geo is TextEntity || geo is AnnotationBase,
            "block" or "blocks" => obj is InstanceObject,
            _ => obj.ObjectType.ToString().ToLowerInvariant().Contains(type)
        };
    }
    
    private JObject SelectObjectsLegacy(JObject parameters, List<RhinoObject> objects)
    {
        JObject filters = (JObject)parameters["filters"];
        var selectedObjects = new List<Guid>();
        var filtersType = parameters["filters_type"]?.ToString() ?? "and";

        var hasName = false;
        var hasColor = false;
        var customAttributes = new Dictionary<string, List<string>>();

        foreach (JProperty f in filters.Properties())
        {
            if (f.Name == "name") hasName = true;
            if (f.Name == "color") hasColor = true;
            if (f.Name != "name" && f.Name != "color") customAttributes.Add(f.Name, castToStringList(f.Value));
        }

        var name = hasName ? castToString(filters.SelectToken("name")) : null;
        var color = hasColor ? castToIntArray(filters.SelectToken("color")) : null;

        if (filtersType == "and")
            foreach (var obj in objects)
            {
                var attributeMatch = true;
                if (hasName && obj.Name != name) continue;
                if (hasColor && obj.Attributes.ObjectColor.R != color[0] && obj.Attributes.ObjectColor.G != color[1] && obj.Attributes.ObjectColor.B != color[2]) continue;
                foreach (var customAttribute in customAttributes)
                {
                    foreach (var value in customAttribute.Value)
                    {
                        if (obj.Attributes.GetUserString(customAttribute.Key) != value) attributeMatch = false;
                    }
                }
                if (!attributeMatch) continue;

                selectedObjects.Add(obj.Id);
            }
        else if (filtersType == "or")
            foreach (var obj in objects)
            {
                var attributeMatch = false;
                if (hasName && obj.Name == name) attributeMatch = true;
                if (hasColor && obj.Attributes.ObjectColor.R == color[0] && obj.Attributes.ObjectColor.G == color[1] && obj.Attributes.ObjectColor.B == color[2]) attributeMatch = true;

                foreach (var customAttribute in customAttributes)
                {
                    foreach (var value in customAttribute.Value)
                    {
                        if (obj.Attributes.GetUserString(customAttribute.Key) == value) attributeMatch = true;
                    }
                }
                if (!attributeMatch) continue;

                selectedObjects.Add(obj.Id);
            }

        var doc = RhinoDoc.ActiveDoc;
        doc.Objects.UnselectAll();
        doc.Objects.Select(selectedObjects);
        doc.Views.Redraw();

        return new JObject { ["count"] = selectedObjects.Count };
    }
}