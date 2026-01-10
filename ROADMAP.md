# RhinoMCP Roadmap

> Strategic plan for evolving RhinoMCP from proof-of-concept to professional product.

**Last Updated:** 2026-01-10  
**Current Version:** 0.1.3.6

---

## Vision

Transform RhinoMCP into a **professional, monetizable** MCP integration that enables AI-powered 3D modeling in Rhino with enterprise-grade reliability.

---

## Phases Overview

| Phase | Focus | Status | Timeline |
|-------|-------|--------|----------|
| **A** | Stability & Foundation | ✅ Complete | Q1 2026 |
| **B** | Core Features | 🔄 In Progress | Q2 2026 |
| **C** | Advanced Features | 📋 Planned | Q3 2026 |
| **D** | Monetization | 📋 Planned | Q4 2026 |

---

## Phase A: Stability & Foundation ✅

**Goal:** Make RhinoMCP reliable and maintainable.

### User Stories (Complete)

| ID | Title | Status |
|----|-------|--------|
| US-001 | Structured error codes | ✅ |
| US-002 | Auto-reconnect on connection drop | ✅ |
| US-003 | Complete C# handlers for annotations | ✅ |
| US-004 | Pytest test suite (34 tests) | ✅ |
| US-005 | GitHub Actions CI | ✅ |
| US-006 | Configurable script timeout | ✅ |

### Bug Fixes

| ID | Issue | Status |
|----|-------|--------|
| P-0002 | PBR material not visible in Rhino | ✅ Fixed |
| P-0003 | Objects created on wrong layer | ✅ Fixed |
| P-0004 | assign_material_to_layer null error | ✅ Fixed |

### Achievements
- ✅ All 6 stories completed
- ✅ CI pipeline green on every PR
- ✅ Zero known critical bugs
- ✅ Documentation up-to-date

---

## Phase B: Core Features 🔄

**Goal:** Add essential geometry and transformation capabilities.

### User Stories (see `Ralph/prd_phase_b.json`)

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| US-B01 | Boolean Operations (Union, Difference, Intersection) | 1 | ⬜ |
| US-B02 | Transform Tools (Copy, Mirror, Array) | 2 | ⬜ |
| US-B03 | Curve Operations (Offset, Fillet, Chamfer) | 3 | ⬜ |
| US-B04 | Surface from Curves (Loft, Extrude, Revolve) | 4 | ⬜ |
| US-B05 | Dimension Tools (Linear, Angular, Radial) | 5 | ⬜ |
| US-B06 | Get/Set Object Properties | 6 | ⬜ |

### Success Criteria
- [ ] Boolean operations work reliably on solids
- [ ] At least 5 new geometry operations supported
- [ ] All new features have tests
- [ ] Documentation updated for each feature

---

## Phase C: Advanced Features

**Goal:** Enable complex workflows and integrations.

### Planned Features

| Feature | Description | Complexity |
|---------|-------------|------------|
| Grasshopper Integration | Evaluate definitions, set parameters, bake | High |
| Mesh I/O | Import/export OBJ, STL, 3MF | Medium |
| Groups & Blocks | Create, modify, explode groups/blocks | Medium |
| Render Settings | Camera, lighting, render presets | Medium |
| File Operations | Open, save, export documents | Low |
| Viewport Control | Set view, zoom, pan, named views | Low |

### Success Criteria
- [ ] Grasshopper integration functional
- [ ] Mesh round-trip works (import → modify → export)
- [ ] 90% of common Rhino workflows possible via MCP

---

## Phase D: Monetization

**Goal:** Enable sustainable business model.

### Planned Features

| Feature | Description | Model |
|---------|-------------|-------|
| License System | API keys, subscription tiers | SaaS |
| Usage Analytics | Track tool usage, performance metrics | Internal |
| Premium Features | Advanced tools behind paywall | Freemium |
| Team Features | Shared projects, collaboration | Enterprise |
| Cloud Version | Hosted MCP server (no local Rhino) | Cloud |

### Business Models to Evaluate
1. **Freemium**: Basic tools free, advanced paid
2. **Subscription**: Monthly/yearly plans with tiers
3. **Per-seat**: License per Rhino installation
4. **API Usage**: Pay-per-call pricing

---

## Technical Debt

| Item | Description | Phase | Status |
|------|-------------|-------|--------|
| Socket handling | Fragile, no keepalive | A | ✅ Fixed (auto-reconnect) |
| Missing tests | Only dev_test.py exists | A | ✅ Fixed (34 pytest tests) |
| Inconsistent returns | Mix of strings and dicts | A | ✅ Fixed (structured responses) |
| No type hints in C# | JObject everywhere | B | ⬜ |
| Large files | server.py could be split | B | ⬜ |

---

## How to Contribute

1. Read `Ralph/progress.txt` for codebase patterns
2. Check `Ralph/prd_phase_b.json` for current stories
3. Pick highest priority story with `passes: false`
4. Implement in small steps
5. Update `Ralph/progress.txt` with learnings
6. Mark story as `passes: true`

See [Ralph/README.md](Ralph/README.md) for the complete workflow.

---

## References

| Document | Purpose |
|----------|---------|
| [AGENTS.md](AGENTS.md) | Agent development guide |
| [USAGE.md](USAGE.md) | Tool usage guide |
| [Ralph/README.md](Ralph/README.md) | Development workflow |
| [Ralph/progress.txt](Ralph/progress.txt) | Patterns & learnings |
| [FUNCTIONAL_STATUS.md](FUNCTIONAL_STATUS.md) | Feature status log |
| [MCP_TOOL_STANDARDS.md](MCP_TOOL_STANDARDS.md) | Tool standards |
