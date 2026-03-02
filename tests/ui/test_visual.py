"""UI-Tests: Visuelle Screenshots und responsive Darstellung."""

import pytest

from utils.chat_helpers import ChatHelper


pytestmark = pytest.mark.ui


# Typische Geräte-Viewports
VIEWPORTS = {
    "desktop": {"width": 1280, "height": 720},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 375, "height": 812},
}


class TestVisualScreenshots:
    """Erstellt Screenshots für manuelle visuelle Prüfung."""

    def test_screenshot_desktop(self, page, screenshot_path):
        """Screenshot in Desktop-Auflösung."""
        page.set_viewport_size(VIEWPORTS["desktop"])
        page.wait_for_timeout(500)
        page.screenshot(path=screenshot_path("visual_desktop"))

    def test_screenshot_tablet(self, page, screenshot_path):
        """Screenshot in Tablet-Auflösung."""
        page.set_viewport_size(VIEWPORTS["tablet"])
        page.wait_for_timeout(500)
        page.screenshot(path=screenshot_path("visual_tablet"))

    def test_screenshot_mobile(self, page, screenshot_path):
        """Screenshot in Mobile-Auflösung."""
        page.set_viewport_size(VIEWPORTS["mobile"])
        page.wait_for_timeout(500)
        page.screenshot(path=screenshot_path("visual_mobile"))

    def test_screenshot_after_message(self, page, selectors, screenshot_path):
        """Screenshot nach dem Senden einer Nachricht."""
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait("Hallo, was sind die Öffnungszeiten?")

        if result["success"]:
            page.wait_for_timeout(500)

        page.screenshot(path=screenshot_path("visual_after_message"))

    def test_widget_responsive_desktop(self, page, selectors):
        """Widget passt sich der Desktop-Auflösung an."""
        page.set_viewport_size(VIEWPORTS["desktop"])
        page.wait_for_timeout(500)
        container = page.query_selector(selectors["container"])
        assert container.is_visible(), "Widget nicht sichtbar bei Desktop"

    def test_widget_responsive_mobile(self, page, selectors):
        """Widget passt sich der Mobile-Auflösung an."""
        page.set_viewport_size(VIEWPORTS["mobile"])
        page.wait_for_timeout(500)

        container = page.query_selector(selectors["container"])
        if container is None:
            pytest.skip("Container bei Mobile-Viewport nicht gefunden")

        assert container.is_visible(), "Widget nicht sichtbar bei Mobile"

        box = container.bounding_box()
        viewport = VIEWPORTS["mobile"]
        # Auf Mobile sollte das Widget den vollen Viewport nutzen können
        assert box["width"] <= viewport["width"], (
            f"Widget breiter als Mobile-Viewport: {box['width']}px > {viewport['width']}px"
        )
