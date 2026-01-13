# "Land the Plane" - Session Cleanup Routine Plan

> **Status:** Draft Plan - Not yet implemented
> **Created:** 2026-01-13
> **Purpose:** Structured cleanup routine for ending development sessions when context window is full

---

## 🎯 Zielsetzung

Eine strukturierte Routine für Session-Ende, die:
- ✅ Sauber dokumentiert (Learnings extrahiert)
- ✅ "Mess" aufräumt (temporäre Dateien, unfertige Code-Änderungen)
- ✅ Wichtige Dateien schützt (keine Löschung von produktivem Code)
- ✅ Repo brauchbar hält (keine Breaking Changes ohne Dokumentation)
- ✅ Kontext für nächste Session vorbereitet

---

## 📋 Bestehende Cleanup-Mechanismen

### Bereits vorhanden:

1. **Scripts Cleanup** (`scripts/cleanup_temp.py`)
   - Automatisches Cleanup von `scripts/temp/` nach 7 Tagen
   - Manuelles Cleanup möglich (`--days`, `--all`, `--dry-run`)

2. **Dokumentation Hygiene** (AGENTS.md)
   - Remove solved problems from `progress.txt`
   - Archive valuable learnings to `docs/archive/solved_issues/`
   - Keep progress.txt brief (5-10 lines per session, max ~100-150 lines)

3. **Session Logging** (Ralph/progress.txt)
   - Brief session logs (5-10 lines)
   - Archive completed phases to `progress_archive_phase_X.txt`

4. **Learning Documentation System**
   - Quick learnings → `Ralph/progress.txt`
   - Complex topics → `docs/learnings/*.md`
   - Solved issues → `docs/archive/solved_issues/`

### Inspiriert von Beads (steveyegge/beads):

5. **Compaction / Semantic Memory Decay** (Zukünftig)
   - Alte geschlossene Sessions semantisch zusammenfassen
   - Kern-Informationen behalten, Details reduzieren
   - Ähnlich wie menschliche Erinnerung: Episodisch → Semantisch

6. **Git-backed Persistence**
   - Alle Änderungen in Git versionieren
   - Explizites Commit als Teil des Cleanups
   - Git-History als Backup und Audit-Trail

7. **Structured Session Protocol**
   - Klare Phasen: Start → Work → Cleanup → Sync
   - Explizite Status-Updates während der Session
   - Vorbereitung für nächste Session

---

## 🛡️ Sicherheitsregeln (SACRED - Nie verletzen!)

### ❌ NIEMALS löschen/ändern:

1. **Produktiver Code**
   - `rhino_mcp_server/src/rhinomcp/` - Core MCP server code
   - `rhino_mcp_plugin/Functions/` - C# command handlers
   - `rhino_mcp_server/tests/` - Test suite
   - `docs/USAGE.md`, `docs/ROADMAP.md` - Core documentation

2. **Konfigurationsdateien**
   - `pyproject.toml`, `rhinomcp.csproj` - Build configs
   - `.github/workflows/` - CI/CD pipelines
   - `manifest.yml` - Plugin manifest

3. **Dokumentation (wenn aktuell)**
   - `AGENTS.md` - Agent guide (nur aktualisieren, nie löschen)
   - `README.md`, `README_MCP.md` - Project docs
   - `docs/learnings/*.md` - Learning files (nur archivieren wenn veraltet)

4. **Versionierte Daten**
   - `testdata/*.3dm` - Test files
   - `demo_chats/*.txt` - Demo conversations
   - `learning/*.json` - Training data

### ✅ DARF aufgeräumt werden:

1. **Temporäre Scripts**
   - `scripts/temp/*.py` - Älter als 7 Tage (automatisch)
   - `rhino_mcp_server/dev/*.py` - Nur wenn explizit temporär markiert

2. **Dokumentation (wenn veraltet)**
   - Gelöste Probleme aus `progress.txt` entfernen
   - Alte Session-Logs archivieren (wenn >100-150 Zeilen)
   - Veraltete Learning-Files archivieren (nur wenn komplett ersetzt)

3. **Build-Artefakte**
   - `rhino_mcp_plugin/bin/`, `rhino_mcp_plugin/obj/` - Build outputs
   - `*.pyc`, `__pycache__/` - Python cache (sollte in .gitignore sein)

4. **Logs**
   - `rhino_mcp_server/logs/*.jsonl` - Älter als 30 Tage (optional)

---

## 📝 "Land the Plane" Checkliste

### Phase 1: Dokumentation abschließen

- [ ] **Session-Log aktualisieren** (`Ralph/progress.txt`)
  - Brief summary (5-10 lines)
  - Key achievements
  - Quick learnings (wenn nicht komplex)
  - Status: ✅ Complete / ⚠️ Partial / ❌ Failed

- [ ] **Learnings extrahieren**
  - Quick learnings → `Ralph/progress.txt` (5-10 lines)
  - Complex topics → `docs/learnings/*.md` (nur wenn wirklich komplex)
  - Solved issues → `docs/archive/solved_issues/ISSUE_NAME.md`

- [ ] **Gelöste Probleme archivieren**
  - Aus `progress.txt` entfernen
  - Nach `docs/archive/solved_issues/` verschieben
  - Format: Problem, Failed attempts, Solution, Learnings

- [ ] **Progress.txt aufräumen**
  - Alte Sessions archivieren (wenn >100-150 Zeilen)
  - Nach `progress_archive_phase_X.txt` verschieben
  - Aktive Datei kurz halten (max ~100-150 Zeilen)

- [ ] **AGENTS.md aktualisieren** (wenn nötig)
  - Neue Tools hinzufügen
  - Test-Count aktualisieren
  - Status-Updates (Phase, Version)

### Phase 2: Code aufräumen

- [ ] **Unfertige Änderungen**
  - Unfertige Features: Kommentieren mit `# TODO: Complete in next session`
  - Breaking Changes: Revert oder dokumentieren in `FUTURE_ISSUES.md`
  - Test-Failures: Dokumentieren oder fixen

- [ ] **Temporäre Scripts organisieren**
  - Nützliche Scripts → `scripts/examples/` verschieben
  - Temporäre Scripts → `scripts/temp/` belassen
  - Cleanup ausführen: `python scripts/cleanup_temp.py --dry-run` (prüfen)

- [ ] **Build-Artefakte** (optional)
  - `dotnet clean` im Plugin-Verzeichnis
  - Python cache löschen (wenn nötig)

### Phase 3: Tests & Status prüfen

- [ ] **Tests laufen lassen**
  - `uv run pytest tests/ -v` - Mindestens einmal pro Session
  - Test-Failures dokumentieren oder fixen

- [ ] **Status-Dokumentation aktualisieren**
  - `docs/FUNCTIONAL_STATUS.md` - Wenn neue Issues gefunden
  - `FUTURE_ISSUES.md` - Wenn neue Issues gefunden
  - `Ralph/prd_phase_X.json` - Story-Status aktualisieren

### Phase 4: Git State & Sync

- [ ] **Git State aufräumen** (Inspiriert von Beads)
  - Stashes prüfen: `git stash list` - Alte Stashes löschen oder anwenden
  - Alte Branches: `git branch` - Nicht mehr benötigte Branches löschen
  - Uncommitted Changes: Entscheiden (commit, stash, oder revert)

- [ ] **Git Sync** (Kritisch für Persistenz!)
  - Alle Änderungen committen: `git add .` + `git commit -m "Session: [Summary]"`
  - Oder: Explizites Staging für wichtige Änderungen
  - Git-History als Backup und Audit-Trail nutzen

- [ ] **Remote Sync** (optional, aber empfohlen)
  - `git push` - Änderungen zum Remote pushen
  - Oder: Lokales Backup erstellen

### Phase 5: Nächste Session vorbereiten

- [ ] **Nächste Tasks identifizieren**
  - `Ralph/prd_phase_X.json` - Höchste Priorität mit `passes: false`
  - `FUTURE_ISSUES.md` - Offene Issues prüfen

- [ ] **Kontext für nächste Session**
  - `Ralph/progress.txt` - Aktueller Status klar dokumentiert
  - `AGENTS.md` - Aktuell und vollständig
  - Wichtige Learnings referenziert
  - Session-Summary für schnellen Einstieg

---

## 🔄 Automatisierung (Zukünftig)

### Mögliche Scripts:

1. **`scripts/land_the_plane.py`**
   - Interaktive Checkliste durchgehen
   - Automatische Prüfungen (Tests, Build, etc.)
   - Dry-run Modus für Sicherheit
   - Git-State-Check (stashes, branches, uncommitted changes)
   - Automatisches Git-Commit mit Session-Summary

2. **Compaction Script** (Inspiriert von Beads `bd compact`)
   - Alte Sessions semantisch zusammenfassen (LLM-basiert)
   - Progress.txt automatisch kompaktieren wenn >150 Zeilen
   - Archivierte Sessions zusammenfassen
   - Kern-Informationen behalten, Details reduzieren

3. **Pre-Commit Hook** (optional)
   - Progress.txt Größe prüfen
   - Test-Suite laufen lassen
   - Temporäre Scripts warnen
   - Git-State-Check (stashes, uncommitted changes)

4. **GitHub Action** (optional)
   - Automatisches Cleanup von alten Logs
   - Archivierung von alten Sessions
   - Compaction von alten Sessions

---

## 📊 Cleanup-Kategorien

### 1. Dokumentation Cleanup

**Was:** Session-Logs, gelöste Probleme, veraltete Learnings

**Regeln:**
- Progress.txt: Max ~100-150 Zeilen, dann archivieren
- Gelöste Probleme: Nach `docs/archive/solved_issues/` verschieben
- Veraltete Learnings: Archivieren wenn komplett ersetzt

**Sicherheit:**
- ✅ Archivieren statt löschen
- ✅ Backup vor größeren Änderungen
- ❌ Nie produktive Dokumentation löschen

### 2. Code Cleanup

**Was:** Temporäre Scripts, unfertige Features, Build-Artefakte

**Regeln:**
- Temporäre Scripts: `scripts/temp/` → Auto-cleanup nach 7 Tagen
- Unfertige Features: Kommentieren oder dokumentieren
- Build-Artefakte: Optional, sollte in .gitignore sein

**Sicherheit:**
- ✅ Nur temporäre Scripts löschen
- ✅ Nützliche Scripts nach `scripts/examples/` verschieben
- ❌ Nie produktiven Code löschen

### 3. Test & Status Cleanup

**Was:** Test-Failures, Status-Updates, Issue-Tracking

**Regeln:**
- Tests: Mindestens einmal pro Session laufen lassen
- Failures: Dokumentieren oder fixen
- Status: `FUNCTIONAL_STATUS.md`, `FUTURE_ISSUES.md` aktualisieren

**Sicherheit:**
- ✅ Tests nie löschen
- ✅ Failures dokumentieren
- ❌ Nie Test-Suite beschädigen

### 4. Git State Cleanup (Inspiriert von Beads)

**Was:** Stashes, alte Branches, uncommitted Changes

**Regeln:**
- Stashes: Prüfen, anwenden oder löschen
- Branches: Nicht mehr benötigte löschen
- Uncommitted Changes: Committen, stashen oder revert

**Sicherheit:**
- ✅ Git-History als Backup nutzen
- ✅ Wichtige Änderungen immer committen
- ❌ Nie Force-Push ohne Backup
- ❌ Nie uncommitted wichtige Änderungen verlieren

### 5. Compaction / Memory Decay (Zukünftig)

**Was:** Alte Sessions semantisch zusammenfassen

**Regeln:**
- Alte geschlossene Sessions zusammenfassen
- Kern-Informationen behalten, Details reduzieren
- Ähnlich wie menschliche Erinnerung: Episodisch → Semantisch

**Sicherheit:**
- ✅ Archivieren statt löschen
- ✅ Kern-Informationen immer behalten
- ❌ Nie wichtige Learnings verlieren

---

## 🎓 Best Practices

### DO:

1. **Dokumentation zuerst**
   - Learnings extrahieren BEVOR Code aufgeräumt wird
   - Session-Log aktualisieren während noch Kontext vorhanden ist

2. **Sicherheit zuerst**
   - Dry-run bei Cleanup-Scripts
   - Backup vor größeren Änderungen
   - Archivieren statt löschen

3. **Konsistenz**
   - Gleiche Struktur für alle Sessions
   - Gleiche Dokumentationsformate
   - Gleiche Archivierungs-Patterns

4. **Klarheit**
   - Status klar dokumentieren (✅/⚠️/❌)
   - Nächste Steps identifizieren
   - Kontext für nächste Session vorbereiten

### DON'T:

1. **Nie produktiven Code löschen**
   - Auch nicht "temporäre" Fixes die funktionieren
   - Auch nicht "experimentelle" Features die nützlich sind

2. **Nie Dokumentation löschen ohne Backup**
   - Archivieren statt löschen
   - Git-History als Backup nutzen

3. **Nie Breaking Changes ohne Dokumentation**
   - In `FUTURE_ISSUES.md` dokumentieren
   - Oder revert wenn nicht fertig

4. **Nie Tests überspringen**
   - Mindestens einmal pro Session
   - Failures dokumentieren oder fixen

---

## 🔍 Prüf-Fragen vor Session-Ende

1. **Dokumentation:**
   - [ ] Sind alle Learnings extrahiert?
   - [ ] Ist progress.txt aktuell und kurz?
   - [ ] Sind gelöste Probleme archiviert?

2. **Code:**
   - [ ] Sind temporäre Scripts organisiert?
   - [ ] Sind unfertige Features dokumentiert?
   - [ ] Läuft die Test-Suite?

3. **Status:**
   - [ ] Ist AGENTS.md aktuell?
   - [ ] Sind neue Issues dokumentiert?
   - [ ] Ist nächste Session vorbereitet?

4. **Git & Persistence:**
   - [ ] Sind alle wichtigen Änderungen committed?
   - [ ] Sind Stashes und alte Branches aufgeräumt?
   - [ ] Ist Git-State sauber (oder dokumentiert)?

5. **Sicherheit:**
   - [ ] Wurden keine produktiven Dateien gelöscht?
   - [ ] Wurden Breaking Changes dokumentiert?
   - [ ] Ist Repo in brauchbarem Zustand?

---

## 📚 Referenzen

### Interne Dokumentation:
- **AGENTS.md** - Dokumentations-Hygiene Guidelines
- **scripts/README.md** - Script-Organisation
- **scripts/cleanup_temp.py** - Temporäre Scripts Cleanup
- **Ralph/progress.txt** - Session-Log Format
- **docs/archive/solved_issues/** - Archivierungs-Format

### Externe Inspiration:
- **[Beads (steveyegge/beads)](https://github.com/steveyegge/beads)** - Git-backed issue tracker für AI Agents
  - Compaction / Memory Decay Konzept
  - Session Protocol Patterns
  - Git-backed Persistence
  - Structured cleanup workflows

---

## 🚀 Nächste Schritte

1. **Plan reviewen** - Dieser Plan sollte mit dem Team/User besprochen werden
2. **Prioritäten setzen** - Welche Teile sind am wichtigsten?
3. **Automatisierung planen** - Welche Teile können automatisiert werden?
4. **Erste Implementierung** - Script oder Checkliste erstellen
5. **Testen** - Mit einer echten Session testen
6. **Refinen** - Basierend auf Erfahrungen anpassen

---

## 💡 Ideen für Erweiterungen

1. **Git Integration** (Inspiriert von Beads)
   - Automatisches Commit vor Cleanup
   - Branch für unfertige Features
   - Tags für Session-Ende
   - Git-State-Check (stashes, branches, uncommitted)

2. **Compaction / Memory Decay** (Inspiriert von Beads `bd compact`)
   - LLM-basierte semantische Zusammenfassung alter Sessions
   - Automatische Kompaktierung von progress.txt wenn >150 Zeilen
   - Archivierte Sessions zusammenfassen
   - Kern-Informationen behalten, Details reduzieren

3. **Metriken**
   - Session-Dauer tracken
   - Cleanup-Zeit tracken
   - Code-Quality-Metriken
   - Compaction-Effektivität messen

4. **Templates**
   - Session-Log Template
   - Issue-Report Template
   - Learning-Document Template
   - Git-Commit-Message Template

5. **Integration mit Tools**
   - Cursor/Amp Integration
   - GitHub Actions
   - CI/CD Pipeline
   - Beads Integration (falls verwendet)

6. **Session Protocol** (Inspiriert von Beads)
   - Strukturierte Session-Phasen
   - Explizite Status-Updates während Session
   - Ready-Tasks Identifikation
   - Dependency-Tracking

---

**Status:** Draft - Ready for Review
**Next:** Review with user, refine based on feedback, implement first version
