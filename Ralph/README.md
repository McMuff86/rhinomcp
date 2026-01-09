# Ralph - Structured Development Workflow for RhinoMCP

Ralph is a structured workflow system for systematic, iterative development. Instead of tackling large features at once, Ralph breaks work into small user stories that fit within a single context window.

## Workflow

### 1. Create a PRD (Product Requirements Document)

Define your feature as a set of small, atomic user stories in `prd.json`:

```json
{
  "project": "RhinoMCP",
  "branchName": "feature/my-feature",
  "description": "Short description of the feature",
  "userStories": [
    {
      "id": "US-001",
      "title": "Add X to Y",
      "description": "As a developer, I need X so that Y.",
      "acceptanceCriteria": [
        "Criterion 1",
        "Criterion 2",
        "Tests pass"
      ],
      "priority": 1,
      "passes": false,
      "notes": ""
    }
  ]
}
```

### 2. Work Through Stories One at a Time

For each story:

1. **Read** `progress.txt` first (patterns, gotchas, context)
2. **Select** the highest priority story where `passes: false`
3. **Implement** in small, safe steps
4. **Test** manually (start Rhino plugin + MCP server)
5. **Commit** with clear message: `feat/story/US-001: description`
6. **Update** `progress.txt` with learnings
7. **Mark** story as `passes: true` in `prd.json`
8. **Repeat** until all stories complete

### 3. Document Learnings

After each story, add learnings to `progress.txt`:
- New patterns discovered
- Gotchas and pitfalls
- Useful context for future work

## Key Files

| File | Purpose |
|------|---------|
| `prd.json` | User stories with `passes` status (the task list) |
| `prd.json.example` | Example PRD format for reference |
| `progress.txt` | Append-only learnings for future iterations |
| `scripts/ralph/prompt.md` | Instructions for AI agents (Cursor, Claude, etc.) |
| `AGENTS.md` | Agent-specific documentation |

## Critical Concepts

### Small Tasks = Better Results

Each story should be small enough to complete in one context window. This avoids the "dumb zone" where LLMs produce poor code due to context overflow.

**Right-sized stories:**
- Add a new MCP tool
- Fix a specific bug
- Add a parameter to existing function
- Update documentation

**Too big (split these):**
- "Refactor the entire server"
- "Add authentication system"
- "Redesign the API"

### Learnings Persist via progress.txt

The `progress.txt` file is the memory between sessions:
- Codebase patterns (SACRED - always follow)
- Discovered gotchas
- Useful context

### AGENTS.md Updates Are Critical

After iterations, update relevant `AGENTS.md` files with:
- Patterns discovered
- Gotchas ("don't forget to X when doing Y")
- Useful context ("the settings are in component X")

## RhinoMCP-Specific Commands

```bash
# Start Rhino plugin (in Rhino command line)
mcpstart

# Start MCP server
cd rhino_mcp_server
uv run python -m rhinomcp

# Run dev tests
uv run python dev/dev_test.py

# Build Python package
uv build
```

## Example: Adding a New MCP Tool

**Story:** "Add ping tool for health checks"

1. Create `rhino_mcp_server/src/rhinomcp/tools/ping.py`
2. Register in `server.py`
3. Test manually: call ping from Cursor/Claude
4. Commit: `feat/story/US-001: add ping tool for health checks`
5. Update `progress.txt` with learnings
6. Mark story `passes: true`

## Debugging

```bash
# Check story status
cat Ralph/prd.json | jq '.userStories[] | {id, title, passes}'

# See learnings
cat Ralph/progress.txt

# Check git history
git log --oneline -10
```

## References

- [Geoffrey Huntley's Ralph article](https://ghuntley.com/ralph/)
- [RhinoMCP AGENTS.md](../AGENTS.md)
- [MCP Tool Standards](../MCP_TOOL_STANDARDS.md)
