# Functional Status, Problems and Solutions Log

Purpose: Track what works, what is flaky or broken, and how issues were solved. This complements `AGENTS.md` by capturing operational reality over time.

## How to use this log

- Add a new entry whenever you:
  - Validate a feature works reliably
  - Hit an error/limitation, or observe flaky behavior
  - Implement a fix or workaround
- Use short IDs to cross-reference from PRs/issues and `AGENTS.md`.
- Keep entries concise but actionable. Include repro steps and environment.

### Entry template

```
ID: <W-/P-/S-####>
Title: <short title>
Type: <WORKS|PROBLEM|SOLUTION>
Status: <OPEN|RESOLVED|N/A>
Date: <YYYY-MM-DD>
Environment: { OS: <...>, Rhino: <...>, MCP server: <version>, Plugin: <version> }
Related: [<IDs/PRs/commits/links>]

Summary:
- <1-3 bullets>

Details:
- Steps to reproduce (if applies)
- Expected vs actual
- Logs/errors (trimmed)

Outcome:
- <for SOLUTION: what changed, verification steps>
```

## Status board

- Works well
  - W-0001: Block creation and castle assembly via RhinoScript (AddBlock/InsertBlock/AddBox)
  - W-0002: Artwork generation (cubes/spheres/cylinders/cones/torus) with colors
  - W-0003: Metallic materials (Gold/Silver) with object assignment and cube creation
  - W-0004: PBR materials (Gold/Silver/Platinum) with metallic and roughness parameters
- Flaky/Investigate
  - (none currently)
- Broken
  - (none currently)
- Resolved
  - P-0001: Intermittent "No data received" on script execution - FIXED with configurable timeout

## Entries

### W-0001 — Block creation and castle assembly
Type: WORKS • Status: N/A • Date: 2025-08-26
Environment: { OS: Windows 10 (10.0.26100), Rhino: unknown, MCP server: 0.1.3.6, Plugin: 0.1.3.6 }
Related: `AGENTS.md` (Testing instructions)

Summary:
- Creating a cubic block with `AddBox` then defining with `AddBlock` and instancing with `InsertBlock` works.
- Constructed perimeter walls, towers, and a central keep; ~597 instances placed.

Details:
- Methods used: `AddBox`, `AddBlock`, `InsertBlock`
- Verified via `get_document_info` counts and layer content

---

### W-0002 — Artwork generation with colored primitives
Type: WORKS • Status: N/A • Date: 2025-08-26
Environment: { OS: Windows 10 (10.0.26100), Rhino: unknown, MCP server: 0.1.3.6, Plugin: 0.1.3.6 }
Related: `AGENTS.md` (Testing instructions)

Summary:
- Generated mixed geometry (cubes, spheres, cylinders, cones, torus) with HSV palette.
- Objects placed on layer `Artwork`; verified via `get_document_info`.

Details:
- Methods used: `AddBox`, `AddSphere`, `AddCylinder`, `AddCone`, `AddTorus`, `ObjectColor`
- Radial ring, spiral tower, pylons with caps, central halo, voxel cloud

---

### P-0001 — Intermittent "No data received" on execute_rhinoscript_python_code
Type: PROBLEM • Status: RESOLVED • Date: 2025-08-26 • Resolved: 2026-01-10
Environment: { OS: Windows 10 (10.0.26100), Rhino: unknown, MCP server: 0.1.3.6, Plugin: 0.1.3.6 }
Related: S-0001

Summary:
- Running a larger RhinoScript via `execute_rhinoscript_python_code` sometimes returns "Communication error with Rhino: No data received".
- Despite the error, objects are often created (side effects present), indicating a response/timeout issue.

Details:
- Repro: Execute a long script that creates many objects; occasionally the server returns error while the model updates.
- Expected: Stable success response after completion.
- Actual: Error reported; `get_document_info` shows geometry present (false negative).

---

### S-0001 — Workaround and remediation for intermittent response timeout
Type: SOLUTION • Status: RESOLVED (workaround) • Date: 2025-08-26
Environment: { OS: Windows 10 (10.0.26100), Rhino: unknown, MCP server: 0.1.3.6, Plugin: 0.1.3.6 }
Related: P-0001

Summary:
- Workaround: Retry script execution; follow with a `get_document_info` validation step.
- Suggest splitting large scripts into smaller batches or using C# batch handlers for heavy operations.

Outcome:
- Verified: After error, document contained `Artwork` layer with expected objects.
- **RESOLVED (2026-01-10):** Added configurable `timeout` parameter to `execute_rhinoscript_python_code`.
  - Default: 15 seconds, Max: 120 seconds
  - Usage: `execute_rhinoscript_python_code(code="...", timeout=60)`
  - See USAGE.md for documentation.
  - Consider adding explicit C# endpoints for batch geometry creation to avoid monolithic scripts.

### W-0003 — Gold and Silver Materials with Cube Creation
Type: WORKS • Status: N/A • Date: 2025-10-21
Environment: { OS: Windows 10, Rhino: 8.0, MCP server: 0.1.3.6, Plugin: latest }

Summary:
- Successfully created Gold and Silver metallic materials with high shine values
- Deleted previous spheres and created new cubes with material assignments
- Demonstrated complete workflow: delete → create materials → create objects → assign materials

Details:
- Created materials: Gold_Material (ID: 4, color: [255,215,0], shine: 0.9), Silver_Material (ID: 5, color: [192,192,192], shine: 0.8)
- Created cubes: Gold_Cube (2x2x2) at [0,0,0], Silver_Cube (1.5x1.5x1.5) at [3,0,0]
- Material assignment via ObjectMaterialSource and ObjectMaterialIndex worked reliably
- All operations logged with AI thoughts for traceability

Outcome:
- Confirmed: Materials render correctly in Rhino with metallic appearance
- Verified: Object-to-material assignment persists and displays in Rendered viewport
- Added USAGE.md documentation for future reference

### W-0004 — Layer-Based PBR Materials with Sphere Creation
Type: WORKS • Status: RESOLVED • Date: 2025-10-21
Environment: { OS: Windows 10, Rhino: 8.0, MCP server: 0.1.3.6, Plugin: latest }

Summary:
- Successfully implemented TRUE LAYER-BASED PBR (Physically Based Rendering) material system
- Created Gold, Silver, and Platinum PBR materials with realistic metallic properties using Layer inheritance
- Created three spheres on dedicated PBR material layers demonstrating proper Rhino workflow
- RESOLVED: Fixed "Custom vs PBR" issue using correct Layer-based material assignment approach

Details:
- Enhanced CreateMaterial function to support material_type='pbr' parameter with enhanced PBR implementation
- Added metallic (0.0-1.0) and roughness (0.0-1.0) parameters for proper PBR materials
- Created Layer-based system: Gold_Material_Layer, Silver_Material_Layer, Platinum_Material_Layer
- Created TRUE PBR materials: Gold_PBR (ID: 7, metallic: 0.95, roughness: 0.05), Silver_PBR (ID: 8, metallic: 0.90, roughness: 0.08), Platinum_PBR (ID: 9, metallic: 0.92, roughness: 0.06)
- Created spheres on respective layers: Gold_Sphere (-3,0,0), Silver_Sphere (0,0,0), Platinum_Sphere (3,0,0)
- Objects automatically inherit PBR materials from their layers via RenderMaterialIndex
- Updated documentation (USAGE.md) with correct Layer-based PBR examples and parameter guidelines

Outcome:
- ✅ RESOLVED: TRUE PBR materials render with realistic metallic appearance in Rendered viewport
- ✅ VERIFIED: Layer-based PBR parameter system (metallic/roughness) functions correctly
- ✅ COMPLETED: Enhanced material system supports Layer-based PBR material assignment
- ✅ SUCCESS: "Custom vs PBR" issue completely resolved with proper Rhino Layer-based workflow
- ✅ TESTED: All three metallic materials successfully created, assigned to layers, and inherited by objects

## Backlog / Next candidates

- Add batch endpoints for bulk geometry operations (create_objects for parametric primitives)
- Expose configurable timeout for `execute_rhinoscript_python_code`
- Add health-check tool (`ping`) returning immediate OK from plugin
- Extend serializer coverage for more geometry types and attributes
