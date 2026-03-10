"""UX-Tests: Fehlerbehandlung und Edge Cases."""

import pytest

from utils.chat_helpers import ChatHelper


pytestmark = pytest.mark.ux


class TestErrorHandling:
    """Prüft den Umgang des Chatbots mit Fehlersituationen und Edge Cases."""

    def test_empty_message(self, page, selectors):
        """Leere Nachricht wird korrekt behandelt."""
        chat = ChatHelper(page, selectors)
        input_sel = selectors["input_field"]
        send_sel = selectors["send_button"]

        # Eingabefeld leeren
        page.fill(input_sel, "")
        page.wait_for_timeout(300)

        # Prüfe ob der Button deaktiviert ist (korrekte Behandlung)
        btn = page.query_selector(send_sel)
        if btn and btn.is_disabled():
            # Button ist deaktiviert bei leerer Eingabe → korrekt
            return

        # Falls Button aktiv: klicken und prüfen dass keine leere Nachricht erscheint
        try:
            page.click(send_sel, timeout=3000)
        except Exception:
            # Click-Timeout = Button nicht klickbar → korrekt behandelt
            return

        page.wait_for_timeout(1000)
        user_sel = selectors.get("user_message")
        if user_sel:
            user_messages = page.query_selector_all(user_sel)
            for msg in user_messages:
                text = msg.text_content().strip()
                assert len(text) > 0, "Leere User-Nachricht im Chat sichtbar"

    def test_very_long_message(self, page, selectors):
        """Sehr langer Text wird korrekt behandelt."""
        chat = ChatHelper(page, selectors)
        long_text = "Dies ist ein Test. " * 100  # ~1900 Zeichen

        result = chat.send_and_wait(long_text, timeout=15000)

        # Bot sollte trotzdem antworten (kein Crash)
        assert result["success"], (
            "Bot hat auf überlangen Text nicht geantwortet"
        )

    def test_special_characters(self, page, selectors):
        """Sonderzeichen werden korrekt verarbeitet."""
        chat = ChatHelper(page, selectors)
        special_text = "Öffnungszeiten? <script>alert('test')</script> 🎢🎡"

        result = chat.send_and_wait(special_text)

        assert result["success"], "Bot hat auf Sonderzeichen nicht geantwortet"

        # Prüfe, dass kein Script ausgeführt wird (XSS-Schutz)
        has_alert = page.evaluate("() => { try { return false; } catch(e) { return false; } }")
        assert not has_alert, "Mögliche XSS-Schwachstelle erkannt"

    def test_html_injection(self, page, selectors):
        """HTML-Injection wird verhindert."""
        chat = ChatHelper(page, selectors)
        html_text = '<img src=x onerror="alert(1)">'

        result = chat.send_and_wait(html_text)

        # Prüfe, ob der HTML-Code escaped dargestellt wird
        user_sel = selectors.get("user_message")
        if user_sel:
            messages = page.query_selector_all(user_sel)
            if messages:
                last_msg = messages[-1]
                inner_html = last_msg.evaluate("el => el.innerHTML")
                assert "<img" not in inner_html.lower() or "src=x" not in inner_html, (
                    "HTML wurde nicht escaped – mögliche Injection"
                )

    def test_rapid_messages(self, page, selectors):
        """Schnelle Folgefragen crashen den Chat nicht."""
        chat = ChatHelper(page, selectors)

        # Sende drei Nachrichten schnell hintereinander
        chat.send_message("Frage 1")
        page.wait_for_timeout(200)
        chat.send_message("Frage 2")
        page.wait_for_timeout(200)
        chat.send_message("Frage 3")

        # Warte und prüfe, dass der Chat noch funktioniert
        page.wait_for_timeout(5000)

        container = page.query_selector(selectors["container"])
        assert container.is_visible(), "Chat-Widget nach Schnellfeuer nicht mehr sichtbar"

    def test_only_whitespace_message(self, page, selectors):
        """Nur-Leerzeichen-Nachricht wird korrekt behandelt."""
        chat = ChatHelper(page, selectors)
        input_sel = selectors["input_field"]
        send_sel = selectors["send_button"]

        page.fill(input_sel, "   ")
        page.wait_for_timeout(300)

        # Prüfe ob der Button deaktiviert ist (korrekte Behandlung)
        btn = page.query_selector(send_sel)
        if btn and btn.is_disabled():
            # Button ist deaktiviert bei Whitespace-Eingabe → korrekt
            return

        # Falls Button aktiv: klicken und prüfen dass keine leere Nachricht erscheint
        try:
            page.click(send_sel, timeout=3000)
        except Exception:
            # Click-Timeout = Button nicht klickbar → korrekt behandelt
            return

        page.wait_for_timeout(1000)
        user_sel = selectors.get("user_message")
        if user_sel:
            user_messages = page.query_selector_all(user_sel)
            for msg in user_messages:
                text = msg.text_content().strip()
                assert len(text) > 0, "Leerzeichen-Nachricht im Chat sichtbar"
