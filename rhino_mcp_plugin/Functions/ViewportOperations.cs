using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Display;
using Rhino.Geometry;
using Rhino.UI;
using System.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject SetView(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;

        string viewType = parameters["view_type"]?.ToString();
        string viewportName = parameters["viewport_name"]?.ToString() ?? "Perspective";

        if (string.IsNullOrEmpty(viewType))
            throw new ArgumentException("view_type is required");

        // Find the viewport
        RhinoView viewport = null;
        foreach (var rv in doc.Views)
        {
            if (rv.MainViewport.Name == viewportName)
            {
                viewport = rv;
                break;
            }
        }

        if (viewport == null)
            throw new ArgumentException($"Viewport '{viewportName}' not found");

        // Set the view based on type
        switch (viewType.ToLowerInvariant())
        {
            case "top":
                viewport.MainViewport.SetCameraDirection(Vector3d.ZAxis, true);
                viewport.MainViewport.CameraUp = Vector3d.YAxis;
                break;
            case "bottom":
                viewport.MainViewport.SetCameraDirection(-Vector3d.ZAxis, true);
                viewport.MainViewport.CameraUp = Vector3d.YAxis;
                break;
            case "left":
                viewport.MainViewport.SetCameraDirection(-Vector3d.XAxis, true);
                viewport.MainViewport.CameraUp = Vector3d.ZAxis;
                break;
            case "right":
                viewport.MainViewport.SetCameraDirection(Vector3d.XAxis, true);
                viewport.MainViewport.CameraUp = Vector3d.ZAxis;
                break;
            case "front":
                viewport.MainViewport.SetCameraDirection(-Vector3d.YAxis, true);
                viewport.MainViewport.CameraUp = Vector3d.ZAxis;
                break;
            case "back":
                viewport.MainViewport.SetCameraDirection(Vector3d.YAxis, true);
                viewport.MainViewport.CameraUp = Vector3d.ZAxis;
                break;
            case "perspective":
                // Set to isometric perspective view
                viewport.MainViewport.SetCameraDirection(new Vector3d(-1, -1, -1), true);
                viewport.MainViewport.CameraUp = Vector3d.ZAxis;
                break;
            case "twopointperspective":
                // Set to two-point perspective
                viewport.MainViewport.SetCameraDirection(new Vector3d(-1, -1, -1), true);
                viewport.MainViewport.CameraUp = Vector3d.ZAxis;
                break;
            default:
                throw new ArgumentException($"Unknown view type: {viewType}");
        }

        viewport.Redraw();
        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            status = "success",
            viewport = viewportName,
            view_type = viewType
        });
    }

    public JObject ZoomExtents(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;

        string viewportName = parameters["viewport_name"]?.ToString() ?? "Perspective";
        bool includeHidden = parameters["include_hidden"]?.Value<bool>() ?? true;

        // Find the viewport
        RhinoView viewport = null;
        foreach (var rv in doc.Views)
        {
            if (rv.MainViewport.Name == viewportName)
            {
                viewport = rv;
                break;
            }
        }

        if (viewport == null)
            throw new ArgumentException($"Viewport '{viewportName}' not found");

        // Zoom to extents
        var bbox = new BoundingBox();

        // Include all objects or only non-hidden objects
        foreach (var obj in doc.Objects)
        {
            if (includeHidden || !obj.IsHidden)
            {
                bbox.Union(obj.Geometry.GetBoundingBox(false));
            }
        }

        if (bbox.IsValid)
        {
            viewport.MainViewport.ZoomBoundingBox(bbox);
        }
        else
        {
            // If no objects, zoom to a default view
            viewport.MainViewport.ZoomExtents();
        }

        viewport.Redraw();
        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            status = "success",
            viewport = viewportName,
            zoomed_to_extents = true,
            include_hidden = includeHidden
        });
    }

    public JObject ZoomSelected(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;

        string viewportName = parameters["viewport_name"]?.ToString() ?? "Perspective";
        var objectIds = parameters["object_ids"]?.ToObject<List<string>>();

        // Find the viewport
        RhinoView viewport = null;
        foreach (var rv in doc.Views)
        {
            if (rv.MainViewport.Name == viewportName)
            {
                viewport = rv;
                break;
            }
        }

        if (viewport == null)
            throw new ArgumentException($"Viewport '{viewportName}' not found");

        BoundingBox bbox;

        if (objectIds != null && objectIds.Count > 0)
        {
            // Zoom to specific objects
            bbox = new BoundingBox();
            foreach (string idStr in objectIds)
            {
                if (Guid.TryParse(idStr, out Guid objId))
                {
                    var obj = doc.Objects.FindId(objId);
                    if (obj != null)
                    {
                        bbox.Union(obj.Geometry.GetBoundingBox(false));
                    }
                }
            }
        }
        else
        {
            // Zoom to currently selected objects
            var selectedObjects = doc.Objects.GetSelectedObjects(false, false);
            bbox = new BoundingBox();
            foreach (var obj in selectedObjects)
            {
                bbox.Union(obj.Geometry.GetBoundingBox(false));
            }
        }

        if (bbox.IsValid)
        {
            viewport.MainViewport.ZoomBoundingBox(bbox);
        }
        else
        {
            throw new InvalidOperationException("No valid objects to zoom to");
        }

        viewport.Redraw();
        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            status = "success",
            viewport = viewportName,
            zoomed_to_selected = true,
            object_count = objectIds?.Count ?? 0
        });
    }

    public JObject CaptureViewport(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;

        string viewportName = parameters["viewport_name"]?.ToString() ?? "Perspective";
        int width = parameters["width"]?.Value<int>() ?? 1920;
        int height = parameters["height"]?.Value<int>() ?? 1080;
        string filename = parameters["filename"]?.ToString();

        // Find the viewport
        RhinoView viewport = null;
        foreach (var rv in doc.Views)
        {
            if (rv.MainViewport.Name == viewportName)
            {
                viewport = rv;
                break;
            }
        }

        if (viewport == null)
            throw new ArgumentException($"Viewport '{viewportName}' not found");

        // Capture the viewport
        var bitmap = viewport.CaptureToBitmap(new Size(width, height));

        if (!string.IsNullOrEmpty(filename))
        {
            // Save to file
            var format = filename.ToLower().EndsWith(".png") ? ImageFormat.Png : ImageFormat.Jpeg;
            bitmap.Save(filename, format);

            return JObject.FromObject(new
            {
                status = "success",
                viewport = viewportName,
                saved_to_file = filename,
                width = width,
                height = height
            });
        }
        else
        {
            // Convert to base64
            using (var ms = new MemoryStream())
            {
                bitmap.Save(ms, ImageFormat.Png);
                var imageBytes = ms.ToArray();
                var base64String = Convert.ToBase64String(imageBytes);

                return JObject.FromObject(new
                {
                    status = "success",
                    viewport = viewportName,
                    image_data = base64String,
                    format = "png",
                    width = width,
                    height = height
                });
            }
        }
    }
}