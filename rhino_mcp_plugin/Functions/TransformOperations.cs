using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Copy an object with optional translation.
    /// </summary>
    public JObject CopyObject(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string objectIdStr = parameters["object_id"]?.ToString();
        if (string.IsNullOrEmpty(objectIdStr))
            throw new ArgumentException("object_id is required");
        
        if (!Guid.TryParse(objectIdStr, out Guid objId))
            throw new ArgumentException($"Invalid GUID: {objectIdStr}");
        
        RhinoObject obj = doc.Objects.FindId(objId);
        if (obj == null)
            throw new ArgumentException($"Object not found: {objectIdStr}");
        
        var translationArray = parameters["translation"]?.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
        if (translationArray.Length != 3)
            throw new ArgumentException("translation must be [x, y, z]");
        
        int count = parameters["count"]?.Value<int>() ?? 1;
        if (count < 1)
            throw new ArgumentException("count must be at least 1");
        
        Vector3d translation = new Vector3d(translationArray[0], translationArray[1], translationArray[2]);
        
        List<string> newIds = new List<string>();
        int currentLayerIndex = doc.Layers.CurrentLayerIndex;
        
        for (int i = 1; i <= count; i++)
        {
            Transform xform = Transform.Translation(translation * i);
            
            ObjectAttributes attrs = obj.Attributes.Duplicate();
            attrs.LayerIndex = currentLayerIndex;
            
            Guid newId = doc.Objects.Transform(objId, xform, false);
            if (newId != Guid.Empty)
            {
                newIds.Add(newId.ToString());
            }
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_id = objectIdStr,
            copy_ids = newIds,
            count = newIds.Count
        });
    }
    
    /// <summary>
    /// Mirror an object across a plane.
    /// </summary>
    public JObject MirrorObject(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string objectIdStr = parameters["object_id"]?.ToString();
        if (string.IsNullOrEmpty(objectIdStr))
            throw new ArgumentException("object_id is required");
        
        if (!Guid.TryParse(objectIdStr, out Guid objId))
            throw new ArgumentException($"Invalid GUID: {objectIdStr}");
        
        RhinoObject obj = doc.Objects.FindId(objId);
        if (obj == null)
            throw new ArgumentException($"Object not found: {objectIdStr}");
        
        var originArray = parameters["plane_origin"]?.ToObject<double[]>();
        if (originArray == null || originArray.Length != 3)
            throw new ArgumentException("plane_origin must be [x, y, z]");
        
        var normalArray = parameters["plane_normal"]?.ToObject<double[]>();
        if (normalArray == null || normalArray.Length != 3)
            throw new ArgumentException("plane_normal must be [x, y, z]");
        
        bool deleteInput = parameters["delete_input"]?.Value<bool>() ?? false;
        
        Point3d origin = new Point3d(originArray[0], originArray[1], originArray[2]);
        Vector3d normal = new Vector3d(normalArray[0], normalArray[1], normalArray[2]);
        normal.Unitize();
        
        Plane mirrorPlane = new Plane(origin, normal);
        Transform xform = Transform.Mirror(mirrorPlane);
        
        int currentLayerIndex = doc.Layers.CurrentLayerIndex;
        
        // Create the mirrored copy
        Guid newId = doc.Objects.Transform(objId, xform, false);
        if (newId == Guid.Empty)
            throw new InvalidOperationException("Failed to create mirrored copy");
        
        // Set layer
        RhinoObject newObj = doc.Objects.FindId(newId);
        if (newObj != null)
        {
            ObjectAttributes attrs = newObj.Attributes.Duplicate();
            attrs.LayerIndex = currentLayerIndex;
            doc.Objects.ModifyAttributes(newObj, attrs, true);
        }
        
        if (deleteInput)
        {
            doc.Objects.Delete(obj, true);
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_id = objectIdStr,
            mirror_id = newId.ToString(),
            deleted_input = deleteInput
        });
    }
    
    /// <summary>
    /// Create a linear array of objects.
    /// </summary>
    public JObject ArrayLinear(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string objectIdStr = parameters["object_id"]?.ToString();
        if (string.IsNullOrEmpty(objectIdStr))
            throw new ArgumentException("object_id is required");
        
        if (!Guid.TryParse(objectIdStr, out Guid objId))
            throw new ArgumentException($"Invalid GUID: {objectIdStr}");
        
        RhinoObject obj = doc.Objects.FindId(objId);
        if (obj == null)
            throw new ArgumentException($"Object not found: {objectIdStr}");
        
        var directionArray = parameters["direction"]?.ToObject<double[]>();
        if (directionArray == null || directionArray.Length != 3)
            throw new ArgumentException("direction must be [x, y, z]");
        
        int count = parameters["count"]?.Value<int>() ?? 2;
        if (count < 2)
            throw new ArgumentException("count must be at least 2");
        
        double spacing = parameters["spacing"]?.Value<double>() ?? 10.0;
        if (spacing <= 0)
            throw new ArgumentException("spacing must be positive");
        
        Vector3d direction = new Vector3d(directionArray[0], directionArray[1], directionArray[2]);
        direction.Unitize();
        
        List<string> newIds = new List<string>();
        int currentLayerIndex = doc.Layers.CurrentLayerIndex;
        
        // Create count-1 copies (original is included in count)
        for (int i = 1; i < count; i++)
        {
            Vector3d translation = direction * spacing * i;
            Transform xform = Transform.Translation(translation);
            
            Guid newId = doc.Objects.Transform(objId, xform, false);
            if (newId != Guid.Empty)
            {
                // Set layer
                RhinoObject newObj = doc.Objects.FindId(newId);
                if (newObj != null)
                {
                    ObjectAttributes attrs = newObj.Attributes.Duplicate();
                    attrs.LayerIndex = currentLayerIndex;
                    doc.Objects.ModifyAttributes(newObj, attrs, true);
                }
                newIds.Add(newId.ToString());
            }
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_id = objectIdStr,
            array_ids = newIds,
            total_count = count,
            spacing = spacing
        });
    }
    
    /// <summary>
    /// Create a polar (radial) array of objects around a center point.
    /// </summary>
    public JObject ArrayPolar(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string objectIdStr = parameters["object_id"]?.ToString();
        if (string.IsNullOrEmpty(objectIdStr))
            throw new ArgumentException("object_id is required");
        
        if (!Guid.TryParse(objectIdStr, out Guid objId))
            throw new ArgumentException($"Invalid GUID: {objectIdStr}");
        
        RhinoObject obj = doc.Objects.FindId(objId);
        if (obj == null)
            throw new ArgumentException($"Object not found: {objectIdStr}");
        
        var centerArray = parameters["center"]?.ToObject<double[]>();
        if (centerArray == null || centerArray.Length != 3)
            throw new ArgumentException("center must be [x, y, z]");
        
        var axisArray = parameters["axis"]?.ToObject<double[]>();
        if (axisArray == null || axisArray.Length != 3)
            throw new ArgumentException("axis must be [x, y, z]");
        
        int count = parameters["count"]?.Value<int>() ?? 6;
        if (count < 2)
            throw new ArgumentException("count must be at least 2");
        
        double totalAngleDegrees = parameters["angle"]?.Value<double>() ?? 360.0;
        
        Point3d center = new Point3d(centerArray[0], centerArray[1], centerArray[2]);
        Vector3d axis = new Vector3d(axisArray[0], axisArray[1], axisArray[2]);
        axis.Unitize();
        
        // Calculate angle step
        // If full circle (360), divide evenly
        // If partial, divide by count-1 to include endpoints
        double angleStepDegrees;
        if (Math.Abs(totalAngleDegrees - 360.0) < 0.001)
        {
            angleStepDegrees = totalAngleDegrees / count;
        }
        else
        {
            angleStepDegrees = totalAngleDegrees / (count - 1);
        }
        
        double angleStepRadians = angleStepDegrees * Math.PI / 180.0;
        
        List<string> newIds = new List<string>();
        int currentLayerIndex = doc.Layers.CurrentLayerIndex;
        
        // Create count-1 copies (original is included in count)
        for (int i = 1; i < count; i++)
        {
            double rotationAngle = angleStepRadians * i;
            Transform xform = Transform.Rotation(rotationAngle, axis, center);
            
            Guid newId = doc.Objects.Transform(objId, xform, false);
            if (newId != Guid.Empty)
            {
                // Set layer
                RhinoObject newObj = doc.Objects.FindId(newId);
                if (newObj != null)
                {
                    ObjectAttributes attrs = newObj.Attributes.Duplicate();
                    attrs.LayerIndex = currentLayerIndex;
                    doc.Objects.ModifyAttributes(newObj, attrs, true);
                }
                newIds.Add(newId.ToString());
            }
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_id = objectIdStr,
            array_ids = newIds,
            total_count = count,
            angle = totalAngleDegrees
        });
    }
}
