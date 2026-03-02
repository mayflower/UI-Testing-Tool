"""Accessibility-Tests: WCAG 2.1 AA Compliance via axe-core."""

import json

import pytest
from axe_playwright_python.sync_playwright import Axe


pytestmark = pytest.mark.a11y


class TestWCAGCompliance:
    """Automatisierte WCAG 2.1 AA Prüfung mit axe-core."""

    def test_axe_full_page_audit(self, page):
        """Vollständiger axe-core Audit der gesamten Seite."""
        axe = Axe()
        results = axe.run(page)

        violations = results.response.get("violations", [])

        if violations:
            # Formatiere Violations für den Report
            violation_details = []
            for v in violations:
                violation_details.append(
                    f"  - [{v['impact']}] {v['id']}: {v['description']} "
                    f"({len(v['nodes'])} Elemente betroffen)"
                )
            details = "\n".join(violation_details)

            # Test schlägt fehl, zeigt aber alle Details
            critical_or_serious = [
                v for v in violations
                if v.get("impact") in ("critical", "serious")
            ]

            assert len(critical_or_serious) == 0, (
                f"{len(violations)} WCAG-Violations gefunden "
                f"({len(critical_or_serious)} kritisch/schwerwiegend):\n{details}"
            )

    def test_axe_chat_widget_audit(self, page, selectors):
        """axe-core Audit nur für das Chat-Widget."""
        axe = Axe()
        container_sel = selectors["container"]
        results = axe.run(page, context=container_sel)

        violations = results.response.get("violations", [])
        critical = [
            v for v in violations
            if v.get("impact") in ("critical", "serious")
        ]

        assert len(critical) == 0, (
            f"{len(critical)} kritische/schwerwiegende Violations im Chat-Widget"
        )

    def test_color_contrast(self, page):
        """Farbkontraste erfüllen WCAG AA (4.5:1 für Text)."""
        axe = Axe()
        results = axe.run(page)

        violations = results.response.get("violations", [])
        contrast_violations = [
            v for v in violations if v["id"] == "color-contrast"
        ]

        if contrast_violations:
            nodes = contrast_violations[0].get("nodes", [])
            details = []
            for node in nodes[:5]:  # Zeige max. 5 Beispiele
                details.append(f"  - {node.get('html', 'unbekannt')[:80]}")

            assert False, (
                f"{len(nodes)} Kontrast-Violations gefunden:\n"
                + "\n".join(details)
            )

    def test_images_have_alt_text(self, page):
        """Alle Bilder haben Alt-Texte."""
        axe = Axe()
        results = axe.run(page)

        violations = results.response.get("violations", [])
        image_violations = [
            v for v in violations
            if v["id"] in ("image-alt", "input-image-alt")
        ]

        total_nodes = sum(len(v.get("nodes", [])) for v in image_violations)
        assert total_nodes == 0, (
            f"{total_nodes} Bilder ohne Alt-Text gefunden"
        )

    def test_save_axe_report(self, page, screenshot_path):
        """Speichere detaillierten axe-Report als JSON."""
        from config.settings import REPORTS_DIR
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        axe = Axe()
        results = axe.run(page)

        report_path = REPORTS_DIR / "axe_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results.response, f, indent=2, ensure_ascii=False)
