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
    /// Create a text entity (annotation text).
    /// </summary>
    public JObject CreateText(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string text = parameters["text"]?.ToString();
        if (string.IsNullOrEmpty(text))
            throw new ArgumentException("text is required");
        
        // Position
        var positionArray = parameters["position"]?.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
        if (positionArray.Length != 3)
            throw new ArgumentException("position must be [x, y, z]");
        Point3d position = new Point3d(positionArray[0], positionArray[1], positionArray[2]);
        
        // Height
        double height = parameters["height"]?.Value<double>() ?? 1.0;
        if (height <= 0)
            throw new ArgumentException("height must be positive");
        
        // Font (optional)
        string fontName = parameters["font"]?.ToString() ?? "Arial";
        
        // Bold/Italic
        bool bold = parameters["bold"]?.Value<bool>() ?? false;
        bool italic = parameters["italic"]?.Value<bool>() ?? false;
        
        // Plane normal (default: looking at XY plane from +Z)
        var normalArray = parameters["normal"]?.ToObject<double[]>() ?? new double[] { 0, 0, 1 };
        Vector3d normal = new Vector3d(normalArray[0], normalArray[1], normalArray[2]);
        normal.Unitize();
        
        // Create plane at position
        Plane plane = new Plane(position, normal);
        
        // Get or create dimension style
        var dimStyle = doc.DimStyles.Current;
        
        // Create text entity
        var textEntity = TextEntity.Create(
            text,
            plane,
            dimStyle,
            false,  // wrapped
            0,      // rect width (0 = auto)
            0       // rotation
        );
        
        if (textEntity == null)
            throw new InvalidOperationException("Failed to create text entity");
        
        // Set text height
        textEntity.TextHeight = height;
        
        // Set font
        var font = new Rhino.DocObjects.Font(fontName, bold ? Rhino.DocObjects.Font.FontWeight.Bold : Rhino.DocObjects.Font.FontWeight.Normal, 
                                              italic ? Rhino.DocObjects.Font.FontStyle.Italic : Rhino.DocObjects.Font.FontStyle.Upright);
        textEntity.Font = font;
        
        // Object attributes
        ObjectAttributes attrs = new ObjectAttributes();
        attrs.LayerIndex = doc.Layers.CurrentLayerIndex;
        
        // Name
        string name = parameters["name"]?.ToString();
        if (!string.IsNullOrEmpty(name))
            attrs.Name = name;
        
        // Color
        var colorArray = parameters["color"]?.ToObject<int[]>();
        if (colorArray != null && colorArray.Length >= 3)
        {
            attrs.ColorSource = ObjectColorSource.ColorFromObject;
            attrs.ObjectColor = System.Drawing.Color.FromArgb(colorArray[0], colorArray[1], colorArray[2]);
        }
        
        // Add to document
        Guid newId = doc.Objects.AddText(textEntity, attrs);
        
        if (newId == Guid.Empty)
            throw new InvalidOperationException("Failed to add text to document");
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            id = newId.ToString(),
            text = text,
            position = positionArray,
            height = height,
            font = fontName
        });
    }
    
    /// <summary>
    /// Create 3D text (extruded text curves).
    /// </summary>
    public JObject Create3DText(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string text = parameters["text"]?.ToString();
        if (string.IsNullOrEmpty(text))
            throw new ArgumentException("text is required");
        
        // Position
        var positionArray = parameters["position"]?.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
        Point3d position = new Point3d(positionArray[0], positionArray[1], positionArray[2]);
        
        // Height (text height)
        double height = parameters["height"]?.Value<double>() ?? 1.0;
        
        // Depth (extrusion depth)
        double depth = parameters["depth"]?.Value<double>() ?? height * 0.2;
        
        // Font
        string fontName = parameters["font"]?.ToString() ?? "Arial";
        bool bold = parameters["bold"]?.Value<bool>() ?? false;
        bool italic = parameters["italic"]?.Value<bool>() ?? false;
        
        // Plane
        var normalArray = parameters["normal"]?.ToObject<double[]>() ?? new double[] { 0, 0, 1 };
        Vector3d normal = new Vector3d(normalArray[0], normalArray[1], normalArray[2]);
        normal.Unitize();
        Plane plane = new Plane(position, normal);
        
        // Create font
        var font = new Rhino.DocObjects.Font(fontName, 
            bold ? Rhino.DocObjects.Font.FontWeight.Bold : Rhino.DocObjects.Font.FontWeight.Normal,
            italic ? Rhino.DocObjects.Font.FontStyle.Italic : Rhino.DocObjects.Font.FontStyle.Upright);
        
        // Get text outlines as curves
        var dimStyle = doc.DimStyles.Current;
        Curve[] textCurves = Curve.CreateTextOutlines(text, font, height, 0, false, plane, 0.0, doc.ModelAbsoluteTolerance);
        
        if (textCurves == null || textCurves.Length == 0)
            throw new InvalidOperationException("Failed to create text curves");
        
        // Extrude curves
        Vector3d extrudeDir = normal * depth;
        
        List<string> newIds = new List<string>();
        ObjectAttributes attrs = new ObjectAttributes();
        attrs.LayerIndex = doc.Layers.CurrentLayerIndex;
        
        string name = parameters["name"]?.ToString();
        if (!string.IsNullOrEmpty(name))
            attrs.Name = name;
        
        var colorArray = parameters["color"]?.ToObject<int[]>();
        if (colorArray != null && colorArray.Length >= 3)
        {
            attrs.ColorSource = ObjectColorSource.ColorFromObject;
            attrs.ObjectColor = System.Drawing.Color.FromArgb(colorArray[0], colorArray[1], colorArray[2]);
        }
        
        foreach (Curve curve in textCurves)
        {
            if (curve.IsClosed)
            {
                // Create planar surface then extrude
                Brep[] planarBreps = Brep.CreatePlanarBreps(curve, doc.ModelAbsoluteTolerance);
                if (planarBreps != null)
                {
                    foreach (Brep planarBrep in planarBreps)
                    {
                        // Extrude the surface
                        Brep extruded = planarBrep.Faces[0].CreateExtrusion(new LineCurve(Point3d.Origin, new Point3d(extrudeDir)), true);
                        if (extruded != null)
                        {
                            Guid id = doc.Objects.AddBrep(extruded, attrs);
                            if (id != Guid.Empty)
                                newIds.Add(id.ToString());
                        }
                    }
                }
            }
        }
        
        // If no solids created, add the curves instead
        if (newIds.Count == 0)
        {
            foreach (Curve curve in textCurves)
            {
                Guid id = doc.Objects.AddCurve(curve, attrs);
                if (id != Guid.Empty)
                    newIds.Add(id.ToString());
            }
        }
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            ids = newIds,
            text = text,
            height = height,
            depth = depth,
            count = newIds.Count
        });
    }
    
    /// <summary>
    /// Create a text dot (screen-oriented label).
    /// </summary>
    public JObject CreateTextDot(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string text = parameters["text"]?.ToString();
        if (string.IsNullOrEmpty(text))
            throw new ArgumentException("text is required");
        
        var positionArray = parameters["position"]?.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
        Point3d position = new Point3d(positionArray[0], positionArray[1], positionArray[2]);
        
        string secondaryText = parameters["secondary_text"]?.ToString() ?? "";
        
        // Create text dot
        TextDot dot = new TextDot(text, position);
        if (!string.IsNullOrEmpty(secondaryText))
        {
            dot.SecondaryText = secondaryText;
        }
        
        // Font height (optional)
        int fontHeight = parameters["font_height"]?.Value<int>() ?? 14;
        dot.FontHeight = fontHeight;
        
        ObjectAttributes attrs = new ObjectAttributes();
        attrs.LayerIndex = doc.Layers.CurrentLayerIndex;
        
        string name = parameters["name"]?.ToString();
        if (!string.IsNullOrEmpty(name))
            attrs.Name = name;
        
        Guid newId = doc.Objects.AddTextDot(dot, attrs);
        
        if (newId == Guid.Empty)
            throw new InvalidOperationException("Failed to add text dot");
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            id = newId.ToString(),
            text = text,
            position = positionArray,
            font_height = fontHeight
        });
    }
    
    /// <summary>
    /// Create a leader (annotation with arrow pointing to geometry).
    /// </summary>
    public JObject CreateLeader(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string text = parameters["text"]?.ToString() ?? "";
        
        var pointsArray = parameters["points"]?.ToObject<double[][]>();
        if (pointsArray == null || pointsArray.Length < 2)
            throw new ArgumentException("points array with at least 2 points is required");
        
        List<Point3d> points = new List<Point3d>();
        foreach (var pt in pointsArray)
        {
            if (pt.Length != 3)
                throw new ArgumentException("Each point must be [x, y, z]");
            points.Add(new Point3d(pt[0], pt[1], pt[2]));
        }
        
        // Create plane from first two points
        Vector3d dir = points[1] - points[0];
        Plane plane = new Plane(points[0], Vector3d.ZAxis);
        
        // Create leader using 2D points on plane
        List<Point2d> points2d = new List<Point2d>();
        foreach (Point3d pt3d in points)
        {
            double u, v;
            plane.ClosestParameter(pt3d, out u, out v);
            points2d.Add(new Point2d(u, v));
        }
        
        var dimStyle = doc.DimStyles.Current;
        Leader leader = Leader.Create(text, plane, dimStyle, points2d);
        
        if (leader == null)
            throw new InvalidOperationException("Failed to create leader");
        
        ObjectAttributes attrs = new ObjectAttributes();
        attrs.LayerIndex = doc.Layers.CurrentLayerIndex;
        
        Guid newId = doc.Objects.AddLeader(leader, attrs);
        
        if (newId == Guid.Empty)
            throw new InvalidOperationException("Failed to add leader");
        
        doc.Views.Redraw();
        
        return JObject.FromObject(new
        {
            id = newId.ToString(),
            text = text,
            point_count = points.Count
        });
    }
}
