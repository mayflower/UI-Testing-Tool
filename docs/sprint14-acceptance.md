# Sprint 14 — Acceptance-Test-Pläne (Ecki-Bot, Projekt KI)

**Sprint:** Sprint 14 (aktiv)
**Laufzeit:** 2026-07-28 – 2026-08-11
**Stand des Dokuments:** 2026-08-06
**Quelle:** Jira-Projekt KI, `sprint = "Sprint 14" AND status = "Ready for PO"`

Ziel des Dokuments: für die aktuell **abnahmebereiten** Tickets beschreiben, **wie ein PO/QA die Abnahme durchführt** — Vorbereitung, konkrete Schritte, erwartetes Verhalten, Verifikation. Scope dieses Dokuments: **nur Status „Ready for PO"** (3 Vorgänge).

---

## Inhaltsverzeichnis

- [KI-372 — LiteLLM-Endpunkt als OpenAI-kompatibler Inference-Layer](#ki-372)
- [KI-334 — Warnung bei alten Confluence-Informationen](#ki-334)
- [KI-253 — Scrollbars im leeren Inputfeld beim Zoomen (Safari)](#ki-253)
- [Offene Klärungspunkte vor dem Test](#offene-punkte)

---

<a id="ki-372"></a>
## KI-372 — LiteLLM-Endpunkt als OpenAI-kompatibler Inference-Layer

- **Jira:** [KI-372](https://atlassian.europapark.de/jirasw/browse/KI-372)
- **Status:** Ready for PO · **Typ:** Story · **Priorität:** High · **Sprint 13 → 14**
- **Reporter:** Michael Schempp · **Assignee:** Eric Stocklassa (Mayflower)
- **Verlinkt:** wird geklont von KI-375 „API für Ecki (damit man MCP für ihn bauen kann)" — To Do

### Worum geht's

Ein OpenAI-kompatibler Inference-Endpunkt auf Basis von LiteLLM, damit externe Werkzeuge
(z. B. OpenCode als Coding Agent) direkt gegen die Plattform laufen können. Requests werden
durch LiteLLM an Sonnet-5 weitergereicht.

### Kernregeln (aus den Akzeptanzkriterien)
- `POST /v1/chat/completions`, OpenAI-kompatibel.
- Fehler im OpenAI-Format: `{ "error": { "message": …, "type": …, "code": … } }`.
- API-Key zwingend erforderlich; Keys per SQL-Insert in einer Datenbank.
- Keys sicher gespeichert (bcrypt/Salted Hash oder gleichwertiges One-Way-Verfahren).
- Je Key: UUID, freie Beschreibung, aktivierbar/deaktivierbar, `created_at`, `updated_at` sichtbar.

### Out of Scope (laut Ticket Folgetickets)
Modellwechsel (Gemini Flash 3, Opus 4.8 …), Rate Limiting, Quotas, Scopes, User-Zuordnung, Streaming.

### Status-Hinweise (aus Kommentaren)
- **Michael (13.07.):** Story bewusst auf den LiteLLM-Endpunkt umgebaut; die MCP-API für Ecki
  wurde als eigene Story (KI-375) abgetrennt.
- **Eric (21.07.):** Ein eigener API-Gateway-Service war bereits fertig, bevor auffiel, dass
  LiteLLM alle Anforderungen inklusive Endpunkt nativ mitbringt. Richtungsentscheidung erfragt.
- **Eric (05.08.):** Gelöst über **LiteLLM-Native-Features** mit Ingress auf `litellm.stage.ecki.ai`;
  API-Key und Endpunkt an Michael zur Evaluation gegeben.

> ⚠️ **Vor der Abnahme klären:** Die Umsetzung ist LiteLLM-nativ, die AKs beschreiben eine
> eigene Key-Verwaltung per SQL-Insert. Formal gegen die AKs getestet fällt die Story durch,
> obwohl das Ziel erreicht ist. Entscheidung von Michael/Eric einholen, ob die AKs als
> „durch LiteLLM erfüllt" gelten oder nachgezogen werden.

### Wie testen

**Umgebung:** `https://litellm.stage.ecki.ai`
**Vorbereitung:** eigener gültiger API-Key (nicht Michaels), ein zweiter Key zum Deaktivieren,
Zugriff auf DB oder LiteLLM-Admin-UI für die Key-Attribute.
**Hinweis:** Key ausschließlich als Umgebungsvariable verwenden, nie inline im Kommando.

| TF | Prüfung | Erwartet |
|---|---|---|
| TF1 | `POST /v1/chat/completions` mit gültigem Key, einfache User-Message | 200, OpenAI-konformes Response-Objekt, Antwort von Sonnet-5 (Modellfeld prüfen) |
| TF2 | Gleicher Request **ohne** `Authorization`-Header | 401, Fehlerkörper exakt im OpenAI-Format |
| TF3 | Ungültiger/erfundener Key | 401, gleiches Fehlerformat |
| TF4 | Fehlerhafter Body (leeres `messages`, unbekanntes Modell) | 4xx im OpenAI-Fehlerformat — **kein** Stacktrace, kein Plain-Text |
| TF5 | OpenCode gegen den Endpunkt konfigurieren | Werkzeug arbeitet ohne Anpassung — der eigentliche Nutzen der Story |
| TF6 | Key-Speicherung in der Datenbank ansehen | Kein Klartext-Key; Hash mit Salt (bcrypt o. ä.) |
| TF7 | Key-Metadaten | UUID, freie Beschreibung, `created_at`, `updated_at` vorhanden und plausibel |
| TF8 | Key deaktivieren, TF1 wiederholen | 401; `updated_at` hat sich geändert |
| TF9 | Key wieder aktivieren | TF1 funktioniert erneut |
| TF10 | Sehr langer Prompt, Sonderzeichen und Umlaute | Kein Crash, korrekte Kodierung in der Antwort |

**Abnahme-Blocker:** TF6 und TF8. Ein Key, der nach Deaktivierung weiter funktioniert, oder
Klartextspeicherung ist kein Schönheitsfehler.

---

<a id="ki-334"></a>
## KI-334 — Confluence: Warnung bei alten Confluence-Informationen

- **Jira:** [KI-334](https://atlassian.europapark.de/jirasw/browse/KI-334)
- **Status:** Ready for PO · **Typ:** Story · **Priorität:** Medium · **Sprint 12 → 13 → 14**
- **Reporter:** Michael Schempp · **Assignee:** – (nicht gesetzt)
- **Anhang:** Mockup `Bildschirmfoto 2026-06-16 um 14.59.32.png`

### Worum geht's

Werden zur Beantwortung Confluence-Dokumente einbezogen, die **älter als 1 Jahr** sind, warnt
Ecki an der Quellenangabe:

> „Diese Information ist bereits **älter als** 1 **Jahr**, bitte überprüfe und aktualisiere ggf.
> die Dokumente auf Confluence"

### Status-Hinweise (aus Kommentaren)
- **Lukas (06.07.):** Für die englische und französische Fassung gab es keine Vorgabe; die Texte
  sind vorerst **LLM-generiert**. Beim PO-Test ist zu entscheiden, ob sie so bleiben.
- **Lukas (07.07., mit Pascal beschlossen):** Umsetzung weicht vom Mockup ab — es wird der
  **gesamte Text** nach veralteten URLs durchsucht, hinter die URL kommt ein **Marker (⚠️)**,
  und die Warnmeldung erscheint **am Ende der Nachricht**, mit dem Marker als Präfix.

> ⚠️ **Gegen den Kommentarstand testen, nicht gegen das Mockup.**

### Wie testen

**Vorbereitung:** je eine bekannte Confluence-Seite mit `lastModified`
(a) deutlich älter als 1 Jahr, (b) deutlich jünger, (c) knapp an der Grenze (~11–13 Monate).
Fragen so wählen, dass die Retrieval-Quelle vorhersagbar ist. Verifikation der tatsächlich
einbezogenen Quellen jeweils über den **Langfuse-Trace**, nicht nur über die sichtbare Antwort.

| TF | Frage/Situation | Erwartet |
|---|---|---|
| TF1 | Frage, die genau eine >1 Jahr alte Confluence-Seite zieht | Marker hinter der Quellen-URL, Warntext am Ende der Nachricht |
| TF2 | Frage, die nur aktuelle Seiten (<1 Jahr) zieht | Kein Marker, kein Warntext |
| TF3 | Frage, die mehrere alte Quellen zieht | Jede alte URL markiert; Warntext **genau einmal** am Ende, nicht je Quelle |
| TF4 | Gemischt: alte + aktuelle Quellen | Nur die alten markiert |
| TF5 | Grenzfall ~12 Monate | Verhalten dokumentieren und als Definition festhalten (>365 Tage?) |
| TF6 | Nicht-Confluence-Quelle (z. B. POI/Produktdaten), alt | Keine Confluence-Warnung — darf nicht auf fremde Quellen überspringen |
| TF7 | Gleiche Frage auf **Englisch** | Warntext englisch, sprachlich korrekt |
| TF8 | Gleiche Frage auf **Französisch** | Warntext französisch, sprachlich korrekt |
| TF9 | Darstellung im Frontend | Marker und Text werden gerendert (kein roher Markdown/HTML), auch mobil lesbar |

TF7/TF8 sind **Freigabeentscheidungen** des PO, keine reinen Pass/Fail-Fälle — den final
freigegebenen Wortlaut im Ticket dokumentieren.

---

<a id="ki-253"></a>
## KI-253 — Reinzoomen zeigt Scrollbars im leeren Ecki-Inputfeld

- **Jira:** [KI-253](https://atlassian.europapark.de/jirasw/browse/KI-253)
- **Status:** Ready for PO · **Typ:** Bug · **Priorität:** Medium · **Sprint 13 → 14**
- **Reporter:** Lukas Schröder · **Assignee:** Florian Metz
- Keine Kommentare, keine Akzeptanzkriterien. Beschreibung vollständig:
  „Beim Zoomen in Safari ist der Fehler noch reproduzierbar"

### Status-Hinweise (aus dem Work-Log)
- **Florian (29.07., 1 h):** Recherche ergibt einen **WebKit-Bug**, der nur durch die Verwendung
  des **Placeholders** auftritt. Placeholder entfernen würde es beheben, kostet aber UI/UX —
  gewählt wurde ein Workaround über `overflow-x`.

> Weil der Fix am Overflow ansetzt, ist der **Regressionsteil** (legitimes Scrollen bleibt
> erhalten) genauso wichtig wie der Fehlerfall selbst.

### Wie testen

**Umgebungsmatrix:** Safari macOS (aktuell), Safari iOS/iPadOS, dazu Chrome und Firefox als
Gegenprobe. Zoomstufen 50 / 80 / 100 / 125 / 150 / 200 / 250 %, jeweils Rein- **und** Rauszoomen.

| TF | Prüfung | Erwartet |
|---|---|---|
| TF1 | Safari macOS, leeres Inputfeld, schrittweise über alle Zoomstufen | Auf keiner Stufe horizontale oder vertikale Scrollbalken |
| TF2 | Wie TF1, rauszoomen und zurück auf 100 % | Ausgangszustand, keine Restartefakte |
| TF3 | Kurzer Text im Feld, gleiche Zoomreihe | Text vollständig sichtbar, nichts abgeschnitten |
| TF4 | Sehr langer/mehrzeiliger Text, gleiche Zoomreihe | Erwünschtes Scrollverhalten bleibt erhalten — der Fix darf legitimes Scrollen nicht abwürgen |
| TF5 | Placeholder-Darstellung auf allen Zoomstufen | Placeholder sichtbar und nicht abgeschnitten (er wurde bewusst behalten) |
| TF6 | Safari iOS/iPadOS, Pinch-Zoom, Hoch- und Querformat | Kein Scrollbalken, Eingabe bedienbar, Tastatur überdeckt das Feld nicht |
| TF7 | Chrome + Firefox, gleiche Zoomreihe | Keine Regression gegenüber vorher |
| TF8 | Bei 200 % Zoom eingeben, absenden, Feld leert sich | Nach dem Leeren kein Scrollbalken (der Bug betrifft explizit den leeren Zustand) |
| TF9 | Zoom + schmales Fenster / Split View | Layout bricht nicht, Sendebutton bleibt erreichbar |

**Belegführung:** Screenshots je Browser bei mindestens 100 %, 200 % und 250 %. Der Bug ist rein
visuell — ohne Bild ist ein PASS nicht belastbar.

---

<a id="offene-punkte"></a>
## Offene Klärungspunkte vor dem Test

1. **KI-372 — AK-Abweichung.** Umsetzung LiteLLM-nativ statt eigener SQL-Key-Verwaltung.
   Entscheidung von Michael/Eric nötig, sonst fällt die Story formal durch, obwohl das Ziel
   erreicht ist.
2. **KI-372 — eigener API-Key.** Bisher hat nur Michael einen Key zur Evaluation.
3. **KI-334 — kein Assignee.** Zuständigkeit für die Umsetzung ist offen.
4. **KI-334 — Ein-Jahres-Grenze unscharf.** „>1 Jahr" ist nirgends präzisiert (>365 Tage?
   Kalenderjahr?). Ergebnis aus TF5 als Definition festhalten.
5. **KI-334 — EN/FR-Wortlaut.** LLM-generiert, PO-Freigabe steht laut Kommentar 108378 aus.
6. **KI-253 — keine AKs.** Die Abnahmegrenze ergibt sich allein aus dieser Testmatrix; vor dem
   Test mit Florian abgleichen, welche Zoomstufen als verbindlich gelten.
