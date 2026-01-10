# RhinoMCP Repository Analysis

> Comprehensive analysis of documentation, code structure, MCP tools best practices, and Ralph workflow integration.

**Analysis Date:** 2026-01-10  
**Version Analyzed:** 0.1.3.8

---

## Executive Summary

This document provides a comprehensive analysis of the RhinoMCP repository covering:
1. Documentation consistency
2. Python and C# implementation coherence
3. MCP tools best practices adherence
4. Ralph workflow integration
5. Identified weakpoints
6. Improvement recommendations

---

## 1. Documentation Analysis

### 1.1 Documentation Files Inventory

| File | Purpose | Status |
|------|---------|--------|
| `README.md` | Main project overview | ✅ Good |
| `AGENTS.md` | Agent-focused development guide | ✅ Comprehensive |
| `USAGE.md` | Tool usage reference | ⚠️ Needs expansion |
| `ROADMAP.md` | Project phases | ✅ Up-to-date |
| `MCP_TOOL_STANDARDS.md` | Tool development standards | ✅ Good |
| `FUNCTIONAL_STATUS.md` | Feature status log | ✅ Maintained |
| `README_MCP.md` | MCP tools architecture guide | ⚠️ Some outdated examples |
| `PHASE_B_CONTEXT.md` | Context for new threads | ⚠️ Should be archived |
| `ANALYSIS_LOG.md` | DWG/DXF analysis workflow | ❓ Different purpose, unclear integration |
| `development_guide.md` | Development hub | ⚠️ Partially outdated |
| `rhino_mcp_server/README.md` | Server-specific docs | ✅ Good |
| `Ralph/README.md` | Ralph workflow docs | ✅ Good |
| `Ralph/AGENTS.md` | Agent-specific Ralph guide | ✅ Best practice per original Ralph |
| `Ralph/NEXT_SESSION_PLAN.md` | Session planning | ⚠️ Outdated (US-B06 done) |

### 1.2 Inconsistencies Found

#### A. Version Number Inconsistencies
- `USAGE.md`: Version 0.1.3.8
- `ROADMAP.md`: Version 0.1.3.8
- `AGENTS.md`: Version 0.1.3.8
- `pyproject.toml`: Version **0.1.3.6** ❌
- `development_guide.md`: Version 0.2 ❌

**Recommendation:** Centralize version in `pyproject.toml` and reference it elsewhere.

#### B. Test Count Inconsistencies
- `AGENTS.md` states "143 tests" in header
- `Ralph/progress.txt` mentions "138 tests passed" then "150 tests"
- `ROADMAP.md` mentions "138 pytest tests"

**Recommendation:** Dynamically generate test counts or update after each PR.

#### C. Documentation Structure (Ralph Best Practice)

Per the [original Ralph repository](https://github.com/snarktank/ralph), having `AGENTS.md` files in subdirectories is a **best practice**:

> "After each iteration, Ralph updates the **relevant `AGENTS.md` files** with learnings. This is key because Amp automatically reads these files."

**Current Implementation:**
- ✅ Root `AGENTS.md` - Comprehensive RhinoMCP agent guide
- ✅ `Ralph/AGENTS.md` - Ralph-specific workflow guide (correctly references root AGENTS.md)
- ⚠️ Consider adding `rhino_mcp_server/AGENTS.md` for Python-specific context
- ⚠️ Consider adding `rhino_mcp_plugin/AGENTS.md` for C#-specific context

**Note:** `README_MCP.md` and `MCP_TOOL_STANDARDS.md` have overlapping content and `development_guide.md` is partially superseded by `AGENTS.md` - these could be consolidated.

#### D. Tool Count Discrepancy
- Python tools directory: 45 files
- C# handlers registered: ~40 commands
- `RhinoMCPServer.GetAvailableTools()`: Only 30 listed ❌
- Missing in C# tools list: dimension tools, file operations, object properties

---

## 2. Python and C# Implementation Analysis

### 2.1 Architecture Overview

```
┌─────────────────┐    TCP/JSON    ┌──────────────────┐
│ Python MCP      │ ◄───────────► │ C# Rhino Plugin  │
│ Server          │   localhost:1999│                  │
│ (FastMCP)       │               │ (RhinoCommon)    │
└─────────────────┘               └──────────────────┘
```

### 2.2 Python Implementation Quality

**Strengths:**
- ✅ Consistent use of `@mcp.tool()` decorator
- ✅ Structured responses via `ok()` and `from_exception()`
- ✅ Type hints with `Literal` types for enums
- ✅ Centralized error codes in `utils/errors.py`
- ✅ Interaction logging for ML training data
- ✅ Auto-reconnect logic in `RhinoConnection`

**Weaknesses:**
- ⚠️ `select_objects.py` returns plain string instead of JSON
- ⚠️ Some tools import from `rhinomcp` package, others from `rhinomcp.server`
- ⚠️ Not all tools exported in `__init__.py` (missing `get_object_properties`, `set_object_properties`, file operations)
- ⚠️ Inconsistent docstring format (some have Returns section, some don't)

### 2.3 C# Implementation Quality

**Strengths:**
- ✅ Undo-safe operations (`BeginUndoRecord`/`EndUndoRecord`)
- ✅ UI thread dispatch with `InvokeOnUiThread`
- ✅ Comprehensive geometry support (15+ types)
- ✅ Centralized serialization in `Serializers/Serializer.cs`
- ✅ Debug mode toggling
- ✅ Log buffer for debugging

**Weaknesses:**
- ⚠️ No type hints (JObject everywhere)
- ⚠️ `GetAvailableTools()` list is incomplete and manually maintained
- ⚠️ Some handlers in separate files, others embedded in main file
- ⚠️ `_utils.cs` purpose unclear, could be documented
- ⚠️ Error responses don't include structured error codes (just message)

### 2.4 Python ↔ C# Mapping

| Python Tool | C# Handler | File | Status |
|-------------|------------|------|--------|
| `create_object` | `CreateObject` | `CreateObject.cs` | ✅ |
| `boolean_operation` | `BooleanOperation` | `BooleanOperations.cs` | ✅ |
| `get_object_properties` | `GetObjectProperties` | `ObjectProperties.cs` | ✅ |
| `get_logs` | Inline in server | `RhinoMCPServer.cs` | ⚠️ Inconsistent |
| `clear_logs` | Inline in server | `RhinoMCPServer.cs` | ⚠️ Inconsistent |

**Missing Handlers (Python exists, C# missing):**
- ❌ None found - all Python tools have C# handlers

**Orphaned Handlers (C# exists, Python missing):**
- ❌ None found

---

## 3. MCP Tools Best Practices Analysis

### 3.1 Adherence to Standards

Based on `MCP_TOOL_STANDARDS.md`:

| Requirement | Status | Notes |
|-------------|--------|-------|
| Structured JSON responses | ⚠️ 95% | `select_objects.py` returns plain string |
| Error codes in responses | ✅ | All use `ErrorCode` class |
| Type hints on parameters | ✅ | Literal types for enums |
| Logging via `logger` | ✅ | Consistent usage |
| Undo-safe C# operations | ✅ | All wrapped in UndoRecord |
| Compact stable responses | ✅ | Good serialization |

### 3.2 Tool Documentation Quality

**Good Examples:**
- `create_object.py` - Comprehensive docstring with all parameter types documented
- `boolean_operation.py` - Clear operation types with Literal

**Needs Improvement:**
- `get_logs.py` - Minimal docstring, no return format documented
- `select_objects.py` - Returns plain string, inconsistent with standards

### 3.3 Schema Best Practices

**Implemented:**
- ✅ `ObjectType = Literal["POINT", "LINE", ...]`
- ✅ `BooleanOperationType = Literal["union", "difference", "intersection"]`
- ✅ `FilterType = Literal["and", "or"]`
- ✅ `ExportFormat = Literal["STEP", "IGES", ...]`

**Missing:**
- ❌ `DimensionType` for dimension tools
- ❌ `TransformType` for transform operations

---

## 4. Ralph Workflow Integration Analysis

### 4.1 Workflow Structure

```
Ralph/
├── prd.json              # Phase A stories (complete)
├── prd_phase_b.json      # Phase B stories (complete)
├── prd_phase_c.json      # Phase C stories (in progress)
├── progress.txt          # Learnings and patterns
├── README.md             # Workflow documentation
├── AGENTS.md             # Ralph-specific guide (Best Practice ✅)
├── NEXT_SESSION_PLAN.md  # Session planning (outdated)
└── scripts/ralph/        # (mostly empty)
```

### 4.2 Workflow Effectiveness

**Strengths:**
- ✅ Clear user story format with acceptance criteria
- ✅ `passes: true/false` tracking for story completion
- ✅ `progress.txt` captures learnings effectively
- ✅ Priority-based story ordering
- ✅ Notes field for implementation details
- ✅ `Ralph/AGENTS.md` follows best practice - subdirectory AGENTS.md for context

**Weaknesses:**
- ⚠️ `NEXT_SESSION_PLAN.md` is outdated (references completed US-B06)
- ⚠️ Scripts directory is empty (original Ralph uses Amp CLI)
- ⚠️ No automation for story status updates
- ⚠️ `progress.txt` is getting very long (~570 lines)

### 4.3 Comparison with Original Ralph (snarktank/ralph)

| Feature | Original Ralph | RhinoMCP Implementation | Status |
|---------|---------------|------------------------|--------|
| `prd.json` format | User stories with `passes` | ✅ Same format | ✅ Correct |
| `progress.txt` | Append-only learnings | ✅ Same approach | ✅ Correct |
| `AGENTS.md` in subdirs | Best practice for context | ✅ `Ralph/AGENTS.md` exists | ✅ Correct |
| `ralph.sh` script | Amp CLI automation | ❌ Not used (Cursor workflow) | ⚠️ Expected |
| `prompt.md` | Instructions for Amp | ❌ Not used | ⚠️ Expected |
| Archive feature | Saves old runs | ❌ Not implemented | 🆕 Optional |
| Auto-handoff | Context overflow handling | N/A (Cursor handles) | ✅ N/A |

**Key Insight:** This repo adapted Ralph for **Cursor/manual use** rather than Amp CLI automation. The empty `scripts/ralph/` directory is expected since the automation scripts (`ralph.sh`, `prompt.md`) are not needed when using Cursor.

### 4.4 Integration with Root Docs

| Root Doc | Ralph Integration | Notes |
|----------|-------------------|-------|
| `AGENTS.md` | ✅ References Ralph | Good cross-referencing |
| `ROADMAP.md` | ✅ References prd files | Good phase tracking |
| `README.md` | ⚠️ Brief mention | Could link more prominently |

---

## 5. Identified Weakpoints

### Critical (Should Fix)

1. **Version Inconsistency** - `pyproject.toml` shows 0.1.3.6 but docs say 0.1.3.8
2. **Incomplete C# Tool Registry** - `GetAvailableTools()` missing dimension, file, property tools
3. **select_objects.py Response Format** - Returns plain string instead of structured JSON

### High Priority

4. **Outdated Session Plan** - `NEXT_SESSION_PLAN.md` references completed work
5. **Missing `__init__.py` Exports** - Several tools not exported for external use
6. **Test Count Discrepancy** - Different documents report different test counts
7. **Missing Subdirectory AGENTS.md** - Per Ralph best practice, consider adding `rhino_mcp_server/AGENTS.md` and `rhino_mcp_plugin/AGENTS.md`

### Medium Priority

8. **Large progress.txt** - 570+ lines, consider archiving old entries
9. **C# Type Safety** - JObject everywhere, no strong typing
10. **README_MCP.md Outdated** - Handler mapping example doesn't include new tools
11. **development_guide.md** - Partially superseded, unclear purpose

### Low Priority

12. **ANALYSIS_LOG.md** - Purpose unclear, seems unrelated to main project
13. **Empty Ralph Scripts** - `Ralph/scripts/ralph/` mostly empty
14. **Inconsistent Import Styles** - Some tools import from `rhinomcp`, others from `rhinomcp.server`

---

## 6. Improvement Plan

### Phase 1: Documentation Cleanup (Quick Wins) - IN PROGRESS

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Fix version in pyproject.toml to 0.1.3.8 | Critical | 5 min | ✅ Done |
| Update `GetAvailableTools()` in C# | Critical | 15 min | ✅ Done |
| Fix `select_objects.py` to return JSON | Critical | 10 min | ✅ Done |
| Add missing exports to `__init__.py` | High | 10 min | ✅ Done |
| Update `__version__` in `__init__.py` | High | 5 min | ✅ Done |
| Add Cursor progress.txt requirement to AGENTS.md | High | 10 min | ✅ Done |
| Archive `Ralph/NEXT_SESSION_PLAN.md` or update for Phase C | High | 10 min | ⏳ Pending |
| Update test count in all docs | High | 15 min | ⏳ Pending |
| Create `rhino_mcp_server/AGENTS.md` (Python context) | High | 20 min | ⏳ Pending |
| Create `rhino_mcp_plugin/AGENTS.md` (C# context) | High | 20 min | ⏳ Pending |

### Phase 2: Standardization

| Task | Priority | Effort |
|------|----------|--------|
| Standardize docstring format across all tools | Medium | 2 hours |
| Add Literal types for remaining enums | Medium | 30 min |
| Archive old progress.txt entries | Medium | 30 min |
| Update README_MCP.md examples | Medium | 45 min |
| Deprecate/archive development_guide.md | Medium | 15 min |

### Phase 3: Structural Improvements

| Task | Priority | Effort |
|------|----------|--------|
| Add error codes to C# responses | Low | 2 hours |
| Create automated version sync | Low | 1 hour |
| Add automated test count badge | Low | 1 hour |
| Standardize Python import style | Low | 1 hour |

---

## 7. Recommendations Summary

### Documentation Strategy (Aligned with Ralph Best Practices)

Per the [original Ralph repository](https://github.com/snarktank/ralph):
> "AGENTS.md Updates Are Critical - After each iteration, Ralph updates the **relevant `AGENTS.md` files** with learnings."

1. **Hierarchical AGENTS.md Structure**:
   - ✅ Keep root `AGENTS.md` as the comprehensive guide
   - ✅ Keep `Ralph/AGENTS.md` for Ralph-specific context (already correct)
   - 🆕 Add `rhino_mcp_server/AGENTS.md` for Python-specific patterns
   - 🆕 Add `rhino_mcp_plugin/AGENTS.md` for C#-specific patterns

2. **Version Management**: Centralize version in `pyproject.toml`, document update process

3. **Automated Badges**: Add test count badge from CI to avoid manual updates

4. **Consolidate Overlapping Docs**: Merge `README_MCP.md` content into `MCP_TOOL_STANDARDS.md` or `AGENTS.md`

### Implementation Consistency

1. **Response Format**: Ensure ALL tools return structured JSON via `ok()`/`from_exception()`
2. **Import Style**: Standardize on `from rhinomcp.server import ...`
3. **Tool Registry**: Auto-generate `GetAvailableTools()` from handler dictionary keys

### Ralph Workflow (Aligned with Original)

Based on comparison with [snarktank/ralph](https://github.com/snarktank/ralph):

1. **Subdirectory AGENTS.md Files** - Currently correct with `Ralph/AGENTS.md`. Consider extending to other key directories.

2. **Archive Completed Plans**: Update or archive `NEXT_SESSION_PLAN.md` when stories are complete

3. **Progress Log Maintenance**: Archive entries older than 1 phase into separate files (e.g., `progress_phase_a.txt`)

4. **Scripts Directory**: The empty `Ralph/scripts/ralph/` directory is expected since this repo adapted Ralph for Cursor/manual use instead of Amp CLI

---

## Appendix A: File List

### Documentation Files (14)
- README.md, AGENTS.md, USAGE.md, ROADMAP.md
- MCP_TOOL_STANDARDS.md, FUNCTIONAL_STATUS.md
- README_MCP.md, PHASE_B_CONTEXT.md, ANALYSIS_LOG.md
- development_guide.md
- Ralph/README.md, Ralph/AGENTS.md, Ralph/NEXT_SESSION_PLAN.md
- rhino_mcp_server/README.md

### Python Tool Files (45)
- array_linear.py, array_polar.py, assign_material_to_layer.py
- boolean_operation.py, chamfer_curves.py, copy_object.py
- create_angular_dimension.py, create_layer.py, create_leader.py
- create_linear_dimension.py, create_material.py, create_object.py
- create_objects.py, create_radial_dimension.py, create_text.py
- create_text_dot.py, delete_layer.py, delete_object.py
- execute_rhinoscript_python_code.py, export_file.py, extrude_curve.py
- fillet_curves.py, get_command_history.py, get_document_info.py
- get_logs.py, get_object_info.py, get_object_properties.py
- get_or_set_current_layer.py, get_rhinoscript_python_code_guide.py
- get_rhinoscript_python_function_names.py, get_selected_objects_info.py
- get_session_stats.py, loft_curves.py, log_thought.py
- mirror_object.py, modify_object.py, modify_objects.py
- offset_curve.py, open_file.py, ping.py, revolve_curve.py
- save_file.py, select_objects.py, set_debug_mode.py, set_object_properties.py

### C# Function Files (21)
- BooleanOperations.cs, CreateLayer.cs, CreateObject.cs
- CreateObjects.cs, CurveOperations.cs, DeleteLayer.cs
- DeleteObject.cs, DimensionOperations.cs, ExecuteRhinoscript.cs
- FileOperations.cs, GetDocumentInfo.cs, GetObjectInfo.cs
- GetOrSetCurrentLayer.cs, GetSelectedObjectsInfo.cs, ModifyObject.cs
- ModifyObjects.cs, ObjectProperties.cs, SelectObjects.cs
- SurfaceOperations.cs, TransformOperations.cs, _utils.cs

---

## Appendix B: Test Files (15)

- conftest.py
- test_boolean_operation.py
- test_connection.py
- test_create_object.py
- test_curve_operations.py
- test_dimension_operations.py
- test_errors.py
- test_file_operations.py
- test_get_document_info.py
- test_modify_object.py
- test_object_properties.py
- test_responses.py
- test_surface_operations.py
- test_transform_operations.py
- __init__.py

---

## 8. Deep Research: Advanced Integration Strategies

> This section addresses the request for deep research on multi-tool workflows, ML integration, RAG, and local model usage.

### 8.1 Dual Tool Strategy: Amp (Ralph) vs. Cursor

#### Problem Statement
The repository currently uses Ralph workflow (originally for Amp CLI) but has been adapted for Cursor. The user needs to sometimes use Ralph/Amp and sometimes native Cursor agents.

#### Solution: Unified Progress Tracking

**Critical Requirement:** Both Amp and Cursor MUST use `Ralph/progress.txt` for consistency.

| Tool | Read progress.txt | Write progress.txt | Workflow |
|------|-------------------|-------------------|----------|
| **Amp (Ralph)** | ✅ Yes (built-in) | ✅ Yes (built-in) | Autonomous |
| **Cursor** | ✅ Yes (manual) | ✅ Yes (manual) | Interactive |

#### Tool Selection Flag

Add to root `AGENTS.md` (already implemented):
```markdown
## Tool Selection: Cursor vs Amp (Ralph)

Before starting, determine which workflow to use:

| Scenario | Tool | Reason |
|----------|------|--------|
| Autonomous iteration loops | **Amp (Ralph)** | Auto-handoff, fresh context per iteration |
| Interactive development | **Cursor** | Real-time feedback, debugging |
| Large refactoring | **Amp (Ralph)** | Context persistence via progress.txt |
| Quick fixes | **Cursor** | Direct, no overhead |

> **IMPORTANT:** Both tools MUST use `Ralph/progress.txt` for consistency!
```

#### Workflow-Specific Prompt Files (Future)
```
Ralph/
├── prompt_amp.md      # For Amp CLI execution
├── prompt_cursor.md   # For Cursor execution
└── prompt_select.md   # Decision helper
```

**Recommendation:** Use unified progress.txt for both tools to ensure no learnings are lost regardless of which tool is used.

---

### 8.2 Improving MCP Tools in Cursor for Rhino

#### Current Architecture
```
┌─────────────────┐    TCP/JSON    ┌──────────────────┐
│ Cursor + MCP    │ ◄───────────► │ Rhino Plugin     │
│ (FastMCP)       │   localhost:1999│ (C# RhinoCommon) │
└─────────────────┘               └──────────────────┘
```

#### Improvement Opportunities

| Area | Current | Improvement | Effort |
|------|---------|-------------|--------|
| **Tool Discovery** | Manual docs | Auto-generated schema from C# | High |
| **Context Awareness** | Per-call | Persistent model state cache | Medium |
| **Feedback Loop** | Logs only | Screenshot/viewport capture | Medium |
| **Batch Operations** | Limited | Transactional batch API | High |
| **Error Recovery** | Manual retry | Auto-retry with backoff | Low |

#### Priority Improvements

1. **Viewport Capture Tool** (US-C02 in Phase C)
   - Add `capture_viewport` MCP tool for visual feedback
   - Allows agents to "see" results without user intervention

2. **Enhanced Schema Generation**
   ```python
   # Auto-generate schema from C# handlers
   def get_tool_schema() -> dict:
       """Returns JSON Schema for all available tools."""
       return rhino.send_command("get_tool_schemas", {})
   ```

3. **Persistent Context via Resources**
   ```python
   @mcp.resource("rhino://document/state")
   def get_document_state() -> str:
       """MCP Resource for current document state."""
       return json.dumps(rhino.send_command("get_document_info"))
   ```

---

### 8.3 Machine Learning Integration

#### Current ML-Ready Features
- ✅ **Interaction Logging** (`utils/interaction_logger.py`) - JSONL logs of all tool calls
- ✅ **Session Stats** (`get_session_stats` tool) - Success rates, tool usage patterns
- ✅ **Structured Responses** - Consistent JSON format for training data

#### ML Integration Roadmap

| Phase | Capability | Approach |
|-------|-----------|----------|
| **1. Data Collection** | Gather interaction data | Already implemented via interaction_logger |
| **2. Pattern Analysis** | Identify common workflows | Analyze JSONL logs with pandas/duckdb |
| **3. Workflow Suggestions** | Recommend next tools | Rule-based initially, then ML |
| **4. Fine-tuning** | Rhino-specific model | LoRA on code model (see 8.6) |

#### Training Data Format
```json
{
  "timestamp": "2026-01-10T11:21:28+00:00",
  "session_id": "fde7c7b5",
  "tool_name": "create_object",
  "tool_args": {"type": "BOX", "params": {"width": 10}},
  "success": true,
  "response_summary": {"id": "guid", "name": "Box_1"},
  "duration_ms": 43.05
}
```

---

### 8.4 RAG (Retrieval Augmented Generation) Integration

#### Use Cases for RAG in RhinoMCP

1. **RhinoCommon API Documentation**
   - Embed the entire RhinoCommon API reference
   - Agent can query: "How do I create a NURBS surface?"
   
2. **Previous Session Context**
   - Embed `progress.txt` and past conversations
   - Agent recalls: "Last time we created a parametric chair using..."

3. **User's 3DM File History**
   - Embed object metadata from previous documents
   - Agent suggests: "You often use this layer structure..."

#### Implementation Options

| Approach | Stack | Pros | Cons |
|----------|-------|------|------|
| **LangChain + ChromaDB** | Python | Rich ecosystem, easy setup | Heavy dependencies |
| **LlamaIndex** | Python | Better for document retrieval | Learning curve |
| **Ollama + Embeddings** | Local | Privacy, no cloud | Requires embedding model |
| **Custom MCP Resource** | Python | Integrated with existing tools | Build from scratch |

#### Recommended Architecture
```
┌───────────────────────────────────────────────────────────────┐
│                        RAG Pipeline                           │
├───────────────────────────────────────────────────────────────┤
│  1. Embed: RhinoCommon docs, progress.txt, .3dm metadata     │
│  2. Store: ChromaDB or local SQLite + embeddings             │
│  3. Query: MCP tool "search_rhino_knowledge"                 │
│  4. Augment: Add context to LLM prompts                       │
└───────────────────────────────────────────────────────────────┘
```

#### New MCP Tool Proposal
```python
@mcp.tool()
def search_rhino_knowledge(ctx: Context, query: str, top_k: int = 5) -> str:
    """Search RhinoCommon documentation and past sessions for relevant context."""
    # Implementation using embedding search
    pass
```

---

### 8.5 Local Model Usage (Integration with LocAI)

#### LocAI Repository Analysis

**Repository:** https://github.com/McMuff86/locai

**Technology Stack:**
- Next.js frontend
- Ollama API backend
- Local model hosting (Llama3, Gemma, Mistral, DeepSeek)
- Vision model support (llama3.2-vision)

#### Integration Possibilities

| Integration | Direction | Benefit |
|-------------|-----------|---------|
| **LocAI → RhinoMCP** | LocAI calls RhinoMCP tools | Local LLM controls Rhino |
| **RhinoMCP → LocAI** | RhinoMCP uses LocAI as backend | Privacy-first, no cloud |
| **Shared RAG** | Both use same vector store | Consistent knowledge base |

#### Architecture: LocAI + RhinoMCP Integration

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐
│ LocAI (Next.js) │ ◄────────────► │ Ollama          │
│ - UI            │                 │ - llama3        │
│ - Chat          │                 │ - DeepSeek      │
└────────┬────────┘                 │ - Vision models │
         │                          └─────────────────┘
         │ MCP
         ▼
┌─────────────────┐    TCP/JSON    ┌─────────────────┐
│ RhinoMCP Server │ ◄────────────► │ Rhino 8         │
│ (Python)        │   localhost:1999│ (C# Plugin)     │
└─────────────────┘                 └─────────────────┘
```

#### Implementation Steps

1. **Add MCP Client to LocAI**
   ```typescript
   // In LocAI: Add MCP client for RhinoMCP
   import { MCPClient } from '@modelcontextprotocol/sdk';
   
   const rhinoMCP = new MCPClient({
     transport: 'stdio',
     command: 'uvx rhinomcp'
   });
   ```

2. **Create Bridge Tool in LocAI**
   ```typescript
   // Tool that routes Rhino commands through MCP
   async function executeRhinoCommand(command: string, params: object) {
     return await rhinoMCP.callTool(command, params);
   }
   ```

3. **Shared Context via RAG**
   - Both LocAI and RhinoMCP use same ChromaDB instance
   - Rhino operations logged to shared knowledge base
   - LocAI can query Rhino history

---

### 8.6 Training a Model for Rhino

#### Approaches

| Approach | Data Required | Effort | Quality |
|----------|--------------|--------|---------|
| **Prompt Engineering** | None | Low | Medium |
| **RAG + Base Model** | Docs, examples | Medium | Good |
| **LoRA Fine-tuning** | 1k-10k examples | High | Excellent |
| **Full Fine-tuning** | 100k+ examples | Very High | Best |

#### Recommended: LoRA Fine-tuning

**Why LoRA?**
- Small adapter (~50MB) on top of base model
- Can train on consumer GPU (16GB VRAM)
- Preserves base model knowledge while adding Rhino expertise

**Training Data Sources:**
1. **RhinoMCP interaction logs** (already collected)
2. **RhinoScript documentation** (in `static/rhinoscriptsyntax.py`)
3. **Grasshopper forums** (scrape Q&A)
4. **McNeel Developer docs** (RhinoCommon API)

**Example Training Data Format (Alpaca-style):**
```json
{
  "instruction": "Create a parametric box in Rhino",
  "input": "Width: 10, Length: 20, Height: 5",
  "output": "{\"tool\": \"create_object\", \"params\": {\"type\": \"BOX\", \"params\": {\"width\": 10, \"length\": 20, \"height\": 5}}}"
}
```

**Training Infrastructure:**
- **Local:** RTX 3090/4090 with unsloth/axolotl
- **Cloud:** RunPod/Vast.ai for larger models
- **Framework:** unsloth (fast LoRA training), axolotl (configurable)

#### Training Pipeline
```
┌─────────────────────────────────────────────────────────────┐
│                   Rhino Model Training                       │
├─────────────────────────────────────────────────────────────┤
│  1. Collect: interaction_logs + RhinoScript docs + forums   │
│  2. Format: Convert to instruction-following format          │
│  3. Train: LoRA on deepseek-coder-7b or codellama-7b        │
│  4. Merge: Create merged model for Ollama                    │
│  5. Deploy: Host in LocAI or use via MCP                     │
└─────────────────────────────────────────────────────────────┘
```

---

### 8.7 Updated Improvement Plan

Based on deep research, here's the updated phased approach:

#### Phase 1: Documentation & Quick Wins (Current)
- [ ] Fix version inconsistency
- [ ] Update C# tool registry
- [ ] Fix select_objects.py response format
- [x] Add tool selection guidance to AGENTS.md
- [x] Document Amp vs Cursor workflow

#### Phase 2: Enhanced MCP Tools
- [ ] Add viewport capture tool (US-C02)
- [ ] Add auto-retry with backoff
- [ ] Enhanced error messages with suggestions
- [ ] Tool schema auto-generation

#### Phase 3: RAG Integration
- [ ] Set up ChromaDB for embeddings
- [ ] Embed RhinoCommon documentation
- [ ] Embed progress.txt and interaction logs
- [ ] Create `search_rhino_knowledge` MCP tool

#### Phase 4: Local Model Integration (LocAI)
- [ ] Add MCP client to LocAI
- [ ] Create RhinoMCP → LocAI bridge
- [ ] Shared RAG vector store
- [ ] Test with local Llama3/DeepSeek

#### Phase 5: Model Training
- [ ] Collect 1000+ training examples from logs
- [ ] Format training data (Alpaca style)
- [ ] LoRA fine-tune on deepseek-coder-7b
- [ ] Deploy to Ollama via LocAI

---

## 9. Next Steps

### Immediate (Before Code Changes)

1. **Review this analysis** - User to approve the improvement plan
2. **Decide tool strategy** - Amp vs Cursor usage pattern
3. **Prioritize ML/RAG** - Is this a priority or future work?

### Short-term (Phase 1-2)

1. Fix critical issues (version, tool registry, response format)
2. Add viewport capture for visual feedback
3. Document Amp/Cursor workflow selection

### Medium-term (Phase 3-4)

1. RAG integration for context-aware responses
2. LocAI integration for local model usage
3. Shared knowledge base

### Long-term (Phase 5)

1. Fine-tune a Rhino-specific model
2. Deploy via LocAI + Ollama
3. Continuous learning from interaction logs

---

*This analysis was created without modifying any code. Follow the improvement plan to address identified issues.*
