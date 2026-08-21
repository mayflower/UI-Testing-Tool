"""UX-Tests: Gesprächsverläufe und Antwortqualität.

Fachliche Fragen und Sprachindikatoren kommen aus `config/prompts.yaml`
(Vorlage: `config/prompts.example.yaml`), nicht aus diesem Modul.
"""

import pytest

from utils.chat_helpers import ChatHelper
from tests.prompt_helpers import (
    case_or_skip,
    generic,
    require_indicators,
    value_or_skip,
)


pytestmark = pytest.mark.ux


class TestConversation:
    """Prüft grundlegende Gesprächsfähigkeiten des Chatbots."""

    def test_welcome_message_present(self, page, selectors):
        """Bot zeigt eine Begrüßungsnachricht an."""
        chat = ChatHelper(page, selectors)
        welcome = chat.get_welcome_message()
        assert welcome is not None, "Keine Begrüßungsnachricht vorhanden"
        assert len(welcome) > 0, "Begrüßungsnachricht ist leer"

    def test_welcome_message_language(self, page, selectors, prompts):
        """Begrüßungsnachricht ist in der erwarteten Sprache."""
        indicators = require_indicators(prompts, "greeting_language")

        chat = ChatHelper(page, selectors)
        welcome = chat.get_welcome_message()
        if not welcome:
            pytest.skip("Keine Begrüßungsnachricht vorhanden")

        welcome_lower = welcome.lower()
        matches = any(word.lower() in welcome_lower for word in indicators)
        assert matches, (
            f"Begrüßung enthält keinen der erwarteten Begriffe: '{welcome[:100]}'"
        )

    def test_simple_question(self, page, selectors, prompts):
        """Bot antwortet auf eine einfache Frage."""
        case = case_or_skip(prompts, "simple_question", "domain_knowledge")
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait(case["prompt"])

        assert result["success"], "Bot hat nicht geantwortet"
        assert len(result["response"]) > 10, (
            f"Antwort zu kurz: '{result['response']}'"
        )

    def test_greeting_response(self, page, selectors, prompts):
        """Bot reagiert freundlich auf eine Begrüßung."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait(generic(prompts, "greeting"))

        assert result["success"], "Bot hat nicht auf Begrüßung geantwortet"

    def test_followup_question(self, page, selectors, prompts):
        """Bot kann Folgefragen im Kontext beantworten."""
        first = value_or_skip(prompts, "context", "followup", "first")
        second = value_or_skip(prompts, "context", "followup", "second")

        chat = ChatHelper(page, selectors)

        result1 = chat.send_and_wait(first)
        assert result1["success"], "Bot hat auf erste Frage nicht geantwortet"

        result2 = chat.send_and_wait(second)
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
