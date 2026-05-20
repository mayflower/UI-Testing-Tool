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

**Abgedeckt:** 6 von 9 KI-259-Testfragen aus `docs/sprint9-acceptance.md`.
**Nicht abgedeckt:** Übersetzung EN/FR · Stress-Test 3-Tages-Aufenthalt · Tool-Routing „Voltron + Show".

**Außerhalb der Vergleichs-Session (Live, eigener Smoke-Test):**
- `67a39a2b30df4727bf34b0721c7f6ce2` 07:16:19, Session `8b19f55c-fd68-4e9b-ae8a-0e4ec45244f3` — Query „Erstelle mit eine Excell mit 9000 Datensätzen". Kein KI-259-Test.

---

## Lauf 2 — 2026-05-20, separate Chats nur zur 5-Tages-Tourplanung

Frage in beiden Umgebungen in jeweils neuer (leerer) Session gestellt.

| Umgebung | Modell | Zeit | Trace-ID | Session | Latenz | Obs |
|---|---|---|---|---|---|---|
| **Stage** | `vertex-ai/claude-sonnet-4-6` | 07:41:46 | `a5de3cfeca7e4929b9857db1ad076d7c` | `f3d0bd28-8730-4227-9146-7276beb46704` | **255 s** | 90 |
| **Live** | `vertex-ai/claude-sonnet-4-5` | 07:36:49 | `08b0b071133a450a8516c2befce0f682` | `e1e34544-db40-4d4c-a255-7a4226565dd7` | **189 s** | 39 |

**Weitere Live-Traces vom 2026-05-20 (kein langserve_agent-Top-Level, vermutlich Telemetrie):**
- `7db0b6e67d694e7ba2426db29e34a98f` 07:34:19, Session `f09be8c0-7728-43c9-9316-52b63472818f`, root-name `get_poi_info`, 89 s, 57 obs.
- ~78 zusätzliche Mikro-Traces (0,25–0,46 s, jeweils 2 obs) in derselben Session `f09be8c0…` zwischen 07:35:17 und 07:36:37. Vermutlich Stream- oder Polling-Events, keine Chat-Antworten.

---

## Beobachtungen

**Latenz-Regression auf Stage (4.6).** Im Lauf 1 war Stage in 5 von 6 Fragen langsamer als Live; die 5-Tages-Tour 3,5× langsamer (191 s vs. 54 s). AC „TTFT ≤ Baseline" aktuell verletzt.

**Tagessprung Live (4.5).** Die identische 5-Tages-Tour-Frage in leerer Session brauchte am 2026-05-20 auf Live 189 s — am 2026-05-19 nur 54 s (+250 %). Cache-/Last-Effekt nicht ausgeschlossen.

**Inhaltliche Auffälligkeit Frage 3 (Top-3-Wartezeiten).** Live antwortet, es lägen „keine Live-Wartezeitdaten" vor, obwohl beide Umgebungen über `get_poi_info` den gleichen Datenstand abfragen sollten. Inhaltlicher Stage-Live-Diff wert.

**Sessions wie erwartet.** Lauf 1 = je 1 zusammenhängende Session pro Umgebung mit 6 Folge-Turns (Kontextakkumulation). Lauf 2 = jede Umgebung in eigener neuer Session ohne History.

---

## Offene Punkte

- Inhaltlicher Diff Stage 4.6 vs. Live 4.5 für mind. die 5-Tages-Tour-Antwort (Tagesstruktur, Größenhinweise, Hotelempfehlung).
- Fehlende KI-259-Testfragen ergänzen (Übersetzung EN/FR, Stress-Test 3 Tage, Tool-Routing Voltron).
- Latenz-Messung wiederholen sobald 4.6 evtl. produktiv geht — heutiger Live-Sprung deutet auf Tagesvarianz hin, Baseline neu vermessen.
