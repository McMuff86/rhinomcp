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
- Flaky/Investigate
  - P-0001: Intermittent "No data received" on script execution, despite side effects
- Broken
  - (none currently)

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
Type: PROBLEM • Status: OPEN • Date: 2025-08-26
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
- Next steps (engineering):
  - Increase server read timeout for script execution responses.
  - Stream progress or chunk long operations (e.g., create in batches of N).
  - Consider adding explicit C# endpoints for batch geometry creation to avoid monolithic scripts.

## Backlog / Next candidates

- Add batch endpoints for bulk geometry operations (create_objects for parametric primitives)
- Expose configurable timeout for `execute_rhinoscript_python_code`
- Add health-check tool (`ping`) returning immediate OK from plugin
- Extend serializer coverage for more geometry types and attributes
