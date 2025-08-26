# RhinoMCP: 2D-DWG/DXF Analysis – Workflow & Learning File (ANALYSIS_LOG.md)

> Goal: Automatically understand 2D drawings (DWG/DXF), extract useful context (rebate depth, rebate width, gasket groove, etc.), and build reusable knowledge. This document serves as a **learning file (ANALYSIS_LOG.md)**, which we will update with every run.

---

## 1) High-Level Pipeline

1. **Import & Normalization**
   - File type: DWG/DXF → Rhino (R8)
   - Unify units & scaling (mm), document `ModelAbsoluteTolerance`
   - Read layer and block names, mapping/normalization (regex tables)

2. **Geometry Capture (2D Primitives)**
   - Lines, polylines, arcs, circles, splines, hatches, texts/leaders, dimensions
   - Explode block instances (if needed) and/or read attribute values
   - Separate visible vs. construction/auxiliary geometry (layer policies)

3. **Feature Extraction / Semantics**
   - **Profiles & Rebate**: detect parallel offsets/contours → rebate width/depth
   - **Gasket groove**: typical groove geometry (narrow, continuous grooves), layer/linetype heuristics
   - **Hardware / drilling patterns**: regular hole arrays (pattern detection), dimension text parsing
   - **Section/View**: hatches (cut faces), arrows/leaders; scale & projection
   - **Texts & styles**: keywords, style mapping (e.g. “Standard 1:10 Title”, position labels)

4. **Property Derivation & Validation**
   - Combine multiple heuristics (geometry, layer, text, dims)
   - Confidence for each property (0.0–1.0) + reason/trace (why recognized)
   - Consistency checks (e.g. rebate width ≤ frame width – wall thickness)

5. **Export & Learning**
   - JSON with **properties** (see schema below)
   - Markdown append in **ANALYSIS_LOG.md** (this file): new case study + “learnings”
   - Optional: PNG preview with annotated overlays (IDs/bounding boxes) for review

---

## 2) Properties Schema (JSON)

```json
{
  "metadata": {
    "source_file": "",
    "units": "mm",
    "scale": 1.0,
    "tolerance": 0.01,
    "view_type": "section|elevation|detail|unknown",
    "detected_blocks": [""],
    "layer_map_version": "v1"
  },
  "frame": {
    "frame_width": {"value": null, "conf": 0.0, "trace": ""},
    "profile_type": {"value": "steel|aluminum|wood|unknown", "conf": 0.0, "trace": ""},
    "rebate_width": {"value": null, "conf": 0.0, "trace": ""},
    "rebate_depth": {"value": null, "conf": 0.0, "trace": ""},
    "gasket_present": {"value": false, "conf": 0.0, "trace": ""},
    "gasket_width": {"value": null, "conf": 0.0, "trace": ""},
    "gasket_depth": {"value": null, "conf": 0.0, "trace": ""},
    "groove_position": {"value": "rebate_bottom|rebate_side|center", "conf": 0.0, "trace": ""}
  },
  "leaf_panel": {
    "panel_thickness": {"value": null, "conf": 0.0, "trace": ""},
    "edge_build": {"value": "laminate|ABS|steel_edge|unknown", "conf": 0.0, "trace": ""},
    "rebate_type": {"value": "single|double|none", "conf": 0.0, "trace": ""}
  },
  "hardware": {
    "hinges": {"count": 0, "type": "2D|3D|concealed|unknown", "conf": 0.0, "trace": ""},
    "lock_type": {"value": "profile_cylinder|warded|panic|unknown", "conf": 0.0, "trace": ""},
    "drilling_pattern": {"pattern": "", "conf": 0.0, "trace": ""}
  },
  "sealing": {
    "num_levels": {"value": 0, "conf": 0.0, "trace": ""},
    "type": {"value": "perimeter|frame_only|threshold_only|unknown", "conf": 0.0, "trace": ""}
  },
  "clear_dimensions": {
    "clear_width": {"value": null, "conf": 0.0, "trace": ""},
    "clear_height": {"value": null, "conf": 0.0, "trace": ""},
    "handing": {"value": "left|right|both|unknown", "conf": 0.0, "trace": ""}
  },
  "notes": [""],
  "version": "2025-08-26"
}
```

> **Note:** Each field carries **value**, **conf** (confidence), and **trace** (why detected).

---

## 3) Heuristics (Quick Reference)

- **Rebate width/depth:** search for parallel inner-shadow contour vs. outer contour of a frame (offset distance). Depth ≈ perpendicular distance from outer edge to rebate bottom.
- **Gasket groove:** narrow, uniform groove (typically 3–6 mm) along rebate; often a separate layer/linetype; sometimes labeled with text/leader “gasket”/“EPDM”.
- **Section vs. elevation:** hatches → section. No hatches + visible edges → elevation. Dim texts with “Ø”, “M” → drilling/thread info.
- **Hardware:** regular hole patterns (circles) along hinge side; spacing patterns (e.g. 20/80) identify system.
- **Text parsing:** regex on text/dims: `(?i)(rebate|gasket|groove|EPDM|KK\d|EI\d+)` → properties & classification.
- **Units/scaling:** check distances of known elements (e.g. 100 mm grid) → validate import scale.

---

## 4) Rhino Evaluation – Object Classes & Checks

**Basic classes**
- Lines/polylines/arcs/circles/splines → contours, grooves, drilling patterns
- Hatches → material/section representation
- Dims/leaders → measurements, labels
- Blocks + attributes → manufacturer details, type keys

**Checks**
- Layer conventions (mapping table): e.g. `*GASKET*`, `*REBATE*`, `*LOCK*`, `*HINGE*`
- Minimum distances & parallelism (epsilon ~ tolerance)
- Squareness (dot product ~ 0) → detect rectangular frame contour

---

## 5) Automated Export (Files)

- `/analysis/<dwg-name>/properties.json` → filled property schema
- `/analysis/<dwg-name>/preview.png` → annotated preview
- Append in **ANALYSIS_LOG.md** → new case study + learnings

---

## 6) ANALYSIS_LOG.md – Append Template per Drawing

### Case Study: `<DWG/DXF filename>`
- **Context**: short description (project, manufacturer, source)
- **Import**: units, tolerance, scale
- **Detected view**: section/elevation/detail (reason)
- **Properties (short)**:
  - Rebate width: … mm (conf …)
  - Rebate depth: … mm (conf …)
  - Gasket: yes/no, width/depth, position (conf …)
  - Panel thickness: … mm (conf …)
  - Hardware: hinges x … (type …), lock … (conf …)
  - Clear dims: W×H …×… mm (conf …)
- **Special patterns/heuristic matches**: …
- **Uncertainties/To‑do**: …
- **Learnings** (rules/regex/layer map updates): …

---

## 7) MCP Tooling (for Cursor / rhinomcp)

**Goal**: An MCP tool that
- accepts a file (DWG/DXF/3DM),
- controls Rhino (headless) via Rhino.Compute or Rhino Python CLI,
- returns JSON properties + preview,
- appends this learning file (ANALYSIS_LOG.md).

**Tool I/O (suggestion)**
- **input**: `{ "file_path": "…", "assumptions": "(optional) free text", "layer_map_id": "v1" }`
- **output**: `{ "properties_path": "…/properties.json", "preview_path": "…/preview.png", "summary": "short text" }`

**Config**
- `layer_map.json` (regex → normal form) e.g. `{".*GASKET.*":"GASKET",".*REBATE.*":"REBATE"}`
- `regex_rules.json` (text detection) e.g. NCS colors, KK climate classes, EI30 etc.

---

## 8) Short Algorithm for Rebate & Gasket Groove (Pseudo)

1. Find outer frame: largest closed rectangular polyline on layer “FRAME|PROFILE”
2. Search inner offset contour (offset ~ 10–30 mm): → **rebate width**
3. Rebate bottom → distance outer edge → inner step: → **rebate depth**
4. Gasket groove candidates: narrow elongated polylines/arcs near rebate bottom (distance < 8 mm)
5. Aggregation: combine hits + text labels + layer mapping, compute `conf`

---

## 9) Example: Properties (Short)

```json
{
  "frame": {
    "rebate_width": {"value": 18.0, "conf": 0.86, "trace": "Offset pair #12 (Layer PROFILE)"},
    "rebate_depth": {"value": 25.0, "conf": 0.78, "trace": "Distance outer edge→step (section hatch present)"},
    "gasket_present": {"value": true, "conf": 0.92, "trace": "Polyline (w=4.0 mm) on layer GASKET"}
  }
}
```

---

## 10) Review Checklist (per file)

- [ ] Units/tolerance checked and logged
- [ ] Layer mapping applied (version noted)
- [ ] View type correctly identified
- [ ] Rebate values plausible (compare to frame width)
- [ ] Gasket groove consistent around perimeter
- [ ] Hardware drilling patterns detected (if present)
- [ ] JSON/preview generated
- [ ] Case study + learnings appended

---

## 11) Next Iterations

- ML‑based classification (HOG/SVM or lightweight CNNs) for patterns (gasket/hinge)
- Rule editor (GUI) for layer/regex/heuristics
- Unit tests with gold samples (expected JSON)
- Export to BORM/CSV for further automation

---

## Ready-to-Use Append Template

### Case Study: `<DWG/DXF filename>`
- **Context**: …
- **Import**: Units = … | Tolerance = … | Scale = …
- **Detected view**: …
- **Properties**:
  - Rebate width: … mm (conf …)
  - Rebate depth: … mm (conf …)
  - Gasket: yes/no – width … mm, depth … mm, position … (conf …)
  - Panel thickness: … mm (conf …)
  - Hardware: Hinges x … (type …), Lock: … (conf …)
  - Clear dims: W×H …×… mm (conf …)
- **Special patterns/heuristic matches**: …
- **Uncertainties/To‑do**: …
- **Learnings**: …

