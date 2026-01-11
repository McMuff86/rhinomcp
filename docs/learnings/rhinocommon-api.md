# RhinoCommon API Learnings

> Patterns and learnings from working with RhinoCommon in the C# plugin.

## Quick Reference

- `Brep.CreateBooleanUnion/Difference/Intersection()` for boolean operations
- Must convert Extrusion to Brep first for boolean ops
- Objects must be closed solids (`brep.IsSolid`)
- `doc.Objects.Transform(objId, xform, false)` creates a copy
- Normalize vectors with `Unitize()`
- `Curve.CreateFilletCurves()` with radius=0 creates chamfer
- `VolumeMassProperties.Compute()` only valid for closed solids
- `RhinoApp.RunScript()` for complex native commands

---

## Detailed Learnings

### Learning: Boolean Operations Require Breps
**Date:** 2026-01-10
**Context:** Implementing US-B01 Boolean Operations
**Solution:** Convert Extrusions to Breps before boolean operations

```csharp
// Convert Extrusion to Brep
if (obj is Extrusion extrusion)
{
    brep = extrusion.ToBrep();
}

// Then use boolean operations
Brep[] result = Brep.CreateBooleanUnion(breps, tolerance);
```

---

### Learning: Object Copying with Transform
**Date:** 2026-01-10
**Context:** Implementing US-B02 Transform Tools (copy, mirror, array)
**Solution:** Use `doc.Objects.Transform()` with copy flag

```csharp
// Create copy using transform
Guid newId = doc.Objects.Transform(objId, xform, false);  // false = delete original
Guid copyId = doc.Objects.Transform(objId, xform, true);  // true = keep original

// Normalize direction vectors
Vector3d direction = new Vector3d(x, y, z);
direction.Unitize();
```

---

### Learning: Fillet and Chamfer Use Same API
**Date:** 2026-01-10
**Context:** Implementing US-B03 Curve Operations
**Solution:** `CreateFilletCurves` with radius=0 creates chamfer

```csharp
// Fillet with radius
Curve[] fillets = Curve.CreateFilletCurves(curve1, pt1, curve2, pt2, radius, true, true, true, tolerance, tolerance);

// Chamfer = fillet with radius 0
Curve[] chamfers = Curve.CreateFilletCurves(curve1, pt1, curve2, pt2, 0, true, true, true, tolerance, tolerance);
```

---

### Learning: DimensionStyle API Changed in Rhino 8
**Date:** 2026-01-10
**Context:** Implementing US-B05 Dimension Tools
**Solution:** Use `doc.DimStyles.FindName()` which returns style directly

```csharp
// Rhino 8 style
DimensionStyle style = doc.DimStyles.FindName(styleName);

// Socket timeout fix: use ManualResetEventSlim for UI thread sync
using var waitHandle = new ManualResetEventSlim(false);
RhinoApp.InvokeOnUiThread(() => {
    // UI work
    waitHandle.Set();
});
waitHandle.Wait(timeout);
```

---

### Learning: Volume Properties Only for Closed Solids
**Date:** 2026-01-10
**Context:** Implementing US-B06 Object Properties
**Solution:** Check `IsSolid` before computing volume

```csharp
if (brep.IsSolid)
{
    var volumeProps = VolumeMassProperties.Compute(brep);
    double volume = volumeProps.Volume;
}
```

---

### Learning: RunScript for Complex Native Commands
**Date:** 2026-01-10
**Context:** Implementing Groups, Blocks, File Operations
**Solution:** Use `RhinoApp.RunScript()` for complex operations

```csharp
// Groups
RhinoApp.RunScript("_-Group", false);

// Blocks
RhinoApp.RunScript("_-Block", false);

// File operations
RhinoApp.RunScript("_-Export", false);

// Selection required before many operations
foreach (Guid id in objectIds)
{
    doc.Objects.Select(id);
}
```

---

### Learning: Viewport API Patterns
**Date:** 2026-01-10
**Context:** Implementing US-C02 Viewport Control
**Solution:** Various viewport API methods

```csharp
// Set camera direction
viewport.SetCameraDirection(Vector3d direction, bool updateCameraLocation);

// Zoom to bounding box
viewport.ZoomBoundingBox(bbox);

// Capture to bitmap (requires System.Drawing.Common)
Bitmap bmp = viewport.CaptureToBitmap(width, height);
```

---

## Best Practices

1. **Always check object type** before operations (Brep vs Extrusion vs Mesh)
2. **Use tolerance from document** (`doc.ModelAbsoluteTolerance`)
3. **Call `doc.Views.Redraw()`** after geometry changes
4. **Use UI thread** for operations that require Rhino UI
5. **Prefer RunScript** for complex multi-step operations
