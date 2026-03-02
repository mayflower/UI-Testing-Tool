"""UI-Tests: Layout, Dimensionen und Positionierung des Chat-Widgets."""

import pytest


pytestmark = pytest.mark.ui


class TestChatWidgetLayout:
    """Prüft Layout und Dimensionen des Chat-Widgets."""

    def test_widget_is_visible(self, page, selectors):
        """Chat-Widget ist sichtbar auf der Seite."""
        container = page.query_selector(selectors["container"])
        assert container is not None, "Chat-Widget-Container nicht gefunden"
        assert container.is_visible(), "Chat-Widget ist nicht sichtbar"

    def test_widget_has_reasonable_dimensions(self, page, selectors):
        """Chat-Widget hat angemessene Mindestgröße."""
        container = page.query_selector(selectors["container"])
        box = container.bounding_box()
        assert box is not None, "Bounding-Box konnte nicht ermittelt werden"
        assert box["width"] >= 300, f"Widget zu schmal: {box['width']}px (min. 300px)"
        assert box["height"] >= 400, f"Widget zu niedrig: {box['height']}px (min. 400px)"

    def test_input_field_is_visible(self, page, selectors):
        """Eingabefeld ist sichtbar und nutzbar."""
        input_el = page.query_selector(selectors["input_field"])
        assert input_el is not None, "Eingabefeld nicht gefunden"
        assert input_el.is_visible(), "Eingabefeld ist nicht sichtbar"
        assert input_el.is_enabled(), "Eingabefeld ist deaktiviert"

    def test_send_button_is_visible(self, page, selectors):
        """Senden-Button ist sichtbar."""
        btn = page.query_selector(selectors["send_button"])
        assert btn is not None, "Senden-Button nicht gefunden"
        assert btn.is_visible(), "Senden-Button ist nicht sichtbar"

    def test_message_area_exists(self, page, selectors):
        """Nachrichtenbereich existiert."""
        msg_list = selectors.get("message_list")
        if not msg_list:
            pytest.skip("message_list Selektor nicht konfiguriert")
        el = page.query_selector(msg_list)
        assert el is not None, "Nachrichtenbereich nicht gefunden"

    def test_header_exists(self, page, selectors):
        """Chat-Header existiert."""
        header_sel = selectors.get("header")
        if not header_sel:
            pytest.skip("header Selektor nicht konfiguriert")
        el = page.query_selector(header_sel)
        assert el is not None, "Chat-Header nicht gefunden"
        assert el.is_visible(), "Chat-Header ist nicht sichtbar"

    def test_widget_not_overlapping_page_content(self, page, selectors):
        """Chat-Widget überlagert nicht den gesamten Seiteninhalt."""
        container = page.query_selector(selectors["container"])
        box = container.bounding_box()
        viewport = page.viewport_size
        # Widget sollte nicht mehr als 80% des Viewports einnehmen
        widget_area = box["width"] * box["height"]
        viewport_area = viewport["width"] * viewport["height"]
        ratio = widget_area / viewport_area
        assert ratio < 0.8, (
            f"Widget nimmt {ratio:.0%} des Viewports ein (max. 80%)"
        )

    def test_screenshot_initial_state(self, page, selectors, screenshot_path):
        """Screenshot der Anfangsansicht für manuelle Prüfung."""
        page.screenshot(path=screenshot_path("ui_initial_state"))
