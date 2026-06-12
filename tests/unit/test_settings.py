"""Unit-Tests fuer config/settings.py — YAML-Loader, Round-trips."""

from __future__ import annotations

import pytest

from config import settings as cfg


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path)
    return tmp_path


class TestLoadYaml:
    def test_missing_file_returns_empty(self, tmp_config):
        assert cfg._load_yaml("does_not_exist.yaml") == {}

    def test_loads_yaml_file(self, tmp_config):
        (tmp_config / "x.yaml").write_text("foo: bar\n", encoding="utf-8")
        assert cfg._load_yaml("x.yaml") == {"foo": "bar"}

    def test_empty_yaml_returns_empty_dict(self, tmp_config):
        (tmp_config / "x.yaml").write_text("", encoding="utf-8")
        assert cfg._load_yaml("x.yaml") == {}


class TestEnvironments:
    def test_get_environments_empty(self, tmp_config):
        assert cfg.get_environments() == {}

    def test_get_environments_loads_data(self, tmp_config):
        (tmp_config / "environments.yaml").write_text(
            "environments:\n  stage:\n    url: https://s.example\n",
            encoding="utf-8",
        )
        envs = cfg.get_environments()
        assert "stage" in envs

    def test_add_and_get_environment(self, tmp_config, monkeypatch):
        monkeypatch.delenv("CHATBOT_URL", raising=False)
        cfg.add_environment("ci", "https://ci.example", description="CI Env")
        env = cfg.get_environment("ci")
        assert env["url"] == "https://ci.example"
        assert env["description"] == "CI Env"
        assert env["name"] == "ci"

    def test_remove_environment(self, tmp_config, monkeypatch):
        monkeypatch.delenv("CHATBOT_URL", raising=False)
        cfg.add_environment("ci", "https://ci.example")
        cfg.remove_environment("ci")
        assert "ci" not in cfg.get_environments()

    def test_remove_unknown_environment_is_noop(self, tmp_config):
        cfg.remove_environment("never-existed")  # should not raise

    def test_get_environment_unknown_raises(self, tmp_config, monkeypatch):
        monkeypatch.delenv("CHATBOT_URL", raising=False)
        monkeypatch.delenv("DEFAULT_ENV", raising=False)
        cfg.add_environment("stage", "https://s.example")
        with pytest.raises(ValueError, match="nicht gefunden"):
            cfg.get_environment("doesnotexist")

    def test_direct_url_override_via_env(self, tmp_config, monkeypatch):
        monkeypatch.setenv("CHATBOT_URL", "https://direct.example")
        monkeypatch.setenv("CHATBOT_USERNAME", "user")
        env = cfg.get_environment()
        assert env["url"] == "https://direct.example"
        assert env["username"] == "user"
        assert env["description"] == "Direkte URL"

    def test_add_environment_optional_fields(self, tmp_config, monkeypatch):
        monkeypatch.delenv("CHATBOT_URL", raising=False)
        cfg.add_environment(
            "full",
            "https://x",
            description="d",
            login_url="https://login",
            username="u",
            password="p",
        )
        env = cfg.get_environment("full")
        assert env["login_url"] == "https://login"
        assert env["username"] == "u"
        assert env["password"] == "p"


class TestSaveEnvironmentsDefault:
    def test_save_with_default(self, tmp_config):
        cfg.save_environments({"a": {"url": "u"}}, default="a")
        loaded = cfg._load_yaml("environments.yaml")
        assert loaded["default"] == "a"


class TestSelectors:
    def test_empty_selectors_returns_empty_dict(self, tmp_config):
        assert cfg.get_selectors() == {}

    def test_save_and_load_selectors(self, tmp_config):
        cfg.save_selectors({"input_field": "#x", "send_button": "#y"})
        assert cfg.get_selectors() == {"input_field": "#x", "send_button": "#y"}


class TestBrand:
    def test_empty_brand_returns_empty_dict(self, tmp_config):
        assert cfg.get_brand() == {}

    def test_loads_brand_data(self, tmp_config):
        (tmp_config / "brand.yaml").write_text(
            "brand:\n  primary_color: '#ff0'\n", encoding="utf-8"
        )
        assert cfg.get_brand() == {"primary_color": "#ff0"}


class TestJiraConfig:
    def test_save_and_load_roundtrip(self, tmp_config):
        config = {
            "base_url": "https://jira.example",
            "api_token": "tok",
            "project_key": "KI",
            "issue_type": "Bug",
            "email": "x@y.de",
        }
        cfg.save_jira_config(config)
        assert cfg.get_jira_config() == config

    def test_fallback_to_env(self, tmp_config, monkeypatch):
        monkeypatch.setenv("JIRA_BASE_URL", "https://from-env")
        monkeypatch.setenv("JIRA_API_TOKEN", "envtok")
        monkeypatch.setenv("JIRA_PROJECT_KEY", "PRJ")
        config = cfg.get_jira_config()
        assert config["base_url"] == "https://from-env"
        assert config["api_token"] == "envtok"
        assert config["project_key"] == "PRJ"

    def test_fallback_skips_empty_envs(self, tmp_config, monkeypatch):
        for var in ("JIRA_BASE_URL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY",
                    "JIRA_ISSUE_TYPE", "JIRA_EMAIL"):
            monkeypatch.delenv(var, raising=False)
        # JIRA_ISSUE_TYPE hat Default "Bug" - nur dieses Feld erwartet
        config = cfg.get_jira_config()
        assert config == {"issue_type": "Bug"}
