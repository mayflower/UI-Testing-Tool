"""Jira REST API Integration fuer das UI/UX-Testing-Tool."""

from __future__ import annotations

from base64 import b64encode
from datetime import datetime
from typing import Any

import requests

from config.settings import get_jira_config


def _headers(config: dict) -> dict:
    """Erstelle Authorization-Header fuer Jira REST API."""
    email = (config.get("email") or "").strip()
    token = (config.get("api_token") or "").strip()
    if not email or not token:
        raise ValueError("Jira E-Mail und API-Token sind erforderlich.")
    credentials = b64encode(f"{email}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _base_url(config: dict) -> str:
    url = (config.get("base_url") or "").rstrip("/")
    if not url:
        raise ValueError("Jira-URL ist nicht konfiguriert.")
    return url


def test_connection() -> dict:
    """Teste die Jira-Verbindung. Gibt {'ok': True, 'user': ...} oder {'ok': False, 'error': ...} zurueck."""
    config = get_jira_config()
    try:
        url = f"{_base_url(config)}/rest/api/3/myself"
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
    url = f"{_base_url(config)}/rest/api/3/project/search?maxResults=50&orderBy=name"
    resp = requests.get(url, headers=_headers(config), timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return [
        {"key": p["key"], "name": p["name"]}
        for p in data.get("values", [])
    ]


def _build_description(result: dict, environment_url: str, run_date: str) -> dict:
    """Erstelle eine ADF-Beschreibung fuer ein Jira-Ticket."""
    test_name = result.get("name", "")
    suite = result.get("suite", "")
    message = result.get("message", "") or "Kein weiterer Fehlerdetail verfuegbar."

    def paragraph(*texts: str) -> dict:
        return {
            "type": "paragraph",
            "content": [{"type": "text", "text": t} for t in texts if t],
        }

    def bold_text(text: str) -> dict:
        return {"type": "text", "text": text, "marks": [{"type": "strong"}]}

    def code_block(text: str) -> dict:
        return {
            "type": "codeBlock",
            "attrs": {},
            "content": [{"type": "text", "text": text}],
        }

    return {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    bold_text("Automatisch erstellt durch UI/UX-Testing-Tool"),
                ],
            },
            {
                "type": "table",
                "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                "content": [
                    _table_row("Datum", run_date),
                    _table_row("URL", environment_url),
                    _table_row("Testsuite", suite.upper() if suite else "-"),
                    _table_row("Test", test_name),
                ],
            },
            paragraph(""),
            {
                "type": "paragraph",
                "content": [bold_text("Fehlermeldung:")],
            },
            code_block(message),
        ],
    }


def _table_row(label: str, value: str) -> dict:
    def cell(text: str, header: bool = False) -> dict:
        return {
            "type": "tableCell" if not header else "tableHeader",
            "attrs": {},
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
        }
    return {"type": "tableRow", "content": [cell(label, header=True), cell(value)]}


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

    if not project:
        raise ValueError("Jira-Projektschluessel ist nicht konfiguriert.")

    payload: dict[str, Any] = {
        "fields": {
            "project": {"key": project},
            "issuetype": {"name": itype},
            "summary": summary,
            "description": _build_description(result, environment_url, run_date),
        }
    }

    url = f"{_base_url(config)}/rest/api/3/issue"
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
