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

        # Klick + fill fuer zuverlaessige React-Kompatibilitaet
        loc = self.page.locator(input_sel)
        loc.click()
        loc.fill(text)
        self.page.click(send_sel)

    # Texte die auf UI-Kontrollelemente hinweisen (nicht Bot-Antworten)
    _FEEDBACK_PATTERNS = ("was this helpful", "give feedback", "hilfreich")

    def wait_for_response(self, timeout: int = 30000) -> str | None:
        """
        Warte auf eine neue Bot-Antwort.

        Unterstuetzt Streaming-Antworten: wartet nicht nur auf ein neues
        Element, sondern auch darauf, dass es tatsaechlich Text enthaelt.
        Faellt auf message_list-basierte Erkennung zurueck falls
        bot_message-Selektor nicht funktioniert.

        Returns:
            Der Text der Bot-Antwort oder None bei Timeout.
        """
        bot_sel = self.selectors.get("bot_message")
        msg_list_sel = self.selectors.get("message_list")

        # Snapshot VOR dem Warten fuer den Fallback
        initial_text_len = 0
        if msg_list_sel:
            initial_text_len = self.page.evaluate(f"""() => {{
                const el = document.querySelector('{msg_list_sel}');
                return el ? el.textContent.trim().length : 0;
            }}""") or 0

        # Primaerstrategie: bot_message Selektor
        if bot_sel:
            result = self._wait_for_bot_message(bot_sel, timeout)
            if result and not self._is_feedback_text(result):
                return result

        # Fallback: Textaenderung im message_list Container erkennen
        if msg_list_sel:
            return self._wait_for_new_text_in_container(
                msg_list_sel, timeout, initial_text_len
            )

        return None

    def _wait_for_bot_message(self, bot_sel: str, timeout: int) -> str | None:
        """Warte auf neues Element das zum bot_message Selektor passt."""
        initial_count = len(self.page.query_selector_all(bot_sel))

        try:
            self.page.wait_for_function(
                f"""() => {{
                    const msgs = document.querySelectorAll('{bot_sel}');
                    if (msgs.length <= {initial_count}) return false;
                    const last = msgs[msgs.length - 1];
                    return (last.textContent || '').trim().length > 0;
                }}""",
                timeout=timeout,
            )
            # Kurz warten damit Streaming-Antwort sich stabilisiert
            self.page.wait_for_timeout(500)
            messages = self.page.query_selector_all(bot_sel)
            if messages:
                return messages[-1].text_content().strip()
        except Exception:
            return None
        return None

    def _wait_for_new_text_in_container(
        self, container_sel: str, timeout: int, initial_len: int = 0
    ) -> str | None:
        """Fallback: Erkenne neue Bot-Antwort anhand von Textaenderung im Container."""
        try:
            # Warte bis der Container deutlich mehr Text hat (>20 Zeichen neu)
            self.page.wait_for_function(
                f"""(initLen) => {{
                    const el = document.querySelector('{container_sel}');
                    if (!el) return false;
                    const newLen = el.textContent.trim().length;
                    return newLen > initLen + 20;
                }}""",
                arg=initial_len,
                timeout=timeout,
            )
            # Warten damit Streaming sich stabilisiert
            self.page.wait_for_timeout(1000)
            # Neuen Text extrahieren
            full_text = self.page.evaluate(f"""() => {{
                const el = document.querySelector('{container_sel}');
                return el ? el.textContent.trim() : '';
            }}""") or ""
            # Der neue Text ist die Bot-Antwort (nach dem initialen Text)
            new_text = full_text[initial_len:].strip()
            # Feedback-Text am Ende entfernen
            for pattern in self._FEEDBACK_PATTERNS:
                idx = new_text.lower().find(pattern)
                if idx > 0:
                    new_text = new_text[:idx].strip()
            return new_text if len(new_text) > 5 else None
        except Exception:
            return None

    def _is_feedback_text(self, text: str) -> bool:
        """Pruefe ob der Text ein UI-Kontrollelement ist statt einer Bot-Antwort."""
        lower = text.lower()
        return any(p in lower for p in self._FEEDBACK_PATTERNS)

    def send_and_wait(self, text: str, timeout: int = 30000) -> dict:
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
