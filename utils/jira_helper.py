"""Jira REST API Integration fuer das UI/UX-Testing-Tool.

Unterstuetzt Jira Server/Data Center (REST API v2) und Jira Cloud (REST API v3).
Erkennung erfolgt automatisch ueber /rest/api/2/serverInfo.
"""

from __future__ import annotations

from base64 import b64encode
from datetime import datetime
from typing import Any

import requests

from config.settings import get_jira_config

# Cache fuer erkannte API-Version (pro base_url)
_api_version_cache: dict[str, int] = {}


def _is_server(config: dict) -> bool:
    """Pruefe ob es sich um Jira Server/DC handelt (API v2)."""
    return _detect_api_version(config) == 2


def _headers(config: dict) -> dict:
    """Erstelle Authorization-Header fuer Jira REST API.

    Jira Server/DC: Bearer Token (Personal Access Token)
    Jira Cloud: Basic Auth (email:api_token)
    """
    email = (config.get("email") or "").strip()
    token = (config.get("api_token") or "").strip()
    if not token:
        raise ValueError("Jira API-Token ist erforderlich.")

    base = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if _is_server(config):
        # Jira Server/DC: PAT als Bearer Token
        base["Authorization"] = f"Bearer {token}"
    elif email:
        # Jira Cloud: Basic Auth mit email:token
        credentials = b64encode(f"{email}:{token}".encode()).decode()
        base["Authorization"] = f"Basic {credentials}"
    else:
        raise ValueError("Fuer Jira Cloud ist eine E-Mail-Adresse erforderlich.")

    return base


def _base_url(config: dict) -> str:
    url = (config.get("base_url") or "").rstrip("/")
    if not url:
        raise ValueError("Jira-URL ist nicht konfiguriert.")
    return url


def _detect_api_version(config: dict) -> int:
    """Erkennt ob Jira Server (v2) oder Jira Cloud (v3) vorliegt."""
    base = _base_url(config)
    if base in _api_version_cache:
        return _api_version_cache[base]

    token = (config.get("api_token") or "").strip()
    # Teste Server-API ohne _headers (vermeidet Rekursion)
    try:
        resp = requests.get(
            f"{base}/rest/api/2/serverInfo",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("deploymentType") == "Server" or data.get("versionNumbers"):
                _api_version_cache[base] = 2
                return 2
    except (requests.RequestException, ValueError):
        pass

    _api_version_cache[base] = 3
    return 3


def _api_url(config: dict, path: str) -> str:
    """Erstelle die vollstaendige API-URL mit korrekter Versionsnummer."""
    version = _detect_api_version(config)
    return f"{_base_url(config)}/rest/api/{version}/{path}"


def test_connection() -> dict:
    """Teste die Jira-Verbindung."""
    config = get_jira_config()
    try:
        url = _api_url(config, "myself")
        resp = requests.get(url, headers=_headers(config), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"ok": True, "user": data.get("displayName", data.get("emailAddress", ""))}
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    except requests.RequestException as e:
        return {"ok": False, "error": str(e)}


def get_projects() -> list[dict]:
    """Gibt eine Liste aller zugaenglichen Jira-Projekte zurueck."""
    config = get_jira_config()
    version = _detect_api_version(config)

    if version == 2:
        # Jira Server: /rest/api/2/project
        url = _api_url(config, "project")
        resp = requests.get(url, headers=_headers(config), timeout=10)
        resp.raise_for_status()
        data = resp.json()  # direkt eine Liste
        return [{"key": p["key"], "name": p["name"]} for p in data]
    else:
        # Jira Cloud: /rest/api/3/project/search
        url = _api_url(config, "project/search?maxResults=50&orderBy=name")
        resp = requests.get(url, headers=_headers(config), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [{"key": p["key"], "name": p["name"]} for p in data.get("values", [])]


def _build_description_wiki(result: dict, environment_url: str, run_date: str) -> str:
    """Erstelle eine Jira-Wiki-Markup-Beschreibung (fuer Jira Server/DC)."""
    test_name = result.get("name", "")
    suite = result.get("suite", "")
    message = result.get("message", "") or "Kein weiterer Fehlerdetail verfuegbar."

    return (
        f"*Automatisch erstellt durch UI/UX-Testing-Tool*\n\n"
        f"||Feld||Wert||\n"
        f"|Datum|{run_date}|\n"
        f"|URL|{environment_url}|\n"
        f"|Testsuite|{suite.upper() if suite else '-'}|\n"
        f"|Test|{test_name}|\n\n"
        f"*Fehlermeldung:*\n"
        f"{{code}}\n{message}\n{{code}}"
    )


def _build_description_adf(result: dict, environment_url: str, run_date: str) -> dict:
    """Erstelle eine ADF-Beschreibung (fuer Jira Cloud)."""
    test_name = result.get("name", "")
    suite = result.get("suite", "")
    message = result.get("message", "") or "Kein weiterer Fehlerdetail verfuegbar."

    def bold_text(text: str) -> dict:
        return {"type": "text", "text": text, "marks": [{"type": "strong"}]}

    def code_block(text: str) -> dict:
        return {
            "type": "codeBlock",
            "attrs": {},
            "content": [{"type": "text", "text": text}],
        }

    def table_row(label: str, value: str) -> dict:
        def cell(text: str, header: bool = False) -> dict:
            return {
                "type": "tableHeader" if header else "tableCell",
                "attrs": {},
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
            }
        return {"type": "tableRow", "content": [cell(label, header=True), cell(value)]}

    return {
        "version": 1,
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [bold_text("Automatisch erstellt durch UI/UX-Testing-Tool")]},
            {
                "type": "table",
                "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                "content": [
                    table_row("Datum", run_date),
                    table_row("URL", environment_url),
                    table_row("Testsuite", suite.upper() if suite else "-"),
                    table_row("Test", test_name),
                ],
            },
            {"type": "paragraph", "content": [bold_text("Fehlermeldung:")]},
            code_block(message),
        ],
    }


def create_ticket(
    summary: str,
    result: dict,
    environment_url: str,
    run_date: str,
    project_key: str | None = None,
    issue_type: str | None = None,
) -> dict:
    """Erstelle ein einzelnes Jira-Ticket fuer ein fehlgeschlagenes Testergebnis."""
    config = get_jira_config()
    project = project_key or config.get("project_key") or ""
    itype = issue_type or config.get("issue_type") or "Bug"
    version = _detect_api_version(config)

    if not project:
        raise ValueError("Jira-Projektschluessel ist nicht konfiguriert.")

    if version == 2:
        description = _build_description_wiki(result, environment_url, run_date)
    else:
        description = _build_description_adf(result, environment_url, run_date)

    payload: dict[str, Any] = {
        "fields": {
            "project": {"key": project},
            "issuetype": {"name": itype},
            "summary": summary,
            "description": description,
        }
    }

    url = _api_url(config, "issue")
    resp = requests.post(url, headers=_headers(config), json=payload, timeout=15)

    if resp.status_code in (200, 201):
        data = resp.json()
        issue_key = data.get("key", "")
        issue_url = f"{_base_url(config)}/browse/{issue_key}"
        return {"ok": True, "key": issue_key, "url": issue_url}

    return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}


def create_tickets_for_failures(
    results: list[dict],
    environment_url: str,
    project_key: str | None = None,
    issue_type: str | None = None,
) -> list[dict]:
    """Erstelle Jira-Tickets fuer alle fehlgeschlagenen Tests eines Laufs."""
    run_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    created = []

    for result in results:
        if result.get("outcome") not in ("failed", "error"):
            continue

        test_name = result.get("name", "")
        suite = (result.get("suite") or "").upper()
        label = test_name.replace("test_", "").replace("_", " ").capitalize()
        summary = f"[{suite}] {label}"

        ticket = create_ticket(
            summary=summary,
            result=result,
            environment_url=environment_url,
            run_date=run_date,
            project_key=project_key,
            issue_type=issue_type,
        )
        ticket["test_name"] = test_name
        created.append(ticket)

    return created
