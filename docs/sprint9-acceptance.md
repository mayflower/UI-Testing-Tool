# Sprint 9 — Acceptance-Test-Pläne (Ecki-Bot, Projekt KI)

**Sprint:** „Ecki kann mehr Confluence und mehr Web Suche"
**Laufzeit:** 2026-05-12 → 2026-05-26
**Stand des Dokuments:** 2026-05-19
**Quelle:** Jira-Projekt KI, Sprint-9-Snapshot via MCP

Ziel des Dokuments: pro Ticket beschreiben, **wie ein PO/QA die Annahme durchführt** — Vorbereitung, konkrete Schritte, Testfragen (copy-paste in Chat), erwartetes Verhalten, Verifikation. Sortierung nach Jira-Status, beginnend mit **Ready for PO** (sofort abnehmbar).

---

## Inhaltsverzeichnis

- [Sprint-Snapshot](#sprint-snapshot)
- [AC-Compliance-Check (User-Story-Regel)](#ac-compliance-check)
- [Status: Ready for PO](#status-ready-for-po)
- [Status: In Review](#status-in-review)
- [Status: In Progress](#status-in-progress)
- [Status: To Do](#status-to-do)
- [Status: Done](#status-done)
- [Status: Declined](#status-declined)
- [Anhang — PO-Empfehlungen](#anhang)

---

## Sprint-Snapshot

| Kennzahl | Wert |
|---|---|
| Gesamt-Tickets | 36 |
| Stories | 22 |
| Subtasks | 8 |
| Bugs | 4 |
| Aufgaben | 2 |
| Ready for PO | 4 |
| In Review | 7 |
| In Progress | 9 |
| To Do | 14 |
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

<a id="status-ready-for-po"></a>
## Status: Ready for PO

> **Sofort abnahmebereit. Hier zuerst testen.**

### KI-259 — LLM-Modell-Upgrade Claude 4.6 Sonnet

**Assignee:** Schröder, Lukas (EP) · **Typ:** Story

**Schritte:**
1. A/B-Vergleich: 10 Gold-Fragen jeweils gegen 4.5 vs. 4.6 stellen.
2. Lange Generierung (~3 k Token Output) erzwingen — Stabilität.
3. Tool-Use prüfen (POI + Confluence + Web).
4. Datei-Upload (PDF) + Bild-Analyse.

**Testfragen** (copy-paste in Chat):
- „Wann ist heute die nächste Show im Europa-Park?"
- „Erstelle ein Sitzungsprotokoll mit 3 Spalten (Datum, Thema, Beschluss) und 5 Beispielzeilen."
- „Vergleiche die Wartezeiten der Top-3-Attraktionen und gib eine Empfehlung."
- „Welche Hotels gibt es im Resort und welches eignet sich am besten für Familien mit Kleinkindern?"
- „Schreibe eine 5-Tages-Tourplanung für eine Familie mit 2 Kindern (4 und 8 Jahre)."
- „Suche in Confluence nach der Urlaubsregelung und fasse die wichtigsten Punkte zusammen."
- „Übersetze deine letzte Antwort auf Englisch und Französisch."
- **Stress-Test:** „Plane mir einen 3-Tages-Aufenthalt: Tag 1 Park, Tag 2 Rulantica, Tag 3 Wandern in der Umgebung — mit Zeitplan, Restauranttipps und Wettervorbehalt." (lange Generierung)
- **Tool-Routing:** „Was ist die Wartezeit auf Voltron, und gibt es heute eine Show dazu?" (zwei Tools im selben Turn)

**Erwartet:**
- TTFT ≤ Baseline (Messung in Langfuse).
- Faktenqualität ≥ Baseline (manueller Score oder Evaluator).
- Tool-Use unverändert funktional.
- Keine Verbindungsabbrüche bei langen Outputs.

**Verifikation:**
- Experiment-Runner (KI-157) sobald verfügbar — sonst manuelle Score-Tabelle.

---

### KI-247 — Tonalität: „Du" + adaptives Mirroring

**Assignee:** Speckner, Christian (MF) · **Typ:** Story

**Schritte:**
1. Initiierung mit Du-Anrede → erwarte Du-Antwort.
2. Initiierung mit Sie-Anrede → erwarte Sie-Antwort.
3. Mid-Session-Test: User wechselt → Bot bleibt bei initialer Anrede.
4. Sprachwechsel-Sanity (EN, FR).

**Testfragen** (jeweils im neuen Chat starten):

*Du-Initiierung:*
- „Hallo, kannst du mir bei der Tagesplanung helfen?"
- „Hi Ecki, was sind deine Top-Empfehlungen heute?"

*Sie-Initiierung:*
- „Guten Tag, könnten Sie mir bitte die Öffnungszeiten nennen?"
- „Sehr geehrtes Team, ich hätte gern eine Auskunft zu den Hotels."

*Mid-Session-Wechsel (im Sie-Chat als 3. Frage):*
- „Übrigens, kannst du mir auch die Wartezeiten zeigen?" → erwarte: Bot bleibt bei Sie.

*Neutral (Test des Defaults):*
- „Ich hätte gern eine Empfehlung für das Mittagessen."

*Sprachwechsel:*
- EN: „Hello Ecki, what's new today?"
- FR: „Bonjour Ecki, peux-tu me conseiller un parcours?"

**Erwartet:**
- Default Du; bei Sie-Initiierung Sie für Rest der Session.
- Keine Anrede-Wechsel innerhalb einer Session.
- Freundlich/professionell, kein Slang.

---

### KI-221 — Originaldokumente bei Attachment-Upload speichern

**Assignee:** Speckner, Christian (MF) · **Typ:** Story

**Schritte:**
1. PDF im Chat hochladen, Frage stellen.
2. Object-Storage-Eintrag prüfen (Asset verschlüsselt mit Thread-Key).
3. Chat löschen.
4. Object-Storage-Eintrag erneut prüfen → Key gelöscht, Asset nicht mehr entschlüsselbar.

**Testfragen** (jeweils nach Upload eines kleinen Test-PDFs):
- „Hier ist mein Plan-PDF, kannst du die wichtigsten Punkte zusammenfassen?"
- *Folgefrage im selben Chat:* „Was steht auf Seite 3?"
- *Nach Chat-Löschung in neuer Session:* „Hier nochmal das gleiche Dokument" → erneut hochladen, sollte funktionieren.
- *Nach Chat-Löschung:* Direkt-Link auf das alte Asset versuchen (falls vorhanden) → 404 erwartet.

**Erwartet:**
- Upload wird gespeichert, Bot kann darauf zugreifen.
- Nach Chat-Löschung sind Datei + Schlüssel weg (Crypto-Shredding).
- Aus User-Sicht: nach Chat-Löschung kein Zugriff mehr auf die Datei.

---

### KI-167 — Öffentliche Events (DS1 v3)

**Assignee:** Weller, Pascal (EP) · **Typ:** Story

**Schritte:**
1. Tagesabfrage.
2. Wochen-/Range-Abfrage.
3. Location-Mapping.
4. Status-Test (Soldout/Canceled).

**Testfragen:**
- „Welche Events laufen heute im Park?"
- „Was gibt es diese Woche an mehrtägigen Veranstaltungen?"
- „Welche Events sind am Wochenende für Familien geeignet?"
- „Wo findet [Event-Name] statt?"
- „Gibt es heute Abend Live-Musik?"
- „Was sind die nächsten 3 Events?"
- „Ist [ausverkauftes Event] noch buchbar?"
- „Welche Events stehen für nächste Woche schon fest?"

**Erwartet:**
- Nur Events mit `status: live`.
- Mehrtägig via Range, Einzel via `eventTimes`.
- Location als POI-Name (nicht interne ID).

---

<a id="status-in-review"></a>
## Status: In Review

> **Code liegt vor, wartet auf Review/Test. Nach Review-Freigabe direkt abnehmbar.**

### KI-254 — Bug: Parkschließung vor 14:00

**Assignee:** Schröder, Lukas (EP) · **Typ:** Bug · **Priority:** High

**Vorbereitung:**
- Test vor 14:00 Uhr durchführen (System-/Echtzeit).
- POI-Tool-Response für Parkbetrieb prüfen können.

**Schritte:**
1. Szenario A (vor 14:00, definitiver Wert != 18:00).
2. Szenario B (vor 14:00, definitiver Wert leer oder = 18:00).
3. Szenario C (nach 14:00).

**Testfragen** (Uhrzeit-Slot beachten):

*Vormittag (z. B. 09:00):*
- „Wann schließt der Park heute?"
- „Bis wann kann ich heute fahren?"
- „Wie lange ist Voltron heute in Betrieb?"

*Direkt vor 14:00 (z. B. 13:55):*
- „Wann macht der Park heute zu?"
- „Kann ich noch bis 19:00 Uhr bleiben?"

*Direkt nach 14:00 (z. B. 14:05):*
- „Wann schließt der Park heute?" → API-Wert muss als definitiv gelten.

*Nachmittag (z. B. 16:00):*
- „Wie lange habe ich heute noch Zeit im Park?"
- „Bis wann sind die Achterbahnen heute offen?"

**Erwartet:**
- A: „Park bis 19:00 Uhr geöffnet" (Default vermieden).
- B: „mindestens bis 18:00 Uhr, finale Schließzeit wird um 14:00 festgelegt".
- C: API-Wert als definitiv ausgegeben.

**Verifikation:** 3 Traces, Vergleich gegen `definitive_close`-Feld. Grenzfälle 13:59 / 14:01.

---

### KI-225 — Shared Langfuse-Middleware (mcp-common)

**Assignee:** unassigned · **Typ:** Story (faktisch Tech-Task)

**Acceptance:** Dev-Review.
- Migration mcp-poi: inline-TraceMiddleware ersetzt, Tests grün.
- mcp-confluence-retrieval verwendet shared Middleware.
- Header-Extraktion, ContextVar-Reset, trace_id-Normalisierung, OTel-Propagation, graceful degradation: alle Unit-Tests grün.
- Tilt + Docker laufen lokal.
- Kein doppeltes Span-Logging in End-to-End-Trace.

**Testfragen** (End-to-End-Sanity nach Migration):
- „Wartezeit Voltron?" → triggert mcp-poi.
- „Was steht in der Urlaubsregelung?" → triggert mcp-confluence-retrieval.
- „Wie lange muss ich an Wodan warten und was steht in der aktuellen Sicherheitsregel?" → beide MCPs in einem Turn.

**Verifikation:** In Langfuse-Trace pro Frage beide Tool-Spans korrekt verknüpft, keine Doppel-Logs.

---

### KI-224 — Bug: MCP-Reload zur Laufzeit

**Assignee:** Stocklassa, Eric (MF) · **Typ:** Bug · **Priority:** High

**Vorbereitung:**
- ⚠️ **AC fehlt im Ticket.** Vor Acceptance vom PO ergänzen lassen.

**Schritte:**
1. langserve laufen lassen, Chat mit Tool X.
2. MCP-Konfiguration ändern (Tool Y hinzufügen, Tool X entfernen) **ohne langserve-Restart**.
3. Neuen Chat, beide Tools ansprechen.

**Testfragen:**

*Vor Reload:*
- „Wartezeit Voltron?" (Tool X, klappt)

*Nach Reload (neuer Chat):*
- „Wartezeit Voltron?" → muss weiter klappen (oder freundlich melden, falls Tool entfernt).
- „Wie ist die Urlaubsregelung?" (Tool Y neu) → muss jetzt funktionieren.
- „[Frage zu entferntem Tool]" → freundliche Fehlermeldung, kein Crash.

*Stress:*
- „Erzähl mir was über Wartezeiten." (offen, soll Tools dynamisch wählen)

---

### KI-195 — Bug: Promptlänge-Fehlermeldung

**Assignee:** Stocklassa, Eric (MF) · **Typ:** Bug · **Priority:** Low

**Schritte:**
1. Sehr lange Eingabe (~500 k Zeichen) pasten und senden.
2. Sofort kurze Folgefrage stellen (Chat-Funktionalität).
3. Mit Anhang (PDF/HTML > Limit) wiederholen.

**Testfragen:**
- *Riesen-Eingabe:* 500 k Zeichen aus einem Wikipedia-Dump pasten + Fragezeichen.
- *Nach Fehler:* „Hallo, funktioniert es jetzt wieder?"
- „Wie spät ist es?"
- *Wiederholung:* nochmal Riesen-Eingabe (Wiederholbarkeit).
- *Mit Upload:* sehr großes HTML als Datei mit Frage „Fasse das zusammen."

**Erwartet:**
- Verständliche Fehlermeldung („Eingabe ist zu lang. Bitte kürzen.").
- Chat **bleibt funktional**, Folgefragen klappen.
- Kein „kaputter" Chat-State.

---

### KI-158 — STACKIT Image Registry aufräumen

**Assignee:** Bajorat, Ben (MF) · **Typ:** Aufgabe

**Acceptance:** Lieferdokument + Skript.
- Skript mit klaren Regeln (Alter, Tag-Pattern).
- Trockenlauf-Output dokumentiert.
- Turnus festgelegt (z. B. wöchentlich).

**Testfragen:** Nicht zutreffend — reine Infrastruktur-Wartung.

---

### KI-150 — Langfuse-Trace-Repost-CLI

**Assignee:** unassigned · **Typ:** Subtask

**Acceptance:** Dev-Review.
- Unit-Tests grün.
- Trockenlauf: `eval repost --from 2026-05-18 --to 2026-05-19` → Markdown-Report mit Cluster-Verteilung, Negativ-Feedback hervorgehoben.
- Default ohne Argumente = Vortag.
- User-/Session-Filter testen.

**Testfragen:** Nicht zutreffend — CLI-Tool ohne Chat-Komponente. Verifikation an Output-Datei.

---

### KI-141 — POI-Wartezeiten Live

**Assignee:** Schröder, Lukas (EP) · **Typ:** Story

**Schritte:**
1. Einzel-POI-Anfragen.
2. Multi-POI-Anfragen.
3. Wetter-/Wartungs-Status.
4. Cache-Check (Sekunden-Folge).

**Testfragen:**
- „Wartezeit Voltron?"
- „Wie lange muss ich an Wodan anstehen?"
- „Was sind die kürzesten Wartezeiten gerade?"
- „Top-5 längste Wartezeiten?"
- „Welche Attraktionen haben aktuell unter 10 Minuten Wartezeit?"
- „Kann ich gerade Eurosat fahren?"
- „Ist die Tiroler Wildwasserbahn geöffnet?" (bei Regen)
- „Warum ist Blue Fire geschlossen?" (Wartung oder Wetter)
- „Wie ist die Wartezeit auf Voltron?" → *direkt nochmal die gleiche Frage* (Cache-Check ≤ 60 s).

**Erwartet:**
- Wartezeit korrekt zum API-Wert.
- Wetter/Wartung in natürlicher Sprache (kein `closedDueToWeather` als Begriff).
- Letzte Frage zeigt frischen Wert oder Cache-Hinweis.

---

<a id="status-in-progress"></a>
## Status: In Progress

> **Aktiv in Arbeit — Preview-Tests sinnvoll, finale Annahme nach Status-Wechsel.**

### KI-256 — Bildgenerierung Gemini 2.5 Flash Image

**Assignee:** Speckner, Christian (MF) · **Typ:** Story

**Schritte:**
1. Bildgenerierung initiieren.
2. Folge-Prompt (Verfeinerung).
3. Download + ggf. Vergrößerung.
4. Rate-Limit-Test.
5. SynthID-Wasserzeichen prüfen.

**Testfragen:**
- „Erzeuge ein Bild von einem klassischen Karussell im Europa-Park-Stil."
- „Bitte ein Bild von einer Achterbahn bei Sonnenuntergang."
- *Folge-Prompt:* „Mach das Bild heller und mit mehr Beleuchtung."
- „Erzeuge eine Skizze eines Familienhotels in alpinem Stil."
- „Generiere ein Bild für ein Sommerfest-Plakat."
- „Bitte ein Bild im Querformat, Motiv: Wasserrutsche bei Rulantica."
- *Rate-Limit:* 5× hintereinander unterschiedliche Bildanfragen.
- *Edge-Case:* „Erzeuge ein Bild einer bekannten Politiker-Person" → Refusal erwartet.

**Erwartet:**
- Bild rendert performant, Download als Datei.
- Bei Rate-Limit nutzerfreundliche Meldung, Chat bleibt funktional.
- SynthID-Wasserzeichen nachweisbar.

**Verifikation:** Langfuse-Kostentracking pro Bild, Auto-Prompt-Expansion sichtbar.

---

### KI-237 — Öffentliche Confluence-Spaces integriert

**Assignee:** Bajorat, Ben (MF) · **Typ:** Story · **Priority:** High

**Schritte:**
1. Frage in jeden öffentlichen Bereich.
2. Versuch gegen privaten Space.
3. PII-Test in Confluence-Inhalt.

**Testfragen:**
- „Was steht im Wochenendplan dieser Woche?" (Allgemein-Bereich)
- „Wie ist die aktuelle Sales-Argumentation für Familientickets?" (Sales)
- „Welche Arbeitsschutz-Regeln gibt es für Höhenarbeit?" (Arbeitsschutz)
- „Was ist die Urlaubsregelung?" (Personal — falls öffentlich)
- „Gibt es eine Übersicht zur Marketing-Kampagne 2026?"
- *Versionierung:* Frage zu einer Seite mit zwei Versionen → Antwort muss aktuellere nehmen.
- *Privater Space:* „Was steht im Confluence-Space [Privater-Name]?" → erwartet: kein Treffer aus diesem Space.
- *PII-Test:* Confluence-Testseite mit Klar-PII anlegen, dann fragen → PII anonymisiert (zusammen mit KI-234).

**Erwartet:**
- Antwort mit funktionalem Direktlink.
- Neueste Version bevorzugt.
- Privater Space liefert keinen Treffer.

**Verifikation:** Index-Lauf-Log (Mo 06:00), Trace zeigt `search_confluence` mit Treffer-Metadaten.

---

### KI-234 — Privacy Sandwich (Microsoft Presidio)

**Assignee:** Stocklassa, Eric (MF) · **Typ:** Story

**Schritte:** Pro PII-Entität eine Frage, dann Langfuse-Trace prüfen.

**Testfragen** (Klar-PII, fiktiv!):
- „Mein Name ist Max Mustermann, kannst du eine Beschwerde für mich formulieren?"
- „Meine E-Mail ist max.mustermann@example.com, schick mir bitte Infos zum nächsten Sommerfest."
- „Meine IBAN ist DE89 3704 0044 0532 0130 00, ist das eine deutsche IBAN?"
- „Meine Telefonnummer 030 12345678, kann mich der Service darüber erreichen?"
- „Mein Passwort ist Hunter2 — ist das ein sicheres Passwort?"
- „Ich wohne in der Musterstraße 12, 77977 Rust. Wie weit ist das zum Park?"
- „Meine IP-Adresse ist 192.168.1.42, kann ich damit ins WLAN?"
- *Kombi-Test:* „Mein Name ist Max Mustermann, E-Mail max@example.com, ich möchte einen Tisch reservieren."

**Erwartet:**
- Antwort wirkt natürlich, Klar-Name erscheint wieder (Re-Identifizierung).
- In Langfuse-Trace: Klar-PII durch Platzhalter ersetzt.
- Mapping bleibt nur innerhalb der Session.

**Verifikation:** Langfuse-Trace pro Frage öffnen → kein Klartext-Wert sichtbar. TTFT-Impact messen.

---

### KI-231 — Langfuse user_id Pseudonymisierung

**Assignee:** Oppelt, Thomas (MF) · **Typ:** Aufgabe · **Priority:** High

**Schritte:** Beliebige Chats triggern, dann Langfuse-Trace + MCP-Logs prüfen.

**Testfragen** (Inhalt egal, Hauptsache es entstehen Traces):
- „Hallo Ecki, was läuft heute?"
- „Wie ist die Wartezeit auf Voltron?"
- *Mehrfach derselbe User:* dieselbe Frage zweimal aus zwei Sessions.
- *Wechsel-User:* anderer Account, gleiche Frage.

**Erwartet:**
- `user_id` als 32-Zeichen-Hex-String in Langfuse.
- Idempotent gleicher Pepper, neuer Pepper = neuer Hash.
- MCP-Header `X-User-Id` pseudonymisiert.
- Keine Klar-IDs in Logs.

**Verifikation:**
- Integrationstest aus AC grün.
- Grep-Gate: `grep -r "<test-user-id>" services/langserve/logs/` = 0.

---

### KI-181 — Retrieval-Evaluator (Context Recall)

**Assignee:** unassigned · **Typ:** Subtask

**Acceptance:** Dev-Review.
- Extrahiert `search_confluence`-Outputs aus Trace.
- Score 0–1, Anteil belegter Claims.
- Unit-Tests mit gemocktem LLM.

**Testfragen:** Nicht zutreffend — Evaluator-Logik wird gegen Datasets getestet, nicht im Chat.

---

### KI-156 — Guardrail-Evaluator

**Assignee:** unassigned · **Typ:** Subtask

**Acceptance:** Dev-Review.
- Regex-basiert, deterministisch (kein LLM).
- Standardregel „Europa-Park-Schreibweise" immer aktiv (auch ohne expected-Feld).
- Forbidden/required korrekt.

**Testfragen:** Nicht zutreffend — Unit-Tests gegen Datasets. **Indirekter Test:** Auf einen Dataset-Run, der „Europapark" (falsche Schreibweise) generiert, muss Guardrail-Score = 0 sein.

---

### KI-155 — Trajectory-Evaluator

**Assignee:** unassigned · **Typ:** Subtask

**Acceptance:** Dev-Review.
- Set-Modus: Reihenfolge egal.
- Strict-Modus: Reihenfolge exakt.
- `max_tool_calls` pro Tool, 0 = verboten.
- Comment listet fehlende/unerwartete/zu häufige Tools.

**Testfragen:** Nicht zutreffend — Evaluator gegen Dataset-Items mit erwarteten Trajektorien.

---

### KI-154 — Fakten-Evaluator (LLM-as-Judge)

**Assignee:** unassigned · **Typ:** Subtask

**Acceptance:** Dev-Review.
- Mit GT: Score = 1.0 bei vorhandenen Facts, 0.0 bei fehlenden.
- Ohne GT (Backtesting): Faithfulness gegen Tool-Output.
- Comments enthalten gefundene/fehlende/nicht-belegte Facts.

**Testfragen:** Nicht zutreffend — LLM-Judge gegen Dataset-Items.

---

### KI-152 — Kuratiertes/synthetisches Benchmark-Dataset

**Assignee:** Oppelt, Thomas (MF) · **Typ:** Story (faktisch Tech-Task)

**Acceptance:** Dev-Review + Domänenexperten-Sign-Off.
- Repo enthält Dataset; Upload-Skript läuft sauber.
- Schema-Validierung verweigert defekte Einträge.
- ≥ 20 Cases pro MCP-Service.
- 3 Sprachen (de/en/fr) abgedeckt.

**Testfragen:** Nicht zutreffend — die Dataset-Items SIND die Testfragen für andere Tickets. Stichprobe als Sanity:
- 5 zufällige Dataset-Items prüfen: User-Question realistisch? `response_facts` korrekt?
- Mind. 1 Case pro Pattern aus `project_ecki_negative_feedback.md` enthalten?

---

<a id="status-to-do"></a>
## Status: To Do

> **Noch nicht begonnen — Testpläne als Vorbereitung, Annahme nach Implementierung.**

### KI-265 — Zeit-Awareness bei Show-/Park-Antworten

**Assignee:** Schröder, Lukas (EP) · **Typ:** Story

**Vorbereitung:**
- Aktuelle Uhrzeit kennen (Systemzeit oder echte Tageszeit nahe Show-Slots).
- Saison-Plan zur Hand.

**Schritte:**
1. Show-Anfrage nach erstem Show-Slot des Tages.
2. „Heute"-Routing in Themenbereich.
3. Außersaison-Frage.

**Testfragen:**

*Nach 14:30 (Eisshow-Slot bereits vorbei):*
- „Wann ist heute die nächste Eisshow?"
- „Welche Eisshow kann ich heute noch sehen?"

*Tagesfragen:*
- „Was läuft jetzt gerade im Park?"
- „Welche Shows gibt es heute Nachmittag noch?"
- „Wann ist die letzte Show heute?"

*Themenbereich-Routing:*
- „Was läuft heute in Spanien?"
- „Welche Attraktion-/Show-Highlights gibt es heute in Italien?"

*Park-/Restaurant-Zeiten:*
- „Wann hat der Park heute geöffnet?"
- „Bis wann hat das Ammolite heute auf?"

*Außersaison (im Mai):*
- „Findet die [Wintershow] im Mai statt?" → muss korrekt verneinen, ohne Daten zu halluzinieren.

**Erwartet:**
- Keine vergangenen Showzeiten als „nächste".
- Bei leeren POI-Zeiten: „noch nicht festgelegt".
- Keine Saison-Halluzinationen.

**Verifikation:** Langfuse-Trace pro Frage; Soll-Vergleich mit Belegen 239c209a, 8d44efa0, 9755a7ee.

---

### KI-261 — Standardisierung Typografie 16px

**Assignee:** Speckner, Christian (MF) · **Typ:** Story

**Schritte:** Live-UI öffnen, DevTools-Font-Size in Sidebar/Input/Modals; Resize-Test 320–1920 px.

**Testfragen:** Nicht zutreffend — UI-Test im Browser/DevTools. **Verifikations-Checkliste:**
- Sidebar-Menü: 16 px? ✓/✗
- Eingabe-Placeholder: 16 px? ✓/✗
- Optionen-Popup: 16 px? ✓/✗
- Disclaimer: kleiner als 16 px? ✓/✗
- Version: kleiner? ✓/✗
- Resize 320 px: keine Cut-offs? ✓/✗
- Resize 1920 px: kein zu großer Leerraum? ✓/✗

---

### KI-260 — Evaluierung POI-MCP-Schnitt

**Assignee:** unassigned · **Typ:** Subtask (faktisch Spike)

**Acceptance:** Lieferdokument mit Trennvorschlag + Pro/Contra.

**Testfragen:** Nicht zutreffend — Spike, kein User-Flow.

---

### KI-252 — SPIKE: Voice-Features

**Assignee:** unassigned · **Typ:** Story (Spike) · **Timebox:** 1 PT

**Acceptance:** Lieferdokument.
- Vergleich Web Speech API vs. Mayflower Voice-Stack.
- Empfehlung A oder B mit Zeitschätzung.
- Architekturskizze.

**Testfragen:** Nicht zutreffend — Spike.

---

### KI-248 — Web-Search-Fallback bei leeren internen Treffern

**Assignee:** unassigned · **Typ:** Story

**Schritte:**
1. Confluence-leer-Frage → Fallback.
2. Off-Topic → Refusal, kein Fallback-Missbrauch.
3. Trust-Liste-Test.

**Testfragen:**

*Confluence-leer / aktueller Web-Inhalt:*
- „Welche neuen Aktionen gibt es gerade auf europapark.de?"
- „Was steht heute prominent auf der Europa-Park-Startseite?"
- „Welche Stellenausschreibungen gibt es aktuell?" (jobs.europapark.de)

*MACK-Group / Trust-Liste:*
- „Was macht die Firma MACK Rides gerade?"
- „Wer hat den schnellsten Coaster der Welt?" (rcdb.com)
- „Welche Restaurants gehören zu Mack?" (eatrenalin, ammolite-restaurant)

*Off-Topic (Refusal-Test, KEIN web_search erwartet):*
- „Wer ist gerade Bundeskanzler?"
- „Wie steht der DAX?"
- „Wie wird das Wetter morgen in Berlin?"
- „Was ist die Hauptstadt von Frankreich?"

*Grenzfall:*
- „Welche Hotels in Rust außerhalb des Resorts gibt es?" (nicht Trust-Liste → entweder Refusal oder Hinweis auf interne Daten).

**Erwartet:**
- Confluence-leer-Pfad: Web-Search-Hinweis + Quellenlink.
- Off-Topic: Refusal, kein web_search im Trace.
- Trust-Liste-Pfad: Antwort mit Trust-Listen-Quelle.

**⚠️ Wechselwirkung** mit Pattern 4 (Off-Topic-Refusal-Lücke) — Off-Topic darf nicht aufgeweicht werden.

---

### KI-246 — VIP-Privacy für GF

**Assignee:** unassigned · **Typ:** Story

**Schritte:** GF-Account-Chat (Entra-Rolle für GF) → Langfuse-Suche → Negative Control mit Nicht-GF.

**Testfragen** (mit GF-Test-Account):
- „Hallo Ecki, was läuft heute?"
- „Wie ist die Urlaubsregelung?"
- „Erzeuge mir ein Bild von einem Karussell."
- *Mit Upload:* PDF anhängen + „Fasse das zusammen."
- *Mehrere Sessions:* Logout/Login, neue Session, weitere Frage.

**Erwartet:**
- Für GF-Session: **0 Einträge** in Langfuse (auch kein „Anonym/Unbekannt").
- Funktionalität für GF identisch.
- Token-Verbrauch nur aggregiert in GCP-Billing/STACKIT sichtbar.

**Verifikation:** Langfuse-Suche nach Session-ID + Zeitfenster → 0 Treffer. Negative Control (Nicht-GF) → Trace vorhanden.

---

### KI-235 — SPIKE: Kostenoptimierung durch liteLLM (Caching)

**Assignee:** unassigned · **Typ:** Story (Spike) · **Timebox:** 1 PT

**Acceptance:** Lieferdokument.

**Testfragen:** Nicht zutreffend — Spike.

---

### KI-193 — Öffentliche Tickets/Produkte zu Events

**Assignee:** unassigned · **Typ:** Story

**Schritte:** Produkt-Frage, Preis-Frage, Verfügbarkeit, Deep-Link.

**Testfragen:**
- „Welche Tickets gibt es für [Event im Sprintzeitraum]?"
- „Wieviel kostet die Jahreskarte?"
- „Was kostet ein Tagesticket für Erwachsene?"
- „Gibt es Familienpakete für das Sommerfest?"
- „Welche Hotel-Pakete kann ich aktuell buchen?"
- „Wo kann ich Tickets für Rulantica kaufen?"
- „Ist die Familienkarte für [Event] noch verfügbar?"
- „Was ist gerade ausverkauft?"
- „Wie kann ich [Event] buchen?" → Deep-Link erwartet.

**Erwartet:**
- Preis als Euro (29,00 €), nicht Cent.
- Status korrekt: ausverkauft / abgesagt / wenige verfügbar.
- Deep-Link funktioniert.

**Verifikation:** Vergleich mit `tickets.mackinternational.de` Produkt-Detail.

---

### KI-180 — Confluence Synthesizer

**Assignee:** unassigned · **Typ:** Subtask

- ⚠️ **Beschreibung leer im Ticket** — vor Acceptance konkretisieren lassen.

**Testfragen:** Erst nach AC-Klärung möglich.

---

### KI-172 — Dataset Synthesizer (Agent)

**Assignee:** Oppelt, Thomas (MF) · **Typ:** Subtask

**Acceptance:** Dev-Review.
- `eval fetch-traces` liefert vollständige Traces als JSON.
- `eval synthesize` erzeugt Items pro Kategorie (`opening_hours`, `poi_facts`, `confluence_search`), 3 Sprachen.
- Claude-Code-Agent read-only (Write/Edit blockiert).
- Structured Output gegen `DatasetItem` validiert.

**Testfragen:** Nicht zutreffend — CLI-Tool. **Stichprobe** auf generierten Output:
- 3 generierte Items pro Kategorie auf Plausibilität sichten.
- Sprachen-Mix prüfen (de/en/fr alle vertreten).
- Stichprobe ins Repo-Dataset einreihen → KI-152.

---

### KI-157 — Experiment-Runner

**Assignee:** Oppelt, Thomas (MF) · **Typ:** Story (faktisch Tech-Task)

**Acceptance:** Dev-Review.
- Komplettlauf gegen Dataset, Traces verknüpft, Pflicht-Metadata gesetzt, gewichteter Gesamtscore.

**Testfragen:** Nicht zutreffend — Run-Tool. **Verifikations-Run:**
- `eval run --dataset <name> --variant baseline` → Run im Langfuse-Dashboard sichtbar mit allen Scores.

---

### KI-153 — Evaluatoren aufsetzen (Wrapper)

**Assignee:** Oppelt, Thomas (MF) · **Typ:** Story (faktisch Tech-Task)

**Acceptance:** Dev-Review.
- Smoke-Run pro Evaluator gegen 5 Testfälle.
- Items mit leerem expected-Feld werden übersprungen.

**Testfragen:** Nicht zutreffend.

---

### KI-151 — Backtesting gegen Live-Negativ-Traces

**Assignee:** Oppelt, Thomas (MF) · **Typ:** Story (faktisch Tech-Task)

**Acceptance:** Dev-Review.
- Filter: Score ≤ 0 + Kommentar nicht-trivial.
- Re-Run gegen aktuelle Agent-Version.
- Bericht besser/unverändert/schlechter.

**Testfragen:** Nicht zutreffend — Re-Run-Tool. **Verifikation:**
- Bericht für Zeitraum 2026-05-06 bis 2026-05-13 (14 Negativ-Cases aus Live-Auswertung) generieren → Vergleich gegen aktuelle Version sichtbar.

---

### KI-40 — Confluence Attachments (PDF, Bilder, Excel)

**Assignee:** unassigned · **Typ:** Story

**Schritte:**
1. Test-Confluence-Seite mit Multi-Format-Attachments.
2. Frage pro Format.
3. Negative: ignorierte Formate.
4. ACL-Test.

**Testfragen** (nach Anlegen einer Test-Confluence-Seite mit Attachments):
- „Was steht im angehängten PDF auf der Seite [X]?"
- „Welcher Wert steht in der Excel-Tabelle in der Zeile [Y]?"
- „Was zeigt das Bild im Sales-Bereich (Datei [name].png)?"
- „Fasse die wichtigsten Punkte aus der Präsentation [name].pptx zusammen."
- „Was steht im DOCX [name]?"
- *Negative:* „Was ist im MP4-Video [name].mp4?" → Tool ignoriert / kein Treffer.
- *ACL:* mit User ohne Leseberechtigung dieselbe Frage → kein Treffer.

**Erwartet:**
- Inhalte korrekt extrahiert (Docling).
- Link zur Original-Datei in Antwort.
- Ignorierte Formate werden nicht aufgegriffen.

**Verifikation:** Dagster-Pipeline-Log, Object-Storage-Eintrag in STACKIT.

---

<a id="status-done"></a>
## Status: Done

### KI-145 — Bug: Feedback geben nach Stop

**Assignee:** Stocklassa, Eric (MF) · **Typ:** Bug

**Nachtest empfohlen:**

**Testfragen** (Antwort gezielt lang machen, um Stop sinnvoll zu treffen):
- „Plane mir einen kompletten Tag im Europa-Park mit allen Highlights, Pausen und Restaurantempfehlungen."
- „Erstelle einen 7-Tages-Reiseplan für eine Familie mit 2 Kindern (Park + Rulantica + Umgebung)."
- „Erkläre mir ausführlich, wie der Park entstanden ist."

Während der Generierung **Stop drücken** → Feedback-Buttons müssen sichtbar sein → 👎 + Kommentar abschicken → in Langfuse als Score-Eintrag verifizieren.

---

<a id="status-declined"></a>
## Status: Declined

### KI-232 — Sende-Icon (Goldener Zauberstab)

**Assignee:** Schempp, Michael (EP) · **Typ:** Story

- Nicht testen.

---

<a id="anhang"></a>
## Anhang — PO-Empfehlungen

**Vor Sprint-Review klären:**
- KI-224 + KI-180: AC fehlen → vor Acceptance einfordern.
- KI-261 / KI-256 / KI-259 / KI-237 / KI-234 / KI-231 / KI-225 / KI-141 / KI-193 / KI-167: AC stark technisch. Reformulierung aus User-Sicht empfohlen (siehe AC-Compliance-Check).
- KI-150/151/152/153/154/155/156/157/172/180/181/225 / KI-231 / KI-158: Typ-Wechsel „Story → Aufgabe" erwägen (User-Story-Regel sonst nicht anwendbar).

**Test-Reihenfolge im Sprint-Review (= Reihenfolge dieses Dokuments):**
1. **Ready for PO** (4): KI-259, KI-247, KI-221, KI-167 — sofort abnehmbar.
2. **In Review** (7): KI-254, KI-225, KI-224, KI-195, KI-158, KI-150, KI-141 — nach Code-Review-Freigabe.
3. **In Progress** (9): Preview-Tests sinnvoll für KI-256, KI-237, KI-234, KI-231.
4. **To Do** (14): nur Vorbereitung, finale Annahme nach Implementierung.
5. **Done** (1): KI-145 Nachtest.
6. **Declined** (1): KI-232 — überspringen.

**Hinweise zu den Testfragen:**
- Klar-PII in den Testfragen (KI-234) ist fiktiv — IBAN und Adresse aus Beispiel-Datenbanken, nicht von realen Personen.
- Zeitabhängige Testfragen (KI-265, KI-254) erfordern den richtigen Tagesabschnitt — alternativ Systemzeit manipulieren oder Trace-Replay verwenden.
- Live-Testfragen, die externe Tools auslösen (KI-248 web_search), erzeugen echte Anfragen — sparsam und mit Bedacht testen.
