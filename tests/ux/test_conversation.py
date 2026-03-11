"""UX-Tests: Gesprächsverläufe und Antwortqualität."""

import pytest

from utils.chat_helpers import ChatHelper


pytestmark = pytest.mark.ux


class TestConversation:
    """Prüft grundlegende Gesprächsfähigkeiten des Chatbots."""

    def test_welcome_message_present(self, page, selectors):
        """Bot zeigt eine Begrüßungsnachricht an."""
        chat = ChatHelper(page, selectors)
        welcome = chat.get_welcome_message()
        assert welcome is not None, "Keine Begrüßungsnachricht vorhanden"
        assert len(welcome) > 0, "Begrüßungsnachricht ist leer"

    def test_welcome_message_is_german(self, page, selectors):
        """Begrüßungsnachricht ist auf Deutsch."""
        chat = ChatHelper(page, selectors)
        welcome = chat.get_welcome_message()
        if not welcome:
            pytest.skip("Keine Begrüßungsnachricht vorhanden")

        # Einfache Heuristik: Deutsche Wörter in der Begrüßung
        german_indicators = [
            "willkommen", "hallo", "guten", "herzlich",
            "kann ich", "helfe", "fragen", "erlebnis",
            "danke", "bitte", "gerne",
        ]
        welcome_lower = welcome.lower()
        has_german = any(word in welcome_lower for word in german_indicators)
        assert has_german, (
            f"Begrüßung scheint nicht deutsch zu sein: '{welcome[:100]}'"
        )

    def test_simple_question(self, page, selectors):
        """Bot antwortet auf eine einfache Frage."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Was sind die Öffnungszeiten?")

        assert result["success"], "Bot hat nicht geantwortet"
        assert len(result["response"]) > 10, (
            f"Antwort zu kurz: '{result['response']}'"
        )

    def test_greeting_response(self, page, selectors):
        """Bot reagiert freundlich auf eine Begrüßung."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Hallo!")

        assert result["success"], "Bot hat nicht auf Begrüßung geantwortet"

    def test_followup_question(self, page, selectors):
        """Bot kann Folgefragen im Kontext beantworten."""
        chat = ChatHelper(page, selectors)

        # Erste Frage
        result1 = chat.send_and_wait("Welche Achterbahnen gibt es?")
        assert result1["success"], "Bot hat auf erste Frage nicht geantwortet"

        # Folgefrage
        result2 = chat.send_and_wait("Welche davon ist die schnellste?")
        assert result2["success"], "Bot hat auf Folgefrage nicht geantwortet"

    def test_input_field_clears_after_send(self, page, selectors):
        """Eingabefeld wird nach dem Senden geleert."""
        chat = ChatHelper(page, selectors)
        chat.send_message("Test-Nachricht")

        # Kurz warten
        page.wait_for_timeout(500)
        assert chat.is_input_empty(), "Eingabefeld wurde nach Senden nicht geleert"

    def test_input_placeholder_text(self, page, selectors):
        """Eingabefeld hat einen sinnvollen Platzhaltertext."""
        chat = ChatHelper(page, selectors)
        placeholder = chat.get_input_placeholder()

        if placeholder is None:
            pytest.skip("Kein Platzhaltertext vorhanden")

        assert len(placeholder) > 0, "Platzhaltertext ist leer"
