# AXE MCP Server - Setup-Anleitung

Der AXE MCP Server ermöglicht interaktive Accessibility-Analysen direkt in Claude Code.
Er ergänzt die automatisierten axe-playwright-Tests um eine tiefgehende, KI-gestützte Analyse.

## Option 1: Community a11y-mcp-server (empfohlen für den Einstieg)

### Installation

Voraussetzung: Node.js installiert

### Claude Code MCP-Konfiguration

Füge in deiner Claude Code Konfiguration (`~/.claude/settings.json` oder Projekt-Einstellungen)
folgendes hinzu:

```json
{
  "mcpServers": {
    "a11y-accessibility": {
      "command": "npx",
      "args": ["-y", "a11y-mcp-server"]
    }
  }
}
```

### Nutzung in Claude Code

Nach der Konfiguration kannst du in Claude Code direkt fragen:
- "Prüfe die Accessibility der Seite https://chatbot.europapark.de"
- "Analysiere die WCAG-Violations und schlage Fixes vor"
- "Welche Kontrast-Probleme gibt es auf der Seite?"

## Option 2: Offizieller Deque axe MCP Server

Für umfangreichere Analysen mit Enterprise-Features:

### Voraussetzungen
- Docker installiert
- Deque axe Account (https://www.deque.com/axe/mcp-server/)

### Konfiguration

```json
{
  "mcpServers": {
    "axe-mcp-server": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "dequelabs/axe-mcp-server"]
    }
  }
}
```

## Workflow: Automatisiert + Interaktiv

1. **Zuerst**: Automatisierte Tests ausführen
   ```bash
   python run.py --suite a11y
   ```

2. **Dann**: axe-Report prüfen in `reports/axe_report.json`

3. **Vertiefung**: In Claude Code den MCP Server nutzen für:
   - Detaillierte Analyse einzelner Violations
   - Kontext-spezifische Empfehlungen
   - Diskussion von Lösungsansätzen mit dem Entwicklungsteam

## Quellen
- [Deque axe MCP Server](https://www.deque.com/axe/mcp-server/)
- [Community a11y-mcp](https://github.com/priyankark/a11y-mcp)
- [Axe MCP Server Docs](https://docs.deque.com/devtools-server/4.0.0/en/axe-mcp-server/)
