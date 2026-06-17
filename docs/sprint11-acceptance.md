# Sprint 11 — Acceptance-Test-Pläne (Ecki-Bot, Projekt KI)

**Sprint:** Sprint 11 (aktiv)
**Laufzeit:** 2026-06-15 – 2026-06-30
**Sprint-Ziel:** Integration Preise, Verfügbarkeiten & Produkte; Eval-Framework; Presidio Go-Live; Confluence nach Nutzerberechtigungen
**Stand des Dokuments:** 2026-06-16
**Quelle:** Jira-Projekt KI, `sprint = "Sprint 11" AND status = "Ready for PO"`

Ziel des Dokuments: für die aktuell **abnahmebereiten** Tickets beschreiben, **wie ein PO/QA die Annahme durchführt** — Vorbereitung, konkrete Schritte, Testfragen (copy-paste in Chat), erwartetes Verhalten, Verifikation. Scope dieses Dokuments: **nur Status „Ready for PO"** (3 Tickets). Für die vollständige Sprint-Übersicht siehe das `sprint-summary`-Skill.

---

## Inhaltsverzeichnis

- [Status: Ready for PO](#status-ready-for-po)
  - [KI-224 — langserve MCP-Server-Discovery zur Laufzeit](#ki-224)
  - [KI-234 — Privacy Sandwich via Microsoft Presidio](#ki-234)
  - [KI-40 — Erweiterte Confluence-Anbindung (PDFs, Bilder & Excel)](#ki-40)
- [Offene Klärungspunkte vor dem Test](#offene-punkte)

---

<a id="status-ready-for-po"></a>
## Status: Ready for PO

> **Sofort abnahmebereit** (Status-Definition: „Task is ready for Product Owner to test").

<a id="ki-224"></a>
### KI-224 — „langserve" soll MCP-Server nicht nur beim Start abfragen

**Typ:** Bug · **Priority:** High · **Assignee:** — · [KI-224](https://atlassian.europapark.de/jirasw/browse/KI-224)

**Ziel laut Ticket:** Ecki funktioniert auch, wenn sich die MCPs **nach dem Start** verändern; Tools sollen idealerweise bei jedem Request neu abgefragt werden.

> ⚠️ **Hinweis:** Das Ticket hat **keine formalen Akzeptanzkriterien** und keine Umsetzungs-Kommentare. Die folgenden Tests sind aus der Bug-Beschreibung abgeleitet — vor dem Testen mit dem Dev (Lukas/Eric) abgleichen, ob „pro Request" oder „periodisch" umgesetzt wurde.

**Voraussetzungen:**
- Laufende Ecki-Instanz (Stage) ohne Neustart-Möglichkeit währenddessen.
- Zugriff auf die MCP-Konfiguration / mind. einen zu- und abschaltbaren MCP-Server.
- Langfuse-Trace-View offen.

**Schritte:**
1. Mit bestehender Tool-Landschaft eine normale Frage stellen (Baseline).
2. Einen MCP-Server / ein Tool **zur Laufzeit hinzufügen**.
3. Einen MCP-Server **zur Laufzeit stoppen/entfernen**.
4. Einen MCP-Server **zur Laufzeit verändern** (Tool umbenennen / Parameter ändern).
5. In keinem Schritt Ecki neu starten.

**Testaktionen & Erwartung:**
- [ ] **Neues Tool zur Laufzeit:** nach Hinzufügen nutzt die **nächste Frage** das neue Tool — **ohne Neustart**.
- [ ] **Entferntes Tool:** nach Stoppen fällt Ecki sauber zurück (kein Crash, kein Aufruf des toten Tools); Tool ist nicht mehr verfügbar.
- [ ] **Geändertes Tool:** geänderte Tool-Definition wird erkannt und korrekt verwendet.
- [ ] **Kein Restart nötig:** in keinem Fall ist ein Neustart von Ecki/langserve erforderlich.
- [ ] **Regression:** Konversation mit bestehenden Tools funktioniert unverändert.

**Verifikation:** Langfuse-Trace zeigt, dass die nach der MCP-Änderung gestellte Frage die **aktualisierte** Tool-Liste verwendet; keine Fehler-Spans durch verwaiste/tote Tool-Aufrufe.

---

<a id="ki-234"></a>
### KI-234 — Privacy Sandwich via Microsoft Presidio (PII-Anonymisierung)

**Typ:** Story · **Priority:** Medium · **Assignee:** — · [KI-234](https://atlassian.europapark.de/jirasw/browse/KI-234) · verknüpft mit [KI-313](https://atlassian.europapark.de/jirasw/browse/KI-313)

**Ziel laut Ticket:** Prompts an externe LLMs (Claude/Gemini) werden **vorab im Hintergrund pseudonymisiert**, damit keine PII das interne Netz verlässt — **ohne** Freigabe-Dialog für den Nutzer.

> ⚠️ **Scope-Hinweis (wichtig fürs Testen):** Laut Kommentaren (Eric, 2026-05-19) ist der aktuelle Stand **Code-Level-Filterung + Shadow Mode + Evaluations-Harness** (`presidio-evaluator`); Module werden schrittweise aktiviert. Der **reversible Round-Trip** (Mapping persistieren + Re-Identifizierung auf der Rückfahrt) ist im verknüpften **KI-313 „Presidio Pseudonymisierung" (noch In Progress)** verortet. Heißt: Die **Erkennung/Filterung (Hinfahrt)** ist hier testbar, die **vollständige Rückübersetzung evtl. noch nicht**. Vor dem Test bestätigen, ob KI-234 nur Erkennung/Filterung umfasst.

**Voraussetzungen:**
- Test-Instanz mit aktiviertem Presidio-Filter (welche Module aktiv sind, vorab klären).
- Langfuse-Trace-View offen (zur Leak-Prüfung).
- Testdaten mit PII in **DE- und FR-Formaten** vorbereitet.

**Schritte:**
1. Pro PII-Entität (s. u.) je eine Frage mit eingebetteter PII stellen.
2. Kombinierte Frage mit mehreren PII-Typen.
3. DE/FR-spezifische Formate testen.
4. Langfuse-Trace / Logs auf Klartext-PII prüfen.
5. Falls in Scope: Antwort auf korrekte Re-Identifizierung prüfen.

**Testkriterien:**
- [ ] **PII-Erkennung greift:** PII wird durch Platzhalter ersetzt, **bevor** sie nach außen / an Langfuse geht.
- [ ] **Abgedeckte Entitäten** je einzeln: Personenname · E-Mail · Telefonnummer · physische Adresse · IP-Adresse · Finanzdaten (IBAN/Kreditkarte) · IT-Secrets (Passwörter/Keys).
- [ ] **DE/FR-Formate:** deutsche/französische Adressen & Telefonnummern werden ebenfalls erkannt.
- [ ] **Silent / kein Human-in-the-Loop:** kein Bestätigungs-/Freigabe-Dialog; Workflow läuft ununterbrochen.
- [ ] **Kein PII-Leak in Observability:** in Langfuse/Logs nur Platzhalter, keine Originaldaten.
- [ ] **Re-Identifizierung (falls in Scope):** Antwort enthält Originaldaten korrekt wieder eingesetzt — *vorbehaltlich KI-313*.
- [ ] **Performance:** Time-to-First-Token wird durch den Analyse-Schritt nicht unverhältnismäßig verlängert.
- [ ] **Verifizierbarkeit:** Evaluator-Liste / Shadow-Mode-Auswertung liegt vor (offenes TODO „Liste der Evaluatoren ins Confluence" — Stand prüfen).

**Verifikation:** Langfuse-Trace zeigt im an das externe LLM gesendeten Prompt **nur Platzhalter**; presidio-evaluator-Auswertung (Shadow Mode) belegt Erkennungsrate je Entitätsklasse.

---

<a id="ki-40"></a>
### KI-40 — Erweiterte Confluence-Anbindung: PDFs, Bilder & Excel einbeziehen

**Typ:** Story · **Priority:** Medium · **Assignee:** — · [KI-40](https://atlassian.europapark.de/jirasw/browse/KI-40) · [PR #41 ep-services](https://bitbucket.org/europapark/ep-services/pull-requests/41) (Ben Bajorat)

**Ziel laut Ticket:** Ecki bezieht bei der Suche auch den Inhalt von **Confluence-Dateianhängen** (PDF, Office, Bilder, Plaintext) ein — nicht nur den Text auf der Confluence-Seite selbst.

> ⚠️ **Scope-Hinweis (wichtig fürs Testen):** Pascal Weller hat am 2026-06-09 im Ticket nachgefragt, ob nur **PDFs** umgesetzt sind oder auch weitere Prio-Dateitypen. **Bens Antwort steht noch aus.** Test-Schritte zu DOCX/XLSX/PPTX (Prio 1), PNG/JPG/SVG (Prio 2) und CSV/MD/TXT (Prio 3) erst durchführen, wenn der umgesetzte Scope bestätigt ist — sonst werden Cases gegen einen nie angefassten Scope getestet.
> **AC 4 (ACL/Permissions)** ist im Ticket explizit als „nächste Schritte JUNI" markiert → vermutlich **nicht** in PR #41 enthalten; Abnahme nicht darauf blocken (separat aufsetzen).

**Dateityp-Priorisierung laut Ticket:**
- Prio 1: PDF, DOCX, XLSX, PPTX
- Prio 2: PNG, JPG, SVG
- Prio 3: CSV, MD, TXT
- Bewusst ignoriert: MP4, MP3, ZIP, RAR, 7Z, DOC, XLS, PPT

**Voraussetzungen:**
- Umgesetzter Scope mit Ben bestätigt (s. Scope-Hinweis).
- Dagster-Sync-Status für Confluence-Attachments auf Dev/Stage geklärt; idealerweise manueller Trigger verfügbar (sonst über Nacht testen).
- Test-Confluence-Seite mit Anhängen, je mit **eindeutigem Codewort** (z. B. „ZIRKUS-2026-XYZ"): PDF, DOCX, XLSX (Tabelle: Attraktion/Höhenrestriktion/Wartezeit), PPTX, PNG mit lesbarem Text, SVG, CSV, MD, TXT; zusätzlich 1× bewusst ignorierter Typ (DOC/MP3); 1× Datei in restricted Space.
- Zwei Test-User: einer mit voller Leseberechtigung, einer ohne Zugriff auf den restricted Space.
- Langfuse-Trace-View offen.

**Schritte:**
1. Pro umgesetztem Dateityp eine Frage stellen, deren Antwort nur im jeweiligen Anhang steht (Codewort abfragen).
2. Bei einer Antwort auf die angegebene Quelle klicken (Link-Test).
3. XLSX/DOCX mit Tabellen gezielt zu einzelnen Zellen/Spalten befragen.
4. Frage stellen, deren Antwort nirgends steht (Negativ-Test).
5. Falls Sync triggerbar: Datei neu ablegen / löschen / ersetzen und nach Sync erneut fragen.

**Testkriterien:**
- [ ] **Multiformat-Coverage (AC 1):** Inhalt der umgesetzten Dateitypen wird gefunden und korrekt wiedergegeben; Codewort erscheint in der Antwort.
- [ ] **Ignorierte Typen:** DOC/MP3 o. Ä. erscheinen **nicht** als Quelle.
- [ ] **Quellenangabe (AC 2):** Jede aus einem Dokument stammende Information ist als Quelle deklariert; Quelle als **funktionierender Hyperlink** auf Original-Datei bzw. Parent-Seite (kein 404).
- [ ] **Sprechende Quelle:** Dateiname/Titel klar erkennbar (nicht nur Hash/ID).
- [ ] **Mehrere Quellen:** Antwort aus zwei Anhängen → beide separat gelistet, beide Links funktional; Mix Seite + Anhang korrekt deklariert.
- [ ] **Multimodales Verständnis (AC 3):** Tabellen (XLSX/DOCX) und mehrspaltige Layouts (PDF-Flyer) logisch korrekt interpretiert — keine vertauschten Zellen, kein „Wortsalat", korrekte Reading-Order.
- [ ] **Negativ-Acceptance:** Frage ohne Quelle → kontrollierte „nicht gefunden"-Antwort, **keine halluzinierte Quelle**.
- [ ] **Sync-Lifecycle (AC 1, falls testbar):** neues Dokument nach Sync findbar; gelöschtes nicht mehr in Antworten; ersetztes nutzt die neue Version.
- [ ] **ACL/Permissions (AC 4 — „nächste Schritte JUNI", falls in Scope):** User mit Berechtigung bekommt Inhalt + Quelle; User ohne Berechtigung bekommt **keinen** Inhalt und **keine** Quelle (kein Leak).

**Verifikation:** Langfuse-Trace einer Antwort mit Dokumenten-Quelle zeigt einen Retrieval-Span mit Treffer-Dokument; die in der Antwort verlinkte Quelle ist klickbar und führt auf den Original-Anhang im Confluence.

---

<a id="offene-punkte"></a>
## Offene Klärungspunkte vor dem Test

- **KI-224:** Umsetzungs-Scope mit Dev bestätigen (keine AC im Ticket) — „pro Request" vs. „periodische" Tool-Aktualisierung.
- **KI-234:** Round-Trip-Abgrenzung zu **KI-313** klären (Erkennung hier vs. reversible Pseudonymisierung dort); aktive Presidio-Module erfragen; Stand der Evaluator-Liste im Confluence prüfen.
- **KI-40:** Umgesetzten Dateityp-Scope mit Ben bestätigen (Pascals Frage vom 2026-06-09 offen — nur PDF oder auch Prio-1/2/3-Typen?); Dagster-Sync-Status auf Stage + manuellen Trigger klären; AC 4 (Permissions) als „nächste Schritte JUNI" voraussichtlich nicht in PR #41 → Abnahme nicht darauf blocken.
