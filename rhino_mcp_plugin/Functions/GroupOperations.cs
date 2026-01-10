using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject CreateGroup(JObject parameters)
    {
        var objectIds = parameters["object_ids"]?.ToObject<List<string>>();
        if (objectIds == null || objectIds.Count == 0)
            throw new ArgumentException("object_ids is required and cannot be empty");

        string groupName = parameters["group_name"]?.ToString();

        // Select the objects first
        var doc = RhinoDoc.ActiveDoc;
        doc.Objects.UnselectAll();

        foreach (string idStr in objectIds)
        {
            if (!Guid.TryParse(idStr, out Guid objId))
                throw new ArgumentException($"Invalid GUID: {idStr}");

            RhinoObject obj = doc.Objects.FindId(objId);
            if (obj == null)
                throw new ArgumentException($"Object not found: {idStr}");

            obj.Select(true);
        }

        // Create group using Rhino command
        string script = "_Group";
        if (!string.IsNullOrEmpty(groupName))
        {
            script += $" \"{groupName}\"";
        }
        script += " _Enter";

        bool success = RhinoApp.RunScript(script, false);

        if (!success)
            throw new InvalidOperationException("Failed to create group");

        // Get the group that was just created (last created group)
        Group lastGroup = null;
        for (int i = 0; i < doc.Groups.Count; i++)
        {
            Group group = doc.Groups.FindIndex(i);
            if (group != null)
            {
                lastGroup = group;
            }
        }

        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            group_id = lastGroup?.Id.ToString() ?? "unknown",
            group_name = lastGroup?.Name ?? groupName,
            object_count = objectIds.Count
        });
    }

    public JObject Ungroup(JObject parameters)
    {
        string groupIdStr = parameters["group_id"]?.ToString();
        if (string.IsNullOrEmpty(groupIdStr))
            throw new ArgumentException("group_id is required");

        if (!Guid.TryParse(groupIdStr, out Guid groupId))
            throw new ArgumentException($"Invalid group GUID: {groupIdStr}");

        var doc = RhinoDoc.ActiveDoc;

        // Find and select objects in the group
        Group group = doc.Groups.FindId(groupId);
        if (group == null)
            throw new ArgumentException($"Group not found: {groupIdStr}");

        RhinoObject[] groupObjects = doc.Objects.FindByGroup(group.Index);
        doc.Objects.UnselectAll();

        foreach (RhinoObject obj in groupObjects)
        {
            obj.Select(true);
        }

        // Ungroup using Rhino command
        string script = "_Ungroup _Enter";
        bool success = RhinoApp.RunScript(script, false);

        if (!success)
            throw new InvalidOperationException("Failed to ungroup");

        List<string> ungroupedIds = new List<string>();
        foreach (RhinoObject obj in groupObjects)
        {
            ungroupedIds.Add(obj.Id.ToString());
        }

        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            group_id = groupId.ToString(),
            object_ids = ungroupedIds,
            object_count = ungroupedIds.Count
        });
    }

    public JObject CreateBlock(JObject parameters)
    {
        string name = parameters["name"]?.ToString();
        if (string.IsNullOrEmpty(name))
            throw new ArgumentException("name is required");

        if (name.Contains("\""))
            throw new ArgumentException("name cannot contain quotes");

        var objectIds = parameters["object_ids"]?.ToObject<List<string>>();
        if (objectIds == null || objectIds.Count == 0)
            throw new ArgumentException("object_ids is required and cannot be empty");

        var basePoint = parameters["base_point"]?.ToObject<List<double>>();
        if (basePoint == null || basePoint.Count != 3)
            throw new ArgumentException("base_point must be [x, y, z]");

        // Select the objects first
        var doc = RhinoDoc.ActiveDoc;
        doc.Objects.UnselectAll();

        foreach (string idStr in objectIds)
        {
            if (!Guid.TryParse(idStr, out Guid objId))
                throw new ArgumentException($"Invalid GUID: {idStr}");

            RhinoObject obj = doc.Objects.FindId(objId);
            if (obj == null)
                throw new ArgumentException($"Object not found: {idStr}");

            obj.Select(true);
        }

        // Create block using Rhino command
        string script = $"_-Block \"{name}\" {basePoint[0].ToString(System.Globalization.CultureInfo.InvariantCulture)},{basePoint[1].ToString(System.Globalization.CultureInfo.InvariantCulture)},{basePoint[2].ToString(System.Globalization.CultureInfo.InvariantCulture)} _Enter";
        bool success = RhinoApp.RunScript(script, false);

        if (!success)
            throw new InvalidOperationException("Failed to create block");

        // Find the newly created block definition
        string blockId = null;
        var blockDefinitions = doc.InstanceDefinitions;
        foreach (var blockDef in blockDefinitions)
        {
            if (blockDef.Name == name)
            {
                blockId = blockDef.Id.ToString();
                break;
            }
        }

        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            block_name = name,
            block_id = blockId,
            object_count = objectIds.Count
        });
    }

    public JObject InsertBlock(JObject parameters)
    {
        string blockName = parameters["block_name"]?.ToString();
        if (string.IsNullOrEmpty(blockName))
            throw new ArgumentException("block_name is required");

        if (blockName.Contains("\""))
            throw new ArgumentException("block_name cannot contain quotes");

        var position = parameters["position"]?.ToObject<List<double>>();
        if (position == null || position.Count != 3)
            throw new ArgumentException("position must be [x, y, z]");

        var scale = parameters["scale"]?.ToObject<List<double>>() ?? new List<double> { 1.0, 1.0, 1.0 };
        var rotation = parameters["rotation"]?.ToObject<List<double>>() ?? new List<double> { 0.0, 0.0, 0.0 };

        var doc = RhinoDoc.ActiveDoc;

        // Get the current object count before insertion
        int objectCountBefore = doc.Objects.Count;

        // Insert block using Rhino command
        string script = $"_-Insert \"{blockName}\" {position[0].ToString(System.Globalization.CultureInfo.InvariantCulture)},{position[1].ToString(System.Globalization.CultureInfo.InvariantCulture)},{position[2].ToString(System.Globalization.CultureInfo.InvariantCulture)} {scale[0].ToString(System.Globalization.CultureInfo.InvariantCulture)},{scale[1].ToString(System.Globalization.CultureInfo.InvariantCulture)},{scale[2].ToString(System.Globalization.CultureInfo.InvariantCulture)} {rotation[0].ToString(System.Globalization.CultureInfo.InvariantCulture)},{rotation[1].ToString(System.Globalization.CultureInfo.InvariantCulture)},{rotation[2].ToString(System.Globalization.CultureInfo.InvariantCulture)} _Enter";
        bool success = RhinoApp.RunScript(script, false);

        if (!success)
            throw new InvalidOperationException("Failed to insert block");

        // Find the newly inserted block instance
        string instanceId = null;
        if (doc.Objects.Count > objectCountBefore)
        {
            // Get the last added object (assuming it's the block instance)
            RhinoObject lastObj = null;
            foreach (RhinoObject obj in doc.Objects)
            {
                lastObj = obj; // Keep overwriting to get the last one
            }
            if (lastObj != null)
            {
                instanceId = lastObj.Id.ToString();
            }
        }

        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            block_name = blockName,
            instance_id = instanceId,
            position = position,
            scale = scale,
            rotation = rotation
        });
    }

    public JObject ExplodeBlock(JObject parameters)
    {
        string instanceIdStr = parameters["instance_id"]?.ToString();
        if (string.IsNullOrEmpty(instanceIdStr))
            throw new ArgumentException("instance_id is required");

        if (!Guid.TryParse(instanceIdStr, out Guid instanceId))
            throw new ArgumentException($"Invalid instance GUID: {instanceIdStr}");

        var doc = RhinoDoc.ActiveDoc;

        // Select the block instance
        RhinoObject instanceObj = doc.Objects.FindId(instanceId);
        if (instanceObj == null)
            throw new ArgumentException($"Block instance not found: {instanceIdStr}");

        doc.Objects.UnselectAll();
        instanceObj.Select(true);

        // Explode using Rhino command
        string script = "_Explode _Enter";
        bool success = RhinoApp.RunScript(script, false);

        if (!success)
            throw new InvalidOperationException("Failed to explode block");

        // Get the newly created objects (this is approximate since we can't easily track them)
        var selectedObjects = doc.Objects.GetSelectedObjects(false, false);
        List<string> explodedIds = new List<string>();
        foreach (RhinoObject obj in selectedObjects)
        {
            explodedIds.Add(obj.Id.ToString());
        }

        doc.Views.Redraw();

        return JObject.FromObject(new
        {
            instance_id = instanceId.ToString(),
            object_ids = explodedIds,
            object_count = explodedIds.Count
        });
    }
}