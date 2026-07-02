# KI-257 — Mackstore API-Integration für Online-Produktverfügbarkeit & Preise

- **Jira:** [KI-257](https://atlassian.europapark.de/jirasw/browse/KI-257)
- **Status:** Ready for PO · **Typ:** Story · **Sprint 12** (aktiv)
- **Reporter:** Michael Schempp · **Assignee:** –
- **Blockiert durch:** KI-193 (DS1-API-Abfrage) — Done
- **PR:** [ep-services #45](https://bitbucket.org/europapark/ep-services/pull-requests/45) — testbar auf **dev-1**

## Worum geht's

Ecki soll auf Fragen nach **Online-Ticketshop-Produkten** (Tickets, Events) mit **aktuellen
Preisen und Verfügbarkeiten** antworten. Die Daten werden **live** aus zwei APIs gezogen:

- **DS1 Product API** → Produkt-Stammdaten (Name, Beschreibung, `enabled`, `soldout`, `canceled`),
  liefert die `extId`.
- **Mackstore API** → Verfügbarkeit + Preise. Die `extId` wird als `productId` weiterverwendet,
  `bookingLocation=Online`. Preise kommen in **Cent** (7600 = 76,00 €).

### Kernregeln
- Preise/Verfügbarkeit **immer live**, kein Caching (Kontingente ändern sich in Verkaufsphasen schnell).
- Nur Produkte mit `mackStoreProduct: true` verarbeiten.
- Tarifkategorien (Erwachsen/Kind/Senior…) korrekt unterscheiden.
- **Ecki darf nicht selbst rechnen** (keine LLM-„Schätzungen" von Summen), außer über einen dedizierten Skill.
- Bei API-Timeout > 5 s / Fehler: klar kommunizieren, dass keine Live-Aussage möglich ist
  (Graceful Degradation: DS1-Daten ggf. trotzdem zeigen).

### Out of Scope
Kein Kauf/Warenkorb/Checkout, keine Buchung/Reservierung, keine Schreiboperationen auf Mackstore.

## Status-Hinweise (aus Kommentaren)
- ⚠️ **Lukas (26.05.):** Story geflaggt — „Braucht Domänenüberblick und architektonische
  Entscheidung, wie wir MCP-Server schneiden." Vor dem Test klären, ob erledigt.
- **Ben (25.06.):** PR #45 liegt vor, testbar auf dev-1.

## Wie testen

**Umgebung:** dev-1. Beispielfragen von Ben:

- „Was kostet aktuell eine Europa-Park Tageskarte?"
- „Welche Tageskarten gibt es und was kosten sie?"
- „Ist Rulantica am kommenden Samstag geöffnet und was kosten die Tickets?"
- „Was kostet ein Mondflug-Ticket?"
- „How much is a Europa-Park day ticket?" (Englisch → Mehrsprachigkeit)

### Überblick Testfälle

| # | Szenario | Beispiel-Frage | Soll-Verhalten |
|---|---|---|---|
| 1 | Verfügbares Produkt + Preis | „Was kostet ein Tagesticket für Erwachsene am 15.7., ist es verfügbar?" | korrekter Preis (Cent→€), „verfügbar" |
| 2 | Ausverkauft | „Gibt es noch Tickets für die Dinner-Show am Samstag?" | „ausverkauft" (kein Preis-Fake) |
| 3 | Storniert/abgesagt | „Kann ich noch Tickets für XYZ kaufen?" | „abgesagt", keine Verfügbarkeitsabfrage |
| 4 | Geringe Verfügbarkeit | „Sind für Rulantica am 10.9. noch Karten frei?" | „nur begrenzt verfügbar" (bei <20 %) |
| 5 | API-Timeout/Fehler | Preisfrage bei nicht erreichbarer Mackstore-API | „aktuell keine Auskunft möglich" statt Falschantwort |
| 6 | Mehrere Tarife | „Was kostet ein Ticket für 2 Erwachsene + 2 Kinder?" | Einzelpreise pro Kategorie, **keine** eigenmächtige Summe |
| 7 | Produkt nicht gefunden (404) | „Gibt es noch das Sonderticket XYZ?" | „nicht gefunden", verständlich |

## Testvorbereitung (einmalig, vor allen Fällen)

Der Kern jeder Prüfung ist ein **Ground-Truth-Abgleich**: Wir müssen die *korrekte* Antwort
unabhängig von Ecki kennen, sonst testen wir gegen eine Vermutung. Drei Quellen:

1. **Offizieller Ticketshop** (`ticketshop.europapark.de`) — Referenz für Preise/Verfügbarkeit aus
   Endkundensicht. Für jeden Testfall vorab die tatsächliche Zahl notieren (mit Zeitstempel, da live).
2. **DS1 Product API & Mackstore API direkt** — für `extId`/`productId`, `soldout`/`canceled`-Flags
   und Preise. Konkrete Endpunkte + valide `extId`-Beispiele bei **Ben/Michael**
   erfragen (Ticket-Hinweis: reale Sonderfälle sind saisonabhängig schwer zu finden).
   > **Beobachtung (Stage 02.07.):** `get_product_availability` liefert `min_euro_prices`/
   > `max_euro_prices` bereits **in Euro** (z. B. `Adult: 76`); die Cent-Liste `prices` war leer
   > (`prices: []`, `contingents: []`). Der im Ticket genannte „Cent"-Wert (7600 → 76,00 €) ist
   > also nicht garantiert der Pfad, über den der Preis in die Antwort kommt — siehe Cent→Euro unten.
3. **Langfuse (live)** — zum Nachweis, *wie* Ecki zur Antwort kam. Über den Langfuse-MCP den Trace
   der Testfrage öffnen und die Tool-/Skill-Spans prüfen:
   - Wurde der Mackstore-Skill überhaupt aufgerufen? (sonst hat das LLM geraten)
   - Stimmt der Aufrufparameter: `get_product_availability` nimmt **nur `ext_id`** entgegen
     (die DS1-`extId`, die zugleich die Mackstore-`productId` ist). Ein Parameter
     `bookingLocation` existiert im Tool-Vertrag **nicht** — hier nichts erwarten (verifiziert
     am Stage-Trace `e074e1a0…`, 02.07.2026).
   - Kam die Antwort *nach* dem Tool-Span (Daten genutzt) oder *davor* (halluziniert)?

**Datenmatrix anlegen:** Vor der Session pro Fall eine Zeile mit *erwartetem* Wert (aus Quelle 1/2)
festhalten. Ecki-Antwort daneben, Abweichung markieren. Ergebnis später als
`docs/sprintXX-acceptance.md` dokumentieren (analog zu bestehenden Acceptance-Files).

**Reproduzierbarkeit:** Preise sind live und können sich zwischen „Soll notieren" und „Ecki fragen"
ändern. Daher Ground-Truth **unmittelbar vor** der Ecki-Frage ziehen (Minuten, nicht Stunden).

## Detaillierte Testdurchführung

### Testfall 1 — Verfügbares Produkt + Preis
- **Ziel:** Happy Path — Ecki gibt für ein buchbares Produkt korrekten Live-Preis und Verfügbarkeit.
- **Vorbedingung:** Produkt mit `mackStoreProduct: true`, `enabled`, nicht `soldout`/`canceled`.
  Preis + „verfügbar" vorab aus Ticketshop/Mackstore notieren.
- **Schritte:** Frage stellen („Was kostet ein Tagesticket für Erwachsene am 15.7., ist es verfügbar?").
- **So am besten prüfen:** Ecki-Preis 1:1 mit Ticketshop vergleichen; im Langfuse-Trace verifizieren,
  dass der Skill mit korrektem `ext_id` aufgerufen wurde und der genannte Preis exakt dem
  API-Rückgabewert entspricht (i. d. R. direkt `min_euro_prices`/`max_euro_prices` in Euro; nur wenn
  `prices` befüllt ist, greift die Cent/100-Umrechnung).
- **Soll:** korrekter Preis in €, Aussage „verfügbar".
- **Fallstricke:** LLM nennt einen plausiblen, aber veralteten „Erinnerungspreis" ohne Tool-Aufruf →
  nur über den Trace erkennbar, nicht an der Antwort allein.
- **✅ Verifiziert (Stage 02.07.2026, Trace `e074e1a0…`):** Frage „Tagesticket Erwachsene 15.7.,
  verfügbar?" → echte `search_products`- + `get_product_availability`-Calls (`ext_id "111"`),
  `status: available`, Antwort **76,00 € Erwachsene / 65,00 € Kind/Senior**, „✅ Verfügbar", keine
  Halluzination, kein ERROR. Ground-Truth Mack-Ticketshop (flexibles/Gutschein-Tagesticket):
  Erwachsene 76,00 €, Kind 65,00 €, Senior 65,00 € — **exakte Übereinstimmung → PASS**.

### Testfall 2 — Ausverkauft
- **Ziel:** Bei `soldout` sagt Ecki ehrlich „ausverkauft" statt einen Preis zu erfinden.
- **Vorbedingung:** Ein real ausverkauftes Produkt (`soldout: true`). Ggf. echte `extId` bei
  Ben/Michael erfragen — saisonabhängig schwer zu finden.
- **Schritte:** „Gibt es noch Tickets für die Dinner-Show am Samstag?"
- **So am besten prüfen:** Antwort darf **keinen** Kaufpreis als Angebot nennen; Flag `soldout` im
  API-Rückgabewert (Quelle 2) gegen die Aussage prüfen.
- **Soll:** klare „ausverkauft"-Aussage, kein Preis-Fake, ggf. Verweis auf Ticketshop.
- **Fallstricke:** Ecki nennt trotzdem den (letzten bekannten) Preis „falls wieder verfügbar" — als
  Abweichung werten und dokumentieren.

### Testfall 3 — Storniert / abgesagt
- **Ziel:** Bei `canceled` keine Verfügbarkeits-/Preisabfrage, sondern „abgesagt".
- **Vorbedingung:** Produkt mit `canceled: true` (Beispiel bei Ben/Michael erfragen).
- **Schritte:** „Kann ich noch Tickets für <abgesagtes Event> kaufen?"
- **So am besten prüfen:** Im Trace prüfen, dass **keine** (oder eine als abgesagt erkannte)
  Mackstore-Verfügbarkeitsabfrage erfolgt — die `canceled`-Info kommt bereits aus DS1.
- **Soll:** „abgesagt", verständlich formuliert, kein Kaufangebot.
- **Fallstricke:** Verwechslung „abgesagt" (canceled) vs. „ausverkauft" (soldout) — beide Fälle
  bewusst getrennt testen, Wording unterscheiden.

### Testfall 4 — Geringe Verfügbarkeit (<20 %)
- **Ziel:** Bei niedrigem Restkontingent kommuniziert Ecki „nur begrenzt verfügbar".
- **Vorbedingung:** Produkt/Datum mit Restkontingent unter der Schwelle. Schwelle (20 %?) mit Ben
  bestätigen — *Regel im Code prüfen, nicht raten.* Kontingentwert aus Mackstore notieren.
- **Schritte:** „Sind für Rulantica am 10.9. noch Karten frei?"
- **So am besten prüfen:** Aus dem Mackstore-Kontingent selbst den Prozentsatz berechnen und gegen die
  Schwelle halten; prüfen, ob die Formulierung ober-/unterhalb der Grenze umschlägt (Randwert-Test:
  knapp über und knapp unter 20 %, falls Datenlage es erlaubt).
- **Soll:** Hinweis „nur begrenzt verfügbar" unterhalb der Schwelle, normale Aussage darüber.
- **Fallstricke:** Schwellenwert eventuell nicht implementiert/anders → dann als offene Frage statt
  als Bug dokumentieren.

### Testfall 5 — API-Timeout / Fehler (Graceful Degradation)
- **Ziel:** Bei nicht erreichbarer/timeout (>5 s) Mackstore-API keine halluzinierten Preise, sondern
  ehrlicher Hinweis; DS1-Basisdaten dürfen trotzdem gezeigt werden.
- **Vorbedingung:** Mackstore-API muss gezielt zum Fehler gebracht werden. **DevTools-Offline ist
  unzuverlässig** (Ecki antwortet trotzdem) — den Fehler serverseitig provozieren:
  Backend/Ben bitten, den Mackstore-Endpunkt auf dev-1 kurzzeitig auf eine ungültige URL zu
  zeigen / zu blocken, oder eine `productId` verwenden, die garantiert einen Fehler wirft.
- **Schritte:** Preisfrage stellen, während Mackstore nicht erreichbar ist.
- **So am besten prüfen:** Im Trace muss der Tool-Span einen Fehler/Timeout zeigen **und** die
  Endantwort darf keinen Preis enthalten. Prüfen, ob DS1-Daten (Name/Beschreibung) trotzdem kommen.
- **Soll:** „aktuell keine Auskunft möglich" + Verweis auf Ticketshop; kein erfundener Preis.
- **Fallstricke:** Schwer reproduzierbar; Fehlerinjektion mit Backend abstimmen und den Zeitpunkt
  exakt notieren, damit der richtige Trace gefunden wird.

### Testfall 6 — Mehrere Tarife (keine eigenmächtige Summe)
- **Ziel:** Ecki nennt Einzelpreise pro Tarifkategorie, **rechnet aber nicht selbst** die Summe
  (außer über den dedizierten Rechen-Skill).
- **Vorbedingung:** Produkt mit mehreren Tarifkategorien (Erwachsen/Kind/Senior).
- **Schritte:** „Was kostet ein Ticket für 2 Erwachsene + 2 Kinder?"
- **So am besten prüfen:** Das ist der **wichtigste Trace-Check**. Wenn Ecki eine Gesamtsumme nennt,
  im Trace verifizieren, dass diese aus dem dedizierten Skill stammt und **nicht** vom LLM
  „ausgerechnet" wurde (kein Additions-Token in der Generation ohne vorherigen Skill-Aufruf).
  Einzelpreise gegen Mackstore-Kategoriepreise abgleichen.
- **Soll:** korrekte Einzelpreise je Kategorie; Summe nur wenn über Skill belegt.
- **Fallstricke:** Antwort *sieht* korrekt aus, Summe wurde aber vom LLM geschätzt — nur am Trace
  erkennbar. Bewusst auch krumme Kombinationen fragen, bei denen ein LLM sich leicht verrechnet.

### Testfall 7 — Produkt nicht gefunden (404)
- **Ziel:** Bei unbekanntem Produkt verständliches „nicht gefunden" statt technischem Fehler/Halluzination.
- **Vorbedingung:** Nach einem nicht existierenden Produkt/`extId` fragen.
- **Schritte:** „Gibt es noch das Sonderticket XYZ?" (XYZ existiert nicht).
- **So am besten prüfen:** Im Trace 404 vom Lookup verifizieren; Antwort darf keinen erfundenen Preis
  und keine rohe Fehlermeldung/Stacktrace enthalten.
- **Soll:** freundliches „nicht gefunden", ggf. Rückfrage/Alternative.
- **Fallstricke:** Ecki „errät" ein ähnliches existierendes Produkt und beantwortet *das* — als
  Abweichung werten (falsche Produktzuordnung).

### Querschnitt — in jedem Fall mitprüfen
1. **Aktualität** — Preis exakt gegen den *jetzigen* Ticketshop-Wert, keine veralteten Werte.
2. **Cent→Euro** — nur relevant, wenn die API tatsächlich Cent liefert. Auf Stage kam der Preis über
   `min_euro_prices`/`max_euro_prices` bereits **in Euro** (keine Umrechnung nötig). Die Cent-Liste
   `prices` war leer. Für einen echten Cent/100-Test daher gezielt ein Produkt suchen, das `prices`
   in Cent befüllt — sonst prüft man einen Pfad, der gar nicht ausgeübt wird. Format immer sauber
   (z. B. 76,00 €), keine krummen Rundungen.
3. **Keine erfundenen Preise/Summen** — v. a. Fall 6; Trace-basiert belegen.
4. **Fehlerfall ehrlich** — Fall 5; bei Ausfall kein halluzinierter Preis, Verweis auf Ticketshop.
5. **Sprache** — jeden relevanten Fall zusätzlich auf **Englisch** stellen (Beispiel-Frage von Ben),
   prüfen dass Zahlen/Verfügbarkeit identisch bleiben und nur die Sprache wechselt.

### Vorab klären
- Ist **PR #45 auf dev-1 bereits deployed**? (sonst wird der alte Stand getestet)
- Ist Lukas' **Flag/Architekturfrage** erledigt? (könnte erklären, warum „Ready for PO" evtl. noch nicht voll funktioniert)
- **Schwellenwert Testfall 4** (geringe Verfügbarkeit) und **Timeout-Grenze Testfall 5** (>5 s) im Code/mit Ben bestätigen.

> Hinweis aus dem Ticket: Reale Beispiele (z. B. tatsächlich ausverkaufte Events) sind je nach
> Saison schwer zu finden — im Zweifel echte `extId`-Beispiele bei Ben/Michael erfragen.
