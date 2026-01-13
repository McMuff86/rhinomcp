# Material Assignment to Layers - Complete Guide

**Date:** 2026-01-13  
**Status:** ✅ RESOLVED  
**Related Issues:** Material assignment to layers, objects appearing white in rendered mode

---

## Problem Summary

Objects were created with materials assigned to layers, but:
1. Objects appeared **white** in rendered mode despite materials being assigned
2. **Material icons were missing** in the Layers panel
3. Materials were created but **not visible** in Rhino's material panel

---

## Root Causes Identified

### 1. Missing MaterialSource Setting (CRITICAL)

**Problem:** Objects were not configured to use layer materials.

**Root Cause:** When creating objects, `MaterialSource` was not set to `MaterialFromLayer`. By default, Rhino objects use their own material or the default material, not layer materials.

**Solution:** Set `rhinoObject.Attributes.MaterialSource = ObjectMaterialSource.MaterialFromLayer` when assigning objects to layers.

**Location:** `rhino_mcp_plugin/Functions/CreateObject.cs`

```csharp
// Assign object to layer
rhinoObject.Attributes.LayerIndex = layerIndex;

// CRITICAL: Set material source to layer so objects use layer materials
rhinoObject.Attributes.MaterialSource = ObjectMaterialSource.MaterialFromLayer;
```

### 2. Incorrect Layer Modification Parameter

**Problem:** Material assignment to layers failed silently.

**Root Cause:** `doc.Layers.Modify()` was called with `layerId` (Guid) instead of `layer.Index` (int).

**Solution:** Always use `layer.Index` (int) for `Modify()` calls, not the layer GUID.

**Location:** `rhino_mcp_plugin/Functions/CreateLayer.cs`

```csharp
// WRONG:
bool modifySuccess = doc.Layers.Modify(layer, layerId, true); // layerId is Guid

// CORRECT:
var layerIndex = layer.Index; // Get int index
bool modifySuccess = doc.Layers.Modify(layer, layerIndex, true); // Use int index
```

### 3. Material Creation Incomplete

**Problem:** Materials were created but not visible in Rhino's UI.

**Root Cause:** Materials were only added to `doc.RenderMaterials`, but not to `doc.Materials`. The UI requires materials in both tables.

**Solution:** Add materials to both `doc.Materials` and `doc.RenderMaterials`.

**Location:** `rhino_mcp_plugin/Functions/GetDocumentInfo.cs` - `CreateMaterial()`

```csharp
// 1. Create base Material
var baseMaterial = new Material { ... };
baseMaterial.CommitChanges();

// 2. CRITICAL: Add to doc.Materials first (for UI visibility)
int materialIndex = doc.Materials.Add(baseMaterial);
if (materialIndex < 0)
{
    throw new InvalidOperationException("Failed to add material to doc.Materials");
}

// 3. Create RenderMaterial from base material
var renderMaterial = Rhino.Render.RenderMaterial.CreateBasicMaterial(baseMaterial, doc);
renderMaterial.Name = name;

// 4. Add to doc.RenderMaterials (for rendering)
bool addSuccess = doc.RenderMaterials.Add(renderMaterial);
if (!addSuccess)
{
    throw new InvalidOperationException("Failed to add RenderMaterial");
}

int renderIndex = doc.RenderMaterials.Count - 1;

// 5. Force UI update
doc.Views.Redraw();
```

---

## Best Practices

### 1. Material Creation Workflow

**Always:**
1. Create `Material` object with properties
2. Convert to PBR if needed (`ToPhysicallyBased()`)
3. Add to `doc.Materials` first (for UI)
4. Create `RenderMaterial` from base material
5. Add to `doc.RenderMaterials` (for rendering)
6. Call `doc.Views.Redraw()` to update UI

**Never:**
- Skip adding to `doc.Materials` (materials won't appear in UI)
- Use only `doc.RenderMaterials` (incomplete)
- Forget to set `renderMaterial.Name` (important for identification)

### 2. Layer Material Assignment

**Always:**
1. Create layer first
2. Wait briefly (`time.sleep(0.1`) to ensure layer is ready
3. Assign material using `assign_material_to_layer` (separate call)
4. Use `layer.Index` (int) for `Modify()` calls, not GUID

**Recommended Pattern:**
```python
# Create layer
rhino.send_command("create_layer", {
    "name": layer_name,
    "color": config["color"]
})

# Small delay to ensure layer is ready
time.sleep(0.1)

# Assign material separately (ensures UI updates properly)
rhino.send_command("assign_material_to_layer", {
    "layer_name": layer_name,
    "material_id": material_id
})
```

### 3. Object Creation with Layer Materials

**Always:**
1. Set `LayerIndex` on object attributes
2. Set `MaterialSource = MaterialFromLayer` (CRITICAL!)
3. Set `ColorSource = ColorFromLayer` if no custom color

**Code Pattern:**
```csharp
// Assign object to layer
rhinoObject.Attributes.LayerIndex = layerIndex;

// Use layer color unless custom color is specified
if (!customColor)
{
    rhinoObject.Attributes.ColorSource = ObjectColorSource.ColorFromLayer;
}

// CRITICAL: Set material source to layer so objects use layer materials
rhinoObject.Attributes.MaterialSource = ObjectMaterialSource.MaterialFromLayer;
```

### 4. Material Assignment Verification

**Always verify:**
1. Material exists in both `doc.Materials` and `doc.RenderMaterials`
2. Layer has correct `RenderMaterialIndex`
3. Object has `MaterialSource = MaterialFromLayer`
4. Object is on correct layer

**Verification Script Pattern:**
```python
verify_script = """
import scriptcontext
doc = scriptcontext.doc

layer = doc.Layers.FindName("LayerName")
if layer:
    print("RenderMaterialIndex: " + str(layer.RenderMaterialIndex))
    if layer.RenderMaterialIndex >= 0:
        render_mat = doc.RenderMaterials[layer.RenderMaterialIndex]
        print("Material: " + render_mat.Name)

obj = doc.Objects.FindByName("ObjectName", 0)
if obj:
    print("MaterialSource: " + str(obj.Attributes.MaterialSource))
    print("LayerIndex: " + str(obj.Attributes.LayerIndex))
"""
```

---

## Common Pitfalls

### ❌ Pitfall 1: Forgetting MaterialSource

**Symptom:** Objects appear white despite materials being assigned to layers.

**Fix:** Always set `MaterialSource = MaterialFromLayer` when assigning objects to layers.

### ❌ Pitfall 2: Using GUID instead of Index

**Symptom:** `Modify()` calls fail silently or return false.

**Fix:** Always use `layer.Index` (int) for `Modify()` calls.

### ❌ Pitfall 3: Only Adding to RenderMaterials

**Symptom:** Materials don't appear in Rhino's material panel.

**Fix:** Add materials to both `doc.Materials` and `doc.RenderMaterials`.

### ❌ Pitfall 4: Assigning Material During Layer Creation

**Symptom:** Material assignment doesn't persist or UI doesn't update.

**Fix:** Create layer first, then assign material in a separate call with a small delay.

---

## Complete Working Example

```python
# 1. Create Material
result = rhino.send_command("create_material", {
    "name": "MyMaterial",
    "color": [255, 0, 0],
    "material_type": "pbr",
    "metallic": 0.5,
    "roughness": 0.5
})
material_id = result.get("id")

time.sleep(0.3)  # Ensure material is ready

# 2. Create Layer
result = rhino.send_command("create_layer", {
    "name": "MyLayer",
    "color": [255, 0, 0]
})

time.sleep(0.1)  # Ensure layer is ready

# 3. Assign Material to Layer
result = rhino.send_command("assign_material_to_layer", {
    "layer_name": "MyLayer",
    "material_id": material_id
})

time.sleep(0.1)  # Ensure assignment is complete

# 4. Create Object on Layer
result = rhino.send_command("create_object", {
    "type": "SPHERE",
    "name": "MySphere",
    "params": {"radius": 2},
    "layer": "MyLayer"  # MaterialSource will be set automatically
})
```

---

## C# Implementation Checklist

When implementing material assignment in C#:

- [ ] Create `Material` object with all properties
- [ ] Convert to PBR if needed (`ToPhysicallyBased()`)
- [ ] Add to `doc.Materials` first
- [ ] Create `RenderMaterial` from base material
- [ ] Set `renderMaterial.Name`
- [ ] Add to `doc.RenderMaterials`
- [ ] Call `doc.Views.Redraw()`
- [ ] Use `layer.Index` (int) for `Modify()` calls
- [ ] Set `MaterialSource = MaterialFromLayer` on objects
- [ ] Verify assignment after modification

---

## Testing Checklist

Before considering material assignment complete:

- [ ] Materials appear in Rhino's material panel
- [ ] Material icons appear in Layers panel
- [ ] Objects use correct materials in rendered mode
- [ ] Material properties (color, metallic, roughness) are correct
- [ ] Material assignment persists after document save/reload
- [ ] Multiple materials can be assigned to different layers
- [ ] Objects inherit materials from their layers correctly

---

## Related Files

- `rhino_mcp_plugin/Functions/CreateMaterial.cs` - Material creation
- `rhino_mcp_plugin/Functions/CreateLayer.cs` - Layer creation
- `rhino_mcp_plugin/Functions/AssignMaterialToLayer.cs` - Material assignment
- `rhino_mcp_plugin/Functions/CreateObject.cs` - Object creation with MaterialSource
- `rhino_mcp_server/src/rhinomcp/tools/create_material.py` - Python tool wrapper
- `rhino_mcp_server/src/rhinomcp/tools/assign_material_to_layer.py` - Python tool wrapper

---

## References

- [RhinoCommon API - Material](https://developer.rhino3d.com/api/rhinocommon/html/T_Rhino_DocObjects_Material.htm)
- [RhinoCommon API - RenderMaterial](https://developer.rhino3d.com/api/rhinocommon/html/T_Rhino_Render_RenderMaterial.htm)
- [RhinoCommon API - Layer](https://developer.rhino3d.com/api/rhinocommon/html/T_Rhino_DocObjects_Layer.htm)
- [RhinoCommon API - ObjectMaterialSource](https://developer.rhino3d.com/api/rhinocommon/html/T_Rhino_DocObjects_ObjectMaterialSource.htm)

---

## Summary

The three critical fixes that resolved material assignment:

1. **Set `MaterialSource = MaterialFromLayer`** on objects (enables layer material inheritance)
2. **Use `layer.Index` (int)** for `Modify()` calls (ensures persistence)
3. **Add materials to both `doc.Materials` and `doc.RenderMaterials`** (ensures UI visibility and rendering)

Following these patterns ensures materials work correctly in Rhino.
