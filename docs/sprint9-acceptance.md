# Sprint 9 — Acceptance-Test-Pläne (Ecki-Bot, Projekt KI)

**Sprint:** „Ecki kann mehr Confluence und mehr Web Suche"
**Laufzeit:** 2026-05-12 → 2026-05-26
**Stand des Dokuments:** 2026-05-19
**Quelle:** Jira-Projekt KI, Sprint-9-Snapshot via MCP

Ziel des Dokuments: pro Ticket beschreiben, **wie ein PO/QA die Annahme durchführt** — Vorbereitung, konkrete Schritte, erwartetes Verhalten, Verifikation. Eval-Infrastruktur und Spikes haben abweichende Acceptance-Pfade (Dev-Review bzw. Lieferdokument), siehe jeweilige Gruppen.

---

## Inhaltsverzeichnis

- [Sprint-Snapshot](#sprint-snapshot)
- [AC-Compliance-Check (User-Story-Regel)](#ac-compliance-check)
- [Gruppe A — Chat-Verhalten (Black-Box PO/QA)](#gruppe-a)
- [Gruppe B — Frontend-UI](#gruppe-b)
- [Gruppe C — Backend & Privacy](#gruppe-c)
- [Gruppe D — Eval-Infrastruktur (Dev-Acceptance)](#gruppe-d)
- [Gruppe E — Spikes (Lieferdokument)](#gruppe-e)
- [Gruppe F — Sonderfälle (Done/Declined)](#gruppe-f)

---

## Sprint-Snapshot

| Kennzahl | Wert |
|---|---|
| Gesamt-Tickets | 36 |
| Stories | 22 |
| Subtasks | 8 |
| Bugs | 4 |
| Aufgaben | 2 |
| To Do | 14 |
| In Progress | 6 |
| In Review | 7 |
| Ready for PO | 6 |
| Done | 1 |
| Declined | 1 |

**Themen-Cluster:** Eval-Pipeline (13), Bot-Verhalten / Confluence / Web-Search (6), Privacy (3), Confluence-Ausbau (2), UI (2), Bildgenerierung (1), Modell-Upgrade (1), POI-Daten (3), Tonalität (1), Spikes (3), Sonstiges (1).

---

## AC-Compliance-Check

Gegen `feedback_user_stories.md` (keine Tech-Details in Story/AC, strikt User-Sicht):

| Key | Verdikt | Befund |
|---|---|---|
| KI-265 | ⚠️ leicht | `{{starts_at}}`/`now()` als Feldnamen — sollte „aktuelle Uhrzeit" lauten. |
| KI-261 | ❌ stark | Tailwind-Klassen, `text-base`, rem, „hardcodiert" → Tech-Sub-Task. |
| KI-260 | ❌ | Reine Tech-Frage, nicht aus User-Sicht. → Spike statt Story. |
| KI-259 | ❌ stark | „Claude 4.6 Sonnet via Vertex AI europe-west1" als AC. |
| KI-256 | ❌ stark | liteLLM, Vertex, europe-west1, SynthID in AC. |
| KI-254 | ✅ | Sauber aus User-Sicht. |
| KI-252 | ➖ | Spike — andere Regeln. |
| KI-248 | ⚠️ | „Web_Fetch", Trust-Liste tech. User-Variante: „bevorzugt offizielle MACK-Domains". |
| KI-247 | ✅ | Sauber. |
| KI-246 | ⚠️ | Entra ID Claims, Langfuse-Bypass → Tech. User-Sicht: „GF-Chats werden nicht protokolliert". |
| KI-237 | ❌ | „Vektoren in STACKIT, Index Mo 06:00" → Tech-Plan. |
| KI-235 | ➖ | Spike. |
| KI-234 | ❌ stark | Presidio, lokales LLM, GPU-Dimensionierung. |
| KI-232 | – | Declined. |
| KI-231 | ❌ stark | Pfade, Funktionsnamen, Helm, K8s-Secret. → Aufgabe statt Story. |
| KI-225 | ❌ stark | ContextVars, OTel, Dockerfiles. → Aufgabe statt Story. |
| KI-224 | ❌ leer | Keine AC. |
| KI-221 | ⚠️ | Object Storage, Crypto-Shredding. User-Sicht: „Beim Löschen des Chats werden Uploads unwiederbringlich entfernt". |
| KI-195 | ⚠️ | AC nur implizit. |
| KI-193 | ❌ | API-Endpoints, cent/100, extId-Mapping. |
| KI-181/180/172/157/156/155/154/153/152/151/150 | ➖ | Eval-Tools, reine Tech-Stories — sollten als „Aufgabe" geführt werden. |
| KI-167 | ❌ | API/Endpoints in AC. |
| KI-158 | ➖ | Tech-Wartung. |
| KI-145 | – | Done, AC fehlte. |
| KI-141 | ❌ | URLs, `externalId`, Status-Enums. |
| KI-40 | ⚠️ | Dagster, Docling, STACKIT in AC; Format-Liste OK. |

**Aggregiert:** 13 starke Verstöße, 6 leichte, 11 faktische Tech-Tasks (Typ-Wechsel empfohlen), 3 saubere User-Stories (KI-254, KI-247, KI-252-Spike).

---

## Gruppe A

### Chat-Verhalten — Black-Box-Acceptance gegen Live oder Stage

### KI-265 — Zeit-Awareness bei Show-/Park-Antworten

**Assignee:** Schröder, Lukas (EP) · **Status:** To Do

**Vorbereitung:**
- Aktuelle Uhrzeit kennen (Systemzeit oder echte Tageszeit nahe Show-Slots).
- Saison-Plan zur Hand (Mai aktiv?).

**Schritte:**
1. Zur Tageszeit nach 16:00 fragen: „Wann ist heute die nächste Eisshow?"
2. Folgefrage: „Was läuft jetzt gerade im Park?"
3. Außersaison-Frage: „Findet die [Wintershow] im Mai statt?"
4. Vergleichsfrage: „Wann hat der Park heute auf?"

**Erwartet:**
- Keine vergangenen Showzeiten als „nächste" ausgewiesen.
- Bei leeren POI-Zeiten: „noch nicht festgelegt, bitte später erneut fragen".
- Keine Saison-Halluzinationen ohne POI-Tool-Beleg.

**Verifikation:**
- Langfuse-Trace pro Frage; Soll-Vergleich mit Trace-Belegen 239c209a, 8d44efa0, 9755a7ee.
- Score 👍/👎 setzen → Tracking in Live-Lauf #3.

---

### KI-254 — Bug: Parkschließung vor 14:00

**Assignee:** Schröder, Lukas (EP) · **Status:** In Review · **Priority:** High

**Vorbereitung:**
- Test vor 14:00 Uhr durchführen (System-/Echtzeit).
- POI-Tool-Response für Parkbetrieb prüfen können (Backend-Zugang oder Trace-Inspektion).

**Schritte:**
1. **Szenario A** (vor 14:00, definitiver Wert != 18:00): Park-Schließzeit erfragen.
2. **Szenario B** (vor 14:00, definitiver Wert leer oder = 18:00): Park-Schließzeit erfragen.
3. **Szenario C** (nach 14:00): Park-Schließzeit erfragen.

**Erwartet:**
- A: „Park bis 19:00 Uhr geöffnet" (Default vermieden).
- B: „mindestens bis 18:00 Uhr, finale Schließzeit wird um 14:00 festgelegt".
- C: API-Wert als definitiv ausgegeben.

**Verifikation:**
- 3 Traces, Vergleich gegen `definitive_close`-Feld im POI-Tool-Output.
- Manuell auch um genau 13:59 / 14:01 testen (Grenzfall).

---

### KI-247 — Tonalität: „Du" + adaptives Mirroring

**Assignee:** Speckner, Christian (MF) · **Status:** Ready for PO

**Schritte:**
1. Neuer Chat: „Hallo, kannst du mir helfen?" → erwarte Du-Antwort.
2. Neuer Chat: „Guten Tag, könnten Sie mir helfen?" → erwarte Sie-Antwort.
3. Im Sie-Chat User wechselt zu Du in Folgefrage → Bot bleibt bei Sie (Konsistenz).
4. EN-Chat: „Hi, can you …?" → keine Du/Sie-Frage relevant (Sprachwechsel-Sanity).
5. FR-Chat: tu/vous-Analogon.

**Erwartet:**
- Default Du; bei Sie-Initiierung Sie für Rest der Session.
- Keine Anrede-Wechsel innerhalb einer Session.
- Freundlich/professionell, kein Slang.

**Verifikation:**
- 5 Sessions, je 3-4 Turns; manuelle Sicht.

---

### KI-248 — Web-Search-Fallback bei leeren internen Treffern

**Assignee:** unassigned · **Status:** To Do

**Schritte:**
1. Frage zu aktuellem Inhalt von europapark.de, der **nicht** in Confluence steht (Aktion/Banner).
2. Off-Topic-Frage Politik: „Wer ist Bundeskanzler?" → muss Refusal sein, kein web_search.
3. MACK-Gruppen-Frage: „Was macht MACK Rides?" → Web-Search auf mack.group erlaubt.
4. Externe Coaster-Frage (rcdb.com Trust-Liste): „Wer hat den schnellsten Coaster?" → web_search via rcdb erlaubt.

**Erwartet:**
- (1) Antwort mit Web-Search-Hinweis und Quellenlink.
- (2) Refusal, kein web_search im Trace.
- (3, 4) Antwort mit Trust-Listen-Quelle.

**Verifikation:**
- Trace-Tool-Sequenz: erst `search_confluence`/`Get_POI_Info`, dann `web_search` (oder Refusal-Pfad).
- ⚠️ Wechselwirkung mit Pattern 4 (Off-Topic-Refusal-Lücke aus Live-Feedback) prüfen — Off-Topic darf nicht aufgeweicht werden.

---

### KI-141 — POI-Wartezeiten Live

**Assignee:** Schröder, Lukas (EP) · **Status:** In Review

**Schritte:**
1. „Wartezeit Voltron?" (geöffnet, Live-Wert).
2. „Wartezeit Tiroler Wildwasserbahn bei Regen?" (Wetter-Status).
3. „Wartezeit Blue Fire?" (z. B. außerhalb Saison oder bei Wartung).
4. „Top-3 kürzeste Wartezeiten?" (Multi-POI).
5. Direkt darauf wieder Frage 1 → Cache-Check.

**Erwartet:**
- Wartezeit korrekt zum API-Wert.
- Wetter/Wartung in natürlicher Sprache übersetzt (kein `closedDueToWeather` als Begriff).
- Frage 5 darf max. 1 min alten Cache zeigen.

**Verifikation:**
- API-Direkt-Call gegen Bot-Antwort.
- Trace zeigt API-Call (oder Cache-Hit < 60 s).

---

### KI-193 — Öffentliche Tickets/Produkte zu Events

**Assignee:** unassigned · **Status:** To Do

**Schritte:**
1. „Welche Tickets gibt es für [Event in laufendem Sprintzeitraum]?"
2. „Wieviel kostet das?" → Preis in EUR.
3. „Ist das noch verfügbar?" → Status-Test.
4. „Wo kann ich es kaufen?" → Deep-Link.

**Erwartet:**
- Preis als Euro (z. B. 29,00 €), nicht Cent.
- Status korrekt: ausverkauft / abgesagt / wenige verfügbar.
- Deep-Link funktioniert (manueller Klick).

**Verifikation:**
- Vergleich mit `tickets.mackinternational.de` Produkt-Detail.

---

### KI-167 — Öffentliche Events (DS1 v3)

**Assignee:** Weller, Pascal (EP) · **Status:** Ready for PO

**Schritte:**
1. „Welche Events laufen heute?" (Einzeltermin, Zeitraum).
2. „Welche mehrtägigen Events laufen diese Woche?" (Range).
3. „Wo findet [Event] statt?" → POI-Mapping (`internalPoiId`).
4. „Ist [ausverkauftes Event] noch buchbar?" → Status-Test.

**Erwartet:**
- Nur Events mit `status: live`.
- Mehrtägig via Range, Einzel via `eventTimes`.
- Location als POI-Name.

---

### KI-256 — Bildgenerierung Gemini 2.5 Flash Image

**Assignee:** Speckner, Christian (MF) · **Status:** In Progress

**Schritte:**
1. „Erzeuge ein Bild von einem Karussell im EP-Stil."
2. Folge-Prompt im selben Chat: „Mache es heller und mit Sonnenuntergang."
3. Bild herunterladen, optional vergrößern.
4. Rate-Limit provozieren (5 schnell hintereinander).
5. Vertraulichkeit: SynthID-Detector über das Bild laufen lassen.

**Erwartet:**
- Bild rendert performant, Download als Datei.
- Bei Rate-Limit nutzerfreundliche Meldung, Chat bleibt funktional.
- SynthID-Wasserzeichen nachweisbar.

**Verifikation:**
- Langfuse-Kostentracking-Eintrag pro Bild.
- Auto-Prompt-Expansion sichtbar (Prompt im Trace länger als User-Prompt).

---

### KI-259 — LLM-Modell-Upgrade Claude 4.6 Sonnet

**Assignee:** Schröder, Lukas (EP) · **Status:** Ready for PO

**Schritte:**
1. A/B-Vergleich: 10 Gold-Fragen (idealerweise KI-152-Dataset, sobald vorhanden) jeweils gegen 4.5 vs. 4.6.
2. Lange Generierung (Protokoll-Style, ~3 k Token Output) erzwingen — Stabilität.
3. Tool-Use prüfen (POI + Confluence + Web).
4. Datei-Upload (PDF) + Bild-Analyse.

**Erwartet:**
- TTFT ≤ Baseline (Messung in Langfuse).
- Faktenqualität ≥ Baseline (manueller Score oder Evaluator).
- Tool-Use unverändert funktional.
- Keine Verbindungsabbrüche bei langen Outputs.

**Verifikation:**
- Experiment-Runner (KI-157) sobald verfügbar — sonst manuelle Score-Tabelle.

---

### KI-237 — Öffentliche Confluence-Spaces integriert

**Assignee:** Bajorat, Ben (MF) · **Status:** In Progress

**Schritte:**
1. Frage zu „Allgemein"-Bereich-Inhalt (Wochenendpläne) — Antwort muss aus Confluence kommen mit Link.
2. Frage zu Sales-Bereich.
3. Frage zu Arbeitsschutz.
4. Frage zu nicht-freigegebenem (privatem) Space → keine Antwort aus diesem Space.
5. PII-Test: Confluence-Seite mit Klar-PII anlegen → Trefferantwort sollte PII anonymisieren (Hand-in-Hand mit KI-234).

**Erwartet:**
- Antwort mit funktionalem Direktlink.
- Neueste Version bevorzugt (Bei zwei Confluence-Seiten mit gleichem Inhalt: jüngeres Änderungsdatum gewinnt).
- Privater Space liefert keinen Treffer.

**Verifikation:**
- Index-Lauf-Log (Mo 06:00) prüfen — Anzahl indizierter Seiten.
- Trace zeigt `search_confluence` mit Treffer-Metadaten.

---

### KI-40 — Confluence Attachments (PDF, Bilder, Excel)

**Assignee:** unassigned · **Status:** To Do

**Schritte:**
1. Test-Confluence-Seite mit PDF-, DOCX-, XLSX-, PPTX-, PNG-, JPG-Attachment anlegen, je mit eindeutigem Faktum.
2. Frage zu Inhalt aus PDF stellen → Antwort + Link.
3. Frage zu Tabellenwert aus XLSX (multimodales Verständnis).
4. Frage zu Inhalt aus PNG (Text auf Bild).
5. Negative: MP4/ZIP-Attachment hochladen → darf nicht indiziert werden.
6. ACL-Test: User ohne Leseberechtigung fragt nach Inhalt → kein Treffer.

**Erwartet:**
- Inhalte korrekt extrahiert (Docling).
- Link zur Original-Datei in Antwort.
- Ignorierte Formate werden nicht zurückgegriffen.

**Verifikation:**
- Dagster-Pipeline-Lauf-Log (nächtlicher Sync).
- Object-Storage-Eintrag in STACKIT.

---

## Gruppe B

### Frontend-UI — Browser-Acceptance

### KI-261 — Standardisierung Typografie 16px

**Assignee:** Speckner, Christian (MF) · **Status:** To Do

**Schritte:**
1. Live-UI öffnen, DevTools → Computed Font-Size in:
   - Sidebar-Menü („Neuer Chat", Chat-Liste, Überschriften, Historien)
   - Eingabebereich (Placeholder + Pille)
   - Optionen-Popup (Design/Sprache/Abmelden)
   - Modals/Dropdowns
2. Disclaimer + Feedback („War das hilfreich?") + Version → muss kleiner sein.
3. Resize-Test: 320, 768, 1024, 1440, 1920 px.
4. Lange Texte in Sidebar provozieren → kein Cut-off, keine Brüche.

**Erwartet:**
- Reguläre Elemente: 16 px (rem-Äquivalent).
- Ausnahmen: kleiner.
- Keine Layout-Brüche.

**Verifikation:**
- Playwright-Snapshot-Test in EP-Testing-Tool (`tests/ui/`).
- Axe-Run gegen Live-URL — Font-Size-Warnings = 0 für reguläre Komponenten.

---

### KI-195 — Bug: Promptlänge-Fehlermeldung

**Assignee:** Stocklassa, Eric (MF) · **Status:** In Review

**Schritte:**
1. Sehr lange Eingabe (z. B. 500 k Zeichen aus Wikipedia-Dump) ins Chat-Feld pasten und senden.
2. Nach Fehlermeldung sofort kurze Frage stellen.
3. Wiederholen mit HTML-Anhang (oder PDF, falls Upload), das über das Modell-Limit hinausgeht.

**Erwartet:**
- Verständliche Fehlermeldung (z. B. „Eingabe ist zu lang. Bitte kürzen.").
- Chat **bleibt funktional**, Schritt 2 funktioniert.
- Kein „kaputter" Chat-State.

**Verifikation:**
- Vorzustand: Chat brach still ab → manuelle Bestätigung.
- Trace: `invalid_request_error` wird gefangen und in User-Meldung übersetzt.

---

## Gruppe C

### Backend & Privacy

### KI-234 — Privacy Sandwich (Microsoft Presidio)

**Assignee:** Stocklassa, Eric (MF) · **Status:** In Progress

**Schritte:**
- Pro PII-Entität eine Frage stellen:
  1. „Mein Name ist Max Mustermann, kannst du mich bei der Stelle XY anmelden?"
  2. „Meine E-Mail ist max@example.com…"
  3. „Meine IBAN ist DE89 3704 0044 0532 0130 00 …"
  4. „Meine Telefonnummer …"
  5. „Mein Passwort ist Hunter2 …"
  6. Adresse, IP.

**Erwartet:**
- Antwort wirkt natürlich, enthält den Klar-Namen wieder (Re-Identifizierung über Mapping).
- In Langfuse-Trace: Klar-PII durch Platzhalter ersetzt.
- Mapping bleibt nur innerhalb der Session.

**Verifikation:**
- Langfuse-Trace pro Frage öffnen → kein Klartext-Wert sichtbar.
- TTFT-Impact messen (Vergleich mit/ohne Presidio aus Logs).

---

### KI-246 — VIP-Privacy für GF

**Assignee:** unassigned · **Status:** To Do

**Schritte:**
1. Mit GF-Test-Account (Entra-Rolle/Gruppe für GF) anmelden.
2. Chat führen (mind. 5 Turns, inkl. Tool-Use + Upload).
3. Zeitstempel notieren, Langfuse durchsuchen.
4. Mit Nicht-GF-Test-Account gleiche Schritte → Trace muss erscheinen (Negative Control).

**Erwartet:**
- Für GF-Session: **0 Einträge** in Langfuse (auch kein „Anonym/Unbekannt").
- Funktionalität für GF identisch (keine Latenz-Regression, Tools laufen).
- Token-Verbrauch nur aggregiert in GCP-Billing/STACKIT sichtbar.

**Verifikation:**
- Langfuse-Suche nach Session-ID und Zeitfenster → 0 Treffer.
- Negative Control aus Schritt 4 → Trace vorhanden.

---

### KI-231 — Langfuse user_id Pseudonymisierung

**Assignee:** Oppelt, Thomas (MF) · **Status:** In Progress · **Priority:** High

**Schritte:**
1. Beliebigen User anmelden, Chat führen.
2. Langfuse-Trace öffnen → `user_id`-Feld prüfen.
3. Wiederholter Login → identischer Hash?
4. Pepper rotieren (Dev/Stage) → neuer Hash bei identischem User?
5. MCP-Outbound: Header `X-User-Id` in MCP-Server-Logs prüfen.
6. Grep über Application-Logs nach Klar-User-ID-Pattern → 0 Treffer.

**Erwartet:**
- `user_id` als 32-Zeichen-Hex-String in Langfuse.
- Idempotent gleicher Pepper, neuer Pepper = neuer Hash.
- MCP-Header pseudonymisiert.
- Keine Klar-IDs in Logs.

**Verifikation:**
- Integrationstest aus AC grün.
- Grep-Gate vor Close: `grep -r "<test-user-id>" services/langserve/logs/` = 0.

---

### KI-224 — Bug: MCP-Reload zur Laufzeit

**Assignee:** Stocklassa, Eric (MF) · **Status:** In Review · **Priority:** High

**Vorbereitung:**
- ⚠️ **AC fehlt im Ticket.** Vor Acceptance vom PO ergänzen lassen, z. B. „Tool-Wechsel < 1 Request nach Aktualisierung sichtbar".

**Schritte:**
1. langserve laufen lassen, Chat führen mit Tool X.
2. MCP-Server-Konfiguration ändern (Tool Y hinzufügen, Tool X entfernen) **ohne langserve-Restart**.
3. Neuen Chat anstoßen, beide Tools ansprechen.

**Erwartet:**
- Tool Y sofort verfügbar.
- Tool X liefert freundliche Fehlermeldung (kein Crash).
- Bestehende Sessions brechen nicht ab.

---

## Gruppe D

### Eval-Infrastruktur — Dev-Acceptance (Code-Review + Smoke-Run)

Für diese Tickets ist „Acceptance" **kein PO-Demo**, sondern Dev-Review + Smoke-Run + Dashboard-Check. PO sieht nur das Endergebnis (Run-Vergleich) im Langfuse-Dashboard.

### KI-150 — Langfuse-Trace-Repost-CLI

- Unit-Tests grün.
- Trockenlauf: `eval repost --from 2026-05-18 --to 2026-05-19` → Markdown-Report mit Cluster-Verteilung, Negativ-Feedback hervorgehoben.
- Default ohne Argumente = Vortag.
- User-/Session-Filter testen.

### KI-152 — Benchmark-Dataset (Source of Truth)

- Repo enthält Dataset; Upload-Skript läuft sauber.
- Schema-Validierung verweigert defekte Einträge.
- ≥ 20 Cases pro MCP-Service (poi + confluence-retrieval).
- 3 Sprachen (de/en/fr) abgedeckt.
- Domänenexperten-Sign-Off dokumentiert (Kommentar im Ticket).

### KI-153 — Evaluatoren aufsetzen (Wrapper)

- Smoke-Run pro Evaluator (`response_facts`, `trajectory`, `guardrails`) gegen 5 Testfälle.
- Items mit leerem expected-Feld werden übersprungen, nicht 0.0.

### KI-154 — Fakten-Evaluator (LLM-as-Judge)

- Mit GT: Score = 1.0 bei vorhandenen Facts, 0.0 bei fehlenden.
- Ohne GT (Backtesting): Faithfulness gegen Tool-Output.
- Comments enthalten gefundene/fehlende/nicht-belegte Facts.

### KI-155 — Trajectory-Evaluator

- Set-Modus: Reihenfolge egal.
- Strict-Modus: Reihenfolge exakt.
- `max_tool_calls` pro Tool, 0 = verboten.
- Comment listet fehlende/unerwartete/zu häufige Tools.

### KI-156 — Guardrail-Evaluator

- Regex-basiert, deterministisch (kein LLM).
- Standardregel „Europa-Park-Schreibweise" immer aktiv (auch ohne expected-Feld).
- Forbidden/required korrekt.

### KI-157 — Experiment-Runner

- Komplettlauf gegen Dataset, Traces korrekt mit DatasetItems verknüpft (Run-Vergleich).
- Pflicht-Metadata gesetzt (`variant`, `dataset_version`, `git_commit`, `description`, `model`, `changed_components`, `prompt_version`).
- Gewichteter Gesamtscore pro Run via `langfuse.create_score(dataset_run_id=...)`.

### KI-172 — Dataset Synthesizer (Agent)

- `eval fetch-traces` liefert vollständige Traces als JSON.
- `eval synthesize` erzeugt Items pro Kategorie (`opening_hours`, `poi_facts`, `confluence_search`), 3 Sprachen.
- Claude-Code-Agent read-only (Write/Edit blockiert).
- Structured Output gegen `DatasetItem` validiert.
- Optionaler Judge-Pass aktivierbar.

### KI-180 — Confluence Synthesizer

- ⚠️ **Beschreibung leer im Ticket** — vor Acceptance konkretisieren lassen.

### KI-181 — Retrieval-Evaluator (Context Recall)

- Extrahiert `search_confluence`-Outputs aus Trace.
- Score 0–1, Anteil belegter Claims.
- Unit-Tests mit gemocktem LLM.

### KI-151 — Backtesting gegen Live-Negativ-Traces

- Filter: Score ≤ 0 + Kommentar nicht-trivial.
- Re-Run gegen aktuelle Agent-Version.
- Bericht besser/unverändert/schlechter, Trajectory + Guardrail laufen mit (ohne GT).

### KI-225 — Shared Langfuse-Middleware (mcp-common)

- Migration mcp-poi: inline-TraceMiddleware ersetzt, Tests grün.
- mcp-confluence-retrieval verwendet shared Middleware.
- Header-Extraktion, ContextVar-Reset, trace_id-Normalisierung, OTel-Propagation, graceful degradation: alle Unit-Tests grün.
- Tilt + Docker laufen lokal.
- Kein doppeltes Span-Logging in End-to-End-Trace.

---

## Gruppe E

### Spikes — Lieferdokument als Acceptance

### KI-252 — Voice-Features (Timebox 1 PT)

- Bericht mit Vergleich Web Speech API o. ä. vs. Mayflower Voice-Stack.
- Empfehlung A oder B mit Zeitschätzung.
- Architekturskizze.
- Keine Prototyp-Anforderung.

### KI-235 — Caching via liteLLM (Timebox 1 PT)

- Bericht zu zwei Cache-Ebenen (Response, Context).
- Empfehlung inkl. Redis-Setup-Aufwand, Provider-Caching-Durchreichung.
- Dashboard-Skizze: Token, Latenz, Cache-Hits, Kosten/Modell.

### KI-260 — POI-MCP-Schnitt

- Bericht mit Vorschlag, wo MCP getrennt werden kann (mehrere Sub-MCPs?).
- Pro/Contra-Liste.

### KI-158 — STACKIT Image Registry aufräumen

- Skript für Aufräumung mit klaren Regeln (Alter, Tag-Pattern).
- Trockenlauf-Output dokumentiert.
- Turnus festgelegt (z. B. wöchentlich).

---

## Gruppe F

### Sonderfälle

### KI-145 — Bug: Feedback nach Stop (Done)

**Nachtest empfohlen:**
- Generierende Antwort starten → Stop-Button drücken → Feedback-Buttons sichtbar.
- 👎 + Kommentar abschicken → in Langfuse als Score-Eintrag verifiziert.

### KI-232 — Sende-Icon Zauberstab (Declined)

- Nicht testen.

### KI-221 — Originaldokumente speichern

**Schritte:**
1. PDF im Chat hochladen, Frage stellen.
2. Object-Storage-Eintrag prüfen (Asset verschlüsselt mit Thread-Key).
3. Chat löschen.
4. Object-Storage-Eintrag erneut prüfen → Key gelöscht, Asset nicht mehr entschlüsselbar.
5. Aus User-Sicht: nach Chat-Löschung kein Zugriff mehr auf die Datei (Deep-Link falls existent liefert 404).

---

## Anhang — Vorschläge für PO

**Vor Sprint-Review klären:**
- KI-224 + KI-180: AC fehlen → vor Acceptance einfordern.
- KI-261 / KI-256 / KI-259 / KI-237 / KI-234 / KI-231 / KI-225 / KI-141 / KI-193 / KI-167: AC stark technisch. Reformulierung aus User-Sicht empfohlen (siehe AC-Compliance-Check). Reformulierungen liegen aus früherer Session vor (für KI-265/267/268/270 — analog für die anderen aus dieser Liste vorbereitbar).
- KI-150/151/152/153/154/155/156/157/172/180/181/225 / KI-231 / KI-158: Typ-Wechsel „Story → Aufgabe" erwägen (User-Story-Regel sonst nicht anwendbar).

**Empfohlene Test-Reihenfolge für Sprint-Review:**
1. Done/In-Review-Bugs zuerst (KI-145, KI-254, KI-195, KI-141, KI-224).
2. Ready-for-PO-Stories (KI-247, KI-259, KI-167, KI-221).
3. In-Progress (KI-256, KI-237, KI-234, KI-231).
4. To-Do — soweit fertig.
