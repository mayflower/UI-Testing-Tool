"""UX-Tests: Antwortzeiten und Performance."""

import pytest

from utils.chat_helpers import ChatHelper
from config.settings import RESPONSE_TIMEOUT


pytestmark = pytest.mark.ux

# Schwellenwerte für Antwortzeiten (in ms)
FAST_THRESHOLD = 10000       # Schnell: unter 10 Sekunden
ACCEPTABLE_THRESHOLD = 15000  # Akzeptabel: unter 15 Sekunden
MAX_THRESHOLD = 30000        # Maximum: unter 30 Sekunden


class TestResponseTime:
    """Prüft Antwortzeiten des Chatbots."""

    def test_simple_question_response_time(self, page, selectors):
        """Einfache Frage wird in akzeptabler Zeit beantwortet."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait(
            "Wie sind die Öffnungszeiten?",
            timeout=MAX_THRESHOLD,
        )

        assert result["success"], "Bot hat nicht innerhalb des Timeouts geantwortet"
        assert result["response_time_ms"] < ACCEPTABLE_THRESHOLD, (
            f"Antwortzeit zu lang: {result['response_time_ms']}ms "
            f"(max. {ACCEPTABLE_THRESHOLD}ms)"
        )

    def test_greeting_response_time(self, page, selectors):
        """Begrüßung wird schnell beantwortet."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Hallo!", timeout=MAX_THRESHOLD)

        assert result["success"], "Bot hat auf Begrüßung nicht geantwortet"
        assert result["response_time_ms"] < FAST_THRESHOLD, (
            f"Begrüßung zu langsam: {result['response_time_ms']}ms "
            f"(max. {FAST_THRESHOLD}ms)"
        )

    def test_complex_question_response_time(self, page, selectors):
        """Komplexe Frage wird in maximal 10 Sekunden beantwortet."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait(
            "Welche Achterbahnen gibt es und welche davon ist für Kinder unter 8 geeignet?",
            timeout=MAX_THRESHOLD,
        )

        assert result["success"], (
            f"Bot hat auf komplexe Frage nicht innerhalb von "
            f"{MAX_THRESHOLD}ms geantwortet"
        )

    def test_multiple_questions_average_time(self, page, selectors):
        """Durchschnittliche Antwortzeit über mehrere Fragen."""
        chat = ChatHelper(page, selectors)
        questions = [
            "Wo kann ich parken?",
            "Was kostet der Eintritt?",
            "Gibt es ein Hotel?",
        ]

        times = []
        for question in questions:
            result = chat.send_and_wait(question, timeout=MAX_THRESHOLD)
            if result["success"]:
                times.append(result["response_time_ms"])
            page.wait_for_timeout(500)  # Kleine Pause zwischen Fragen

        assert len(times) > 0, "Keine der Fragen wurde beantwortet"

        avg_time = sum(times) / len(times)
        assert avg_time < ACCEPTABLE_THRESHOLD, (
            f"Durchschnittliche Antwortzeit zu lang: {avg_time:.0f}ms "
            f"(max. {ACCEPTABLE_THRESHOLD}ms). "
            f"Einzelne Zeiten: {times}"
        )

    def test_page_load_time(self, page, environment):
        """Seitenladezeit ist akzeptabel."""
        import time

        start = time.time()
        page.goto(environment["url"], wait_until="networkidle")
        load_time = (time.time() - start) * 1000

        assert load_time < 10000, (
            f"Seitenladezeit zu lang: {load_time:.0f}ms (max. 10s)"
        )
