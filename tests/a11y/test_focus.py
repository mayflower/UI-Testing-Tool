"""Accessibility-Tests: Fokus-Management und ARIA-Labels."""

import pytest

from utils.chat_helpers import ChatHelper


pytestmark = pytest.mark.a11y


class TestFocusAndAria:
    """Prüft Fokus-Management und ARIA-Attribute."""

    def test_input_has_aria_label(self, page, selectors):
        """Eingabefeld hat ein ARIA-Label oder sichtbares Label."""
        input_sel = selectors["input_field"]
        el = page.query_selector(input_sel)

        aria_label = el.get_attribute("aria-label")
        aria_labelledby = el.get_attribute("aria-labelledby")
        placeholder = el.get_attribute("placeholder")
        title = el.get_attribute("title")

        # Mindestens eine Form von Label sollte vorhanden sein
        has_label = any([aria_label, aria_labelledby, placeholder, title])

        # Prüfe auch ob ein <label> existiert
        input_id = el.get_attribute("id")
        if input_id:
            label = page.query_selector(f"label[for='{input_id}']")
            if label:
                has_label = True

        assert has_label, (
            "Eingabefeld hat kein ARIA-Label, keinen Placeholder, "
            "keinen Title und kein zugehöriges <label>-Element"
        )

    def test_send_button_has_aria_label(self, page, selectors):
        """Senden-Button hat ein ARIA-Label oder sichtbaren Text."""
        btn = page.query_selector(selectors["send_button"])

        aria_label = btn.get_attribute("aria-label")
        text = btn.text_content().strip()
        title = btn.get_attribute("title")

        has_label = any([aria_label, text, title])
        assert has_label, (
            "Senden-Button hat kein ARIA-Label, keinen Text und keinen Title"
        )

    def test_message_area_has_role(self, page, selectors):
        """Nachrichtenbereich hat eine geeignete ARIA-Rolle."""
        msg_sel = selectors.get("message_list")
        if not msg_sel:
            pytest.skip("message_list Selektor nicht konfiguriert")

        el = page.query_selector(msg_sel)
        if not el:
            pytest.skip("Nachrichtenbereich nicht gefunden")

        role = el.get_attribute("role")
        aria_live = el.get_attribute("aria-live")

        # Entweder role="log" oder aria-live sollte gesetzt sein
        has_semantic = role in ("log", "list", "region") or aria_live is not None
        assert has_semantic, (
            "Nachrichtenbereich hat weder role='log' noch aria-live. "
            "Screenreader können neue Nachrichten nicht ankündigen."
        )

    def test_live_region_for_new_messages(self, page, selectors):
        """Neue Nachrichten werden über ARIA Live-Regions angekündigt."""
        # Suche nach aria-live Attribut im Nachrichtenbereich oder seinen Kindern
        container_sel = selectors["container"]

        live_regions = page.query_selector_all(
            f"{container_sel} [aria-live]"
        )

        if not live_regions:
            # Prüfe auch role="status" und role="alert"
            live_regions = page.query_selector_all(
                f"{container_sel} [role='status'], "
                f"{container_sel} [role='alert'], "
                f"{container_sel} [role='log']"
            )

        assert len(live_regions) > 0, (
            "Keine ARIA Live-Region gefunden. "
            "Neue Bot-Nachrichten werden Screenreader-Nutzern nicht angekündigt."
        )

    def test_focus_visible_on_interactive_elements(self, page, selectors):
        """Interaktive Elemente haben einen sichtbaren Fokus-Indikator."""
        input_sel = selectors["input_field"]

        # Fokussiere das Eingabefeld
        page.click(input_sel)

        # Prüfe ob ein Fokus-Stil sichtbar ist
        outline = page.evaluate(
            f"""() => {{
                const el = document.querySelector('{input_sel}');
                const style = window.getComputedStyle(el);
                return {{
                    outline: style.outline,
                    outlineWidth: style.outlineWidth,
                    boxShadow: style.boxShadow,
                    borderColor: style.borderColor,
                }};
            }}"""
        )

        has_focus_indicator = (
            outline.get("outlineWidth", "0px") != "0px"
            or outline.get("boxShadow", "none") != "none"
        )

        if not has_focus_indicator:
            pytest.fail(
                "Eingabefeld hat keinen sichtbaren Fokus-Indikator. "
                f"Outline: {outline.get('outline')}, "
                f"Box-Shadow: {outline.get('boxShadow')}"
            )

    def test_heading_structure(self, page, selectors):
        """Chat-Widget hat eine sinnvolle Überschriftenstruktur."""
        container_sel = selectors["container"]

        headings = page.evaluate(
            f"""() => {{
                const container = document.querySelector('{container_sel}');
                if (!container) return [];
                const hs = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
                return Array.from(hs).map(h => ({{
                    level: parseInt(h.tagName[1]),
                    text: h.textContent.trim().substring(0, 50),
                }}));
            }}"""
        )

        if len(headings) == 0:
            pytest.skip("Keine Überschriften im Chat-Widget (optional)")

        # Prüfe ob Überschriften-Hierarchie sinnvoll ist
        levels = [h["level"] for h in headings]
        # Keine Sprünge um mehr als 1 Level
        for i in range(1, len(levels)):
            diff = levels[i] - levels[i - 1]
            assert diff <= 1, (
                f"Überschriften-Hierarchie hat Sprung: "
                f"h{levels[i-1]} → h{levels[i]}"
            )
