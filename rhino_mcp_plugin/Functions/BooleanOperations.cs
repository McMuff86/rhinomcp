using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject BooleanOperation(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        
        string operation = parameters["operation"]?.ToString()?.ToUpperInvariant();
        if (string.IsNullOrEmpty(operation))
            throw new ArgumentException("operation is required");
        
        var objectIds = parameters["object_ids"]?.ToObject<List<string>>();
        if (objectIds == null || objectIds.Count < 2)
            throw new ArgumentException("At least 2 object_ids are required");
        
        bool deleteInput = parameters["delete_input"]?.Value<bool>() ?? true;
        
        List<Brep> breps = new List<Brep>();
        List<RhinoObject> inputObjects = new List<RhinoObject>();
        
        foreach (string idStr in objectIds)
        {
            if (!Guid.TryParse(idStr, out Guid objId))
                throw new ArgumentException($"Invalid GUID: {idStr}");
            
            RhinoObject obj = doc.Objects.FindId(objId);
            if (obj == null)
                throw new ArgumentException($"Object not found: {idStr}");
            
            Brep brep = null;
            if (obj.Geometry is Brep b)
            {
                brep = b;
            }
            else if (obj.Geometry is Extrusion ext)
            {
                brep = ext.ToBrep();
            }
            else
            {
                throw new ArgumentException($"Object {idStr} is not a solid (Brep or Extrusion)");
            }
            
            if (!brep.IsSolid)
                throw new ArgumentException($"Object {idStr} is not a closed solid");
            
            breps.Add(brep);
            inputObjects.Add(obj);
        }
        
        Brep[] resultBreps = null;
        double tolerance = doc.ModelAbsoluteTolerance;
        
        switch (operation)
        {
            case "UNION":
                resultBreps = Brep.CreateBooleanUnion(breps, tolerance);
                break;
                
            case "DIFFERENCE":
                Brep[] firstSet = new Brep[] { breps[0] };
                Brep[] secondSet = breps.Skip(1).ToArray();
                resultBreps = Brep.CreateBooleanDifference(firstSet, secondSet, tolerance);
                break;
                
            case "INTERSECTION":
                resultBreps = Brep.CreateBooleanIntersection(breps[0], breps[1], tolerance);
                if (resultBreps != null && breps.Count > 2)
                {
                    for (int i = 2; i < breps.Count; i++)
                    {
                        if (resultBreps.Length == 0) break;
                        resultBreps = Brep.CreateBooleanIntersection(resultBreps[0], breps[i], tolerance);
                        if (resultBreps == null || resultBreps.Length == 0) break;
                    }
                }
                break;
                
            default:
                throw new ArgumentException($"Unknown operation: {operation}");
        }
        
        if (resultBreps == null || resultBreps.Length == 0)
            throw new InvalidOperationException($"Boolean {operation} failed - objects may be disjoint or non-intersecting");
        
        List<string> newIds = new List<string>();
        int currentLayerIndex = doc.Layers.CurrentLayerIndex;
        
        foreach (Brep resultBrep in resultBreps)
        {
            ObjectAttributes attrs = new ObjectAttributes();
            attrs.LayerIndex = currentLayerIndex;
            
            Guid newId = doc.Objects.AddBrep(resultBrep, attrs);
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
            operation = operation,
            input_count = objectIds.Count,
            result_ids = newIds,
            deleted_input = deleteInput
        });
    }
}
