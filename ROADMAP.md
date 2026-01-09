# RhinoMCP Roadmap

> Strategic plan for evolving RhinoMCP from proof-of-concept to professional product.

**Last Updated:** 2026-01-09  
**Current Version:** 0.1.3.6

---

## Vision

Transform RhinoMCP into a **professional, monetizable** MCP integration that enables AI-powered 3D modeling in Rhino with enterprise-grade reliability.

---

## Phases Overview

| Phase | Focus | Status | Timeline |
|-------|-------|--------|----------|
| **A** | Stability & Foundation | 🔄 In Progress | Q1 2026 |
| **B** | Core Features | 📋 Planned | Q2 2026 |
| **C** | Advanced Features | 📋 Planned | Q3 2026 |
| **D** | Monetization | 📋 Planned | Q4 2026 |

---

## Phase A: Stability & Foundation

**Goal:** Make RhinoMCP reliable and maintainable.

### User Stories (see `Ralph/prd.json`)

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| US-001 | Structured error codes | 1 | ⬜ |
| US-002 | Auto-reconnect on connection drop | 2 | ⬜ |
| US-003 | Complete C# handlers for annotations | 3 | ⬜ |
| US-004 | Pytest test suite | 4 | ⬜ |
| US-005 | GitHub Actions CI | 5 | ⬜ |
| US-006 | Configurable script timeout | 6 | ⬜ |

### Success Criteria
- [ ] All 6 stories completed
- [ ] CI pipeline green on every PR
- [ ] Zero known critical bugs
- [ ] Documentation up-to-date

---

## Phase B: Core Features

**Goal:** Add essential geometry and transformation capabilities.

### Planned Features

| Feature | Description | Complexity |
|---------|-------------|------------|
| Boolean Operations | Union, Difference, Intersection | Medium |
| NURBS Curves | Create/modify NURBS curves | Medium |
| NURBS Surfaces | Create/modify NURBS surfaces | High |
| Dimensions | Linear, Angular, Radial dimensions | Medium |
| Transform Tools | Copy, Mirror, Array patterns | Medium |
| Curve Operations | Offset, Fillet, Chamfer | Medium |

### Success Criteria
- [ ] Boolean operations work reliably
- [ ] At least 5 new geometry types supported
- [ ] All new features have tests

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
- [ ] Mesh round-trip works
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

## Technical Debt to Address

| Item | Description | Phase |
|------|-------------|-------|
| Socket handling | Fragile, no keepalive | A |
| Missing tests | Only dev_test.py exists | A |
| Inconsistent returns | Mix of strings and dicts | A |
| No type hints in C# | JObject everywhere | B |
| Large files | server.py could be split | B |

---

## How to Contribute

1. Pick a story from `Ralph/prd.json` where `passes: false`
2. Read `Ralph/progress.txt` for patterns
3. Implement in small steps
4. Update documentation
5. Mark story as `passes: true`

See `Ralph/README.md` for the complete workflow.

---

## References

- [AGENTS.md](AGENTS.md) - Agent development guide
- [Ralph/README.md](Ralph/README.md) - Structured development workflow
- [FUNCTIONAL_STATUS.md](FUNCTIONAL_STATUS.md) - What works/problems/solutions
- [MCP_TOOL_STANDARDS.md](MCP_TOOL_STANDARDS.md) - Tool development standards
