using System;
using Newtonsoft.Json.Linq;
using Rhino;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject GetObjectInfo(JObject parameters)
    {
        var obj = getObjectByIdOrName(parameters);

        var data = Serializer.RhinoObject(obj);
        data["attributes"] = Serializer.RhinoObjectAttributes(obj);

        // Enhanced details for learning
        var geometry = obj.Geometry;
        if (geometry != null)
        {
            data["geometry_details"] = new JObject
            {
                ["type"] = geometry.GetType().Name,
                ["is_valid"] = geometry.IsValid,
                ["object_type"] = obj.ObjectType.ToString()
            };

            // Add basic bounding box
            var bbox = geometry.GetBoundingBox(true);
            data["geometry_details"]["bounding_box"] = new JObject
            {
                ["min"] = new JArray { bbox.Min.X, bbox.Min.Y, bbox.Min.Z },
                ["max"] = new JArray { bbox.Max.X, bbox.Max.Y, bbox.Max.Z }
            };

            // Add specific details based on geometry type
            if (geometry is Rhino.Geometry.Mesh mesh)
            {
                data["mesh_details"] = new JObject
                {
                    ["vertex_count"] = mesh.Vertices.Count,
                    ["face_count"] = mesh.Faces.Count,
                    ["is_closed"] = mesh.IsClosed
                };
            }
            else if (geometry is Rhino.Geometry.Brep brep)
            {
                data["brep_details"] = new JObject
                {
                    ["face_count"] = brep.Faces.Count,
                    ["edge_count"] = brep.Edges.Count,
                    ["vertex_count"] = brep.Vertices.Count,
                    ["is_solid"] = brep.IsSolid
                };
            }
            else if (geometry is Rhino.Geometry.Surface surface)
            {
                data["surface_details"] = new JObject
                {
                    ["is_planar"] = surface.IsPlanar()
                };
            }
            else if (geometry is Rhino.Geometry.Curve curve)
            {
                data["curve_details"] = new JObject
                {
                    ["degree"] = curve.Degree,
                    ["is_closed"] = curve.IsClosed
                };
            }
        }

        return data;
    }
}