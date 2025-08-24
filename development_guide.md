# RhinoMCP Development Guide

## Introduction
Dieses Dokument ist der zentrale Hub für die Entwicklung von RhinoMCP. Es beschreibt den aktuellen Stand, Schwächen, Roadmap und Best Practices. Ziel: Ein professionelles Tool für AI-gestützte Rhino-Automatisierung, inkl. Grasshopper und Rhino.Common Integration.

**Version:** 0.1 (Initial Draft)
**Letztes Update:** [Datum einfügen]

## Workspace Overview

- **rhino_mcp_plugin**: C#-basierter Rhino-Plugin für Commands und Socket-Server.
- **rhino_mcp_server**: Python-MCP-Server mit Tools und Rhinoscript-Support.
- **assets**: Doku-Materialien.
- **Weitere**: Test-Modelle (.3dm), README.md.

## Architecture

- **High-Level**: MCP-Server (Python, FastMCP) <-> TCP-Socket <-> Rhino-Plugin (C#, Rhino.Common).
- **Key Components**:
  - Tools in src/rhinomcp/tools (z.B. create_object.py).
  - Rhinoscriptsyntax.py für Scripting.
- **Data Flow**: JSON-Commands von MCP zu Rhino, Responses zurück.

## Identified Weaknesses

1. Begrenzte Geometrie: Nur Primitives – erweitern auf NURBS (NurbsSurface, Brep, SubD), Meshes, Annotations.
2. Keine Grasshopper-Integration: Tools für GH-Definitionen, Param-Evaluation, Baking.
3. Uneinheitliche Rückgabe-Formate: Strings vs Dicts; Standardisiere auf `{success, message, ...}`.
4. Error-Handling inkonsistent: Fehlende Detail-Codes, keine Ursachenketten.
5. Performance/Batching: Mehr Batch-APIs; kein Pagination/Slicing bei großen Abfragen.
6. Stabilität/Verbindung: Reconnect-Strategie, Timeouts, Telemetrie.
7. Schema/Doku: Fehlende Schemas pro Tool; auto-generierte Doku fehlt.
8. Security: Input-Validation, Limits, optional Auth.
9. Testing/CI: Unit-/Integration-Tests, Smoke-Tests mit Rhino Headless, CI.

## Roadmap

### Phase 1: Stabilisieren

- Standardisiere Rückgabe `{success, message, data}` und Fehlerpfad (Python utils).
- Vereinheitliche Logs und Exceptions; bessere Fehlermeldungen im C#-Handler.
- Implementiere erste Tests (Serializers, einfache Tools) und Smoke-Test-Workflow.
- Doku: README_MCP, Tool-Standards, Entwicklungsleitfaden (dieses File).

### Phase 2: Erweitern

- Grasshopper-Tools (z.B. evaluate_gh, set_slider, bake_geometry).
- Mehr Geo-Typen (Brep, SubD, Mesh-IO, Leaders/Texts/Dimensions).
- Selektion/Query-APIs mit Filtern, Pagination, Layer/Group-Scopes.
- Batch-Create/Modify/Query und robuste Transaktion/Undo-Gruppen.

### Phase 3: Polish

- CI/CD mit GitHub Actions (Build, Tests, Paketierung, Release Notes).
- Vollständige Doku + OpenAPI-ähnliche Tool-Schemata + Beispiele.
- Telemetrie/Tracing (optional), Limits und Auth (konfigurierbar).

## Best Practices

- **Coding**: RhinoCommon sauber kapseln, UI-Thread beachten, Undo-Gruppen nutzen.
- **MCP-Tools**: Eindeutige Parameter mit Typen; Rückgabe-Standard `{success, message, ...}`.
- **Fehler**: Früh validieren, präzise Fehlermeldungen, nie Exceptions verschlucken.
- **Performance**: Batchen ab N>10, große Daten streamen/paginieren.
- **Doku**: README_MCP pflegen; Beispiele und Schemata aktuell halten.
- **Git**: Feature-Branches, PRs, Code-Reviews, konventionelle Commits.
- **AI-Freundlich**: Konsistente Schemas, deterministische Antworten, Beispiele.

## Debugging MCP Tools

- **Common Errors**: 'Invalid object type' - Rebuild and reload plugin. 'Unexpected token' in scripts - Flatten code, reduce length.
- **Build Steps**: Clean/Rebuild in VS, yak build, reinstall in Rhino.
- **Script Limits**: IronPython max ~4k lines; split calls.
- **Testing**: Use simple prints, attach VS debugger to rhino.exe.
- **Logs**: Check Rhino command-line, add print() in scripts.

## Changelog

- 0.1: Initial Creation.
- 0.2: Added create_leader MCP tool.
