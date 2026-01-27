using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Geometry.Collections;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Fillet edges of a solid (Brep).
    /// </summary>
    public JObject FilletEdges(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string objectIdStr = parameters["object_id"]?.ToString();
        if (string.IsNullOrEmpty(objectIdStr))
            throw new ArgumentException("object_id is required");
        
        if (!Guid.TryParse(objectIdStr, out Guid objectId))
            throw new ArgumentException($"Invalid GUID: {objectIdStr}");
        
        RhinoObject obj = doc.Objects.FindId(objectId);
        if (obj == null)
            throw new ArgumentException($"Object not found: {objectIdStr}");
        
        Brep brep = null;
        if (obj.Geometry is Brep b)
        {
            brep = b.DuplicateBrep();
        }
        else if (obj.Geometry is Extrusion ext)
        {
            brep = ext.ToBrep();
        }
        else
        {
            throw new ArgumentException($"Object is not a solid: {objectIdStr}");
        }
        
        double radius = parameters["radius"]?.Value<double>() ?? 0;
        if (radius <= 0)
            throw new ArgumentException("radius must be positive");
        
        // Get edge indices to fillet (optional - if not provided, fillet all edges)
        var edgeIndices = parameters["edge_indices"]?.ToObject<int[]>();
        
        double tolerance = doc.ModelAbsoluteTolerance;
        
        // Build arrays for FilletEdges
        int edgeCount = edgeIndices?.Length ?? brep.Edges.Count;
        int[] edges = edgeIndices ?? Enumerable.Range(0, brep.Edges.Count).ToArray();
        double[] radii = Enumerable.Repeat(radius, edgeCount).ToArray();
        
        // Create fillet
        Brep[] filletedBreps = Brep.CreateFilletEdges(
            brep,
            edges,
            radii,
            radii,  // Same radius for both sides
            BlendType.Fillet,
            RailType.DistanceFromEdge,
            tolerance
        );
        
        if (filletedBreps == null || filletedBreps.Length == 0)
            throw new InvalidOperationException("Fillet operation failed - radius may be too large for some edges");
        
        // Delete original and add new
        bool deleteInput = parameters["delete_input"]?.Value<bool>() ?? true;
        
        List<string> newIds = new List<string>();
        ObjectAttributes attrs = obj.Attributes.Duplicate();
        
        foreach (Brep filletedBrep in filletedBreps)
        {
            Guid newId = doc.Objects.AddBrep(filletedBrep, attrs);
            if (newId != Guid.Empty)
            {
                newIds.Add(newId.ToString());
            }
        }
        
        if (deleteInput)
        {
            doc.Objects.Delete(obj, true);
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_id = objectIdStr,
            result_ids = newIds,
            radius = radius,
            edges_filleted = edgeCount,
            deleted_input = deleteInput
        });
    }
    
    /// <summary>
    /// Chamfer edges of a solid (Brep).
    /// </summary>
    public JObject ChamferEdges(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string objectIdStr = parameters["object_id"]?.ToString();
        if (string.IsNullOrEmpty(objectIdStr))
            throw new ArgumentException("object_id is required");
        
        if (!Guid.TryParse(objectIdStr, out Guid objectId))
            throw new ArgumentException($"Invalid GUID: {objectIdStr}");
        
        RhinoObject obj = doc.Objects.FindId(objectId);
        if (obj == null)
            throw new ArgumentException($"Object not found: {objectIdStr}");
        
        Brep brep = null;
        if (obj.Geometry is Brep b)
        {
            brep = b.DuplicateBrep();
        }
        else if (obj.Geometry is Extrusion ext)
        {
            brep = ext.ToBrep();
        }
        else
        {
            throw new ArgumentException($"Object is not a solid: {objectIdStr}");
        }
        
        double distance = parameters["distance"]?.Value<double>() ?? 0;
        if (distance <= 0)
            throw new ArgumentException("distance must be positive");
        
        double distance2 = parameters["distance2"]?.Value<double>() ?? distance;
        
        // Get edge indices to chamfer (optional)
        var edgeIndices = parameters["edge_indices"]?.ToObject<int[]>();
        
        double tolerance = doc.ModelAbsoluteTolerance;
        
        // Build arrays for chamfer
        int edgeCount = edgeIndices?.Length ?? brep.Edges.Count;
        int[] edges = edgeIndices ?? Enumerable.Range(0, brep.Edges.Count).ToArray();
        double[] distances1 = Enumerable.Repeat(distance, edgeCount).ToArray();
        double[] distances2 = Enumerable.Repeat(distance2, edgeCount).ToArray();
        
        // Create chamfer using FilletEdges with Chamfer blend type
        Brep[] chamferedBreps = Brep.CreateFilletEdges(
            brep,
            edges,
            distances1,
            distances2,
            BlendType.Chamfer,
            RailType.DistanceFromEdge,
            tolerance
        );
        
        if (chamferedBreps == null || chamferedBreps.Length == 0)
            throw new InvalidOperationException("Chamfer operation failed - distance may be too large for some edges");
        
        bool deleteInput = parameters["delete_input"]?.Value<bool>() ?? true;
        
        List<string> newIds = new List<string>();
        ObjectAttributes attrs = obj.Attributes.Duplicate();
        
        foreach (Brep chamferedBrep in chamferedBreps)
        {
            Guid newId = doc.Objects.AddBrep(chamferedBrep, attrs);
            if (newId != Guid.Empty)
            {
                newIds.Add(newId.ToString());
            }
        }
        
        if (deleteInput)
        {
            doc.Objects.Delete(obj, true);
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_id = objectIdStr,
            result_ids = newIds,
            distance = distance,
            distance2 = distance2,
            edges_chamfered = edgeCount,
            deleted_input = deleteInput
        });
    }
    
    /// <summary>
    /// Split a Brep with another Brep or surface.
    /// </summary>
    public JObject SplitBrep(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string objectIdStr = parameters["object_id"]?.ToString();
        if (string.IsNullOrEmpty(objectIdStr))
            throw new ArgumentException("object_id is required");
        
        string cutterIdStr = parameters["cutter_id"]?.ToString();
        if (string.IsNullOrEmpty(cutterIdStr))
            throw new ArgumentException("cutter_id is required");
        
        if (!Guid.TryParse(objectIdStr, out Guid objectId))
            throw new ArgumentException($"Invalid GUID: {objectIdStr}");
        
        if (!Guid.TryParse(cutterIdStr, out Guid cutterId))
            throw new ArgumentException($"Invalid GUID: {cutterIdStr}");
        
        RhinoObject obj = doc.Objects.FindId(objectId);
        if (obj == null)
            throw new ArgumentException($"Object not found: {objectIdStr}");
        
        RhinoObject cutterObj = doc.Objects.FindId(cutterId);
        if (cutterObj == null)
            throw new ArgumentException($"Cutter not found: {cutterIdStr}");
        
        Brep brep = null;
        if (obj.Geometry is Brep b)
            brep = b;
        else if (obj.Geometry is Extrusion ext)
            brep = ext.ToBrep();
        else
            throw new ArgumentException($"Object is not a Brep: {objectIdStr}");
        
        Brep cutter = null;
        if (cutterObj.Geometry is Brep cb)
            cutter = cb;
        else if (cutterObj.Geometry is Extrusion cext)
            cutter = cext.ToBrep();
        else if (cutterObj.Geometry is Surface surf)
            cutter = surf.ToBrep();
        else
            throw new ArgumentException($"Cutter must be a Brep or Surface: {cutterIdStr}");
        
        double tolerance = doc.ModelAbsoluteTolerance;
        
        // Split the brep
        Brep[] splitBreps = brep.Split(cutter, tolerance);
        
        if (splitBreps == null || splitBreps.Length == 0)
            throw new InvalidOperationException("Split operation failed - objects may not intersect");
        
        bool deleteInput = parameters["delete_input"]?.Value<bool>() ?? true;
        bool deleteCutter = parameters["delete_cutter"]?.Value<bool>() ?? false;
        
        List<string> newIds = new List<string>();
        ObjectAttributes attrs = obj.Attributes.Duplicate();
        
        foreach (Brep splitBrep in splitBreps)
        {
            Guid newId = doc.Objects.AddBrep(splitBrep, attrs);
            if (newId != Guid.Empty)
            {
                newIds.Add(newId.ToString());
            }
        }
        
        if (deleteInput)
        {
            doc.Objects.Delete(obj, true);
        }
        
        if (deleteCutter)
        {
            doc.Objects.Delete(cutterObj, true);
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_id = objectIdStr,
            cutter_id = cutterIdStr,
            result_ids = newIds,
            result_count = newIds.Count,
            deleted_input = deleteInput,
            deleted_cutter = deleteCutter
        });
    }
    
    /// <summary>
    /// Trim a Brep with another Brep or surface, keeping specified side.
    /// </summary>
    public JObject TrimBrep(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string objectIdStr = parameters["object_id"]?.ToString();
        if (string.IsNullOrEmpty(objectIdStr))
            throw new ArgumentException("object_id is required");
        
        string cutterIdStr = parameters["cutter_id"]?.ToString();
        if (string.IsNullOrEmpty(cutterIdStr))
            throw new ArgumentException("cutter_id is required");
        
        if (!Guid.TryParse(objectIdStr, out Guid objectId))
            throw new ArgumentException($"Invalid GUID: {objectIdStr}");
        
        if (!Guid.TryParse(cutterIdStr, out Guid cutterId))
            throw new ArgumentException($"Invalid GUID: {cutterIdStr}");
        
        RhinoObject obj = doc.Objects.FindId(objectId);
        if (obj == null)
            throw new ArgumentException($"Object not found: {objectIdStr}");
        
        RhinoObject cutterObj = doc.Objects.FindId(cutterId);
        if (cutterObj == null)
            throw new ArgumentException($"Cutter not found: {cutterIdStr}");
        
        Brep brep = null;
        if (obj.Geometry is Brep b)
            brep = b;
        else if (obj.Geometry is Extrusion ext)
            brep = ext.ToBrep();
        else
            throw new ArgumentException($"Object is not a Brep: {objectIdStr}");
        
        Brep cutter = null;
        if (cutterObj.Geometry is Brep cb)
            cutter = cb;
        else if (cutterObj.Geometry is Extrusion cext)
            cutter = cext.ToBrep();
        else if (cutterObj.Geometry is Surface surf)
            cutter = surf.ToBrep();
        else
            throw new ArgumentException($"Cutter must be a Brep or Surface: {cutterIdStr}");
        
        // Point to determine which side to keep
        var keepPointArray = parameters["keep_point"]?.ToObject<double[]>();
        Point3d? keepPoint = null;
        if (keepPointArray != null && keepPointArray.Length == 3)
        {
            keepPoint = new Point3d(keepPointArray[0], keepPointArray[1], keepPointArray[2]);
        }
        
        double tolerance = doc.ModelAbsoluteTolerance;
        
        // Split first
        Brep[] splitBreps = brep.Split(cutter, tolerance);
        
        if (splitBreps == null || splitBreps.Length == 0)
            throw new InvalidOperationException("Trim operation failed - objects may not intersect");
        
        // If keep_point provided, find the piece containing that point
        List<Brep> keptBreps = new List<Brep>();
        
        if (keepPoint.HasValue)
        {
            foreach (Brep splitBrep in splitBreps)
            {
                // Check if point is inside or on the brep
                if (splitBrep.IsPointInside(keepPoint.Value, tolerance, false))
                {
                    keptBreps.Add(splitBrep);
                }
            }
            
            // If no brep contains the point, find closest one
            if (keptBreps.Count == 0)
            {
                double minDist = double.MaxValue;
                Brep closest = null;
                
                foreach (Brep splitBrep in splitBreps)
                {
                    Point3d closestPt = splitBrep.ClosestPoint(keepPoint.Value);
                    double dist = closestPt.DistanceTo(keepPoint.Value);
                    if (dist < minDist)
                    {
                        minDist = dist;
                        closest = splitBrep;
                    }
                }
                
                if (closest != null)
                    keptBreps.Add(closest);
            }
        }
        else
        {
            // No keep_point: keep the largest piece by volume
            Brep largest = splitBreps.OrderByDescending(sb => 
                VolumeMassProperties.Compute(sb)?.Volume ?? 0).FirstOrDefault();
            if (largest != null)
                keptBreps.Add(largest);
        }
        
        if (keptBreps.Count == 0)
            throw new InvalidOperationException("Trim operation failed - could not determine which piece to keep");
        
        bool deleteInput = parameters["delete_input"]?.Value<bool>() ?? true;
        bool deleteCutter = parameters["delete_cutter"]?.Value<bool>() ?? false;
        
        List<string> newIds = new List<string>();
        ObjectAttributes attrs = obj.Attributes.Duplicate();
        
        foreach (Brep keptBrep in keptBreps)
        {
            Guid newId = doc.Objects.AddBrep(keptBrep, attrs);
            if (newId != Guid.Empty)
            {
                newIds.Add(newId.ToString());
            }
        }
        
        if (deleteInput)
        {
            doc.Objects.Delete(obj, true);
        }
        
        if (deleteCutter)
        {
            doc.Objects.Delete(cutterObj, true);
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_id = objectIdStr,
            cutter_id = cutterIdStr,
            result_ids = newIds,
            deleted_input = deleteInput,
            deleted_cutter = deleteCutter
        });
    }
}
