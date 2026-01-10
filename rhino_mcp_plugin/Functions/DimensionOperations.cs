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
    /// Create a linear dimension between two points.
    /// </summary>
    public JObject CreateLinearDimension(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        // Parse parameters
        Point3d startPoint = castToPoint3d(parameters.SelectToken("start_point"));
        Point3d endPoint = castToPoint3d(parameters.SelectToken("end_point"));
        Point3d textPoint = castToPoint3d(parameters.SelectToken("text_point"));
        
        // Optional: dimension style name
        string styleName = castToString(parameters.SelectToken("dimension_style"));
        
        // Get dimension style
        DimensionStyle dimStyle = doc.DimStyles.Current;
        if (!string.IsNullOrEmpty(styleName))
        {
            var foundStyle = doc.DimStyles.FindName(styleName);
            if (foundStyle != null)
            {
                dimStyle = foundStyle;
            }
        }
        
        // Determine the dimension plane and direction
        // Calculate the direction from start to end
        Vector3d direction = endPoint - startPoint;
        direction.Unitize();
        
        // Create a plane that contains both points
        Plane dimPlane;
        if (Math.Abs(direction.Z) < 0.99)
        {
            // Use world Z for cross product
            Vector3d yAxis = Vector3d.CrossProduct(Vector3d.ZAxis, direction);
            yAxis.Unitize();
            dimPlane = new Plane(startPoint, direction, yAxis);
        }
        else
        {
            // Direction is nearly vertical, use world X
            Vector3d yAxis = Vector3d.CrossProduct(direction, Vector3d.XAxis);
            yAxis.Unitize();
            dimPlane = new Plane(startPoint, direction, yAxis);
        }
        
        // Create the linear dimension - use Point3d directly
        var dimension = LinearDimension.Create(
            AnnotationType.Aligned,
            dimStyle,
            dimPlane,
            Vector3d.XAxis,  // horizontal direction in plane
            startPoint,
            endPoint,
            textPoint,
            0.0  // rotation angle
        );
        
        if (dimension == null)
        {
            throw new InvalidOperationException("Failed to create linear dimension");
        }
        
        // Add to document
        Guid objectId = doc.Objects.AddLinearDimension(dimension);
        
        if (objectId == Guid.Empty)
        {
            throw new InvalidOperationException("Failed to add linear dimension to document");
        }
        
        // Set layer
        var rhinoObject = doc.Objects.Find(objectId);
        if (rhinoObject != null)
        {
            rhinoObject.Attributes.LayerIndex = doc.Layers.CurrentLayerIndex;
            doc.Objects.ModifyAttributes(rhinoObject, rhinoObject.Attributes, true);
        }
        
        doc.Views.Redraw();
        
        RhinoApp.WriteLine($"[DIMENSION CREATED] Linear dimension: {objectId}");
        
        return new JObject
        {
            ["id"] = objectId.ToString(),
            ["type"] = "linear_dimension",
            ["distance"] = startPoint.DistanceTo(endPoint)
        };
    }
    
    /// <summary>
    /// Create an angular dimension between two lines meeting at a vertex.
    /// </summary>
    public JObject CreateAngularDimension(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        // Parse parameters
        Point3d vertex = castToPoint3d(parameters.SelectToken("vertex"));
        Point3d startPoint = castToPoint3d(parameters.SelectToken("start_point"));
        Point3d endPoint = castToPoint3d(parameters.SelectToken("end_point"));
        Point3d textPoint = castToPoint3d(parameters.SelectToken("text_point"));
        
        // Optional: dimension style name
        string styleName = castToString(parameters.SelectToken("dimension_style"));
        
        // Get dimension style
        DimensionStyle dimStyle = doc.DimStyles.Current;
        if (!string.IsNullOrEmpty(styleName))
        {
            var foundStyle = doc.DimStyles.FindName(styleName);
            if (foundStyle != null)
            {
                dimStyle = foundStyle;
            }
        }
        
        // Calculate vectors from vertex to points
        Vector3d vec1 = startPoint - vertex;
        Vector3d vec2 = endPoint - vertex;
        vec1.Unitize();
        vec2.Unitize();
        
        // Create the plane for the angular dimension
        // Normal is perpendicular to both vectors
        Vector3d normal = Vector3d.CrossProduct(vec1, vec2);
        if (normal.Length < 0.001)
        {
            // Vectors are parallel, use Z axis as normal
            normal = Vector3d.ZAxis;
        }
        normal.Unitize();
        
        Plane dimPlane = new Plane(vertex, vec1, Vector3d.CrossProduct(normal, vec1));
        
        // Create angular dimension
        var dimension = AngularDimension.Create(
            dimStyle,
            dimPlane,
            Vector3d.XAxis,
            vertex,
            startPoint,
            endPoint,
            textPoint
        );
        
        if (dimension == null)
        {
            throw new InvalidOperationException("Failed to create angular dimension");
        }
        
        // Add to document
        Guid objectId = doc.Objects.AddAngularDimension(dimension);
        
        if (objectId == Guid.Empty)
        {
            throw new InvalidOperationException("Failed to add angular dimension to document");
        }
        
        // Set layer
        var rhinoObject = doc.Objects.Find(objectId);
        if (rhinoObject != null)
        {
            rhinoObject.Attributes.LayerIndex = doc.Layers.CurrentLayerIndex;
            doc.Objects.ModifyAttributes(rhinoObject, rhinoObject.Attributes, true);
        }
        
        doc.Views.Redraw();
        
        // Calculate angle
        double angle = Vector3d.VectorAngle(vec1, vec2) * 180.0 / Math.PI;
        
        RhinoApp.WriteLine($"[DIMENSION CREATED] Angular dimension: {objectId}, angle: {angle:F2}°");
        
        return new JObject
        {
            ["id"] = objectId.ToString(),
            ["type"] = "angular_dimension",
            ["angle_degrees"] = angle
        };
    }
    
    /// <summary>
    /// Create a radial (radius or diameter) dimension for a circle or arc.
    /// </summary>
    public JObject CreateRadialDimension(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        // Parse parameters
        Point3d center = castToPoint3d(parameters.SelectToken("center"));
        Point3d radiusPoint = castToPoint3d(parameters.SelectToken("radius_point"));
        bool isDiameter = parameters.ContainsKey("is_diameter") && castToBool(parameters.SelectToken("is_diameter"));
        
        // Optional: dimension style name
        string styleName = castToString(parameters.SelectToken("dimension_style"));
        
        // Get dimension style
        DimensionStyle dimStyle = doc.DimStyles.Current;
        if (!string.IsNullOrEmpty(styleName))
        {
            var foundStyle = doc.DimStyles.FindName(styleName);
            if (foundStyle != null)
            {
                dimStyle = foundStyle;
            }
        }
        
        // Calculate radius
        double radius = center.DistanceTo(radiusPoint);
        
        // Create a circle plane at the center
        Plane circlePlane = Plane.WorldXY;
        circlePlane.Origin = center;
        
        // Create the radial dimension
        AnnotationType annotationType = isDiameter ? AnnotationType.Diameter : AnnotationType.Radius;
        
        var dimension = RadialDimension.Create(
            dimStyle,
            annotationType,
            circlePlane,
            center,
            radiusPoint,
            radiusPoint  // text point at radius point
        );
        
        if (dimension == null)
        {
            throw new InvalidOperationException("Failed to create radial dimension");
        }
        
        // Add to document
        Guid objectId = doc.Objects.AddRadialDimension(dimension);
        
        if (objectId == Guid.Empty)
        {
            throw new InvalidOperationException("Failed to add radial dimension to document");
        }
        
        // Set layer
        var rhinoObject = doc.Objects.Find(objectId);
        if (rhinoObject != null)
        {
            rhinoObject.Attributes.LayerIndex = doc.Layers.CurrentLayerIndex;
            doc.Objects.ModifyAttributes(rhinoObject, rhinoObject.Attributes, true);
        }
        
        doc.Views.Redraw();
        
        string dimType = isDiameter ? "diameter" : "radius";
        RhinoApp.WriteLine($"[DIMENSION CREATED] Radial dimension ({dimType}): {objectId}, {dimType}: {(isDiameter ? radius * 2 : radius):F2}");
        
        return new JObject
        {
            ["id"] = objectId.ToString(),
            ["type"] = isDiameter ? "diameter_dimension" : "radius_dimension",
            ["radius"] = radius,
            ["diameter"] = radius * 2
        };
    }
}
