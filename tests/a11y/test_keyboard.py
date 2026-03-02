"""Accessibility-Tests: Tastaturnavigation."""

import pytest

from utils.chat_helpers import ChatHelper


pytestmark = pytest.mark.a11y


class TestKeyboardNavigation:
    """Prüft die Tastaturzugänglichkeit des Chat-Widgets."""

    def test_input_focusable_by_tab(self, page, selectors):
        """Eingabefeld ist per Tab erreichbar."""
        input_sel = selectors["input_field"]

        # Fokus auf Body setzen und dann Tab drücken
        page.keyboard.press("Tab")

        # Mehrfach Tab drücken um zum Input zu gelangen (max. 20 Tabs)
        for _ in range(20):
            focused = page.evaluate(
                "() => document.activeElement?.tagName?.toLowerCase()"
            )
            focused_matches = page.evaluate(
                f"() => document.activeElement?.matches('{input_sel}') || false"
            )
            if focused_matches:
                break
            page.keyboard.press("Tab")

        focused_matches = page.evaluate(
            f"() => document.activeElement?.matches('{input_sel}') || false"
        )
        assert focused_matches, (
            "Eingabefeld konnte nicht per Tab-Taste erreicht werden"
        )

    def test_send_message_with_enter(self, page, selectors):
        """Nachricht kann mit Enter-Taste gesendet werden."""
        chat = ChatHelper(page, selectors)
        input_sel = selectors["input_field"]

        # Fokus aufs Eingabefeld
        page.click(input_sel)
        page.fill(input_sel, "Test per Enter")
        page.keyboard.press("Enter")

        # Warte auf Antwort
        response = chat.wait_for_response(timeout=10000)
        assert response is not None, (
            "Enter-Taste hat keine Nachricht gesendet oder Bot hat nicht geantwortet"
        )

    def test_no_keyboard_trap(self, page, selectors):
        """Kein Keyboard-Trap: Nutzer kann das Widget per Tab verlassen."""
        input_sel = selectors["input_field"]

        # Fokus aufs Eingabefeld
        page.click(input_sel)

        # Tab mehrfach drücken – Fokus sollte irgendwann das Widget verlassen
        container_sel = selectors["container"]
        inside_widget = True

        for _ in range(30):
            page.keyboard.press("Tab")
            is_inside = page.evaluate(
                f"""() => {{
                    const container = document.querySelector('{container_sel}');
                    return container?.contains(document.activeElement) || false;
                }}"""
            )
            if not is_inside:
                inside_widget = False
                break

        assert not inside_widget, (
            "Keyboard-Trap: Fokus bleibt im Chat-Widget gefangen"
        )

    def test_escape_closes_or_defocuses(self, page, selectors):
        """Escape-Taste schließt das Widget oder entfernt den Fokus."""
        input_sel = selectors["input_field"]
        container_sel = selectors["container"]

        # Fokus aufs Eingabefeld
        page.click(input_sel)
        page.keyboard.press("Escape")

        page.wait_for_timeout(500)

        # Entweder Widget geschlossen oder Fokus weg
        still_focused = page.evaluate(
            f"""() => {{
                const container = document.querySelector('{container_sel}');
                return container?.contains(document.activeElement) || false;
            }}"""
        )

        # Das ist ein Hinweis, kein harter Fehler
        if still_focused:
            pytest.skip(
                "Escape entfernt den Fokus nicht aus dem Widget "
                "(optional, kein WCAG-Pflichtkriterium)"
            )
