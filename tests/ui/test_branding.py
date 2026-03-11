"""UI-Tests: Branding, Farben und Typografie."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.ui


def _get_computed_style(element, property_name: str) -> str:
    """Hole eine berechnete CSS-Eigenschaft eines Elements."""
    return element.evaluate(
        f"el => window.getComputedStyle(el).getPropertyValue('{property_name}')"
    )


def _rgb_to_hex(rgb_str: str) -> str | None:
    """Konvertiere 'rgb(r, g, b)' oder 'rgba(r, g, b, a)' zu '#rrggbb'."""
    rgb_str = rgb_str.strip()
    if rgb_str.startswith("rgb"):
        parts = rgb_str.replace("rgba(", "").replace("rgb(", "").replace(")", "")
        values = [int(v.strip()) for v in parts.split(",")[:3]]
        return f"#{values[0]:02x}{values[1]:02x}{values[2]:02x}"
    if rgb_str.startswith("#"):
        return rgb_str.lower()
    return None


class TestBranding:
    """Prüft Corporate-Branding-Konformität."""

    def test_primary_color(self, page, selectors, brand):
        """Primärfarbe entspricht Branding-Vorgabe."""
        expected = brand.get("colors", {}).get("primary")
        if not expected:
            pytest.skip("Primärfarbe nicht in brand.yaml konfiguriert")

        container = page.query_selector(selectors["container"])
        bg_color = _get_computed_style(container, "background-color")
        actual = _rgb_to_hex(bg_color)

        assert actual == expected.lower(), (
            f"Primärfarbe: erwartet {expected}, gefunden {actual} ({bg_color})"
        )

    def test_accent_color_on_send_button(self, page, selectors, brand):
        """Akzentfarbe auf dem Senden-Button."""
        expected = brand.get("colors", {}).get("accent")
        if not expected:
            pytest.skip("Akzentfarbe nicht in brand.yaml konfiguriert")

        btn = page.query_selector(selectors["send_button"])
        bg_color = _get_computed_style(btn, "background-color")
        actual = _rgb_to_hex(bg_color)

        assert actual == expected.lower(), (
            f"Button-Farbe: erwartet {expected}, gefunden {actual} ({bg_color})"
        )

    def test_text_color(self, page, selectors, brand):
        """Textfarbe entspricht Branding-Vorgabe."""
        expected = brand.get("colors", {}).get("text")
        if not expected:
            pytest.skip("Textfarbe nicht in brand.yaml konfiguriert")

        container = page.query_selector(selectors["container"])
        color = _get_computed_style(container, "color")
        actual = _rgb_to_hex(color)

        assert actual == expected.lower(), (
            f"Textfarbe: erwartet {expected}, gefunden {actual} ({color})"
        )

    def test_primary_font(self, page, selectors, brand):
        """Primäre Schriftart entspricht Branding-Vorgabe."""
        expected = brand.get("fonts", {}).get("primary")
        if not expected:
            pytest.skip("Primäre Schriftart nicht in brand.yaml konfiguriert")

        container = page.query_selector(selectors["container"])
        font_family = _get_computed_style(container, "font-family")

        assert expected.lower() in font_family.lower(), (
            f"Schriftart: erwartet '{expected}', gefunden '{font_family}'"
        )

    def test_font_size_readable(self, page, selectors):
        """Schriftgröße ist lesbar (mindestens 14px)."""
        container = page.query_selector(selectors["container"])
        font_size = _get_computed_style(container, "font-size")
        size_px = float(font_size.replace("px", ""))

        assert size_px >= 14, (
            f"Schriftgröße zu klein: {size_px}px (Minimum: 14px)"
        )

    def test_logo_present(self, page, selectors, brand):
        """Logo ist vorhanden mit korrektem Alt-Text."""
        header_sel = selectors.get("header")
        if not header_sel:
            pytest.skip("header Selektor nicht konfiguriert")

        # Suche nach img-Elementen im Header
        logo = page.query_selector(f"{header_sel} img")
        if logo is None:
            # Versuche SVG
            logo = page.query_selector(f"{header_sel} svg")

        if logo is None:
            pytest.skip("Kein Logo-Element im Header gefunden")

        expected_alt = brand.get("logo", {}).get("expected_alt_text")
        if expected_alt and logo.get_attribute("alt"):
            alt_text = logo.get_attribute("alt")
            assert expected_alt.lower() in alt_text.lower(), (
                f"Logo Alt-Text: erwartet '{expected_alt}', gefunden '{alt_text}'"
            )

    def test_bot_user_messages_distinguishable(self, page, selectors):
        """Bot- und User-Nachrichten sind visuell unterscheidbar."""
        bot_sel = selectors.get("bot_message")
        user_sel = selectors.get("user_message")

        if not bot_sel or not user_sel:
            pytest.skip("bot_message oder user_message Selektor nicht konfiguriert")

        bot_el = page.query_selector(bot_sel)
        user_el = page.query_selector(user_sel)

        if not bot_el or not user_el:
            pytest.skip("Keine Bot- oder User-Nachricht zum Vergleichen vorhanden")

        bot_bg = _get_computed_style(bot_el, "background-color")
        user_bg = _get_computed_style(user_el, "background-color")

        assert bot_bg != user_bg, (
            "Bot- und User-Nachrichten haben die gleiche Hintergrundfarbe: "
            f"{bot_bg}"
        )
