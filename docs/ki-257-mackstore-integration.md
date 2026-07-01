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

### Testfälle aus dem Ticket

| # | Szenario | Beispiel-Frage | Soll-Verhalten |
|---|---|---|---|
| 1 | Verfügbares Produkt + Preis | „Was kostet ein Tagesticket für Erwachsene am 15.7., ist es verfügbar?" | korrekter Preis (Cent→€), „verfügbar" |
| 2 | Ausverkauft | „Gibt es noch Tickets für die Dinner-Show am Samstag?" | „ausverkauft" (kein Preis-Fake) |
| 3 | Storniert/abgesagt | „Kann ich noch Tickets für XYZ kaufen?" | „abgesagt", keine Verfügbarkeitsabfrage |
| 4 | Geringe Verfügbarkeit | „Sind für Rulantica am 10.9. noch Karten frei?" | „nur begrenzt verfügbar" (bei <20 %) |
| 5 | API-Timeout/Fehler | Preisfrage bei nicht erreichbarer Mackstore-API | „aktuell keine Auskunft möglich" statt Falschantwort |
| 6 | Mehrere Tarife | „Was kostet ein Ticket für 2 Erwachsene + 2 Kinder?" | Einzelpreise pro Kategorie, **keine** eigenmächtige Summe |
| 7 | Produkt nicht gefunden (404) | „Gibt es noch das Sonderticket XYZ?" | „nicht gefunden", verständlich |

### Besonders prüfen
1. **Aktualität** — mit echtem Ticketshop-Preis abgleichen (keine veralteten Werte).
2. **Cent→Euro** — Preise exakt (7600 → 76,00 €), keine krummen Rundungen.
3. **Keine erfundenen Preise/Summen** — Testfall 6: Ecki darf nicht selbst addieren.
4. **Fehlerfall ehrlich** — bei API-Ausfall keine halluzinierten Preise, Verweis auf Ticketshop.
5. **Sprache** — deutsche und englische Anfragen.

### Vorab klären
- Ist **PR #45 auf dev-1 bereits deployed**? (sonst wird der alte Stand getestet)
- Ist Lukas' **Flag/Architekturfrage** erledigt? (könnte erklären, warum „Ready for PO" evtl. noch nicht voll funktioniert)

> Hinweis aus dem Ticket: Reale Beispiele (z. B. tatsächlich ausverkaufte Events) sind je nach
> Saison schwer zu finden — im Zweifel echte `extId`-Beispiele bei Ben/Michael erfragen.
