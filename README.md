# UI-Testing-Tool

UI/UX Testing-Tool für den Europa-Park KI-Chatbot (mAIstack).

## Voraussetzungen

- Python 3.9+
- Node.js (für AXE MCP Server, optional)

## Setup

```bash
# Virtuelle Umgebung erstellen und aktivieren
python3 -m venv .venv
source .venv/bin/activate

# Dependencies installieren
pip install playwright pytest pytest-playwright axe-playwright-python pyyaml python-dotenv jinja2 flask

# Playwright-Browser installieren
playwright install chromium

# Konfiguration anlegen
cp .env.example .env
```

## Konfiguration

### 1. Umgebungen (`config/environments.yaml`)

Trage die URLs eurer Chatbot-Umgebungen ein:

```yaml
environments:
  dev:
    url: "https://dev-chatbot.europapark.example.com"
  staging:
    url: "https://staging-chatbot.europapark.example.com"
  prod:
    url: "https://chatbot.europapark.de"
default: dev
```

### 2. CSS-Selektoren erkennen

```bash
python run.py --discover --env dev
```

Die erkannten Selektoren werden in `config/selectors.yaml` gespeichert.
Bei Bedarf manuell anpassen.

### 3. Branding (optional, `config/brand.yaml`)

Trage die Europa-Park CI-Werte ein, sobald bekannt:

```yaml
brand:
  colors:
    primary: "#244369"
    accent: "#ee353a"
  fonts:
    primary: "Source Sans Pro"
```

## Nutzung

### Web-Frontend (empfohlen)

```bash
# Web-Dashboard starten
python app.py
```

Öffne http://localhost:5000 im Browser. Das Dashboard bietet:
- Umgebung und Testsuite per Dropdown wählen
- Tests per Klick starten mit Live-Ergebnissen
- Selektor-Discovery direkt im Browser
- Reports und Screenshots ansehen

### CLI

```bash
# Alle Tests ausführen
python run.py

# Spezifische Umgebung
python run.py --env staging

# Nur eine Testsuite
python run.py --suite ui      # UI-Konsistenz
python run.py --suite ux      # UX-Flows
python run.py --suite a11y    # Accessibility

# Browser sichtbar (nicht headless)
python run.py --headed

# Umgebungen anzeigen
python run.py --list-envs

# CSS-Selektoren erkennen
python run.py --discover
```

## Testbereiche

### UI-Konsistenz (`tests/ui/`)
- Layout und Dimensionen des Chat-Widgets
- Branding: Farben, Fonts, Logo
- Responsive Darstellung (Desktop, Tablet, Mobile)
- Automatische Screenshots

### UX-Flows (`tests/ux/`)
- Begrüßungsnachricht
- Gesprächsverläufe und Folgefragen
- Fehlerbehandlung (leere Eingabe, Sonderzeichen, XSS)
- Antwortzeiten und Performance

### Accessibility (`tests/a11y/`)
- WCAG 2.1 AA Audit (via axe-core)
- Tastaturnavigation
- ARIA-Labels und Fokus-Management
- Farbkontraste

## Reports

Nach jedem Testlauf wird ein Markdown-Bericht in `reports/` generiert mit:
- Automatischen Testergebnissen als Checkliste
- Manuellen Prüfpunkten zum Abhaken
- Verweisen auf Screenshots in `screenshots/`

## AXE MCP Server (interaktive Analyse)

Für tiefgehende, KI-gestützte Accessibility-Analysen kann zusätzlich der
AXE MCP Server in Claude Code genutzt werden.

Setup-Anleitung: `config/mcp_axe_setup.md`

## Projektstruktur

```
EP-Testing_Tool/
├── app.py                 # Web-Frontend (Flask)
├── run.py                 # CLI-Einstiegspunkt
├── conftest.py            # pytest Fixtures
├── config/                # Konfigurationsdateien
├── tests/
│   ├── ui/                # UI-Tests
│   ├── ux/                # UX-Tests
│   └── a11y/              # Accessibility-Tests
├── utils/                 # Hilfsfunktionen
├── templates/
│   ├── web/               # HTML-Templates (Frontend)
│   └── *.md.j2            # Report-Templates
├── static/                # CSS & JS für Frontend
├── reports/               # Generierte Berichte
└── screenshots/           # Aufgenommene Screenshots
```
