"""Mock-basierte Tests fuer komplexere Endpoints in app.py.

Deckt: Helper-Parsing, Tests-Run-Endpoint (Thread gemockt), Discovery
(utils.discovery gemockt), Jira (utils.jira_helper gemockt), SSE-Streams
(bereits abgeschlossene Runs).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app import (
    _clean_error_block,
    _extract_error_messages,
    _parse_test_line,
    app as flask_app,
    test_runs,
    website_scans,
)


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.test_client() as c:
        yield c
    test_runs.clear()
    website_scans.clear()


class TestParseTestLine:
    def test_passed_ui_suite(self):
        run: dict = {}
        _parse_test_line(run, "tests/ui/test_x.py::TestX::test_a PASSED [  5%]")
        assert run["results"][0]["outcome"] == "passed"
        assert run["results"][0]["suite"] == "ui"
        assert run["results"][0]["name"] == "test_a"

    def test_failed_ux_suite(self):
        run: dict = {}
        _parse_test_line(run, "tests/ux/test_y.py::TestY::test_b FAILED  [ 10%]")
        assert run["results"][0]["outcome"] == "failed"
        assert run["results"][0]["suite"] == "ux"

    def test_error_a11y_suite(self):
        run: dict = {}
        _parse_test_line(run, "tests/a11y/test_z.py::test_c ERROR [ 99%]")
        assert run["results"][0]["suite"] == "a11y"
        assert run["results"][0]["outcome"] == "error"

    def test_ignores_short_summary_line(self):
        run: dict = {}
        _parse_test_line(run, "FAILED tests/foo.py - assertion")
        assert "results" not in run


class TestExtractErrorMessages:
    def test_extracts_failure_block(self):
        output = [
            "tests/x.py::test_a FAILED [  5%]",
            "================================== FAILURES ==================================",
            "___________________________ TestX.test_a __________________________",
            "    def test_a():",
            ">       assert 1 == 2",
            "E       AssertionError: 1 != 2",
            "=========================== short test summary info ============================",
        ]
        errors = _extract_error_messages(output)
        assert "test_a" in errors
        assert "AssertionError" in errors["test_a"]

    def test_setup_error_header(self):
        output = [
            "================================== ERRORS ====================================",
            "___________________ ERROR at setup of TestY.test_b _____________________",
            "E       RuntimeError: setup failed",
            "=========================== short test summary info ============================",
        ]
        errors = _extract_error_messages(output)
        assert "test_b" in errors


class TestCleanErrorBlock:
    def test_prioritizes_E_lines(self):
        lines = ["    foo", "E   AssertionError: 1 != 2", "    bar"]
        assert "AssertionError" in _clean_error_block(lines)

    def test_fallback_when_no_E_lines(self):
        lines = ["alpha", "beta", "gamma"]
        out = _clean_error_block(lines)
        assert "alpha" in out or "gamma" in out


class TestRunTestsEndpoint:
    def test_creates_run_with_env_and_suite(self, client):
        with patch("app.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            r = client.post(
                "/api/tests/run",
                json={"environment": "stage", "suite": "ui"},
            )
            assert r.status_code == 200
            run_id = r.get_json()["run_id"]
            assert run_id in test_runs
            assert test_runs[run_id]["environment"] == "stage"
            assert test_runs[run_id]["suite"] == "ui"
            mock_thread.return_value.start.assert_called_once()

    def test_direct_url_marks_environment_custom(self, client):
        with patch("app.threading.Thread"):
            r = client.post(
                "/api/tests/run",
                json={"url": "https://example.com"},
            )
            run_id = r.get_json()["run_id"]
            assert test_runs[run_id]["environment"] == "custom"
            assert test_runs[run_id]["url"] == "https://example.com"


class TestTestStatusSummary:
    def test_summary_counts(self, client):
        test_runs["xx123456"] = {
            "id": "xx123456",
            "status": "completed",
            "environment": "stage",
            "suite": "ui",
            "results": [
                {"name": "a", "outcome": "passed", "suite": "ui"},
                {"name": "b", "outcome": "failed", "suite": "ui"},
                {"name": "c", "outcome": "skipped", "suite": "ui"},
                {"name": "d", "outcome": "error", "suite": "ui"},
            ],
            "output": ["line1"],
        }
        r = client.get("/api/tests/status/xx123456")
        assert r.status_code == 200
        s = r.get_json()["summary"]
        assert s == {"total": 4, "passed": 1, "failed": 2, "skipped": 1}


class TestSSEStreams:
    def test_tests_stream_completed_run(self, client):
        test_runs["sse12345"] = {
            "id": "sse12345",
            "status": "completed",
            "results": [{"name": "x", "outcome": "passed", "suite": "ui"}],
        }
        r = client.get("/api/tests/stream/sse12345")
        assert r.status_code == 200
        body = r.get_data(as_text=True)
        assert "done" in body
        assert "passed" in body

    def test_tests_stream_unknown_run(self, client):
        r = client.get("/api/tests/stream/no-such-run")
        body = r.get_data(as_text=True)
        assert "not found" in body

    def test_website_scan_stream_completed(self, client):
        website_scans["wsc12345"] = {
            "id": "wsc12345",
            "status": "completed",
            "results": [
                {"name": "a11y", "status": "passed"},
                {"name": "perf", "status": "failed"},
                {"name": "seo", "status": "warning"},
            ],
        }
        r = client.get("/api/website-scan/stream/wsc12345")
        body = r.get_data(as_text=True)
        assert "done" in body


class TestWebsiteScanRunEndpoint:
    def test_creates_scan_with_url(self, client):
        with patch("app.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            r = client.post(
                "/api/website-scan/run",
                json={"url": "https://example.com"},
            )
            assert r.status_code == 200
            run_id = r.get_json()["run_id"]
            assert run_id in website_scans
            assert website_scans[run_id]["url"] == "https://example.com"
            mock_thread.return_value.start.assert_called_once()


class TestDiscoveryEndpoint:
    def test_by_env_merges_selectors(self, client):
        existing = {"input_field": None, "send_button": "#old"}
        result = {"selectors": {"input_field": "#new"}}
        with patch("utils.discovery.discover_selectors", return_value=result), \
             patch("app.get_selectors", return_value=existing), \
             patch("app.save_selectors") as mock_save:
            r = client.post("/api/discovery/run", json={"environment": "stage"})
            assert r.status_code == 200
            merged = mock_save.call_args[0][0]
            assert merged["input_field"] == "#new"
            assert merged["send_button"] == "#old"

    def test_by_url(self, client):
        with patch("utils.discovery.discover_selectors_by_url",
                   return_value={"selectors": {"input_field": "#x"}}), \
             patch("app.get_selectors", return_value={}), \
             patch("app.save_selectors"):
            r = client.post(
                "/api/discovery/run",
                json={"url": "https://e.com"},
            )
            assert r.status_code == 200

    def test_exception_returns_500(self, client):
        with patch("utils.discovery.discover_selectors",
                   side_effect=RuntimeError("boom")):
            r = client.post("/api/discovery/run", json={"environment": "stage"})
            assert r.status_code == 500
            assert "boom" in r.get_json()["error"]


class TestJiraEndpoints:
    def test_jira_test_connection(self, client):
        with patch("utils.jira_helper.test_connection", return_value={"ok": True}):
            r = client.get("/api/jira/test-connection")
            assert r.status_code == 200
            assert r.get_json() == {"ok": True}

    def test_jira_projects_ok(self, client):
        with patch("utils.jira_helper.get_projects", return_value=[{"key": "KI"}]):
            r = client.get("/api/jira/projects")
            assert r.status_code == 200
            data = r.get_json()
            assert data["ok"] is True
            assert data["projects"] == [{"key": "KI"}]

    def test_jira_projects_error(self, client):
        with patch("utils.jira_helper.get_projects", side_effect=RuntimeError("boom")):
            r = client.get("/api/jira/projects")
            assert r.status_code == 400
            assert r.get_json()["ok"] is False

    def test_jira_create_tickets_ok(self, client):
        test_runs["jt123456"] = {
            "id": "jt123456",
            "status": "completed",
            "results": [{"name": "test_a", "outcome": "failed", "suite": "ui"}],
            "url": "https://example.com",
        }
        with patch("utils.jira_helper.create_tickets_for_failures",
                   return_value=[{"key": "KI-999"}]):
            r = client.post("/api/jira/create-tickets",
                            json={"run_id": "jt123456"})
            assert r.status_code == 200
            data = r.get_json()
            assert data["tickets"] == [{"key": "KI-999"}]

    def test_jira_create_tickets_filters_selected(self, client):
        test_runs["jt998877"] = {
            "id": "jt998877",
            "status": "completed",
            "results": [
                {"name": "test_a", "outcome": "failed", "suite": "ui"},
                {"name": "test_b", "outcome": "failed", "suite": "ui"},
            ],
            "url": "https://example.com",
        }
        seen: dict = {}

        def _fake(results, environment_url, project_key, issue_type):
            seen["count"] = len(results)
            return []

        with patch("utils.jira_helper.create_tickets_for_failures",
                   side_effect=_fake):
            r = client.post(
                "/api/jira/create-tickets",
                json={"run_id": "jt998877", "selected_tests": ["A"]},
            )
            assert r.status_code == 200
            assert seen["count"] == 1

    def test_jira_config_save_keeps_existing_token_on_masked_input(self, client):
        existing = {
            "api_token": "real-token",
            "base_url": "x",
            "email": "y",
            "project_key": "K",
            "issue_type": "Bug",
        }
        with patch("app.get_jira_config", return_value=existing), \
             patch("app.save_jira_config") as mock_save:
            r = client.post(
                "/api/jira/config",
                json={
                    "api_token": "***",
                    "base_url": "z",
                    "email": "e",
                    "project_key": "P",
                    "issue_type": "Task",
                },
            )
            assert r.status_code == 200
            saved = mock_save.call_args[0][0]
            assert saved["api_token"] == "real-token"
            assert saved["base_url"] == "z"
            assert saved["issue_type"] == "Task"
