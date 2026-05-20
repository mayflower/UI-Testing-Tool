# KI-259 — Langfuse-Trace-Vergleich Stage vs. Live

**Ticket:** KI-259 — LLM-Modell-Upgrade Claude 4.6 Sonnet
**Assignee:** Schröder, Lukas (EP)
**Stand:** 2026-05-20
**User-ID (alle Traces):** `9827ee2a-af5a-4a10-b800-fde448242a98` (Mario)

## Setup

| Umgebung | Modell | Langfuse-Projekt |
|---|---|---|
| **Stage** | `vertex-ai/claude-sonnet-4-6` (Ziel) | `cmm257iev007sad07fbxck9js` |
| **Live (prod)** | `vertex-ai/claude-sonnet-4-5` (Baseline) | `cmn7bds3l0214ad07semveyli` |

Auf Live ist 4.5 produktiv — der Vergleich zeigt damit echte Baseline gegen das Stage-Upgrade.

---

## Lauf 1 — 2026-05-19, durchgängige Session (6 Testfragen)

**Stage-Session:** `3080c710-17b1-4359-b051-42d6f10dbda9`
**Live-Session:** `51306f1a-ec04-4b68-9ec5-ffb28eaccbc1`

| # | Testfrage | Stage-Trace (Sonnet 4.6) | Stage-Lat. | Live-Trace (Sonnet 4.5) | Live-Lat. |
|---|---|---|---|---|---|
| 1 | Wann ist heute die nächste Show…? | `851ade8dc1eb4abc864a0a67ce0289a8` | 59 s | `e742c7f62ffd4e3fbb7dae49c4ad48eb` | **14,5 s** |
| 2 | Sitzungsprotokoll 3 Spalten | `7170700e822f4a2f97d56893e982694c` | **8,4 s** | `a0f1dd889d9e454cbeee1336a04cd0c7` | 12,7 s |
| 3 | Top-3-Wartezeiten vergleichen | `040d7dc298284eda8f01fea1b7d381c0` | 52 s | `7c9d5c9b42864d119c4e973d22ed578f` | **13,8 s** |
| 4 | Hotels / Familie Kleinkinder | `85bf1ed7db91455a867a641298e6b9ac` | 74 s | `b623cdd2f2234190b8cd654a4c014158` | **49 s** |
| 5 | 5-Tages-Tourplanung 4 + 8 J. | `968e6394e2304df79083a8ec5a54b02c` | 191 s | `dfe032aaa64049de90aa1d7c51a18d94` | **54 s** |
| 6 | Confluence Urlaubsregelung | `b1825eb9178d4f7dafc346e053bd2bc6` | 30 s | `599f8aa837864d13b09e56348329db20` | **19,3 s** |

**Abgedeckt:** 6 von 9 KI-259-Testfragen aus `docs/sprint9-acceptance.md`. Restliche 3 in Lauf 3 nachgezogen.

### Tool-Calls Lauf 1

Top-Level = vom Hauptagent (langserve_agent) aufgerufen · Nested = in `get_poi_info`-Subagent zur POI-/Opentime-Auflösung.

| # | Frage | Stage Top-Level | Stage Nested | Live Top-Level | Live Nested |
|---|---|---|---|---|---|
| 1 | Show | `get_poi_info` ×1 | `execute_sql` ×1 | `get_poi_info` ×1 | `execute_sql` ×1 |
| 2 | Sitzungsprotokoll | — *(LLM antwortet direkt mit Markdown-Tabelle)* | — | `python_run_prepared` ×1 *(Excel-Datei)* | — |
| 3 | Wartezeiten | `get_poi_info` ×2 | `execute_sql` ×2 | `get_poi_info` ×1 | — |
| 4 | Hotels | `get_poi_info` ×3 | `execute_sql` ×7 | `get_poi_info` ×2 | `execute_sql` ×5 |
| 5 | 5-Tages-Tour | `get_poi_info` ×4 | `execute_sql` ×8, `get_today_opentime` ×1 | — *(LLM antwortet direkt aus Vorturn-Kontext)* | — |
| 6 | Confluence Urlaub | `search_confluence` ×3 | — | `search_confluence` ×3 | — |

**Außerhalb der Vergleichs-Session (Live, eigener Smoke-Test):**
- `67a39a2b30df4727bf34b0721c7f6ce2` 07:16:19, Session `8b19f55c-fd68-4e9b-ae8a-0e4ec45244f3` — Query „Erstelle mit eine Excell mit 9000 Datensätzen". Kein KI-259-Test.

---

## Lauf 2 — 2026-05-20, separate Chats nur zur 5-Tages-Tourplanung

Frage in beiden Umgebungen in jeweils neuer (leerer) Session gestellt.

| Umgebung | Modell | Zeit | Trace-ID | Session | Latenz | Obs |
|---|---|---|---|---|---|---|
| **Stage** | `vertex-ai/claude-sonnet-4-6` | 07:41:46 | `a5de3cfeca7e4929b9857db1ad076d7c` | `f3d0bd28-8730-4227-9146-7276beb46704` | **255 s** | 90 |
| **Live** | `vertex-ai/claude-sonnet-4-5` | 07:36:49 | `08b0b071133a450a8516c2befce0f682` | `e1e34544-db40-4d4c-a255-7a4226565dd7` | **189 s** | 39 |

### Tool-Calls Lauf 2

| Umgebung | Top-Level | Nested |
|---|---|---|
| **Stage 4.6** | `get_poi_info` ×6 | `execute_sql` ×10, `get_today_opentime` ×2 |
| **Live 4.5** | `get_poi_info` ×3 | `execute_sql` ×5, `get_future_opentime` ×3 |

**Weitere Live-Traces vom 2026-05-20 (kein langserve_agent-Top-Level, vermutlich Telemetrie):**
- `7db0b6e67d694e7ba2426db29e34a98f` 07:34:19, Session `f09be8c0-7728-43c9-9316-52b63472818f`, root-name `get_poi_info`, 89 s, 57 obs.
- ~78 zusätzliche Mikro-Traces (0,25–0,46 s, jeweils 2 obs) in derselben Session `f09be8c0…` zwischen 07:35:17 und 07:36:37. Vermutlich Stream- oder Polling-Events, keine Chat-Antworten.

---

## Lauf 3 — 2026-05-20 vormittags, restliche 3 KI-259-Testfragen

Schröder hat die fehlenden Fragen 7, 8, 9 ergänzt. Frage 7 und 8a in der bestehenden Lauf-1-Session (mit Vorkontext), Frage 8b zusätzlich in leerer Session, Frage 9 wieder leer.

| # | Testfrage | Session | Stage-Trace (Sonnet 4.6) | Stage-Lat. | Live-Trace (Sonnet 4.5) | Live-Lat. |
|---|---|---|---|---|---|---|
| 7 | Übersetze letzte Antwort EN + FR | Lauf-1-Session fortgesetzt | `c7b964afc9874c0392ea5f7ab3e9e6e7` | 15,3 s | `e0a40379a05e404aacf2dc8ec8b843e6` | **14,8 s** |
| 8a | Stress-Test 3-Tages-Aufenthalt | Lauf-1-Session fortgesetzt | `71d7202f90d54d899d4977f32006d023` | 250 s | `1da2cbe13c66429dbb71b98d37b94698` | **103 s** |
| 8b | 3-Tages-Aufenthalt (ohne „Stress-Test"-Präfix) | jeweils neue, leere Session | `80034771d2da45d588a2aecb58eac60d` | 248 s | `9f3682ccb6624ff2ad773f23f6b99a46` | **172 s** |
| 9 | Voltron Wartezeit + Show *(Tool-Routing-Test)* | jeweils neue, leere Session | `5cf7959f368345b9aec47a1221c64c9e` | 41,6 s | `cba768df394f477d9bae60653457aec2` | **33,9 s** |

**Sessions:**
- Stage 8b: `79319c5a-fae3-4570-a861-0a9ee60575d2` · Live 8b: `41cbd7fe-bfec-4a38-a9dd-c9f9eda35ffe`
- Stage 9: `7e59eadb-6a17-4627-947c-e23241c85bf8` · Live 9: `71f380ae-7e4b-4736-b10c-572865bfa6b0`

### Tool-Calls Lauf 3

| # | Frage | Stage Top-Level | Stage Nested | Live Top-Level | Live Nested |
|---|---|---|---|---|---|
| 7 | Übersetzung | — *(LLM direkt)* | — | — *(LLM direkt)* | — |
| 8a | 3-Tage (Session) | `get_poi_info` ×4, `web_search` ×2, `web_fetch` ×1 | `execute_sql` ×6, `get_today_opentime` ×2 | — *(LLM direkt aus Vorturn-Kontext)* | — |
| 8b | 3-Tage (neue Session) | `get_poi_info` ×6, `web_search` ×2 | `execute_sql` ×11, `get_today_opentime` ×4 | `get_poi_info` ×4 | `execute_sql` ×6, `get_today_opentime` ×1 |
| 9 | Voltron + Show | `get_poi_info` ×2 | `execute_sql` ×2 | `get_poi_info` ×2 | `execute_sql` ×2 |

---

## Beobachtungen

**Latenz-Regression auf Stage (4.6).** Im Lauf 1 war Stage in 5 von 6 Fragen langsamer als Live; die 5-Tages-Tour 3,5× langsamer (191 s vs. 54 s). AC „TTFT ≤ Baseline" aktuell verletzt.

**Tagessprung Live (4.5).** Die identische 5-Tages-Tour-Frage in leerer Session brauchte am 2026-05-20 auf Live 189 s — am 2026-05-19 nur 54 s (+250 %). Cache-/Last-Effekt nicht ausgeschlossen.

**Inhaltliche Auffälligkeit Frage 3 (Top-3-Wartezeiten).** Live antwortet, es lägen „keine Live-Wartezeitdaten" vor, obwohl beide Umgebungen über `get_poi_info` den gleichen Datenstand abfragen sollten. Inhaltlicher Stage-Live-Diff wert.

**Sessions wie erwartet.** Lauf 1 = je 1 zusammenhängende Session pro Umgebung mit 6 Folge-Turns (Kontextakkumulation). Lauf 2 = jede Umgebung in eigener neuer Session ohne History.

**Tool-Use-Divergenz Frage 2 (Sitzungsprotokoll).** Stage 4.6 generiert eine Markdown-Tabelle direkt im LLM-Output (kein Tool); Live 4.5 ruft `python_run_prepared` auf und erzeugt eine Excel-Datei. Unterschiedliche Interpretation derselben Frage — relevant für AC „Tool-Use unverändert funktional".

**Tool-Use-Divergenz Frage 5 (5-Tages-Tour, Lauf 1).** Stage 4.6 ruft 4× `get_poi_info` auf (mit 8 nested SQL-Calls), Live 4.5 ruft KEIN POI-Tool und antwortet aus dem Vorturn-Kontext (Hotel-/POI-Daten aus den vorhergehenden 4 Fragen schon im Context). Das ist eine wesentliche Ursache für den 3,5× Latenz-Unterschied — und zeigt: das 4.6-Modell traut dem Vorwissen weniger und verifiziert nochmal. Auf Stage werden bei der gleichen Frage in leerer Session (Lauf 2) 6× POI-Calls gemacht.

**Tool-Use Frage 6 (Confluence).** Beide Modelle wählen `search_confluence` 3× — vermutlich, weil die DB schlechte Treffer liefert und das LLM nachhakt. Identisches Routing; Stage trotzdem 30 s vs. Live 19 s.

**Frage 7 (Übersetzung EN+FR).** Beide Modelle übersetzen rein im LLM ohne Tool-Calls. Latenz quasi identisch (Stage 15,3 s vs. Live 14,8 s) — sauberer Vergleichspunkt für „pure Generation, kein Tool-Overhead". Kein Indikator für Modellunterschiede in dieser Aufgabe.

**Frage 8 (Stress-Test, doppelt gestellt).** In der akkumulierten Session (8a) verlässt sich Live 4.5 voll auf den Vorturn-Kontext und antwortet **ohne jeden Tool-Call in 103 s**, während Stage 4.6 trotz reichlich Kontext aktiv `get_poi_info` ×4, `web_search` ×2 und sogar `web_fetch` ×1 ausführt (250 s). In leerer Session (8b) rufen beide Tools auf, Stage aber 6× POI + 2× Web vs. Live 4× POI ohne Web → Stage verifiziert insgesamt deutlich häufiger. **Stage 4.6 ist tool-aktiver, Live 4.5 vertraut Kontext stärker** — direkte Folge: höhere Latenz auf Stage, aber potentiell aktuellere Daten.

**Frage 9 (Voltron + Show, Tool-Routing).** Beide Modelle wählen identisch `get_poi_info` ×2 (eine Abfrage für Wartezeit, eine für Show). Routing-Test bestanden auf beiden. Latenz Stage 41,6 s vs. Live 33,9 s (+23 %). Inhaltlich wahrscheinlich derselbe „keine Live-Wartezeiten"-Disclaimer wie bei Frage 3 — Diff prüfen.

---

## Offene Punkte

- Inhaltlicher Diff Stage 4.6 vs. Live 4.5 für mind. die 5-Tages-Tour-Antwort (Tagesstruktur, Größenhinweise, Hotelempfehlung) sowie den Stress-Test 3-Tages-Aufenthalt.
- Voltron-Antworten inhaltlich vergleichen: liefert Stage 4.6 trotz „keine Live-Wartezeiten"-Pattern bessere Show-Info?
- Latenz-Messung wiederholen sobald 4.6 evtl. produktiv geht — heutiger Live-Sprung deutet auf Tagesvarianz hin, Baseline neu vermessen.
- Trade-off bewerten: Stage 4.6 deutlich höhere Tool-Aktivität (= aktuellere Daten, höhere Latenz, höhere Kosten) vs. Live 4.5 stärker kontextverlasse (= schneller, günstiger, Risiko veralteter Aussagen).
