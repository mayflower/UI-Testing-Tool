"""Unit-Tests fuer die Worker-Threads in app.py (subprocess + WebsiteScanner gemockt)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app as app_module
from app import (
    _run_tests_worker,
    _run_website_scan_worker,
    test_runs,
    website_scans,
)


@pytest.fixture(autouse=True)
def clear_state():
    test_runs.clear()
    website_scans.clear()
    yield
    test_runs.clear()
    website_scans.clear()


def _mock_popen(stdout_lines: list[str], returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.stdout = iter([line if line.endswith("\n") else line + "\n"
                        for line in stdout_lines])
    proc.wait.return_value = returncode
    proc.returncode = returncode
    proc.poll.return_value = None
    return proc


class TestRunTestsWorker:
    def test_happy_path_parses_results(self):
        test_runs["w1"] = {"id": "w1", "results": [], "output": []}
        proc = _mock_popen([
            "tests/ui/test_x.py::TestX::test_a PASSED [ 50%]",
            "tests/ui/test_x.py::TestX::test_b FAILED [100%]",
        ])
        with patch("app.subprocess.Popen", return_value=proc), \
             patch("app._generate_report_for_run"):
            _run_tests_worker("w1", env_name="stage", suite=None)

        run = test_runs["w1"]
        assert run["status"] == "completed"
        assert run["exit_code"] == 0
        outcomes = [r["outcome"] for r in run["results"]]
        assert outcomes == ["passed", "failed"]

    def test_suite_mapping(self):
        test_runs["w2"] = {"id": "w2", "results": [], "output": []}
        proc = _mock_popen([])
        captured_cmd = {}

        def _capture(cmd, **kwargs):
            captured_cmd["cmd"] = cmd
            return proc

        with patch("app.subprocess.Popen", side_effect=_capture), \
             patch("app._generate_report_for_run"):
            _run_tests_worker("w2", env_name="stage", suite="ui")

        assert "tests/ui/" in captured_cmd["cmd"]

    def test_url_sets_environment_variables(self):
        test_runs["w3"] = {"id": "w3", "results": [], "output": []}
        proc = _mock_popen([])
        captured_env = {}

        def _capture(cmd, **kwargs):
            captured_env.update(kwargs.get("env", {}))
            return proc

        with patch("app.subprocess.Popen", side_effect=_capture), \
             patch("app._generate_report_for_run"):
            _run_tests_worker(
                "w3", env_name=None, suite=None,
                url="https://e.com", login_url="https://l",
                username="u", password="p",
            )

        assert captured_env["CHATBOT_URL"] == "https://e.com"
        assert captured_env["CHATBOT_LOGIN_URL"] == "https://l"
        assert captured_env["CHATBOT_USERNAME"] == "u"
        assert captured_env["CHATBOT_PASSWORD"] == "p"

    def test_cancel_terminates_process(self):
        test_runs["w4"] = {"id": "w4", "results": [], "output": [], "_cancel": True}

        def line_gen():
            yield "tests/ui/test_x.py::test_a PASSED [ 50%]\n"
            yield "more"  # weitere Zeile triggert Cancel-Check

        proc = MagicMock()
        proc.stdout = line_gen()
        proc.wait.return_value = 0
        proc.poll.return_value = None

        with patch("app.subprocess.Popen", return_value=proc), \
             patch("app._generate_report_for_run"):
            _run_tests_worker("w4", env_name="stage", suite=None)

        assert test_runs["w4"]["status"] == "cancelled"
        proc.terminate.assert_called()

    def test_exception_sets_error_status(self):
        test_runs["w5"] = {"id": "w5", "results": [], "output": []}
        with patch("app.subprocess.Popen", side_effect=RuntimeError("popen-fail")):
            _run_tests_worker("w5", env_name="stage", suite=None)

        assert test_runs["w5"]["status"] == "error"
        assert "popen-fail" in test_runs["w5"]["error"]


class TestRunWebsiteScanWorker:
    def test_happy_path_runs_scanner_and_sets_report(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "utils.report_generator.REPORTS_DIR", tmp_path
        )

        website_scans["s1"] = {"id": "s1", "results": [], "output": []}

        scanner = MagicMock()
        scanner.results = [
            {"name": "a11y", "status": "passed", "category": "a"},
        ]
        scanner.status = "completed"

        with patch("utils.website_scanner.WebsiteScanner", return_value=scanner):
            _run_website_scan_worker(
                "s1", url="https://e.com",
                checks=["a11y"],
            )

        run = website_scans["s1"]
        assert run["status"] == "completed"
        assert run["results"] == scanner.results
        scanner.run.assert_called_once()
        # Report-Datei wurde generiert
        assert "report" in run

    def test_scanner_exception_sets_error(self):
        website_scans["s2"] = {"id": "s2", "results": [], "output": []}

        scanner = MagicMock()
        scanner.run.side_effect = RuntimeError("scanner-boom")
        with patch("utils.website_scanner.WebsiteScanner", return_value=scanner):
            _run_website_scan_worker(
                "s2", url="https://e.com", checks=["a11y"],
            )

        assert website_scans["s2"]["status"] == "error"
        assert "scanner-boom" in website_scans["s2"]["error"]


class TestGenerateReportForRun:
    def test_no_results_returns_early(self):
        run = {"results": []}
        app_module._generate_report_for_run(run, "stage", None)
        assert "report_name" not in run

    def test_with_url_uses_custom_env(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.report_generator.REPORTS_DIR", tmp_path)
        run = {
            "results": [
                {"name": "test_x", "outcome": "passed", "suite": "ui",
                 "message": "", "duration": 0},
            ],
        }
        app_module._generate_report_for_run(run, None, None, url="https://e.com")
        assert "report_name" in run

    def test_suite_branch(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.report_generator.REPORTS_DIR", tmp_path)
        run = {
            "results": [
                {"name": "test_x", "outcome": "passed", "suite": "ui",
                 "message": "", "duration": 0},
            ],
        }
        app_module._generate_report_for_run(run, None, "ui", url="https://e.com")
        assert run["report_name"].startswith("checklist_ui_")
