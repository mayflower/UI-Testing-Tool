# KI-40 — Testplan: Erweiterte Confluence Anbindung

**Story:** Ecki soll bei Antworten auch Inhalte aus Confluence-Dateianhängen einbeziehen (PDF, Office, Bilder, Plaintext) — nicht nur Confluence-Seiten-Text.

**Status:** Ready for PO
**PR:** [#41 ep-services](https://bitbucket.org/europapark/ep-services/pull-requests/41) (Ben Bajorat, 2026-05-29)
**Sprint:** rolled over von Sprint 9 (closed) → Sprint 10 (active)

---

## Kurz-Analyse

### Akzeptanzkriterien-Cluster

1. **Ingestion-Pipeline** (Dagster, Docling, STACKIT-Cache, inkrementell, Lösch-Sync) — *Infra, nicht direkt im Bot testbar*
2. **Quellenangabe mit Confluence-Link** — *im Bot testbar*
3. **Multimodales Verständnis** (Tabellen sauber, kein „Wortsalat") — *im Bot testbar*
4. **ACL / Permissions** — *im Bot testbar, im Ticket explizit als „nächste Schritte JUNI" markiert*

### Offene Punkte vor Test

- **Scope unklar:** Pascal Weller hat am 2026-06-09 im Ticket nachgefragt, ob nur PDFs umgesetzt sind oder auch andere Prio-Dateitypen. Bens Antwort steht aus. Test-Blöcke A2–A4 sind davon abhängig.
- **AC mit Tech-Details:** Die AC erwähnen explizit Dagster, Docling, STACKIT, Vektor-DB — verletzt die User-Story-Regel (strikt User-Sicht). Kein Test-Blocker, aber Reformulierungs-Kandidat.
- **AC 4 (Permissions):** Im Ticket als „nächste Schritte JUNI" markiert → vermutlich nicht in PR #41 enthalten. PO-Acceptance dafür separat aufsetzen.

---

## Vorbereitung

1. **Scope klären:** Bens Antwort auf Pascals Kommentar abwarten.
2. **Sync-Status prüfen:** Letzten Dagster-Lauf für Confluence-Attachments auf Dev/Stage. Wenn nächtlich + inkrementell, erst nach Sync neue Files testen. Klären, ob manueller Trigger verfügbar.
3. **Testdaten in Confluence** (idealerweise eigene Test-Seite mit Anhängen):
   - 1× PDF mit eindeutigem Codewort (z. B. „Test-PDF-Codewort: ZIRKUS-2026-XYZ")
   - 1× DOCX mit anderem Codewort
   - 1× XLSX mit Tabelle (Spalten: Attraktion / Höhenrestriktion / Wartezeit-Soll), eindeutige Zelle
   - 1× PPTX mit Text
   - 1× PNG mit lesbarem Text (für OCR/Vision)
   - 1× SVG, 1× CSV, 1× MD, 1× TXT je mit Codewort
   - 1× DOC (alt), 1× MP3 → bewusst ignorierter Typ
   - 1× Datei in restricted Confluence-Space (für AC 4)
4. **Test-User:** zwei Accounts — einer mit voller Leseberechtigung, einer ohne Zugriff auf den restricted Space.

---

## Test-Blöcke

### A — Multiformat-Coverage (AC 1)

| # | Anfrage | Erwartet |
|---|---|---|
| A1 | „Was steht im Test-PDF Codewort?" | Bot liefert das Codewort aus PDF, Quelle mit Link |
| A2 | Gleiche Frage, DOCX | wie A1 *(nur wenn Scope)* |
| A3 | XLSX-Frage zur konkreten Zelle, z. B. „Welche Höhenrestriktion steht in der Tabelle für Attraktion X?" | korrekte Zelle, als Tabelle/strukturiert wiedergegeben, Quelle mit Link |
| A4 | PPTX-Frage | wie A1 *(nur wenn Scope)* |
| A5 | PNG mit Text — Frage zum sichtbaren Text im Bild | Inhalt erkannt, Quelle mit Link *(Prio 2)* |
| A6 | SVG-Frage | wie A5 *(Prio 2)* |
| A7 | CSV/MD/TXT-Frage | Inhalt erkannt, Quelle mit Link *(Prio 3)* |
| A8 | DOC- oder MP3-Anhang als Quelle? | darf nicht als Quelle erscheinen (bewusst ignoriert) |

**Negative Acceptance:** Frage, deren Antwort nirgends steht → kontrollierte „nicht gefunden"-Antwort, keine halluzinierte Quelle.

### B — Quellenangabe & Verlinkung (AC 2)

| # | Schritt | Erwartet |
|---|---|---|
| B1 | A1 wiederholen, in Antwort auf Quelle klicken | Link führt auf Original-PDF in Confluence (oder Parent-Seite), nicht 404 |
| B2 | Frage, deren Antwort aus 2 verschiedenen Anhängen gespeist wird | beide Quellen separat gelistet, beide Links funktional |
| B3 | Frage, die sowohl aus Confluence-Seite als auch Anhang stammt | Quellen-Mix korrekt deklariert |
| B4 | Dateiname / Titel der Quelle | sprechend, klar erkennbar (nicht nur Hash/ID) |

### C — Tabellen- & Layout-Verständnis (AC 3)

| # | Anfrage | Erwartet |
|---|---|---|
| C1 | XLSX mit ≥2 Spalten — gezielte Spalten-Frage | Spalten-Bezug korrekt, keine vertauschten Zellen |
| C2 | XLSX mit Merged Cells / Hierarchien | Hierarchie erkannt |
| C3 | DOCX mit Tabelle im Fließtext | Tabellen-Inhalt strukturiert, kein „Wortsalat" |
| C4 | PDF mit zweispaltigem Layout (z. B. Flyer) | Reading-Order korrekt, kein Text-Mix der Spalten |

### D — ACL / Permissions (AC 4 — „nächste Schritte JUNI")

| # | Schritt | Erwartet |
|---|---|---|
| D1 | User MIT Berechtigung fragt zu Datei im restricted Space | Antwort kommt + Quelle |
| D2 | User OHNE Berechtigung stellt gleiche Frage | Antwort enthält den Inhalt nicht, Quelle wird nicht zurückgegeben, kein Leak |
| D3 | Datei wird in Confluence später freigegeben → nächster Sync | erscheint für betroffenen User |

→ Wenn AC 4 bewusst aus diesem Sprint herausgehalten ist: D1–D3 als „später / nicht in diesem PR" markieren und PO-Acceptance darauf nicht blocken.

### E — Sync-Lifecycle (AC 1, partiell User-sichtbar)

| # | Schritt | Erwartet |
|---|---|---|
| E1 | Neues PDF in Confluence ablegen → Dagster-Lauf abwarten/triggern → Frage stellen | nach Sync findbar |
| E2 | Dieses PDF löschen → nächster Lauf → Frage stellen | Inhalt nicht mehr in Antworten, Quelle taucht nicht mehr auf |
| E3 | PDF ersetzen (gleicher Name, neuer Inhalt) → Sync → Frage zum neuen Inhalt | neue Version wird genutzt, alte nicht mehr |

→ E1–E3 sind langwierig (Sync-Latenz). Wenn manuell triggerbar: Dev fragen. Sonst über Nacht testen.

### F — Observability / Defense-in-Depth (optional, Tech-Sicht)

- F1: Langfuse-Trace einer Antwort mit Dokumenten-Quelle → Retrieval-Span vorhanden, zeigt Treffer-Doc + Score
- F2: STACKIT-Cache-Hit-Rate (nicht jeder Sync re-parst alles) — eher Ben/Dev-seitig, nicht Acceptance

---

## Risiko-Punkte vor Testbeginn

1. **Scope (Pascal-Frage):** vor jeder Testrunde klären — sonst testest du fehlschlagende Cases gegen einen Scope, der nie angefasst wurde.
2. **Dagster-Sync auf Stage:** läuft schon nächtlich? Manuell triggerbar?
3. **AC 4 (Permissions):** als „nächste Schritte JUNI" markiert → vermutlich nicht in PR #41 enthalten.
4. **„Story rolled over":** großer Umfang für eine Story — wahrscheinlich nur Teil-Scope umgesetzt (passt zu Pascals Frage).
