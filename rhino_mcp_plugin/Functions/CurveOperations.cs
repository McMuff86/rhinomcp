using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Geometry.Intersect;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Offset a curve by a specified distance.
    /// </summary>
    public JObject OffsetCurve(JObject parameters)
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
        
        double distance = parameters["distance"]?.Value<double>() ?? 0;
        if (Math.Abs(distance) < doc.ModelAbsoluteTolerance)
            throw new ArgumentException("distance cannot be zero");
        
        // Get plane for offset
        var originArray = parameters["plane_origin"]?.ToObject<double[]>();
        var normalArray = parameters["plane_normal"]?.ToObject<double[]>() ?? new double[] { 0, 0, 1 };
        
        Point3d planeOrigin;
        if (originArray != null && originArray.Length == 3)
        {
            planeOrigin = new Point3d(originArray[0], originArray[1], originArray[2]);
        }
        else
        {
            // Use curve start point as default
            planeOrigin = curve.PointAtStart;
        }
        
        if (normalArray.Length != 3)
            throw new ArgumentException("plane_normal must be [x, y, z]");
        
        Vector3d normal = new Vector3d(normalArray[0], normalArray[1], normalArray[2]);
        normal.Unitize();
        
        Plane offsetPlane = new Plane(planeOrigin, normal);
        
        // Parse corner style
        string cornerStyleStr = parameters["corner_style"]?.ToString() ?? "sharp";
        CurveOffsetCornerStyle cornerStyle = cornerStyleStr.ToLower() switch
        {
            "round" => CurveOffsetCornerStyle.Round,
            "smooth" => CurveOffsetCornerStyle.Smooth,
            "chamfer" => CurveOffsetCornerStyle.Chamfer,
            _ => CurveOffsetCornerStyle.Sharp
        };
        
        // Perform offset
        Curve[] offsetCurves = curve.Offset(offsetPlane, distance, doc.ModelAbsoluteTolerance, cornerStyle);
        
        if (offsetCurves == null || offsetCurves.Length == 0)
            throw new InvalidOperationException("Offset operation failed - no result curves generated");
        
        List<string> newIds = new List<string>();
        int currentLayerIndex = doc.Layers.CurrentLayerIndex;
        
        foreach (Curve offsetCurve in offsetCurves)
        {
            ObjectAttributes attrs = new ObjectAttributes();
            attrs.LayerIndex = currentLayerIndex;
            
            Guid newId = doc.Objects.AddCurve(offsetCurve, attrs);
            if (newId != Guid.Empty)
            {
                newIds.Add(newId.ToString());
            }
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            source_id = curveIdStr,
            offset_ids = newIds,
            distance = distance,
            corner_style = cornerStyleStr
        });
    }
    
    /// <summary>
    /// Create a fillet arc between two curves.
    /// </summary>
    public JObject FilletCurves(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string curveId1Str = parameters["curve_id_1"]?.ToString();
        if (string.IsNullOrEmpty(curveId1Str))
            throw new ArgumentException("curve_id_1 is required");
        
        string curveId2Str = parameters["curve_id_2"]?.ToString();
        if (string.IsNullOrEmpty(curveId2Str))
            throw new ArgumentException("curve_id_2 is required");
        
        if (!Guid.TryParse(curveId1Str, out Guid curveId1))
            throw new ArgumentException($"Invalid GUID: {curveId1Str}");
        
        if (!Guid.TryParse(curveId2Str, out Guid curveId2))
            throw new ArgumentException($"Invalid GUID: {curveId2Str}");
        
        RhinoObject obj1 = doc.Objects.FindId(curveId1);
        if (obj1 == null)
            throw new ArgumentException($"Object not found: {curveId1Str}");
        
        RhinoObject obj2 = doc.Objects.FindId(curveId2);
        if (obj2 == null)
            throw new ArgumentException($"Object not found: {curveId2Str}");
        
        Curve curve1 = obj1.Geometry as Curve;
        if (curve1 == null)
            throw new ArgumentException($"Object is not a curve: {curveId1Str}");
        
        Curve curve2 = obj2.Geometry as Curve;
        if (curve2 == null)
            throw new ArgumentException($"Object is not a curve: {curveId2Str}");
        
        double radius = parameters["radius"]?.Value<double>() ?? 0;
        if (radius <= 0)
            throw new ArgumentException("radius must be positive");
        
        bool join = parameters["join"]?.Value<bool>() ?? false;
        
        // Get optional points on curves
        Point3d point1, point2;
        var point1Array = parameters["point_on_curve_1"]?.ToObject<double[]>();
        var point2Array = parameters["point_on_curve_2"]?.ToObject<double[]>();
        
        if (point1Array != null && point1Array.Length == 3)
        {
            point1 = new Point3d(point1Array[0], point1Array[1], point1Array[2]);
        }
        else
        {
            // Use midpoint of curve1
            point1 = curve1.PointAt(curve1.Domain.Mid);
        }
        
        if (point2Array != null && point2Array.Length == 3)
        {
            point2 = new Point3d(point2Array[0], point2Array[1], point2Array[2]);
        }
        else
        {
            // Use midpoint of curve2
            point2 = curve2.PointAt(curve2.Domain.Mid);
        }
        
        double tolerance = doc.ModelAbsoluteTolerance;
        
        // Create fillet curves
        Curve[] filletResult = Curve.CreateFilletCurves(
            curve1, point1,
            curve2, point2,
            radius,
            join,      // join
            join,      // trim (only trim if joining)
            true,      // arcExtension
            tolerance,
            tolerance
        );
        
        if (filletResult == null || filletResult.Length == 0)
            throw new InvalidOperationException("Fillet operation failed - curves may not intersect or radius too large");
        
        List<string> newIds = new List<string>();
        int currentLayerIndex = doc.Layers.CurrentLayerIndex;
        
        foreach (Curve resultCurve in filletResult)
        {
            ObjectAttributes attrs = new ObjectAttributes();
            attrs.LayerIndex = currentLayerIndex;
            
            Guid newId = doc.Objects.AddCurve(resultCurve, attrs);
            if (newId != Guid.Empty)
            {
                newIds.Add(newId.ToString());
            }
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            curve_id_1 = curveId1Str,
            curve_id_2 = curveId2Str,
            fillet_ids = newIds,
            radius = radius,
            joined = join
        });
    }
    
    /// <summary>
    /// Create a chamfer (angled line) between two curves.
    /// </summary>
    public JObject ChamferCurves(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string curveId1Str = parameters["curve_id_1"]?.ToString();
        if (string.IsNullOrEmpty(curveId1Str))
            throw new ArgumentException("curve_id_1 is required");
        
        string curveId2Str = parameters["curve_id_2"]?.ToString();
        if (string.IsNullOrEmpty(curveId2Str))
            throw new ArgumentException("curve_id_2 is required");
        
        if (!Guid.TryParse(curveId1Str, out Guid curveId1))
            throw new ArgumentException($"Invalid GUID: {curveId1Str}");
        
        if (!Guid.TryParse(curveId2Str, out Guid curveId2))
            throw new ArgumentException($"Invalid GUID: {curveId2Str}");
        
        RhinoObject obj1 = doc.Objects.FindId(curveId1);
        if (obj1 == null)
            throw new ArgumentException($"Object not found: {curveId1Str}");
        
        RhinoObject obj2 = doc.Objects.FindId(curveId2);
        if (obj2 == null)
            throw new ArgumentException($"Object not found: {curveId2Str}");
        
        Curve curve1 = obj1.Geometry as Curve;
        if (curve1 == null)
            throw new ArgumentException($"Object is not a curve: {curveId1Str}");
        
        Curve curve2 = obj2.Geometry as Curve;
        if (curve2 == null)
            throw new ArgumentException($"Object is not a curve: {curveId2Str}");
        
        double distance1 = parameters["distance_1"]?.Value<double>() ?? 0;
        if (distance1 <= 0)
            throw new ArgumentException("distance_1 must be positive");
        
        double distance2 = parameters["distance_2"]?.Value<double>() ?? distance1;
        if (distance2 <= 0)
            throw new ArgumentException("distance_2 must be positive");
        
        bool join = parameters["join"]?.Value<bool>() ?? false;
        bool trim = parameters["trim"]?.Value<bool>() ?? true;  // Default: trim original curves
        
        // Get optional points on curves
        Point3d point1, point2;
        var point1Array = parameters["point_on_curve_1"]?.ToObject<double[]>();
        var point2Array = parameters["point_on_curve_2"]?.ToObject<double[]>();
        
        if (point1Array != null && point1Array.Length == 3)
        {
            point1 = new Point3d(point1Array[0], point1Array[1], point1Array[2]);
        }
        else
        {
            // Use midpoint of curve1
            point1 = curve1.PointAt(curve1.Domain.Mid);
        }
        
        if (point2Array != null && point2Array.Length == 3)
        {
            point2 = new Point3d(point2Array[0], point2Array[1], point2Array[2]);
        }
        else
        {
            // Use midpoint of curve2
            point2 = curve2.PointAt(curve2.Domain.Mid);
        }
        
        double tolerance = doc.ModelAbsoluteTolerance;
        
        // Find intersection of the two curves to determine chamfer location
        var intersections = Intersection.CurveCurve(curve1, curve2, tolerance, tolerance);
        
        if (intersections == null || intersections.Count == 0)
            throw new InvalidOperationException("Chamfer operation failed - curves do not intersect");
        
        // Use first intersection point
        IntersectionEvent intersection = intersections[0];
        double t1 = intersection.ParameterA;
        double t2 = intersection.ParameterB;
        
        // Calculate points at chamfer distances from intersection
        // We need to determine direction based on the point hints
        double len1 = curve1.GetLength();
        double len2 = curve2.GetLength();
        
        // Normalize distances to curve lengths
        double arcLen1 = distance1;
        double arcLen2 = distance2;
        
        // Get points at chamfer distances
        Point3d chamferPt1, chamferPt2;
        double newT1, newT2;
        
        // Determine direction along curve1 from intersection
        curve1.LengthParameter(t1, out double lenAtT1);
        double targetLen1 = lenAtT1 - arcLen1;  // Try going "backwards" first
        if (targetLen1 < 0 || !curve1.LengthParameter(targetLen1, out newT1))
        {
            targetLen1 = lenAtT1 + arcLen1;  // Try going "forwards"
            if (!curve1.LengthParameter(targetLen1, out newT1))
                throw new InvalidOperationException("Could not calculate chamfer point on curve 1");
        }
        chamferPt1 = curve1.PointAt(newT1);
        
        // Determine direction along curve2 from intersection
        curve2.LengthParameter(t2, out double lenAtT2);
        double targetLen2 = lenAtT2 - arcLen2;  // Try going "backwards" first
        if (targetLen2 < 0 || !curve2.LengthParameter(targetLen2, out newT2))
        {
            targetLen2 = lenAtT2 + arcLen2;  // Try going "forwards"
            if (!curve2.LengthParameter(targetLen2, out newT2))
                throw new InvalidOperationException("Could not calculate chamfer point on curve 2");
        }
        chamferPt2 = curve2.PointAt(newT2);
        
        List<string> newIds = new List<string>();
        int currentLayerIndex = doc.Layers.CurrentLayerIndex;
        
        if (join)
        {
            // Create trimmed curves and chamfer line, then join
            Curve trimmed1, trimmed2;
            
            // Trim curve1 - keep the part away from intersection
            if (newT1 < t1)
            {
                trimmed1 = curve1.Trim(curve1.Domain.Min, newT1);
            }
            else
            {
                trimmed1 = curve1.Trim(newT1, curve1.Domain.Max);
            }
            
            // Trim curve2 - keep the part away from intersection
            if (newT2 < t2)
            {
                trimmed2 = curve2.Trim(curve2.Domain.Min, newT2);
            }
            else
            {
                trimmed2 = curve2.Trim(newT2, curve2.Domain.Max);
            }
            
            // Create chamfer line
            LineCurve chamferLine = new LineCurve(chamferPt1, chamferPt2);
            
            // Try to join all curves
            List<Curve> curvesToJoin = new List<Curve>();
            if (trimmed1 != null) curvesToJoin.Add(trimmed1);
            curvesToJoin.Add(chamferLine);
            if (trimmed2 != null) curvesToJoin.Add(trimmed2);
            
            Curve[] joined = Curve.JoinCurves(curvesToJoin, tolerance);
            
            if (joined != null && joined.Length > 0)
            {
                foreach (Curve joinedCurve in joined)
                {
                    ObjectAttributes attrs = new ObjectAttributes();
                    attrs.LayerIndex = currentLayerIndex;
                    Guid newId = doc.Objects.AddCurve(joinedCurve, attrs);
                    if (newId != Guid.Empty)
                        newIds.Add(newId.ToString());
                }
            }
            else
            {
                // If join failed, add curves separately
                foreach (Curve c in curvesToJoin)
                {
                    ObjectAttributes attrs = new ObjectAttributes();
                    attrs.LayerIndex = currentLayerIndex;
                    Guid newId = doc.Objects.AddCurve(c, attrs);
                    if (newId != Guid.Empty)
                        newIds.Add(newId.ToString());
                }
            }
        }
        else
        {
            // Create chamfer line
            LineCurve chamferLine = new LineCurve(chamferPt1, chamferPt2);
            
            ObjectAttributes attrs = new ObjectAttributes();
            attrs.LayerIndex = currentLayerIndex;
            
            // Add chamfer line
            Guid chamferId = doc.Objects.AddCurve(chamferLine, attrs);
            if (chamferId != Guid.Empty)
            {
                newIds.Add(chamferId.ToString());
            }
            
            // Trim original curves if requested
            if (trim)
            {
                // Trim curve1 - keep the part away from intersection
                Curve trimmed1;
                if (newT1 < t1)
                {
                    trimmed1 = curve1.Trim(curve1.Domain.Min, newT1);
                }
                else
                {
                    trimmed1 = curve1.Trim(newT1, curve1.Domain.Max);
                }
                
                // Trim curve2 - keep the part away from intersection
                Curve trimmed2;
                if (newT2 < t2)
                {
                    trimmed2 = curve2.Trim(curve2.Domain.Min, newT2);
                }
                else
                {
                    trimmed2 = curve2.Trim(newT2, curve2.Domain.Max);
                }
                
                // Replace original curves with trimmed versions
                if (trimmed1 != null)
                {
                    ObjectAttributes attrs1 = obj1.Attributes.Duplicate();
                    doc.Objects.Replace(curveId1, trimmed1);
                }
                
                if (trimmed2 != null)
                {
                    ObjectAttributes attrs2 = obj2.Attributes.Duplicate();
                    doc.Objects.Replace(curveId2, trimmed2);
                }
            }
        }
        
        if (newIds.Count == 0)
            throw new InvalidOperationException("Chamfer operation failed - could not create chamfer geometry");
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            curve_id_1 = curveId1Str,
            curve_id_2 = curveId2Str,
            chamfer_ids = newIds,
            distance_1 = distance1,
            distance_2 = distance2,
            joined = join,
            trimmed = trim
        });
    }
    
    /// <summary>
    /// Join multiple curves into polycurves where they meet.
    /// </summary>
    public JObject JoinCurves(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        var curveIds = parameters["curve_ids"]?.ToObject<List<string>>();
        if (curveIds == null || curveIds.Count < 2)
            throw new ArgumentException("At least 2 curve_ids are required");
        
        bool deleteInput = parameters["delete_input"]?.Value<bool>() ?? true;
        double tolerance = parameters["tolerance"]?.Value<double>() ?? doc.ModelAbsoluteTolerance;
        
        List<Curve> curves = new List<Curve>();
        List<RhinoObject> inputObjects = new List<RhinoObject>();
        
        foreach (string idStr in curveIds)
        {
            if (!Guid.TryParse(idStr, out Guid objId))
                throw new ArgumentException($"Invalid GUID: {idStr}");
            
            RhinoObject obj = doc.Objects.FindId(objId);
            if (obj == null)
                throw new ArgumentException($"Object not found: {idStr}");
            
            Curve curve = obj.Geometry as Curve;
            if (curve == null)
                throw new ArgumentException($"Object is not a curve: {idStr}");
            
            curves.Add(curve);
            inputObjects.Add(obj);
        }
        
        Curve[] joinedCurves = Curve.JoinCurves(curves, tolerance);
        
        if (joinedCurves == null || joinedCurves.Length == 0)
            throw new InvalidOperationException("Join operation failed - curves may not be connected");
        
        List<string> newIds = new List<string>();
        int currentLayerIndex = doc.Layers.CurrentLayerIndex;
        
        foreach (Curve joinedCurve in joinedCurves)
        {
            ObjectAttributes attrs = new ObjectAttributes();
            attrs.LayerIndex = currentLayerIndex;
            
            Guid newId = doc.Objects.AddCurve(joinedCurve, attrs);
            if (newId != Guid.Empty)
            {
                newIds.Add(newId.ToString());
            }
        }
        
        if (deleteInput)
        {
            foreach (RhinoObject obj in inputObjects)
            {
                doc.Objects.Delete(obj, true);
            }
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            input_count = curveIds.Count,
            result_ids = newIds,
            result_count = newIds.Count,
            deleted_input = deleteInput
        });
    }
    
    /// <summary>
    /// Explode a polycurve into its segments.
    /// </summary>
    public JObject ExplodeCurve(JObject parameters)
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
        
        bool deleteInput = parameters["delete_input"]?.Value<bool>() ?? true;
        
        // Get curve segments
        Curve[] segments = null;
        
        if (curve is PolyCurve polyCurve)
        {
            segments = polyCurve.Explode();
        }
        else if (curve is PolylineCurve polyline)
        {
            // Convert to segments
            var pts = new List<Point3d>();
            for (int i = 0; i < polyline.PointCount; i++)
            {
                pts.Add(polyline.Point(i));
            }
            
            segments = new Curve[pts.Count - 1];
            for (int i = 0; i < pts.Count - 1; i++)
            {
                segments[i] = new LineCurve(pts[i], pts[i + 1]);
            }
        }
        else
        {
            // Single segment curve, nothing to explode
            return JObject.FromObject(new
            {
                source_id = curveIdStr,
                segment_ids = new string[] { curveIdStr },
                segment_count = 1,
                message = "Curve has only one segment"
            });
        }
        
        if (segments == null || segments.Length == 0)
            throw new InvalidOperationException("Explode operation failed - no segments generated");
        
        List<string> newIds = new List<string>();
        int currentLayerIndex = obj.Attributes.LayerIndex;
        
        foreach (Curve segment in segments)
        {
            ObjectAttributes attrs = obj.Attributes.Duplicate();
            
            Guid newId = doc.Objects.AddCurve(segment, attrs);
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
            source_id = curveIdStr,
            segment_ids = newIds,
            segment_count = newIds.Count,
            deleted_input = deleteInput
        });
    }
}
