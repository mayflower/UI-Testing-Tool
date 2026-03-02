"""Hilfsfunktionen für die Interaktion mit dem Chat-Widget."""

from __future__ import annotations

import time

from playwright.sync_api import Page


class ChatHelper:
    """Wrapper für Chat-Widget-Interaktionen."""

    def __init__(self, page: Page, selectors: dict):
        self.page = page
        self.selectors = selectors

    def _selector(self, name: str) -> str:
        """Hole einen CSS-Selektor und prüfe ob er konfiguriert ist."""
        sel = self.selectors.get(name)
        if not sel:
            raise ValueError(
                f"Selektor '{name}' nicht konfiguriert. "
                "Führe 'python run.py --discover' aus."
            )
        return sel

    def send_message(self, text: str) -> None:
        """Sende eine Nachricht an den Chatbot."""
        input_sel = self._selector("input_field")
        send_sel = self._selector("send_button")

        self.page.fill(input_sel, text)
        self.page.click(send_sel)

    def wait_for_response(self, timeout: int = 10000) -> str | None:
        """
        Warte auf eine neue Bot-Antwort.

        Returns:
            Der Text der Bot-Antwort oder None bei Timeout.
        """
        bot_sel = self._selector("bot_message")

        # Zähle aktuelle Bot-Nachrichten
        initial_count = len(self.page.query_selector_all(bot_sel))

        try:
            # Warte bis eine neue Bot-Nachricht erscheint
            self.page.wait_for_function(
                f"""() => document.querySelectorAll('{bot_sel}').length > {initial_count}""",
                timeout=timeout,
            )
            # Hole die letzte Bot-Nachricht
            messages = self.page.query_selector_all(bot_sel)
            if messages:
                return messages[-1].text_content().strip()
        except Exception:
            return None

        return None

    def send_and_wait(self, text: str, timeout: int = 10000) -> dict:
        """
        Sende eine Nachricht und warte auf die Antwort.
        Misst gleichzeitig die Antwortzeit.

        Returns:
            Dict mit 'response', 'response_time_ms' und 'success'.
        """
        start = time.time()
        self.send_message(text)
        response = self.wait_for_response(timeout)
        elapsed = (time.time() - start) * 1000

        return {
            "response": response,
            "response_time_ms": round(elapsed),
            "success": response is not None,
        }

    def get_all_messages(self) -> list[dict]:
        """
        Hole alle Nachrichten aus dem Chat-Verlauf.

        Returns:
            Liste von Dicts mit 'role' (user/bot) und 'text'.
        """
        messages = []

        bot_sel = self.selectors.get("bot_message")
        user_sel = self.selectors.get("user_message")

        if bot_sel:
            for el in self.page.query_selector_all(bot_sel):
                messages.append({
                    "role": "bot",
                    "text": el.text_content().strip(),
                })

        if user_sel:
            for el in self.page.query_selector_all(user_sel):
                messages.append({
                    "role": "user",
                    "text": el.text_content().strip(),
                })

        return messages

    def get_welcome_message(self) -> str | None:
        """Hole die Begrüßungsnachricht des Bots (falls vorhanden)."""
        bot_sel = self.selectors.get("bot_message")
        if not bot_sel:
            return None
        messages = self.page.query_selector_all(bot_sel)
        if messages:
            return messages[0].text_content().strip()
        return None

    def is_input_empty(self) -> bool:
        """Prüfe ob das Eingabefeld leer ist."""
        input_sel = self._selector("input_field")
        value = self.page.input_value(input_sel)
        return value.strip() == ""

    def get_input_placeholder(self) -> str | None:
        """Hole den Platzhaltertext des Eingabefelds."""
        input_sel = self._selector("input_field")
        el = self.page.query_selector(input_sel)
        if el:
            return el.get_attribute("placeholder")
        return None
