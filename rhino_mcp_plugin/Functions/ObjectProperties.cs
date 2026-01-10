using System;
using System.Collections.Generic;
using System.Drawing;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Get geometric properties of one or more objects (bounding box, area, volume, centroid).
    /// </summary>
    public JObject GetObjectProperties(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var objectIds = new List<Guid>();

        // Support single or batch
        if (parameters["object_id"] != null)
        {
            objectIds.Add(Guid.Parse(parameters["object_id"].ToString()));
        }
        if (parameters["object_ids"] != null)
        {
            foreach (var id in parameters["object_ids"])
            {
                objectIds.Add(Guid.Parse(id.ToString()));
            }
        }

        if (objectIds.Count == 0)
            throw new ArgumentException("Either object_id or object_ids must be provided");

        var results = new JArray();

        foreach (var objId in objectIds)
        {
            var obj = doc.Objects.FindId(objId);
            if (obj == null)
                throw new ArgumentException($"Object not found: {objId}");

            var geometry = obj.Geometry;
            var props = new JObject
            {
                ["id"] = objId.ToString(),
                ["name"] = obj.Attributes.Name ?? "",
                ["type"] = obj.ObjectType.ToString()
            };

            // Bounding box
            var bbox = geometry.GetBoundingBox(true);
            props["bounding_box"] = new JObject
            {
                ["min"] = new JArray { Math.Round(bbox.Min.X, 6), Math.Round(bbox.Min.Y, 6), Math.Round(bbox.Min.Z, 6) },
                ["max"] = new JArray { Math.Round(bbox.Max.X, 6), Math.Round(bbox.Max.Y, 6), Math.Round(bbox.Max.Z, 6) },
                ["dimensions"] = new JArray { 
                    Math.Round(bbox.Max.X - bbox.Min.X, 6), 
                    Math.Round(bbox.Max.Y - bbox.Min.Y, 6), 
                    Math.Round(bbox.Max.Z - bbox.Min.Z, 6) 
                }
            };

            // Properties for Breps (surfaces, solids)
            if (geometry is Brep brep)
            {
                props["is_solid"] = brep.IsSolid;

                // Area
                var areaProps = AreaMassProperties.Compute(brep);
                if (areaProps != null)
                {
                    props["area"] = Math.Round(areaProps.Area, 6);
                    props["centroid"] = new JArray { 
                        Math.Round(areaProps.Centroid.X, 6), 
                        Math.Round(areaProps.Centroid.Y, 6), 
                        Math.Round(areaProps.Centroid.Z, 6) 
                    };
                }

                // Volume (only for solids)
                if (brep.IsSolid)
                {
                    var volProps = VolumeMassProperties.Compute(brep);
                    if (volProps != null)
                    {
                        props["volume"] = Math.Round(volProps.Volume, 6);
                        props["volume_centroid"] = new JArray { 
                            Math.Round(volProps.Centroid.X, 6), 
                            Math.Round(volProps.Centroid.Y, 6), 
                            Math.Round(volProps.Centroid.Z, 6) 
                        };
                    }
                }
            }
            // Extrusion (can be converted to Brep)
            else if (geometry is Extrusion extrusion)
            {
                var brep2 = extrusion.ToBrep();
                if (brep2 != null)
                {
                    props["is_solid"] = brep2.IsSolid;

                    var areaProps = AreaMassProperties.Compute(brep2);
                    if (areaProps != null)
                    {
                        props["area"] = Math.Round(areaProps.Area, 6);
                        props["centroid"] = new JArray { 
                            Math.Round(areaProps.Centroid.X, 6), 
                            Math.Round(areaProps.Centroid.Y, 6), 
                            Math.Round(areaProps.Centroid.Z, 6) 
                        };
                    }

                    if (brep2.IsSolid)
                    {
                        var volProps = VolumeMassProperties.Compute(brep2);
                        if (volProps != null)
                        {
                            props["volume"] = Math.Round(volProps.Volume, 6);
                            props["volume_centroid"] = new JArray { 
                                Math.Round(volProps.Centroid.X, 6), 
                                Math.Round(volProps.Centroid.Y, 6), 
                                Math.Round(volProps.Centroid.Z, 6) 
                            };
                        }
                    }
                }
            }
            // Mesh
            else if (geometry is Mesh mesh)
            {
                props["is_solid"] = mesh.IsClosed;

                var areaProps = AreaMassProperties.Compute(mesh);
                if (areaProps != null)
                {
                    props["area"] = Math.Round(areaProps.Area, 6);
                    props["centroid"] = new JArray { 
                        Math.Round(areaProps.Centroid.X, 6), 
                        Math.Round(areaProps.Centroid.Y, 6), 
                        Math.Round(areaProps.Centroid.Z, 6) 
                    };
                }

                if (mesh.IsClosed)
                {
                    var volProps = VolumeMassProperties.Compute(mesh);
                    if (volProps != null)
                    {
                        props["volume"] = Math.Round(volProps.Volume, 6);
                    }
                }
            }
            // Curve
            else if (geometry is Curve curve)
            {
                props["curve_length"] = Math.Round(curve.GetLength(), 6);
                props["is_closed"] = curve.IsClosed;
                
                // Centroid for curves (midpoint approximation)
                var midParam = (curve.Domain.Min + curve.Domain.Max) / 2;
                var midPoint = curve.PointAt(midParam);
                props["centroid"] = new JArray { 
                    Math.Round(midPoint.X, 6), 
                    Math.Round(midPoint.Y, 6), 
                    Math.Round(midPoint.Z, 6) 
                };
            }
            // Surface (not Brep)
            else if (geometry is Surface surface)
            {
                var areaProps = AreaMassProperties.Compute(surface);
                if (areaProps != null)
                {
                    props["area"] = Math.Round(areaProps.Area, 6);
                    props["centroid"] = new JArray { 
                        Math.Round(areaProps.Centroid.X, 6), 
                        Math.Round(areaProps.Centroid.Y, 6), 
                        Math.Round(areaProps.Centroid.Z, 6) 
                    };
                }
            }

            results.Add(props);
        }

        // Return single object directly, array for batch
        if (objectIds.Count == 1)
        {
            return (JObject)results[0];
        }
        
        return new JObject
        {
            ["objects"] = results,
            ["count"] = results.Count
        };
    }

    /// <summary>
    /// Set properties on one or more objects (name, layer, color, material).
    /// </summary>
    public JObject SetObjectProperties(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var objectIds = new List<Guid>();

        // Support single or batch
        if (parameters["object_id"] != null)
        {
            objectIds.Add(Guid.Parse(parameters["object_id"].ToString()));
        }
        if (parameters["object_ids"] != null)
        {
            foreach (var id in parameters["object_ids"])
            {
                objectIds.Add(Guid.Parse(id.ToString()));
            }
        }

        if (objectIds.Count == 0)
            throw new ArgumentException("Either object_id or object_ids must be provided");

        string newName = parameters["name"]?.ToString();
        string layerName = parameters["layer"]?.ToString();
        int[] color = parameters["color"]?.ToObject<int[]>();
        int? materialId = parameters["material_id"]?.Value<int>();

        // Validate layer exists if specified
        int layerIndex = -1;
        if (!string.IsNullOrEmpty(layerName))
        {
            layerIndex = doc.Layers.FindByFullPath(layerName, -1);
            if (layerIndex < 0)
            {
                // Try simple name match
                var layer = doc.Layers.FindName(layerName);
                if (layer == null)
                    throw new ArgumentException($"Layer not found: {layerName}");
                layerIndex = layer.Index;
            }
        }

        // Validate material if specified
        if (materialId.HasValue)
        {
            if (materialId.Value < 0 || materialId.Value >= doc.Materials.Count)
                throw new ArgumentException($"Invalid material_id: {materialId.Value}. Valid range: 0-{doc.Materials.Count - 1}");
        }

        int modifiedCount = 0;

        foreach (var objId in objectIds)
        {
            var obj = doc.Objects.FindId(objId);
            if (obj == null)
                throw new ArgumentException($"Object not found: {objId}");

            bool modified = false;

            // Set name
            if (newName != null)
            {
                obj.Attributes.Name = newName;
                modified = true;
            }

            // Set layer
            if (layerIndex >= 0)
            {
                obj.Attributes.LayerIndex = layerIndex;
                modified = true;
            }

            // Set color
            if (color != null && color.Length == 3)
            {
                obj.Attributes.ObjectColor = Color.FromArgb(color[0], color[1], color[2]);
                obj.Attributes.ColorSource = ObjectColorSource.ColorFromObject;
                modified = true;
            }

            // Set material
            if (materialId.HasValue)
            {
                obj.Attributes.MaterialIndex = materialId.Value;
                obj.Attributes.MaterialSource = ObjectMaterialSource.MaterialFromObject;
                modified = true;
            }

            if (modified)
            {
                doc.Objects.ModifyAttributes(obj, obj.Attributes, true);
                modifiedCount++;
            }
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["modified_count"] = modifiedCount,
            ["object_ids"] = new JArray(objectIds.ConvertAll(id => id.ToString()))
        };
    }
}
