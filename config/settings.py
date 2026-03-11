"""Zentrale Konfiguration fuer das UI/UX-Testing-Tool."""

from __future__ import annotations

from pathlib import Path

import yaml
from dotenv import load_dotenv
import os

# Projektverzeichnis
ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
REPORTS_DIR = ROOT_DIR / "reports"
SCREENSHOTS_DIR = ROOT_DIR / "screenshots"
TEMPLATES_DIR = ROOT_DIR / "templates"
AUTH_DIR = ROOT_DIR / ".auth"

# .env laden
load_dotenv(ROOT_DIR / ".env")

# Browser-Einstellungen
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))
BROWSER = os.getenv("BROWSER", "chromium")

# Timeouts
NAVIGATION_TIMEOUT = int(os.getenv("NAVIGATION_TIMEOUT", "30000"))
RESPONSE_TIMEOUT = int(os.getenv("RESPONSE_TIMEOUT", "30000"))

# Report
TESTER_NAME = os.getenv("TESTER_NAME", "Tester")


def _load_yaml(filename: str) -> dict:
    """Lade eine YAML-Konfigurationsdatei."""
    path = CONFIG_DIR / filename
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_environments() -> dict:
    """Lade alle konfigurierten Umgebungen."""
    data = _load_yaml("environments.yaml")
    return data.get("environments", {})


def get_environment(name: str | None = None) -> dict:
    """Lade eine spezifische Umgebung. Fallback auf Default."""
    # Direkter URL-Override via Umgebungsvariable (vom Web-Frontend gesetzt)
    direct_url = os.getenv("CHATBOT_URL")
    if direct_url:
        return {
            "name": name or "custom",
            "url": direct_url,
            "description": "Direkte URL",
            "login_url": os.getenv("CHATBOT_LOGIN_URL", ""),
            "username": os.getenv("CHATBOT_USERNAME", ""),
            "password": os.getenv("CHATBOT_PASSWORD", ""),
        }

    envs = _load_yaml("environments.yaml")
    env_name = name or os.getenv("DEFAULT_ENV") or envs.get("default", "dev")
    environments = envs.get("environments", {})
    if env_name not in environments:
        raise ValueError(
            f"Umgebung '{env_name}' nicht gefunden. "
            f"Verfügbar: {list(environments.keys())}"
        )
    env = environments[env_name]
    env["name"] = env_name
    return env


def save_environments(environments: dict, default: str | None = None) -> None:
    """Speichere Umgebungen in environments.yaml."""
    path = CONFIG_DIR / "environments.yaml"
    data = {"environments": environments}
    if default:
        data["default"] = default
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def add_environment(
    name: str,
    url: str,
    description: str = "",
    login_url: str = "",
    username: str = "",
    password: str = "",
) -> None:
    """Füge eine neue Umgebung hinzu oder aktualisiere eine bestehende."""
    envs = get_environments()
    envs[name] = {"url": url}
    if description:
        envs[name]["description"] = description
    if login_url:
        envs[name]["login_url"] = login_url
    if username:
        envs[name]["username"] = username
    if password:
        envs[name]["password"] = password
    save_environments(envs)


def remove_environment(name: str) -> None:
    """Entferne eine Umgebung."""
    envs = get_environments()
    envs.pop(name, None)
    save_environments(envs)


def get_selectors() -> dict:
    """Lade CSS-Selektoren für das Chat-Widget."""
    data = _load_yaml("selectors.yaml")
    return data.get("chat_widget", {})


def save_selectors(selectors: dict) -> None:
    """Speichere CSS-Selektoren nach Discovery."""
    path = CONFIG_DIR / "selectors.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump({"chat_widget": selectors}, f, default_flow_style=False)


def get_brand() -> dict:
    """Lade Branding-Konfiguration."""
    data = _load_yaml("brand.yaml")
    return data.get("brand", {})
