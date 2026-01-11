# Boolean Operations Learnings

> Patterns and learnings for solid geometry boolean operations.

## Quick Reference

- Objects must be **closed solids** (`brep.IsSolid`)
- Convert **Extrusion to Brep** before operations
- Objects must **geometrically overlap** for valid results
- Use `Brep.CreateBooleanUnion/Difference/Intersection()`
- Result parsing: expect `result_ids[]` array, not single `id`

---

## Detailed Learnings

### Learning: Objects Must Be Closed Solids
**Date:** 2026-01-10
**Context:** Boolean operations failing silently
**Problem:** Open surfaces or non-solid geometry fails
**Solution:** Validate `IsSolid` before operation

```csharp
// Validate input
foreach (var brep in breps)
{
    if (!brep.IsSolid)
    {
        throw new ArgumentException($"Object {id} is not a closed solid");
    }
}
```

---

### Learning: Convert Extrusion to Brep
**Date:** 2026-01-10
**Context:** Boxes and cylinders are Extrusions, not Breps
**Problem:** Boolean operations expect Brep objects
**Solution:** Convert Extrusion to Brep first

```csharp
Brep GetBrep(RhinoObject obj)
{
    if (obj.Geometry is Brep brep)
        return brep;
        
    if (obj.Geometry is Extrusion extrusion)
        return extrusion.ToBrep();
        
    throw new ArgumentException("Object is not a solid");
}
```

---

### Learning: Objects Must Overlap Geometrically
**Date:** 2026-01-10
**Context:** Integration testing boolean operations
**Problem:** Non-overlapping objects return empty result
**Solution:** Ensure objects intersect before operation

```python
# Create overlapping boxes
box1 = create_object(type="BOX", parameters={"width": 10, "height": 10, "depth": 10})
box2 = create_object(type="BOX", parameters={"width": 10, "height": 10, "depth": 10}, 
                     translation=[5, 0, 0])  # Offset to overlap

# Boolean union will work because boxes overlap
result = boolean_operation(object_ids=[box1["id"], box2["id"]], operation="union")
```

---

### Learning: Result Parsing Returns Array
**Date:** 2026-01-10
**Context:** Python tool expecting single `id` field
**Problem:** C# returns `result_ids[]` array
**Solution:** Access first element of array

```python
# WRONG:
result_id = response["id"]  # KeyError!

# CORRECT:
result_id = response["result_ids"][0]
```

---

## Boolean Operation Types

| Operation | Description | Use Case |
|-----------|-------------|----------|
| `union` | Combine solids | Merge objects into one |
| `difference` | Subtract A from B | Cut holes, create cavities |
| `intersection` | Keep overlapping | Find common volume |

---

## Code Examples

### Python Tool Usage

```python
from rhinomcp.tools.boolean_operation import boolean_operation

# Union: Combine two boxes
result = boolean_operation(
    object_ids=["guid-1", "guid-2"],
    operation="union",
    delete_input=True  # Remove original objects
)

# Difference: Cut sphere from box
result = boolean_operation(
    object_ids=["box-guid", "sphere-guid"],
    operation="difference",
    delete_input=True
)

# Intersection: Keep only overlapping part
result = boolean_operation(
    object_ids=["guid-1", "guid-2"],
    operation="intersection",
    delete_input=False  # Keep originals
)
```

### C# Implementation

```csharp
public JObject BooleanOperation(JObject parameters)
{
    string operation = parameters["operation"]?.ToString();
    JArray objectIds = parameters["object_ids"] as JArray;
    bool deleteInput = parameters["delete_input"]?.Value<bool>() ?? true;
    
    // Get Breps
    List<Brep> breps = objectIds.Select(id => GetBrep(id.ToString())).ToList();
    
    // Perform operation
    Brep[] result = operation switch
    {
        "union" => Brep.CreateBooleanUnion(breps, doc.ModelAbsoluteTolerance),
        "difference" => Brep.CreateBooleanDifference(breps[0], breps.Skip(1).ToArray(), 
                                                      doc.ModelAbsoluteTolerance),
        "intersection" => Brep.CreateBooleanIntersection(breps[0], breps[1], 
                                                          doc.ModelAbsoluteTolerance),
        _ => throw new ArgumentException($"Unknown operation: {operation}")
    };
    
    // Add results to document
    List<Guid> resultIds = new List<Guid>();
    foreach (var brep in result)
    {
        resultIds.Add(doc.Objects.AddBrep(brep));
    }
    
    // Optionally delete input
    if (deleteInput)
    {
        foreach (var id in objectIds)
        {
            doc.Objects.Delete(Guid.Parse(id.ToString()), true);
        }
    }
    
    doc.Views.Redraw();
    return JObject.FromObject(new { 
        status = "success", 
        result_ids = resultIds.Select(g => g.ToString()).ToArray()
    });
}
```

---

## Best Practices

1. **Validate solids** before operation
2. **Check for overlap** if operation returns empty
3. **Handle multiple results** - union can return multiple Breps
4. **Use document tolerance** for consistent results
5. **Consider delete_input** - usually want to remove originals
6. **Redraw views** after geometry changes
