# Sprint 11 — Acceptance-Test-Pläne (Ecki-Bot, Projekt KI)

**Sprint:** Sprint 11 (aktiv)
**Laufzeit:** 2026-06-15 – 2026-06-30
**Sprint-Ziel:** Integration Preise, Verfügbarkeiten & Produkte; Eval-Framework; Presidio Go-Live; Confluence nach Nutzerberechtigungen
**Stand des Dokuments:** 2026-06-16
**Quelle:** Jira-Projekt KI, `sprint = "Sprint 11" AND status = "Ready for PO"`

Ziel des Dokuments: für die aktuell **abnahmebereiten** Tickets beschreiben, **wie ein PO/QA die Annahme durchführt** — Vorbereitung, konkrete Schritte, Testfragen (copy-paste in Chat), erwartetes Verhalten, Verifikation. Scope dieses Dokuments: **nur Status „Ready for PO"** (2 Tickets). Für die vollständige Sprint-Übersicht siehe das `sprint-summary`-Skill.

---

## Inhaltsverzeichnis

- [Status: Ready for PO](#status-ready-for-po)
  - [KI-224 — langserve MCP-Server-Discovery zur Laufzeit](#ki-224)
  - [KI-234 — Privacy Sandwich via Microsoft Presidio](#ki-234)
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

<a id="offene-punkte"></a>
## Offene Klärungspunkte vor dem Test

- **KI-224:** Umsetzungs-Scope mit Dev bestätigen (keine AC im Ticket) — „pro Request" vs. „periodische" Tool-Aktualisierung.
- **KI-234:** Round-Trip-Abgrenzung zu **KI-313** klären (Erkennung hier vs. reversible Pseudonymisierung dort); aktive Presidio-Module erfragen; Stand der Evaluator-Liste im Confluence prüfen.
