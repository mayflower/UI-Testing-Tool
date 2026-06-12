"""Unit-Tests fuer utils/jira_helper.py — alle HTTP-Calls gemockt."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from utils import jira_helper as jh


@pytest.fixture(autouse=True)
def clear_version_cache():
    jh._api_version_cache.clear()
    yield
    jh._api_version_cache.clear()


def _mock_response(status_code: int, json_data=None, text: str = "") -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data if json_data is not None else {}
    r.text = text
    r.raise_for_status = MagicMock()
    return r


class TestBaseUrl:
    def test_strips_trailing_slash(self):
        assert jh._base_url({"base_url": "https://j.example/"}) == "https://j.example"

    def test_missing_raises(self):
        with pytest.raises(ValueError, match="nicht konfiguriert"):
            jh._base_url({})


class TestDetectApiVersion:
    def test_server_response_returns_v2(self):
        config = {"base_url": "https://j.example", "api_token": "tok"}
        with patch("utils.jira_helper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(
                200, {"deploymentType": "Server", "versionNumbers": [9, 0, 0]}
            )
            assert jh._detect_api_version(config) == 2

    def test_cloud_fallback_returns_v3(self):
        config = {"base_url": "https://cloud.atlassian.net", "api_token": "tok"}
        with patch("utils.jira_helper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(404)
            assert jh._detect_api_version(config) == 3

    def test_request_exception_returns_v3(self):
        config = {"base_url": "https://j.example", "api_token": "tok"}
        with patch("utils.jira_helper.requests.get",
                   side_effect=requests.RequestException("boom")):
            assert jh._detect_api_version(config) == 3

    def test_cached_after_first_call(self):
        config = {"base_url": "https://j.example", "api_token": "tok"}
        with patch("utils.jira_helper.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, {"deploymentType": "Server"})
            jh._detect_api_version(config)
            jh._detect_api_version(config)
            assert mock_get.call_count == 1


class TestHeaders:
    def test_server_uses_bearer(self):
        with patch("utils.jira_helper._detect_api_version", return_value=2):
            h = jh._headers({"base_url": "x", "api_token": "tok", "email": "ignored"})
            assert h["Authorization"] == "Bearer tok"

    def test_cloud_uses_basic_auth(self):
        with patch("utils.jira_helper._detect_api_version", return_value=3):
            h = jh._headers({"base_url": "x", "api_token": "tok", "email": "u@y.de"})
            assert h["Authorization"].startswith("Basic ")

    def test_missing_token_raises(self):
        with pytest.raises(ValueError, match="API-Token"):
            jh._headers({"base_url": "x", "api_token": ""})

    def test_cloud_without_email_raises(self):
        with patch("utils.jira_helper._detect_api_version", return_value=3):
            with pytest.raises(ValueError, match="E-Mail"):
                jh._headers({"base_url": "x", "api_token": "tok"})


class TestApiUrl:
    def test_builds_with_detected_version(self):
        with patch("utils.jira_helper._detect_api_version", return_value=2):
            url = jh._api_url({"base_url": "https://j.example"}, "issue")
            assert url == "https://j.example/rest/api/2/issue"


class TestTestConnection:
    def test_success(self):
        with patch("utils.jira_helper.get_jira_config",
                   return_value={"base_url": "https://j.example", "api_token": "t"}):
            with patch("utils.jira_helper._detect_api_version", return_value=2):
                with patch("utils.jira_helper.requests.get") as mock_get:
                    mock_get.return_value = _mock_response(
                        200, {"displayName": "Mario"}
                    )
                    result = jh.test_connection()
                    assert result == {"ok": True, "user": "Mario"}

    def test_http_error(self):
        with patch("utils.jira_helper.get_jira_config",
                   return_value={"base_url": "https://x", "api_token": "t"}):
            with patch("utils.jira_helper._detect_api_version", return_value=2):
                with patch("utils.jira_helper.requests.get") as mock_get:
                    mock_get.return_value = _mock_response(401, text="Unauthorized")
                    result = jh.test_connection()
                    assert result["ok"] is False
                    assert "401" in result["error"]

    def test_value_error_returned(self):
        with patch("utils.jira_helper.get_jira_config", return_value={}):
            result = jh.test_connection()
            assert result["ok"] is False
            assert "nicht konfiguriert" in result["error"]

    def test_request_exception_returned(self):
        with patch("utils.jira_helper.get_jira_config",
                   return_value={"base_url": "https://x", "api_token": "t"}):
            with patch("utils.jira_helper._detect_api_version", return_value=2):
                with patch("utils.jira_helper.requests.get",
                           side_effect=requests.RequestException("network down")):
                    result = jh.test_connection()
                    assert result["ok"] is False
                    assert "network down" in result["error"]


class TestGetProjects:
    def test_server_returns_list_directly(self):
        with patch("utils.jira_helper.get_jira_config",
                   return_value={"base_url": "https://j", "api_token": "t"}):
            with patch("utils.jira_helper._detect_api_version", return_value=2):
                with patch("utils.jira_helper.requests.get") as mock_get:
                    mock_get.return_value = _mock_response(
                        200, [{"key": "KI", "name": "KI Project"}]
                    )
                    projects = jh.get_projects()
                    assert projects == [{"key": "KI", "name": "KI Project"}]

    def test_cloud_unwraps_values(self):
        with patch("utils.jira_helper.get_jira_config",
                   return_value={"base_url": "https://c", "api_token": "t", "email": "u@y"}):
            with patch("utils.jira_helper._detect_api_version", return_value=3):
                with patch("utils.jira_helper.requests.get") as mock_get:
                    mock_get.return_value = _mock_response(
                        200, {"values": [{"key": "X", "name": "X"}]}
                    )
                    assert jh.get_projects() == [{"key": "X", "name": "X"}]


class TestBuildDescription:
    def test_wiki_contains_test_metadata(self):
        out = jh._build_description_wiki(
            {"name": "test_x", "suite": "ui", "message": "boom"},
            environment_url="https://e.com",
            run_date="01.01.2026",
        )
        assert "test_x" in out
        assert "UI" in out
        assert "boom" in out
        assert "01.01.2026" in out

    def test_wiki_uses_default_when_no_message(self):
        out = jh._build_description_wiki(
            {"name": "test_x", "suite": "ui"},
            environment_url="https://e",
            run_date="01.01",
        )
        assert "Kein weiterer Fehlerdetail" in out

    def test_adf_is_doc_v1(self):
        out = jh._build_description_adf(
            {"name": "test_x", "suite": "ui", "message": "boom"},
            environment_url="https://e.com",
            run_date="01.01.2026",
        )
        assert out["type"] == "doc"
        assert out["version"] == 1
        # Tabelle und Codeblock vorhanden
        types = [block["type"] for block in out["content"]]
        assert "table" in types
        assert "codeBlock" in types


class TestCreateTicket:
    def test_success_returns_key_and_url(self):
        config = {"base_url": "https://j", "api_token": "t", "project_key": "KI"}
        with patch("utils.jira_helper.get_jira_config", return_value=config):
            with patch("utils.jira_helper._detect_api_version", return_value=2):
                with patch("utils.jira_helper.requests.post") as mock_post:
                    mock_post.return_value = _mock_response(201, {"key": "KI-1"})
                    out = jh.create_ticket(
                        summary="x",
                        result={"name": "test_a", "suite": "ui", "message": "m"},
                        environment_url="https://e",
                        run_date="01.01",
                    )
                    assert out["ok"] is True
                    assert out["key"] == "KI-1"
                    assert out["url"] == "https://j/browse/KI-1"

    def test_missing_project_raises(self):
        config = {"base_url": "https://j", "api_token": "t"}
        with patch("utils.jira_helper.get_jira_config", return_value=config):
            with patch("utils.jira_helper._detect_api_version", return_value=2):
                with pytest.raises(ValueError, match="Projektschluessel"):
                    jh.create_ticket(
                        summary="x",
                        result={"name": "t"},
                        environment_url="",
                        run_date="",
                    )

    def test_http_error_returns_not_ok(self):
        config = {"base_url": "https://j", "api_token": "t", "project_key": "KI"}
        with patch("utils.jira_helper.get_jira_config", return_value=config):
            with patch("utils.jira_helper._detect_api_version", return_value=2):
                with patch("utils.jira_helper.requests.post") as mock_post:
                    mock_post.return_value = _mock_response(400, text="Bad")
                    out = jh.create_ticket(
                        summary="x",
                        result={"name": "t", "suite": "ui"},
                        environment_url="",
                        run_date="",
                    )
                    assert out["ok"] is False
                    assert "400" in out["error"]


class TestCreateTicketsForFailures:
    def test_only_failures_create_tickets(self):
        results = [
            {"name": "test_a", "outcome": "passed", "suite": "ui"},
            {"name": "test_b", "outcome": "failed", "suite": "ui"},
            {"name": "test_c", "outcome": "error", "suite": "ui"},
            {"name": "test_d", "outcome": "skipped", "suite": "ui"},
        ]
        with patch("utils.jira_helper.create_ticket",
                   return_value={"ok": True, "key": "K-1"}) as mock_create:
            out = jh.create_tickets_for_failures(
                results, "https://e", project_key="KI", issue_type="Bug"
            )
            assert mock_create.call_count == 2
            assert len(out) == 2
            assert all(t["ok"] for t in out)
            assert all("test_name" in t for t in out)

    def test_summary_format(self):
        results = [{"name": "test_widget_visible", "outcome": "failed", "suite": "ui"}]
        captured = {}

        def _fake(**kwargs):
            captured.update(kwargs)
            return {"ok": True}

        with patch("utils.jira_helper.create_ticket", side_effect=_fake):
            jh.create_tickets_for_failures(results, "https://e", project_key="KI")
            assert captured["summary"] == "[UI] Widget visible"
