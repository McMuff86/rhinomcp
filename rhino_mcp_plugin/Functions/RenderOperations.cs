using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Display;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject SetRenderSettings(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        int? width = parameters["width"]?.Value<int?>();
        int? height = parameters["height"]?.Value<int?>();
        string quality = parameters["quality"]?.ToString();

        if ((width.HasValue && !height.HasValue) || (!width.HasValue && height.HasValue))
            throw new ArgumentException("width and height must be provided together");

        if (width.HasValue && width.Value <= 0)
            throw new ArgumentException("width must be positive");

        if (height.HasValue && height.Value <= 0)
            throw new ArgumentException("height must be positive");

        var settings = doc.RenderSettings;

        if (width.HasValue && height.HasValue)
        {
            settings.ImageSize = new Size(width.Value, height.Value);
            settings.UseViewportSize = false;
        }

        if (!string.IsNullOrWhiteSpace(quality))
        {
            settings.AntialiasLevel = quality.ToLowerInvariant() switch
            {
                "none" => AntialiasLevel.None,
                "draft" => AntialiasLevel.Draft,
                "good" => AntialiasLevel.Good,
                "high" => AntialiasLevel.High,
                _ => throw new ArgumentException($"Unknown quality: {quality}")
            };
        }

        doc.RenderSettings = settings;

        return JObject.FromObject(new
        {
            status = "success",
            width = settings.ImageSize.Width,
            height = settings.ImageSize.Height,
            quality = settings.AntialiasLevel.ToString().ToLowerInvariant()
        });
    }

    public JObject AddLight(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        string lightType = parameters["light_type"]?.ToString();

        if (string.IsNullOrWhiteSpace(lightType))
            throw new ArgumentException("light_type is required");

        int[] color = parameters["color"] != null
            ? castToIntArray(parameters["color"])
            : new[] { 255, 255, 255 };
        double intensity = parameters["intensity"]?.Value<double>() ?? 1.0;
        string name = parameters["name"]?.ToString();
        double spotAngle = parameters["spot_angle_degrees"]?.Value<double>() ?? 45.0;

        var light = new Light
        {
            Diffuse = Color.FromArgb(color[0], color[1], color[2]),
            Specular = Color.FromArgb(color[0], color[1], color[2]),
            Intensity = intensity,
            IsEnabled = true,
            Name = name ?? string.Empty
        };

        switch (lightType.ToLowerInvariant())
        {
            case "point":
                if (parameters["location"] == null)
                    throw new ArgumentException("location is required for point lights");
                light.LightStyle = LightStyle.WorldPoint;
                light.Location = castToPoint3d(parameters["location"]);
                break;
            case "directional":
                if (parameters["direction"] == null)
                    throw new ArgumentException("direction is required for directional lights");
                light.LightStyle = LightStyle.WorldDirectional;
                var directionArray = castToDoubleArray(parameters["direction"]);
                var direction = new Vector3d(directionArray[0], directionArray[1], directionArray[2]);
                if (direction.IsZero)
                    throw new ArgumentException("direction must be non-zero");
                direction.Unitize();
                light.Direction = direction;
                break;
            case "spot":
                if (parameters["location"] == null || parameters["target"] == null)
                    throw new ArgumentException("location and target are required for spot lights");
                light.LightStyle = LightStyle.WorldSpot;
                var location = castToPoint3d(parameters["location"]);
                var target = castToPoint3d(parameters["target"]);
                var spotDirection = target - location;
                if (spotDirection.IsZero)
                    throw new ArgumentException("spot target must differ from location");
                spotDirection.Unitize();
                light.Location = location;
                light.Direction = spotDirection;
                light.SpotAngleRadians = RhinoMath.ToRadians(spotAngle);
                break;
            default:
                throw new ArgumentException($"Unknown light_type: {lightType}");
        }

        int lightIndex = doc.Lights.Add(light);
        if (lightIndex < 0)
            throw new InvalidOperationException("Failed to add light");

        var lightObject = doc.Lights[lightIndex];
        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            status = "success",
            id = lightObject.Id.ToString(),
            index = lightIndex,
            type = lightType
        });
    }

    public JObject SetCamera(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        string viewportName = parameters["viewport_name"]?.ToString() ?? "Perspective";

        if (parameters["camera_location"] == null)
            throw new ArgumentException("camera_location is required");

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

        var cameraLocation = castToPoint3d(parameters["camera_location"]);
        if (parameters["target_location"] != null)
        {
            var targetLocation = castToPoint3d(parameters["target_location"]);
            viewport.MainViewport.SetCameraLocations(targetLocation, cameraLocation);
        }
        else
        {
            viewport.MainViewport.SetCameraLocation(cameraLocation, false);
        }

        if (parameters["lens_length"] != null)
        {
            double lensLength = parameters["lens_length"]?.Value<double>() ?? 0;
            if (lensLength <= 0)
                throw new ArgumentException("lens_length must be positive");
            viewport.MainViewport.Camera35mmLensLength = lensLength;
        }

        viewport.Redraw();
        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            status = "success",
            viewport = viewportName,
            camera_location = new[] { cameraLocation.X, cameraLocation.Y, cameraLocation.Z },
            target_location = new[]
            {
                viewport.MainViewport.CameraTarget.X,
                viewport.MainViewport.CameraTarget.Y,
                viewport.MainViewport.CameraTarget.Z
            },
            lens_length = viewport.MainViewport.Camera35mmLensLength
        });
    }

    public JObject RenderView(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        string viewportName = parameters["viewport_name"]?.ToString() ?? "Perspective";
        string displayModeName = parameters["display_mode"]?.ToString() ?? "rendered";
        int? width = parameters["width"]?.Value<int?>();
        int? height = parameters["height"]?.Value<int?>();

        if ((width.HasValue && !height.HasValue) || (!width.HasValue && height.HasValue))
            throw new ArgumentException("width and height must be provided together");

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

        var renderSize = doc.RenderSettings.ImageSize;
        int renderWidth = width ?? renderSize.Width;
        int renderHeight = height ?? renderSize.Height;

        if (renderWidth <= 0 || renderHeight <= 0)
            throw new ArgumentException("render width and height must be positive");

        DisplayModeDescription displayMode = null;
        foreach (var mode in DisplayModeDescription.GetDisplayModes())
        {
            if (string.Equals(mode.EnglishName, displayModeName, StringComparison.OrdinalIgnoreCase) ||
                string.Equals(mode.LocalName, displayModeName, StringComparison.OrdinalIgnoreCase))
            {
                displayMode = mode;
                break;
            }
        }

        if (displayMode == null)
            throw new ArgumentException($"Display mode '{displayModeName}' not found");

        var previousMode = viewport.MainViewport.DisplayMode;
        string filename = parameters["filename"]?.ToString();

        try
        {
            viewport.MainViewport.DisplayMode = displayMode;

            var capture = new ViewCapture
            {
                Width = renderWidth,
                Height = renderHeight,
                DrawGrid = false,
                DrawAxes = false,
                DrawGridAxes = false
            };

            using var bitmap = capture.CaptureToBitmap(viewport);

            if (bitmap == null)
                throw new InvalidOperationException("Failed to capture viewport");

            if (!string.IsNullOrWhiteSpace(filename))
            {
                var format = filename.ToLowerInvariant().EndsWith(".png") ? ImageFormat.Png : ImageFormat.Jpeg;
                bitmap.Save(filename, format);

                return JObject.FromObject(new
                {
                    status = "success",
                    viewport = viewportName,
                    saved_to_file = filename,
                    width = renderWidth,
                    height = renderHeight,
                    display_mode = displayModeName
                });
            }

            using var ms = new MemoryStream();
            bitmap.Save(ms, ImageFormat.Png);
            var imageBytes = ms.ToArray();
            var base64String = Convert.ToBase64String(imageBytes);

            return JObject.FromObject(new
            {
                status = "success",
                viewport = viewportName,
                image_data = base64String,
                format = "png",
                width = renderWidth,
                height = renderHeight,
                display_mode = displayModeName
            });
        }
        finally
        {
            viewport.MainViewport.DisplayMode = previousMode;
            viewport.Redraw();
            doc.Views.Redraw();
        }
    }
}
