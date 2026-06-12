"""Unit-Tests fuer utils/report_generator.py — Jinja-Reports ohne Browser."""

from __future__ import annotations

import pytest

from utils.report_generator import (
    _enrich_result,
    _parse_pytest_results,
    generate_report,
    generate_suite_report,
    generate_website_scan_report,
)


class TestEnrichResult:
    def test_known_test_name_uses_label(self):
        r = _enrich_result(
            {"name": "test_widget_is_visible", "outcome": "passed", "duration": 0.5}
        )
        assert r["label"] == "Chat-Widget sichtbar"
        assert r["passed"] is True
        assert r["failed"] is False
        assert r["skipped"] is False
        assert r["duration_ms"] == 500
        assert r["test_id"] == "widget_is_visible"

    def test_unknown_test_falls_back_to_capitalized(self):
        r = _enrich_result({"name": "test_brand_new", "outcome": "failed"})
        assert r["label"] == "Brand new"
        assert r["failed"] is True
        assert r["passed"] is False
        assert r["action"] == ""
        assert r["description"] == ""

    def test_skipped_outcome(self):
        r = _enrich_result({"name": "test_x", "outcome": "skipped"})
        assert r["skipped"] is True
        assert r["passed"] is False
        assert r["failed"] is False

    def test_error_outcome_treated_as_failed(self):
        r = _enrich_result({"name": "test_x", "outcome": "error"})
        assert r["failed"] is True

    def test_message_propagated(self):
        r = _enrich_result(
            {"name": "test_x", "outcome": "failed", "message": "assertion failed"}
        )
        assert r["message"] == "assertion failed"

    def test_missing_duration_defaults_to_zero(self):
        r = _enrich_result({"name": "test_x", "outcome": "passed"})
        assert r["duration_ms"] == 0


class TestParsePytestResults:
    def test_groups_by_suite(self):
        results = [
            {"name": "test_a", "outcome": "passed", "suite": "ui"},
            {"name": "test_b", "outcome": "passed", "suite": "ux"},
            {"name": "test_c", "outcome": "failed", "suite": "a11y"},
        ]
        out = _parse_pytest_results(results)
        assert len(out["ui"]) == 1
        assert len(out["ux"]) == 1
        assert len(out["a11y"]) == 1

    def test_unknown_suite_ignored(self):
        out = _parse_pytest_results([
            {"name": "test_x", "outcome": "passed", "suite": "foo"},
        ])
        assert all(len(v) == 0 for v in out.values())


@pytest.fixture
def tmp_reports(tmp_path, monkeypatch):
    monkeypatch.setattr("utils.report_generator.REPORTS_DIR", tmp_path)
    return tmp_path


class TestGenerateReport:
    def test_writes_file(self, tmp_reports):
        results = [
            {"name": "test_widget_is_visible", "outcome": "passed",
             "suite": "ui", "duration": 0.1},
            {"name": "test_primary_color", "outcome": "failed",
             "suite": "ui", "duration": 0.2, "message": "color mismatch"},
            {"name": "test_simple_question", "outcome": "skipped",
             "suite": "ux", "duration": 0.0},
        ]
        env = {"name": "stage", "url": "https://e.com", "description": "Stage"}
        path = generate_report(results, env)
        assert path.exists()
        assert path.parent == tmp_reports
        assert path.name.startswith("testbericht_")
        content = path.read_text(encoding="utf-8")
        assert "stage" in content

    def test_explicit_output_name(self, tmp_reports):
        path = generate_report(
            [], {"name": "x", "url": ""}, output_name="custom_report"
        )
        assert path.name == "custom_report.md"

    def test_empty_results_no_division_by_zero(self, tmp_reports):
        path = generate_report([], {"name": "x", "url": ""})
        assert path.exists()


class TestGenerateSuiteReport:
    @pytest.mark.parametrize("suite", ["ui", "ux", "a11y"])
    def test_writes_file_per_suite(self, suite, tmp_reports):
        results = [
            {"name": "test_widget_is_visible", "outcome": "passed",
             "suite": suite, "duration": 0.1},
            {"name": "test_other", "outcome": "failed", "suite": suite,
             "duration": 0.2, "message": "boom"},
        ]
        path = generate_suite_report(
            suite, results, {"name": "stage", "url": "https://e.com"}
        )
        assert path.exists()
        assert path.name.startswith(f"checklist_{suite}_")


class TestGenerateWebsiteScanReport:
    def test_writes_file_and_extracts_domain(self, tmp_reports):
        results = [
            {"name": "a11y", "status": "passed", "category": "accessibility"},
            {"name": "lh", "status": "failed", "category": "performance"},
            {"name": "links", "status": "warning", "category": "links"},
            {"name": "meta", "status": "info", "category": "seo"},
        ]
        path = generate_website_scan_report(
            results, "https://example.com", ["accessibility", "performance"]
        )
        assert path.exists()
        assert "example_com" in path.name

    def test_empty_results(self, tmp_reports):
        path = generate_website_scan_report([], "https://example.com", ["a11y"])
        assert path.exists()

    def test_invalid_url_falls_back_to_unknown(self, tmp_reports):
        path = generate_website_scan_report([], "not-a-url", ["a11y"])
        assert "unknown" in path.name
