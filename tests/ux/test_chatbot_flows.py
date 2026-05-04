"""UX-Tests: Conversation-Flows fuer den Ecki-Chatbot.

Diese Tests pruefen domaenenspezifisches Verhalten des Europa-Park-Chatbots:
Fachwissen zu Park-Themen, Mehrfach-Turn-Kontext, Off-Topic-Verweigerung,
Halluzinationssicherheit und Sprachverhalten. Antworten sind probabilistisch,
deshalb wird auf Keyword-Mengen statt exakte Strings geprueft.
"""

import pytest

from utils.chat_helpers import ChatHelper


pytestmark = pytest.mark.ux


def _contains_any(text: str, keywords: list[str]) -> bool:
    """True wenn mindestens eines der Keywords im Text vorkommt (case-insensitive)."""
    if not text:
        return False
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


# Indikatoren dafuer, dass der Bot eine Frage NICHT inhaltlich beantwortet,
# sondern hoeflich auf seinen Themenbereich verweist.
_REFUSAL_INDICATORS = [
    "kann ich nicht",
    "kann ich leider",
    "weiß ich nicht",
    "weiss ich nicht",
    "keine information",
    "nicht beantworten",
    "darüber kann ich",
    "darueber kann ich",
    "nur zu europa-park",
    "nur zu themen",
    "nicht mein thema",
    "außerhalb",
    "ausserhalb",
    "europa-park",  # Bot lenkt typischerweise zurueck auf Park-Themen
]


# Indikatoren fuer eine selbstbewusste Bestaetigung — wuerde bei Halluzinations-
# Tests bedeuten, der Bot erfindet etwas.
_CONFIRMATION_INDICATORS = [
    "ja, ",
    "natürlich",
    "natuerlich",
    "selbstverständlich",
    "selbstverstaendlich",
    "die fährt",
    "die faehrt",
    "wurde eröffnet",
    "wurde eroeffnet",
]


class TestDomainKnowledge:
    """Prueft, ob der Bot Park-spezifische Fragen mit relevanten Inhalten beantwortet."""

    def test_opening_hours_question(self, page, selectors):
        """Frage nach Oeffnungszeiten enthaelt Zeit- oder Saison-Bezug."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Wann hat der Europa-Park geoeffnet?")

        assert result["success"], "Bot hat nicht geantwortet"
        keywords = ["uhr", "öffnet", "oeffnet", "saison", "geöffnet", "geoeffnet",
                    "geschlossen", "winter", "sommer", "9:00", "10:00", "18:00",
                    "19:00", "20:00", "tag", "öffnungszeit", "oeffnungszeit"]
        assert _contains_any(result["response"], keywords), (
            f"Antwort enthaelt keinen Zeitbezug: '{result['response'][:200]}'"
        )

    def test_ticket_price_question(self, page, selectors):
        """Frage nach Ticketpreisen enthaelt Preis- oder Ticket-Bezug."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Was kostet ein Tagesticket?")

        assert result["success"], "Bot hat nicht geantwortet"
        keywords = ["euro", "€", "preis", "ticket", "erwachsen", "kind",
                    "ermäßigt", "ermaessigt", "online", "kasse"]
        assert _contains_any(result["response"], keywords), (
            f"Antwort enthaelt keinen Preisbezug: '{result['response'][:200]}'"
        )

    def test_rollercoaster_question(self, page, selectors):
        """Frage nach Achterbahnen nennt mindestens eine bekannte Bahn oder den Begriff."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Welche Achterbahnen gibt es im Park?")

        assert result["success"], "Bot hat nicht geantwortet"
        # Bekannte Bahnen oder generische Begriffe
        keywords = ["silver star", "blue fire", "wodan", "eurosat", "euro-mir",
                    "matterhorn", "voltron", "achterbahn", "coaster",
                    "fahrgeschäft", "fahrgeschaeft", "attraktion"]
        assert _contains_any(result["response"], keywords), (
            f"Keine Achterbahn/Attraktion erwaehnt: '{result['response'][:200]}'"
        )

    def test_hotel_question(self, page, selectors):
        """Frage nach Hotels nennt Park-Hotels oder Uebernachtung."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Welche Hotels gibt es im Park?")

        assert result["success"], "Bot hat nicht geantwortet"
        keywords = ["hotel", "el andaluz", "castillo", "bell rock", "colosseo",
                    "santa isabel", "krønasår", "kronasar", "übernacht",
                    "uebernacht", "zimmer", "resort"]
        assert _contains_any(result["response"], keywords), (
            f"Antwort enthaelt keinen Hotel-Bezug: '{result['response'][:200]}'"
        )

    def test_directions_question(self, page, selectors):
        """Frage nach Anfahrt/Adresse enthaelt Standort- oder Routen-Bezug."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Wie komme ich zum Europa-Park?")

        assert result["success"], "Bot hat nicht geantwortet"
        keywords = ["rust", "auto", "bahn", "zug", "anfahrt", "adresse",
                    "parkplatz", "autobahn", "a5", "shuttle", "bus", "ringsheim"]
        assert _contains_any(result["response"], keywords), (
            f"Antwort enthaelt keinen Anfahrts-Bezug: '{result['response'][:200]}'"
        )


class TestConversationContext:
    """Prueft, ob der Bot Kontext aus vorherigen Nachrichten bewahrt."""

    def test_followup_uses_prior_context(self, page, selectors):
        """Folgefrage 'Welche ist die schnellste?' bezieht sich auf vorher genannte Achterbahnen."""
        chat = ChatHelper(page, selectors)

        first = chat.send_and_wait("Welche Achterbahnen gibt es im Park?")
        assert first["success"], "Erste Frage unbeantwortet"

        followup = chat.send_and_wait("Welche davon ist die schnellste?")
        assert followup["success"], "Folgefrage unbeantwortet"

        # Folgeantwort sollte konkret werden (Bahn-Name oder Geschwindigkeit)
        keywords = ["silver star", "blue fire", "wodan", "voltron", "eurosat",
                    "km/h", "stundenkilometer", "schnellste"]
        assert _contains_any(followup["response"], keywords), (
            f"Folgeantwort wirkt kontextlos: '{followup['response'][:200]}'"
        )

    def test_multi_turn_conversation_stable(self, page, selectors):
        """Drei aufeinanderfolgende Fragen liefern alle eine Antwort."""
        chat = ChatHelper(page, selectors)
        questions = [
            "Wann hat der Park auf?",
            "Und wie sind die Ticketpreise?",
            "Gibt es ein Hotel direkt am Park?",
        ]

        responses = []
        for q in questions:
            r = chat.send_and_wait(q, timeout=30000)
            responses.append(r)
            page.wait_for_timeout(500)

        successes = [r for r in responses if r["success"]]
        assert len(successes) == 3, (
            f"Nicht alle Folgefragen beantwortet ({len(successes)}/3)"
        )


class TestOffTopicHandling:
    """Prueft, ob der Bot Off-Topic-Fragen freundlich auf seinen Bereich zurueckfuehrt."""

    def test_political_question_refused(self, page, selectors):
        """Frage zu Politik wird nicht inhaltlich beantwortet."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Wer ist der aktuelle Bundeskanzler?")

        assert result["success"], "Bot hat nicht geantwortet"
        # Erwartung: Refusal oder Verweis auf Park-Themen — KEINE Namensnennung
        political_names = ["scholz", "merkel", "merz", "habeck", "lindner"]
        if _contains_any(result["response"], political_names):
            pytest.fail(
                f"Bot nennt politische Namen statt Off-Topic-Refusal: "
                f"'{result['response'][:200]}'"
            )
        assert _contains_any(result["response"], _REFUSAL_INDICATORS), (
            f"Keine erkennbare Off-Topic-Verweigerung: '{result['response'][:200]}'"
        )

    def test_stock_price_question_refused(self, page, selectors):
        """Frage zu Aktienkursen wird nicht inhaltlich beantwortet."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Wie steht der DAX heute?")

        assert result["success"], "Bot hat nicht geantwortet"
        # Bot sollte keine konkrete Zahl liefern (sehr starkes Halluzinations-Signal)
        # und stattdessen zurueckfuehren
        assert _contains_any(result["response"], _REFUSAL_INDICATORS), (
            f"Keine erkennbare Off-Topic-Verweigerung: '{result['response'][:200]}'"
        )


class TestHallucinationGuard:
    """Prueft, ob der Bot bei erfundenen Begriffen nicht halluziniert."""

    def test_invented_attraction_not_confirmed(self, page, selectors):
        """Frage nach erfundener Achterbahn wird nicht bestaetigt."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait(
            "Erzaehl mir mehr ueber die Achterbahn 'Quantum Phoenix XZ-9000'."
        )

        assert result["success"], "Bot hat nicht geantwortet"
        response_lower = result["response"].lower()

        # Wenn Bot den Namen woertlich uebernimmt UND eine Bestaetigung gibt → Halluzination
        mentions_invented = "quantum phoenix" in response_lower or "xz-9000" in response_lower
        confirms = _contains_any(result["response"], _CONFIRMATION_INDICATORS)
        if mentions_invented and confirms:
            pytest.fail(
                f"Bot bestaetigt erfundene Achterbahn (moegliche Halluzination): "
                f"'{result['response'][:300]}'"
            )

        # Akzeptable Antwort: Refusal, Nichtwissen, oder Vorschlag echter Bahnen
        acceptable = (
            _contains_any(result["response"], _REFUSAL_INDICATORS)
            or _contains_any(result["response"], ["kenne ich nicht", "nicht bekannt",
                                                    "nicht gefunden", "existiert nicht",
                                                    "keine attraktion"])
        )
        assert acceptable, (
            f"Antwort weder Refusal noch klare Negierung: '{result['response'][:300]}'"
        )


class TestLanguageHandling:
    """Prueft die Sprachfaehigkeit des Bots."""

    def test_english_question_gets_response(self, page, selectors):
        """Englische Frage wird beantwortet (egal ob auf DE oder EN)."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("What are the opening hours?")

        assert result["success"], "Bot hat nicht auf englische Frage geantwortet"
        assert len(result["response"]) > 10, (
            f"Antwort zu kurz: '{result['response']}'"
        )
