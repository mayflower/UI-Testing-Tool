"""Unit-Tests fuer die Flask-API in app.py (ohne Browser, ohne Live-System)."""

from __future__ import annotations

import pytest

from app import (
    app as flask_app,
    test_runs,
    website_scans,
    _classify_report,
)


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.test_client() as c:
        yield c
    test_runs.clear()
    website_scans.clear()


class TestHealthAndConfig:
    def test_status_ok(self, client):
        r = client.get("/api/status")
        assert r.status_code == 200
        assert r.get_json() == {"status": "ok"}

    def test_environments_get(self, client):
        r = client.get("/api/environments")
        assert r.status_code == 200
        assert isinstance(r.get_json(), (list, dict))

    def test_brand_get(self, client):
        r = client.get("/api/brand")
        assert r.status_code == 200
        assert isinstance(r.get_json(), dict)

    def test_selectors_get(self, client):
        r = client.get("/api/selectors")
        assert r.status_code == 200
        data = r.get_json()
        assert set(data) >= {"selectors", "configured", "total"}
        assert isinstance(data["selectors"], dict)
        assert data["configured"] <= data["total"]


class TestEnvironmentManagement:
    def test_add_missing_name(self, client):
        r = client.post("/api/environments", json={"url": "http://x"})
        assert r.status_code == 400

    def test_add_missing_url(self, client):
        r = client.post("/api/environments", json={"name": "x"})
        assert r.status_code == 400

    def test_add_empty_body(self, client):
        r = client.post("/api/environments", json={})
        assert r.status_code == 400


class TestReportsAndScreenshots:
    def test_reports_listing(self, client):
        r = client.get("/api/reports")
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)

    def test_report_not_found(self, client):
        r = client.get("/api/reports/this_report_does_not_exist_xyz.md")
        assert r.status_code == 404

    def test_screenshots_listing(self, client):
        r = client.get("/api/screenshots")
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)

    def test_live_browser_no_screenshot(self, client):
        r = client.get("/live-browser")
        assert r.status_code in (200, 204)


class TestTestRunEndpoints:
    def test_status_not_found(self, client):
        r = client.get("/api/tests/status/does-not-exist")
        assert r.status_code == 404

    def test_cancel_not_found(self, client):
        r = client.post("/api/tests/cancel/does-not-exist")
        assert r.status_code == 404

    def test_cancel_run_not_running(self, client):
        test_runs["abc12345"] = {"id": "abc12345", "status": "completed"}
        r = client.post("/api/tests/cancel/abc12345")
        assert r.status_code == 400


class TestWebsiteScan:
    def test_run_missing_url(self, client):
        r = client.post("/api/website-scan/run", json={})
        assert r.status_code == 400

    def test_cancel_not_found(self, client):
        r = client.post("/api/website-scan/cancel/unknown")
        assert r.status_code == 404


class TestJira:
    def test_create_tickets_missing_run_id(self, client):
        r = client.post("/api/jira/create-tickets", json={})
        assert r.status_code == 400

    def test_create_tickets_run_not_found(self, client):
        r = client.post("/api/jira/create-tickets", json={"run_id": "nope"})
        assert r.status_code == 404

    def test_jira_config_get_masks_token(self, client):
        r = client.get("/api/jira/config")
        assert r.status_code == 200
        data = r.get_json()
        if data.get("api_token"):
            assert data["api_token"] == "***"


class TestHelpers:
    @pytest.mark.parametrize(
        "name,kind",
        [
            ("website_scan_2026-06-12.md", "website"),
            ("checklist_xyz.md", "checklist"),
            ("testbericht_run.md", "chatbot"),
            ("random.md", "unknown"),
        ],
    )
    def test_classify_report(self, name, kind):
        assert _classify_report(name) == kind
