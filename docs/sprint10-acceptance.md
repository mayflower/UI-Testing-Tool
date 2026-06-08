# Sprint 10 — Acceptance-Test-Pläne (Ecki-Bot, Projekt KI)

**Sprint:** _TBD (Sprint-Customfield nicht im Jira-Dump enthalten — Name/Ziel manuell ergänzen)_
**Laufzeit:** _TBD_
**Stand des Dokuments:** 2026-06-08
**Quelle:** Jira-Projekt KI, Snapshot aus `sprint in openSprints()` am 2026-06-08

Ziel des Dokuments: pro Ticket beschreiben, **wie ein PO/QA die Annahme durchführt** — Vorbereitung, konkrete Schritte, Testfragen (copy-paste in Chat), erwartetes Verhalten, Verifikation. Sortierung nach Jira-Status, beginnend mit **Ready for PO** und **Ready for Deployment** (sofort abnehmbar).

---

## Inhaltsverzeichnis

- [Sprint-Snapshot](#sprint-snapshot)
- [AC-Compliance-Check (User-Story-Regel)](#ac-compliance-check)
- [Status: Ready for PO](#status-ready-for-po)
- [Status: Ready for Deployment](#status-ready-for-deployment)
- [Status: In Review](#status-in-review)
- [Status: In Progress](#status-in-progress)
- [Status: To Do](#status-to-do)
- [Status: Done](#status-done)
- [Status: Declined](#status-declined)
- [Anhang — PO-Empfehlungen](#anhang)

---

<a id="sprint-snapshot"></a>
## Sprint-Snapshot

| Kennzahl | Wert |
|---|---|
| Gesamt-Tickets | 47 |
| Stories | 16 |
| Bugs | 12 |
| Unteraufgaben | 18 |
| Aufgaben | 1 |
| Ready for PO | 2 |
| Ready for Deployment | 5 |
| In Review | 6 |
| In Progress | 7 |
| To Do | 16 |
| Done | 7 |
| Declined | 4 |

**Themen-Cluster (grob):** Eval-Pipeline & Cluster-Taxonomie (15), Bot-Verhalten / POI / Web-Search (8), UI/UX-Bugs (4), Privacy/Logging (2), Confluence-Ausbau (3), Observability/Infra (3), Spikes (1).

---

<a id="ac-compliance-check"></a>
## AC-Compliance-Check

Gegen `feedback_user_stories.md` (keine Tech-Details in Story/AC, strikt User-Sicht). Reformulierungs-Empfehlungen **nur** für To-Do / Ready-for-PO (Workflow-Regel 2026-05-20).

| Key | Status | Verdikt | Befund |
|---|---|---|---|
| KI-237 | Ready for PO | ❌ stark | Vektoren in STACKIT, Index Mo 06:00, „Privacy Sandwich" → Tech-Plan. Reformulierung **empfohlen**. |
| KI-141 | Ready for PO | ❌ stark | URLs, `externalId`, Status-Enums in AC. Reformulierung **empfohlen**. |
| KI-282 | Ready for Deployment | ✅ | Sauber aus User-Sicht. |
| KI-281 | Ready for Deployment | ⚠️ leicht | „Status-Pille" Begriff vertretbar, aber Style-Hinweise (Spinner-Icon) sind UI-Tech. |
| KI-265 | Ready for Deployment | ⚠️ leicht | `{{starts_at}}`/`now()` als Feldnamen — sollte „aktuelle Uhrzeit" lauten. (Reformulierung nicht mehr verpflichtend in diesem Status.) |
| KI-254 | Ready for Deployment | ✅ | Sauber. |
| KI-248 | Ready for Deployment | ⚠️ | „Web_Fetch", Trust-Liste tech. User-Variante: „bevorzugt offizielle MACK-Domains". |
| KI-280 | In Review | ⚠️ | „Web-Fetch" tech, Story-Inhalt aber klar. |
| KI-234 | In Review | ❌ stark | Presidio, lokales LLM, GPU-Dimensionierung. |
| KI-224 | In Review | ❌ | „langserve", „MCP-Server" → Tech-Bug, sollte als Aufgabe geführt werden. |
| KI-158 | In Review | ➖ | Tech-Wartung. |
| KI-40 | In Review | ⚠️ | Dagster, Docling, STACKIT in AC; Format-Liste OK. |
| KI-29 | In Review | ❌ | Crawler-Listen + extId-Mapping, aber Quellen-Hinweis aus User-Sicht OK. |
| KI-302 | In Progress | ✅ | Sauber. |
| KI-278 | In Progress | ❌ stark | Funktionsnamen, ToolResult-repr, Middleware → Aufgabe statt Story. |
| KI-277 | In Progress | ❌ stark | AIMessage, tool_calls, agent_node → Aufgabe statt Story. |
| KI-273 | In Progress | ❌ stark | pgBouncer, Dangling Connections → Aufgabe. |
| KI-252 | In Progress | ➖ | Spike — andere Regeln. |
| KI-246 | In Progress | ⚠️ | Entra-ID-Claim, Langfuse-Bypass → Tech. User-Sicht: „GF-Chats werden nicht protokolliert". |
| KI-285 | To Do | ❌ stark | CLI-Signaturen, JSON-Schema in AC → Aufgabe. Reformulierung **empfohlen**. |
| KI-284 | To Do | ❌ stark | DatasetItem-Schema, ADR-Pfade → Aufgabe. Reformulierung **empfohlen**. |
| KI-274 | To Do | ❌ | Grafana-Dashboards, Tech-Metriken in AC. Reformulierung **empfohlen**. |
| KI-310 | To Do | ❌ stark | Markdown-Chunker, Retrieval-Pipeline → Aufgabe. Reformulierung **empfohlen**. |
| KI-286–299 | To Do | ➖ | Eval-Unteraufgaben, reine Tech — als „Aufgabe" zu führen. |
| KI-232 | Declined | – | Declined. |
| KI-151, KI-156, KI-172 | Declined | ➖ | Declined / Spikes. |

**Aggregiert:** 11 starke Verstöße, 5 leichte, 3 saubere User-Stories (KI-282, KI-254, KI-302). **5 Reformulierungs-Empfehlungen** offen (Ready-for-PO + To-Do).

---

<a id="status-ready-for-po"></a>
## Status: Ready for PO

> **Sofort abnahmebereit.** Detaillierte Testpläne aus PO-Sicht.

### KI-237 — Öffentliche Confluence-Spaces integriert

**Typ:** Story · **Priority:** High · **Assignee:** —

**Voraussetzungen:**
- Index-Lauf mind. einmal erfolgreich (Wochenmontag 06:00).
- Confluence-Testseite mit (a) Klar-PII und (b) zwei Versionen vorbereitet.
- Langfuse-Trace-View bereit.

**Schritte:**
1. Frage in jeden öffentlichen Bereich (Allgemein, Sales, Arbeitsschutz).
2. Aktualitäts-/Versionierungs-Test.
3. PII-Test in Confluence-Inhalt (Verbund mit KI-234).
4. Negativabgrenzung: privater Space, nicht-konfigurierter Inhalt.
5. Quellen-Link-Smoketest.

**Testfragen:**
- „Was steht im Wochenendplan dieser Woche?" (Allgemein)
- „Wie ist die aktuelle Sales-Argumentation für Familientickets?" (Sales)
- „Welche Arbeitsschutz-Regeln gibt es für Höhenarbeit?" (Arbeitsschutz)
- „Was war besonders am letzten Wochenende?" → jüngster Bericht erkennbar.
- *Versionierung:* Frage zu Seite mit zwei Versionen → Antwort priorisiert aktuellere.
- *Privater Space:* „Was steht im Confluence-Space „<privat>"?" → kein Treffer.
- *PII-Test:* Testseite mit Klar-PII anlegen, dann Frage stellen → PII pseudonymisiert; Trace bleibt PII-frei.
- *Negativ:* Frage zu nicht-konfiguriertem Space → „nicht verfügbar", **kein** Web-Fallback unter falschem Label.

**Erwartet:**
- Antwort mit funktionalem Direktlink je Aussage.
- Neueste Version bevorzugt.
- Privater/nicht-konfigurierter Space liefert keinen Treffer.
- Im Langfuse-Prompt keine Klartext-PII.

**Verifikation:** Index-Lauf-Log (Mo 06:00), Trace zeigt `search_confluence` mit Treffer-Metadaten inkl. `lastModified`. 3 Direktlinks stichprobenartig klicken.

---

### KI-141 — POI-Wartezeiten & Statuscodes live

**Typ:** Story · **Priority:** Medium · **Assignee:** —

**Voraussetzungen:**
- Test innerhalb Park-Öffnungszeit (sicherstellt, dass `opened`-POIs existieren).
- Live-Dashboard parallel offen für Soll-Ist-Abgleich.

**Schritte:**
1. Einzel-POI offen → Wartezeit korrekt.
2. Einzel-POI verschiedene Schließgründe (temporär, Wartung, Wetter, Kälte).
3. Multi-POI / Aggregation (Top-N, Filter).
4. Cache-/Live-Daten-Test.
5. Negativabgrenzung: nicht-Wartezeitenfragen, Fantasie-POI, Prognosefragen.

**Testfragen:**
- „Wie lange wartet man bei Voltron?" → Minutenwert, ggf. VirtualLine-Hinweis.
- „Kann ich gerade Wodan fahren?" (temporär geschlossen) → kein Minutenwert in Antwort.
- „Warum hat die Blue Fire zu?" (Wartung) → Grund „Wartung".
- „Warum ist die Tiroler Wildwasserbahn zu?" (Wetter) → Grund „witterungsbedingt", **kein** Enum-Begriff.
- „Was sind die kürzesten Wartezeiten gerade?" → 3–5 POIs aufsteigend, nur offene.
- „Top-5 längste Wartezeiten?" → 5 POIs absteigend.
- „Welche Attraktionen haben unter 10 Minuten Wartezeit?" → keine geschlossenen in der Liste.
- „Welche Attraktionen haben wegen Regen zu?" → zwei Listen (zu + offen).
- *Cache:* selbe Frage zweimal kurz hintereinander → Wert stabil, Trace zeigt API-Call innerhalb 60 s.
- *Negativ:* „Wartezeit Voltron in einer Stunde?" → klare Antwort „nur aktuelle Werte".

**Erwartet:**
- Wartezeit ± 2 min vs. Dashboard.
- Im Antworttext **kein** englischer Enum-Begriff.
- Geschlossen-Status nennt nie eine Wartezeit.
- Multi-POI-Filter respektiert Status.

**Verifikation:** Langfuse zeigt pro Antwort 1 Tool-Call, Latenz API-Teil < 2 s; Stichprobe gegen Live-Dashboard.

---

<a id="status-ready-for-deployment"></a>
## Status: Ready for Deployment

> **Deployment ausstehend.** Sobald die Stage live ist, ist Annahme durch PO möglich. Tests vorab auf Stage durchführbar.

### KI-282 — POI behauptet Hunde seien im Park verboten

**Typ:** Bug · **Priority:** Medium · **Assignee:** —

**Schritte:**
1. Hundefrage direkt stellen.
2. Variante mit Kontext.
3. Negativabgrenzung (andere Tierfragen).

**Testfragen:**
- „Darf ich meinen Hund mit in den Europa-Park nehmen?"
- „Sind Hunde im Europa-Park erlaubt?"
- „Wie ist die Hunderegelung im Park?"
- *Kontextvariante:* „Ich komme mit Familie und Hund — was muss ich beachten?"
- *Negativ:* „Darf ich meine Katze mitbringen?" → ähnliches Antwortmuster, ohne Hunde-Halluzination.

**Erwartet:**
- Keine pauschale Falschaussage „Hunde sind verboten".
- Antwort entweder korrekt (gemäß offizieller EP-Regelung) oder ehrliches „dazu liegen mir keine Daten vor — bitte beim Gästeservice prüfen".
- Bei Tool-Fehler: kontrollierter Fallback, kein erfundener Inhalt.

**Verifikation:** Trace prüfen — Antwort soll auf konkrete Quelle (POI-Tool oder Web/Confluence) zurückführbar sein.

---

### KI-281 — Gestapelte Status-Pillen pro Tool

**Typ:** Bug · **Priority:** Medium · **Assignee:** —

**Schritte:**
1. Frage stellen, die mehrere Tools triggert (z. B. POI + Web-Suche).
2. Während Generierung beobachten.
3. Nach Abschluss UI prüfen.
4. Detail-Aufklappen testen.

**Testfragen:**
- „Was läuft heute am Abend im Park und wie ist das Wetter?" (POI + Web)
- „Welche Shows gibt es heute und welche Restaurants haben offen?" (mehrere Tool-Calls)
- „Gib mir die Top-5 Attraktionen und Wartezeiten." (1 Tool, viele Daten)

**Erwartet:**
- **Maximal eine Pille** pro genutztem Tool, niemals gestapelt.
- Während Generierung: dynamische Pille mit Lade-Zustand (z. B. „Recherchiere…").
- Nach Abschluss: statische Pille mit kompakter Zusammenfassung.
- Klick/Tap → optionales Detail-Panel.

**Verifikation:** Browser-DevTools (DOM-Inspektion) zeigt nur einen Pillen-Knoten pro Tool im finalen Zustand.

---

### KI-265 — Zeit-Awareness bei Show-/Park-Antworten

**Typ:** Story · **Priority:** Medium · **Assignee:** —

**Schritte:**
1. Zeitbezogene Fragen vor / mitten in / nach einer Showzeit stellen.
2. Park-Schließungsfragen früh / spät am Tag.
3. Saisonbezug.

**Testfragen:**
- „Wann ist die nächste Show im Spanischen Theater?" (vormittags) → nur künftige Termine.
- *Selbe Frage nach Showbeginn* → bereits gelaufene Show wird nicht mehr aufgeführt.
- „Welche Shows laufen jetzt gerade?" → nur Shows mit `starts_at` ≤ jetzt ≤ Ende.
- „Wann schließt der Park heute?" (früher als 14:00) → Verhalten gemäß KI-254 (siehe nächster Eintrag).
- „Hat der Park morgen geöffnet?" → nur wenn Daten verfügbar.
- *Negativ:* „Wann ist die nächste Show im Spanischen Theater?" — bei leerem POI-Datensatz → „noch nicht festgelegt, später erneut fragen". **Keine** halluzinierten Zeiten.

**Erwartet:**
- Vergangenes wird ausgefiltert.
- Bei Datenlücke kein Phantasie-Termin.
- Saisonaussagen nur, wenn POI-Tool sie deckt.

**Verifikation:** Mehrere Stichproben über den Tag verteilt; Trace zeigt Filter-Logik (Filter auf `starts_at` gegen aktuelle Zeit).

---

### KI-254 — Parkschließung vor 14:00 Uhr korrekt ausgegeben

**Typ:** Bug · **Priority:** High · **Assignee:** —

**Schritte:**
1. Frage vor 14:00 mit API-Wert ≠ 18:00.
2. Frage vor 14:00 mit API-Wert leer oder = 18:00.
3. Frage nach 14:00.

**Testfragen:**
- „Wann schließt der Park heute?" (jeweils zu den drei Zeitpunkten / Datenständen)
- „Bis wann kann ich heute fahren?"
- „Wie lange ist der Park heute geöffnet?"

**Erwartet:**
- **Vor 14:00, API ≠ 18:00:** API-Zeit als definitiver Wert.
- **Vor 14:00, API leer oder 18:00:** „mindestens bis 18:00", finale Schließzeit „wird um 14:00 fixiert".
- **Nach 14:00:** API-Wert direkt als definitiver Schließwert.
- Sprache bleibt natürlich, keine Tech-Begriffe.

**Verifikation:** Drei Test-Sessions zu unterschiedlichen Uhrzeiten oder mit gemocktem API-Stand (Backend-Team).

---

### KI-248 — Häufigeres Nutzen der Websuche

**Typ:** Story · **Priority:** Medium · **Assignee:** —

**Schritte:**
1. Interne Treffer-Frage (kein Web-Fallback nötig).
2. Externe Frage ohne internen Kontext.
3. Frage mit lückenhaftem internem Treffer.
4. Trust-Domain-Check.

**Testfragen:**
- „Wie ist die aktuelle Sales-Argumentation für Familientickets?" → Confluence-Treffer, **keine** Websuche.
- „Wer hat Voltron entwickelt?" → Websuche aktiv, bevorzugt `mack.group` / `mack-rides.com`.
- „Wo finde ich Infos zur Halloween-Saison 2026?" → bei dürftigem internen Treffer Web-Fallback mit Quellenangabe.
- „Welche neuen Attraktionen kommen 2027?" → externe Quelle, Quelle wird genannt.
- *Trust-Check:* Antwort verlinkt zuerst auf MACK-Domains, andere Quellen nur ergänzend.

**Erwartet:**
- Interne Quellen Erstpriorität.
- Bei null/leer/unzureichend wird **automatisch** zweiter Tool-Call gegen Web-Suche/Web-Fetch ausgeführt.
- Transparenter Hinweis „aus Websuche" + klickbarer Quellenlink in jeder Web-Antwort.

**Verifikation:** Langfuse-Trace zeigt Tool-Reihenfolge `internal → web` bei den Fallback-Cases; bei reinen internen Fragen kein Web-Tool-Call.

---

<a id="status-in-review"></a>
## Status: In Review

> **Code-Review läuft.** Preview-Tests sinnvoll, finale Annahme nach Status-Wechsel.

### KI-280 — Web-Fetch bei Faktenabfragen (Mack Rides / Epic Universe)
**Bug · High · Bajorat** — Antwort muss durch verlinkte Quellen gegroundet sein. Test: „Welche Bahnen baut Mack Rides für Epic Universe?" → Quellen prüfbar, keine Halluzinationen.

### KI-234 — Privacy Sandwich (Microsoft Presidio)
**Story · Medium** — Pro PII-Entität (Name, Mail, IBAN, Telefon, Adresse, IP, Secret, Kombi) eine Frage, Langfuse-Trace prüfen → Klartext-PII ersetzt, Re-Identifizierung in Antwort. Siehe Sprint 9 für Detail-Testkatalog.

### KI-224 — langserve MCP-Server-Discovery zur Laufzeit
**Bug · High** — Test: MCP-Tool zur Laufzeit hinzufügen/entfernen, ohne Bot-Neustart. Erwartet: nächste Frage nutzt die aktualisierte Tool-Liste.

### KI-158 — Stackit Image Registry aufräumen
**Aufgabe · Low** — Reine Infra-Aufgabe, keine User-Annahme nötig. Verifikation: Registry-Listing vorher/nachher, Cleanup-Skript dokumentiert.

### KI-40 — Erweiterte Confluence-Anbindung (PDFs, Bilder, Excel)
**Story · Medium · Schröder** — Pro Dateityp (PDF/DOCX/XLSX/PPTX/PNG) eine Frage gegen eine Testseite mit dem entsprechenden Anhang. Antwort enthält Direkt-Hyperlink zum Anhang; ACL-Beschränkung greift bei berechtigungsgesteuerter Testseite.

### KI-29 — Webseiten-Inhalte werden gecrawled
**Story · Medium · Schröder** — Frage, die nur auf europapark.de oder mack.group beantwortbar ist. Erwartet: Quelle aus offizieller Domain, Quelle in Antwort verlinkt. Test mit 5–10 Web-Quellen-Fragen.

---

<a id="status-in-progress"></a>
## Status: In Progress

> **Aktiv in Arbeit.** Preview-Tests können fachliche Lücken sichtbar machen.

### KI-302 — Fehlermeldung über Eingabefeld bleibt dauerhaft bestehen
**Bug · High · Stocklassa** — Fehler erzeugen (z. B. Backend-Timeout simulieren), dann: (a) X-Icon vorhanden und schließt Banner; (b) Banner verschwindet beim nächsten erfolgreichen Prompt; (c) Banner verschwindet nach Reload.

### KI-278 — Fix `get_poi_info` degenerate returns
**Bug · Medium · Oppelt** — Backend-Testfall: POI-Tool wird zu leerem/listenartigem Return gezwungen → kein 500, kontrollierter Fallback-String, Trace zeigt strukturierte Warning.

### KI-277 — Orphan-`tool_use`-Filter in `agent_node`
**Bug · Medium · Oppelt** — Backend-Testfall: AIMessage mit teilweise resolved tool_calls erzeugen → kein LLM-Aufruf mit verwaisten tool_calls, synthetische Error-ToolMessages auf richtiger Position, Observability-Event geschrieben.

### KI-286 — S1 Cluster-Taxonomie + Coverage-Targets ADR
**Unteraufgabe · Medium · Oppelt** — Architektur-Subtask von KI-284. Annahme: ADR im Repo, Cluster-Liste vollständig, Coverage-Targets dokumentiert.

### KI-273 — Postgres Client Connections
**Bug · Medium · Bajorat** — Lasttest: viele Sessions öffnen/schließen, Connection-Count im DB-Dashboard beobachten. Entscheidung pgBouncer vs. erhöhte Limits dokumentiert.

### KI-252 — SPIKE: Voice-Features
**Story (Spike) · Medium · Stocklassa** — Lieferung: kurzes Memo mit Vergleich Quick-Win vs. Mayflower-Voice-Stack + klare Empfehlung. Annahme = Spike-Lieferung im Repo / Confluence vorhanden.

### KI-246 — VIP-Privacy: kein Langfuse-Logging für GF
**Story · Low · Schröder** — Mit GF-Test-Account chatten → in Langfuse darf weder Trace noch User-ID erscheinen, auch nicht „Anonym". Performance unverändert.

---

<a id="status-to-do"></a>
## Status: To Do

> Noch nicht in Arbeit. Kein Test, nur Übersicht.

| Key | Typ | Summary |
|---|---|---|
| KI-310 | Bug | Confluence Page Tables Chunk |
| KI-299 | Unteraufgabe | D5 — Bridge zu Baseline-Dataset (DatasetItem-Draft) |
| KI-298 | Unteraufgabe | D4 — Batch-Modus + Pattern-Frequency-Aggregation |
| KI-297 | Unteraufgabe | D3 — CLI: `eval diagnose-trace TRACE_ID` |
| KI-296 | Unteraufgabe | D2 — Klassifikations-Agent mit Cluster-Taxonomie |
| KI-295 | Unteraufgabe | D1 — Trace-Walker + Aggregator + Markdown-Renderer |
| KI-294 | Unteraufgabe | S8 — Synthesizer-Reframing als Draft-Tool |
| KI-293 | Unteraufgabe | S7 — Cluster: regression_guards |
| KI-292 | Unteraufgabe | S6 — Cluster: routing_boundary |
| KI-291 | Unteraufgabe | S5 — Cluster: confluence_retrieval |
| KI-290 | Unteraufgabe | S4 — Cluster: poi_facts |
| KI-289 | Unteraufgabe | S3 — Cluster: temporal / show_times |
| KI-287 | Unteraufgabe | S2 — Cluster: opening_hours |
| KI-285 | Story | `eval diagnose-trace` — Agentic Failure-Klassifikation |
| KI-284 | Story | Eval Baseline Dataset — Cluster-basiertes Regression-Testset |
| KI-274 | Story | Observability erweitern |

**Wichtigste Stories aus Sicht der Annahme später:**
- **KI-284 + KI-285** bilden zusammen das neue Regression-Setup. Annahme = Dataset im Repo + diagnose-trace-CLI klassifiziert ein gegebenes TRACE_ID gegen die Cluster.
- **KI-274** = Grafana-Dashboards funktionieren wieder + Langserve/Frontend-Metriken sichtbar.
- **KI-310** = Tabellen aus Confluence werden im Retrieval nicht mehr zerlinearisiert.

---

<a id="status-done"></a>
## Status: Done

| Key | Typ | Summary |
|---|---|---|
| KI-223 | Bug | Dagster-Auto-Updates verhindern (Version pinnen) |
| KI-181 | Unteraufgabe | Retrieval-Evaluator (Context Recall) |
| KI-155 | Unteraufgabe | Trajectory-Evaluator |
| KI-154 | Unteraufgabe | Fakten-Evaluator (LLM-as-Judge) |
| KI-153 | Story | Evaluatoren aufsetzen |
| KI-152 | Story | Kuratiertes/synthetisches Benchmark-Dataset |
| KI-150 | Unteraufgabe | Langfuse trace repost cli |

---

<a id="status-declined"></a>
## Status: Declined

| Key | Typ | Summary | Begründung (Kurz) |
|---|---|---|---|
| KI-232 | Story | Goldener Zauberstab als Sende-Icon | Verworfen — Schempp |
| KI-172 | Unteraufgabe | Dataset Synthesizer | Aus KI-152-Scope rausgelöst |
| KI-156 | Unteraufgabe | Guardrail-Evaluator | — |
| KI-151 | Story | Backtesting gegen Langfuse-Traces | — |

---

<a id="anhang"></a>
## Anhang — PO-Empfehlungen

- **Reihenfolge der Annahme:** Erst die zwei „Ready for PO"-Tickets (KI-237, KI-141) — sie sind das Tor zum Sprint-Erfolg. Danach die fünf „Ready for Deployment"-Tickets, sobald die Stage produziert.
- **Reformulierungs-Empfehlungen** (gem. `feedback_user_stories.md`, nur To-Do + Ready-for-PO):
  - **KI-237** AC neu fassen: „Ecki kann Wochenendberichte und öffentliche Confluence-Inhalte beantworten und nennt die Quelle als klickbaren Link" — ohne STACKIT, ohne Indexierungs-Turnus, ohne „Privacy Sandwich".
  - **KI-141** AC neu fassen: „Ecki kennt zu jeder Attraktion den aktuellen Betriebsstatus und nennt Wartezeit nur, wenn die Attraktion offen ist. Geschlossene Attraktionen werden mit verständlichem Grund (Wartung, Wetter, Kälte, temporär) genannt — nie mit englischem Fachbegriff."
  - **KI-285** als „Aufgabe" umtypisieren (CLI-Tooling).
  - **KI-284** als „Aufgabe" umtypisieren (Dataset-Engineering).
  - **KI-274** AC neu fassen: „Das Team sieht in Grafana wieder Node-, Backend- und Frontend-Auslastung."
  - **KI-310** als „Aufgabe" umtypisieren (Retrieval-Pipeline-Fix).
- **Sprint-Metadaten:** Sprint-Name + Laufzeit oben im Dokument noch eintragen — der Jira-Dump enthielt das Sprint-Customfield nicht.
- **Bekannte Test-Limits aus Sprint 9, weiterhin offen:**
  - 6 A11y/UI-Tests im EP-Testing_Tool rot.
  - 3 echte neue Findings ohne Jira-Ticket (`test_political_question_refused`, `test_stock_price_question_refused`, `test_multiple_questions_average_time`).
  - `test_send_message_with_enter` benutzt `wait_for_response(timeout=10000)` — bei Ø 22 s Stage-Latenz zu knapp.
