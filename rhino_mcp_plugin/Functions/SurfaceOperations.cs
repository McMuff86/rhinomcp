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
    /// Create a lofted surface between multiple curves.
    /// </summary>
    public JObject LoftCurves(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        // Parse curve IDs
        var curveIdsToken = parameters["curve_ids"];
        if (curveIdsToken == null)
            throw new ArgumentException("curve_ids is required");
        
        var curveIdStrings = curveIdsToken.ToObject<string[]>();
        if (curveIdStrings == null || curveIdStrings.Length < 2)
            throw new ArgumentException("At least 2 curve IDs are required for loft");
        
        // Get all curves
        List<Curve> curves = new List<Curve>();
        foreach (string idStr in curveIdStrings)
        {
            if (!Guid.TryParse(idStr, out Guid curveId))
                throw new ArgumentException($"Invalid GUID: {idStr}");
            
            RhinoObject obj = doc.Objects.FindId(curveId);
            if (obj == null)
                throw new ArgumentException($"Object not found: {idStr}");
            
            Curve curve = obj.Geometry as Curve;
            if (curve == null)
                throw new ArgumentException($"Object is not a curve: {idStr}");
            
            curves.Add(curve);
        }
        
        // Parse options
        bool closed = parameters["closed"]?.Value<bool>() ?? false;
        string loftTypeStr = parameters["loft_type"]?.ToString()?.ToUpper() ?? "NORMAL";
        
        LoftType loftType = loftTypeStr switch
        {
            "LOOSE" => LoftType.Loose,
            "TIGHT" => LoftType.Tight,
            "STRAIGHT" => LoftType.Straight,
            _ => LoftType.Normal
        };
        
        // Create loft
        Brep[] loftResult = Brep.CreateFromLoft(
            curves,
            Point3d.Unset,  // start point (unset = use curve end)
            Point3d.Unset,  // end point (unset = use curve end)
            loftType,
            closed
        );
        
        if (loftResult == null || loftResult.Length == 0)
            throw new InvalidOperationException("Loft operation failed - could not create surface from curves");
        
        List<string> newIds = new List<string>();
        int currentLayerIndex = doc.Layers.CurrentLayerIndex;
        
        foreach (Brep brep in loftResult)
        {
            ObjectAttributes attrs = new ObjectAttributes();
            attrs.LayerIndex = currentLayerIndex;
            
            Guid newId = doc.Objects.AddBrep(brep, attrs);
            if (newId != Guid.Empty)
            {
                newIds.Add(newId.ToString());
            }
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_curve_ids = curveIdStrings,
            loft_ids = newIds,
            loft_type = loftTypeStr.ToLower(),
            closed = closed
        });
    }
    
    /// <summary>
    /// Extrude a curve along a direction vector.
    /// </summary>
    public JObject ExtrudeCurve(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string curveIdStr = parameters["curve_id"]?.ToString();
        if (string.IsNullOrEmpty(curveIdStr))
            throw new ArgumentException("curve_id is required");
        
        if (!Guid.TryParse(curveIdStr, out Guid curveId))
            throw new ArgumentException($"Invalid GUID: {curveIdStr}");
        
        RhinoObject obj = doc.Objects.FindId(curveId);
        if (obj == null)
            throw new ArgumentException($"Object not found: {curveIdStr}");
        
        Curve curve = obj.Geometry as Curve;
        if (curve == null)
            throw new ArgumentException($"Object is not a curve: {curveIdStr}");
        
        // Parse direction
        var directionArray = parameters["direction"]?.ToObject<double[]>();
        if (directionArray == null || directionArray.Length != 3)
            throw new ArgumentException("direction must be [x, y, z]");
        
        Vector3d direction = new Vector3d(directionArray[0], directionArray[1], directionArray[2]);
        
        if (direction.IsZero)
            throw new ArgumentException("direction cannot be zero vector");
        
        // Check if distance is provided, scale direction vector
        double? distance = parameters["distance"]?.Value<double>();
        if (distance.HasValue)
        {
            direction.Unitize();
            direction *= distance.Value;
        }
        
        bool cap = parameters["cap"]?.Value<bool>() ?? true;
        
        // Check if curve is closed (for capping)
        bool isClosed = curve.IsClosed;
        
        Guid newId = Guid.Empty;
        string objectType = "surface";
        
        if (isClosed && cap)
        {
            // Create capped extrusion (solid)
            Extrusion extrusion = Extrusion.Create(curve, direction.Length, cap);
            
            if (extrusion == null)
            {
                // Fallback: create surface and cap manually
                Surface extrudedSurface = Surface.CreateExtrusion(curve, direction);
                if (extrudedSurface == null)
                    throw new InvalidOperationException("Extrusion failed - could not create surface");
                
                Brep brep = extrudedSurface.ToBrep();
                if (brep != null)
                {
                    brep = brep.CapPlanarHoles(doc.ModelAbsoluteTolerance);
                    if (brep != null)
                    {
                        ObjectAttributes attrs = new ObjectAttributes();
                        attrs.LayerIndex = doc.Layers.CurrentLayerIndex;
                        newId = doc.Objects.AddBrep(brep, attrs);
                        objectType = "solid";
                    }
                }
            }
            else
            {
                // Extrusion created successfully
                // Transform extrusion to correct position (Extrusion.Create creates at origin)
                Transform move = Transform.Translation(direction * 0); // Already positioned correctly
                
                ObjectAttributes attrs = new ObjectAttributes();
                attrs.LayerIndex = doc.Layers.CurrentLayerIndex;
                newId = doc.Objects.AddExtrusion(extrusion, attrs);
                objectType = "solid";
            }
        }
        else
        {
            // Create open surface extrusion
            Surface extrudedSurface = Surface.CreateExtrusion(curve, direction);
            
            if (extrudedSurface == null)
                throw new InvalidOperationException("Extrusion failed - could not create surface");
            
            ObjectAttributes attrs = new ObjectAttributes();
            attrs.LayerIndex = doc.Layers.CurrentLayerIndex;
            newId = doc.Objects.AddSurface(extrudedSurface, attrs);
            objectType = "surface";
        }
        
        if (newId == Guid.Empty)
            throw new InvalidOperationException("Extrusion failed - could not add object to document");
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_curve_id = curveIdStr,
            extrusion_id = newId.ToString(),
            direction = directionArray,
            distance = distance ?? direction.Length,
            capped = isClosed && cap,
            object_type = objectType
        });
    }
    
    /// <summary>
    /// Revolve a curve around an axis to create a surface of revolution.
    /// </summary>
    public JObject RevolveCurve(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string curveIdStr = parameters["curve_id"]?.ToString();
        if (string.IsNullOrEmpty(curveIdStr))
            throw new ArgumentException("curve_id is required");
        
        if (!Guid.TryParse(curveIdStr, out Guid curveId))
            throw new ArgumentException($"Invalid GUID: {curveIdStr}");
        
        RhinoObject obj = doc.Objects.FindId(curveId);
        if (obj == null)
            throw new ArgumentException($"Object not found: {curveIdStr}");
        
        Curve curve = obj.Geometry as Curve;
        if (curve == null)
            throw new ArgumentException($"Object is not a curve: {curveIdStr}");
        
        // Parse axis
        var axisStartArray = parameters["axis_start"]?.ToObject<double[]>();
        if (axisStartArray == null || axisStartArray.Length != 3)
            throw new ArgumentException("axis_start must be [x, y, z]");
        
        var axisEndArray = parameters["axis_end"]?.ToObject<double[]>();
        if (axisEndArray == null || axisEndArray.Length != 3)
            throw new ArgumentException("axis_end must be [x, y, z]");
        
        Point3d axisStart = new Point3d(axisStartArray[0], axisStartArray[1], axisStartArray[2]);
        Point3d axisEnd = new Point3d(axisEndArray[0], axisEndArray[1], axisEndArray[2]);
        
        if (axisStart.DistanceTo(axisEnd) < doc.ModelAbsoluteTolerance)
            throw new ArgumentException("axis_start and axis_end cannot be the same point");
        
        // Create axis line
        Line axisLine = new Line(axisStart, axisEnd);
        
        // Parse angle (degrees to radians)
        double angleDegrees = parameters["angle"]?.Value<double>() ?? 360.0;
        double angleRadians = angleDegrees * Math.PI / 180.0;
        
        if (Math.Abs(angleRadians) < doc.ModelAbsoluteTolerance)
            throw new ArgumentException("angle cannot be zero");
        
        // Create revolution surface
        RevSurface revSurface = RevSurface.Create(
            curve,
            axisLine,
            0,              // start angle
            angleRadians    // end angle
        );
        
        if (revSurface == null)
            throw new InvalidOperationException("Revolve operation failed - could not create surface of revolution");
        
        // Convert to Brep for better compatibility
        Brep brep = revSurface.ToBrep();
        if (brep == null)
            throw new InvalidOperationException("Revolve operation failed - could not convert to Brep");
        
        ObjectAttributes attrs = new ObjectAttributes();
        attrs.LayerIndex = doc.Layers.CurrentLayerIndex;
        
        Guid newId = doc.Objects.AddBrep(brep, attrs);
        
        if (newId == Guid.Empty)
            throw new InvalidOperationException("Revolve operation failed - could not add object to document");
        
        doc.Views.Redraw();
        
        bool isFullRevolution = Math.Abs(angleDegrees - 360.0) < 0.001 || Math.Abs(angleDegrees + 360.0) < 0.001;
        
        return JObject.FromObject(new
        {
            source_curve_id = curveIdStr,
            revolve_id = newId.ToString(),
            axis_start = axisStartArray,
            axis_end = axisEndArray,
            angle = angleDegrees,
            full_revolution = isFullRevolution
        });
    }
}
