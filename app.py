#!/usr/bin/env python3
"""UI/UX-Testing-Tool: Web-Frontend."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
from flask_wtf.csrf import CSRFProtect

from config.settings import (
    get_environments,
    get_environment,
    get_selectors,
    get_brand,
    save_selectors,
    add_environment,
    remove_environment,
    get_jira_config,
    save_jira_config,
    REPORTS_DIR,
    SCREENSHOTS_DIR,
    ROOT_DIR,
)

def _load_app_secret() -> str:
    """Lese den Flask-Session-Secret-Key aus der Umgebung. Fallback auf
    Zufallswert, wenn FLASK_SECRET_KEY nicht gesetzt ist (lokale Dev).
    Production muss FLASK_SECRET_KEY explizit setzen, sonst werden alle
    Sessions beim Restart ungueltig.
    """
    return os.environ.get("FLASK_SECRET_KEY") or os.urandom(32).hex()


app = Flask(
    __name__,
    template_folder="templates/web",
    static_folder="static",
)
app.secret_key = _load_app_secret()
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"

csrf = CSRFProtect(app)

# Aktive Testläufe speichern
test_runs: dict[str, dict] = {}

_TESTRUN_NOT_FOUND = "Testlauf nicht gefunden"


@app.route("/", methods=["GET"])
def index():
    """Dashboard-Startseite."""
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def api_status():
    """Health-Check-Endpoint fuer Kubernetes Probes."""
    return jsonify({"status": "ok"})


@app.route("/api/environments", methods=["GET"])
def api_environments():
    """Alle konfigurierten Umgebungen."""
    envs = get_environments()
    return jsonify(envs)


@app.route("/api/environments", methods=["POST"])
def api_add_environment():
    """Neue Umgebung hinzufügen oder bestehende aktualisieren."""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    description = (data.get("description") or "").strip()
    login_url = (data.get("login_url") or "").strip()
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not name or not url:
        return jsonify({"error": "Name und URL sind erforderlich"}), 400

    add_environment(name, url, description, login_url, username, password)
    return jsonify({"status": "ok", "name": name})


@app.route("/api/environments/<name>", methods=["DELETE"])
def api_remove_environment(name):
    """Umgebung entfernen."""
    remove_environment(name)
    return jsonify({"status": "ok"})


@app.route("/api/selectors", methods=["GET"])
def api_selectors():
    """Aktuelle CSS-Selektoren."""
    sels = get_selectors()
    configured = sum(1 for v in sels.values() if v is not None)
    return jsonify({
        "selectors": sels,
        "configured": configured,
        "total": len(sels),
    })


@app.route("/api/selectors", methods=["POST"])
def api_save_selectors():
    """CSS-Selektoren speichern."""
    data = request.get_json()
    save_selectors(data)
    return jsonify({"status": "ok"})


@app.route("/api/brand", methods=["GET"])
def api_brand():
    """Branding-Konfiguration."""
    return jsonify(get_brand())


def _classify_report(name: str) -> str:
    """Ordne einen Report-Dateinamen einer Kategorie zu."""
    if name.startswith("website_scan_"):
        return "website"
    if name.startswith("checklist_"):
        return "checklist"
    if name.startswith("testbericht_"):
        return "chatbot"
    return "unknown"


@app.route("/api/reports", methods=["GET"])
def api_reports():
    """Liste aller generierten Reports, neueste zuerst."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(
        REPORTS_DIR.glob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    reports = []
    for f in files:
        reports.append({
            "name": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            "kind": _classify_report(f.name),
        })
    return jsonify(reports)


@app.route("/api/reports/<name>", methods=["GET"])
def api_report_content(name):
    """Inhalt eines Reports."""
    path = REPORTS_DIR / name
    if not path.exists() or not path.is_file():
        return jsonify({"error": "Report nicht gefunden"}), 404
    return jsonify({"content": path.read_text(encoding="utf-8")})


@app.route("/api/screenshots", methods=["GET"])
def api_screenshots():
    """Liste aller Screenshots."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    shots = []
    for f in sorted(SCREENSHOTS_DIR.glob("*.png"), reverse=True):
        shots.append({
            "name": f.name,
            "path": f"/static_screenshots/{f.name}",
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
    return jsonify(shots)


@app.route("/static_screenshots/<name>", methods=["GET"])
def serve_screenshot(name):
    """Screenshot-Dateien ausliefern."""
    from flask import send_from_directory
    return send_from_directory(str(SCREENSHOTS_DIR), name)


@app.route("/static_screenshots/website_scan/<name>", methods=["GET"])
def serve_website_scan_screenshot(name):
    """Website-Scan Screenshots ausliefern."""
    from flask import send_from_directory
    scan_dir = SCREENSHOTS_DIR / "website_scan"
    return send_from_directory(str(scan_dir), name)


@app.route("/live-browser", methods=["GET"])
def live_browser():
    """Aktueller Live-Screenshot des Playwright-Browsers (fuer MFA-Anzeige)."""
    from flask import send_file
    live_path = SCREENSHOTS_DIR / "_live.png"
    if not live_path.exists():
        return "", 204
    response = send_file(str(live_path), mimetype="image/png")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response


_SUITE_PATH_MAP = {
    "ui": "tests/ui/",
    "ux": "tests/ux/",
    "a11y": "tests/a11y/",
    "flows": "tests/ux/test_chatbot_flows.py",
}


def _build_pytest_command(env_name: str, suite: str | None) -> list[str]:
    cmd = [
        sys.executable, "-m", "pytest",
        "-v", "--tb=short",
        "--override-ini=addopts=",
    ]
    if env_name:
        cmd.extend(["--env", env_name])
    suite_path = _SUITE_PATH_MAP.get(suite or "")
    if suite_path:
        cmd.append(suite_path)
    return cmd


def _build_pytest_env(
    url: str | None,
    login_url: str | None,
    username: str | None,
    password: str | None,
) -> dict:
    env = dict(os.environ)
    for key, value in (
        ("CHATBOT_URL", url),
        ("CHATBOT_LOGIN_URL", login_url),
        ("CHATBOT_USERNAME", username),
        ("CHATBOT_PASSWORD", password),
    ):
        if value:
            env[key] = value
    return env


def _cancel_subprocess(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _consume_pytest_output(run: dict, proc: subprocess.Popen) -> list[str] | None:
    """Iteriere stdout, parse Ergebnisse. Gibt None zurueck bei Cancel."""
    output_lines: list[str] = []
    for line in proc.stdout:
        if run.get("_cancel"):
            _cancel_subprocess(proc)
            run["status"] = "cancelled"
            run["finished_at"] = datetime.now().isoformat()
            return None

        line = line.rstrip()
        output_lines.append(line)
        run["output"] = output_lines
        if "::" in line:
            _parse_test_line(run, line)
    return output_lines


def _attach_error_messages(run: dict, output_lines: list[str]) -> None:
    error_messages = _extract_error_messages(output_lines)
    for r in run.get("results", []):
        if r["outcome"] in ("failed", "error") and not r.get("message"):
            r["message"] = error_messages.get(r["name"], "")


def _run_tests_worker(
    run_id: str,
    env_name: str,
    suite: str | None,
    url: str | None = None,
    login_url: str | None = None,
    username: str | None = None,
    password: str | None = None,
):
    """Worker-Thread: Führt pytest aus und sammelt Ergebnisse."""
    run = test_runs[run_id]
    run["status"] = "running"
    run["started_at"] = datetime.now().isoformat()

    cmd = _build_pytest_command(env_name, suite)
    env = _build_pytest_env(url, login_url, username, password)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(ROOT_DIR),
            env=env,
        )
        run["_proc"] = proc

        output_lines = _consume_pytest_output(run, proc)
        if output_lines is None:
            return  # cancelled

        proc.wait()
        run["exit_code"] = proc.returncode
        run["status"] = "completed"
        run["finished_at"] = datetime.now().isoformat()

        _attach_error_messages(run, output_lines)
        _generate_report_for_run(run, env_name, suite, url)

    except Exception as e:
        run["status"] = "error"
        run["error"] = str(e)
    finally:
        run.pop("_proc", None)


_TEST_LINE_RE = re.compile(
    r"^(tests/\S+::\S+)\s+(PASSED|FAILED|SKIPPED|ERROR)"
)


def _parse_test_line(run: dict, line: str):
    """Parse eine pytest-Output-Zeile nach Testergebnissen.

    Erkennt nur echte pytest-verbose-Ergebniszeilen im Format:
      tests/ui/test_file.py::TestClass::test_method PASSED  [ 5%]

    Ignoriert Short-Test-Summary-Zeilen (z.B. 'FAILED tests/...' oder
    'ERROR tests/...') wo das Keyword am Zeilenanfang steht.
    """
    match = _TEST_LINE_RE.match(line.strip())
    if not match:
        return

    test_path = match.group(1)  # z.B. tests/ui/test_file.py::TestClass::test_method
    outcome = match.group(2).lower()  # passed, failed, skipped, error

    # Testname = letzter Teil nach ::
    parts = test_path.split("::")
    name = parts[-1] if parts else test_path

    suite = "unknown"
    if "tests/ui/" in test_path:
        suite = "ui"
    elif "tests/ux/" in test_path:
        suite = "ux"
    elif "tests/a11y/" in test_path:
        suite = "a11y"

    run.setdefault("results", []).append({
        "name": name,
        "outcome": outcome,
        "suite": suite,
        "raw": line.strip(),
    })


_FAILURE_HEADER_RE = re.compile(r"^_+ (.+?) _+$")
_SETUP_ERROR_PREFIX_RE = re.compile(r"^ERROR at (?:setup|teardown) of ")


def _is_failures_section_start(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("=") and ("FAILURES" in line or "ERRORS" in line)


def _is_failures_section_end(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("=") and "short test summary" in line


def _parse_failure_header(line: str) -> str | None:
    match = _FAILURE_HEADER_RE.match(line.strip())
    if not match:
        return None
    header_text = _SETUP_ERROR_PREFIX_RE.sub("", match.group(1))
    return header_text.split(".")[-1] if "." in header_text else header_text


def _extract_error_messages(output_lines: list[str]) -> dict[str, str]:
    """Extrahiere Fehlermeldungen aus dem pytest-Output.

    Sucht nach FAILURES/ERRORS Sektionen und ordnet die Fehlerdetails
    den jeweiligen Testnamen zu.

    Returns:
        Dict {test_name: fehlermeldung}
    """
    errors: dict[str, str] = {}
    current_test: str | None = None
    current_lines: list[str] = []
    in_failures = False

    def _flush():
        if current_test and current_lines:
            errors[current_test] = _clean_error_block(current_lines)

    for line in output_lines:
        if _is_failures_section_start(line):
            in_failures = True
            continue
        if not in_failures:
            continue
        if _is_failures_section_end(line):
            _flush()
            break

        header_name = _parse_failure_header(line)
        if header_name is not None:
            _flush()
            current_test = header_name
            current_lines = []
        elif current_test:
            current_lines.append(line)

    _flush()
    return errors


def _clean_error_block(lines: list[str]) -> str:
    """Bereinige einen Fehlerblock: nur die relevanten Zeilen behalten."""
    relevant = []
    for line in lines:
        stripped = line.strip()
        # Leere Zeilen und Datei-Pfade ueberspringen
        if not stripped:
            continue
        # E-Zeilen (pytest Error-Output) sind am wichtigsten
        if stripped.startswith("E "):
            relevant.append(stripped[2:].strip())
        # AssertionError Zeilen
        elif "Error" in stripped and "::" not in stripped:
            relevant.append(stripped)

    if not relevant:
        # Fallback: letzte nicht-leere Zeilen
        non_empty = [l.strip() for l in lines if l.strip()]
        relevant = non_empty[-3:] if len(non_empty) > 3 else non_empty

    return " | ".join(relevant[:5])  # Max 5 Zeilen, mit | getrennt


def _generate_report_for_run(run: dict, env_name: str, suite: str | None, url: str | None = None):
    """Generiere einen Report nach dem Testlauf."""
    try:
        results = run.get("results", [])
        if not results:
            return

        if url:
            env = {"name": env_name or "custom", "url": url, "description": "Direkte URL"}
        else:
            env = get_environment(env_name)

        # Ergebnisse fürs Report-Format aufbereiten (message bereits in results vorhanden)
        report_results = []
        for r in results:
            report_results.append({
                "name": r["name"],
                "outcome": r["outcome"],
                "message": r.get("message", ""),
                "duration": 0,
                "suite": r["suite"],
            })

        from utils.report_generator import generate_report, generate_suite_report
        if suite:
            path = generate_suite_report(suite, report_results, env)
        else:
            path = generate_report(report_results, env)

        run["report_path"] = str(path)
        run["report_name"] = path.name
    except Exception as e:
        run["report_error"] = str(e)


@app.route("/api/tests/run", methods=["POST"])
def api_run_tests():
    """Starte einen neuen Testlauf."""
    data = request.get_json() or {}
    env_name = data.get("environment")
    suite = data.get("suite")  # leer: alle Suites
    url = (data.get("url") or "").strip() or None  # direkt uebergebene URL
    login_url = (data.get("login_url") or "").strip() or None
    username = (data.get("username") or "").strip() or None
    password = (data.get("password") or "").strip() or None

    run_id = str(uuid.uuid4())[:8]
    test_runs[run_id] = {
        "id": run_id,
        "environment": env_name or "custom",
        "url": url,
        "suite": suite,
        "status": "starting",
        "results": [],
        "output": [],
    }

    thread = threading.Thread(
        target=_run_tests_worker,
        args=(run_id, env_name, suite, url, login_url, username, password),
        daemon=True,
    )
    thread.start()

    return jsonify({"run_id": run_id})


@app.route("/api/tests/status/<run_id>", methods=["GET"])
def api_test_status(run_id):
    """Status eines Testlaufs abfragen."""
    run = test_runs.get(run_id)
    if not run:
        return jsonify({"error": _TESTRUN_NOT_FOUND}), 404

    results = run.get("results", [])
    passed = sum(1 for r in results if r["outcome"] == "passed")
    failed = sum(1 for r in results if r["outcome"] in ("failed", "error"))
    skipped = sum(1 for r in results if r["outcome"] == "skipped")

    return jsonify({
        "id": run["id"],
        "status": run["status"],
        "environment": run.get("environment"),
        "suite": run.get("suite"),
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "results": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        },
        "output": run.get("output", [])[-30:],  # Letzte 30 Zeilen
        "report_name": run.get("report_name"),
        "error": run.get("error"),
    })


@app.route("/api/tests/cancel/<run_id>", methods=["POST"])
def api_cancel_tests(run_id):
    """Laufenden Testlauf abbrechen."""
    run = test_runs.get(run_id)
    if not run:
        return jsonify({"error": _TESTRUN_NOT_FOUND}), 404

    if run["status"] != "running":
        return jsonify({"error": "Testlauf laeuft nicht"}), 400

    # Signal an den Worker-Thread
    run["_cancel"] = True

    # Prozess direkt beenden falls vorhanden
    proc = run.get("_proc")
    if proc and proc.poll() is None:
        proc.terminate()

    return jsonify({"status": "ok", "message": "Abbruch angefordert"})


@app.route("/api/tests/stream/<run_id>", methods=["GET"])
def api_test_stream(run_id):
    """Server-Sent Events Stream für Live-Updates."""
    def generate():
        last_count = 0
        while True:
            run = test_runs.get(run_id)
            if not run:
                yield f"data: {json.dumps({'error': 'not found'})}\n\n"
                break

            results = run.get("results", [])
            if len(results) > last_count:
                for r in results[last_count:]:
                    yield f"data: {json.dumps({'type': 'result', 'data': r})}\n\n"
                last_count = len(results)

            if run["status"] in ("completed", "error", "cancelled"):
                passed = sum(1 for r in results if r["outcome"] == "passed")
                failed = sum(1 for r in results if r["outcome"] in ("failed", "error"))
                skipped = sum(1 for r in results if r["outcome"] == "skipped")
                yield f"data: {json.dumps({'type': 'done', 'data': {'status': run['status'], 'passed': passed, 'failed': failed, 'skipped': skipped, 'report_name': run.get('report_name')}})}\n\n"
                break

            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


def _merge_discovered_selectors(found: dict) -> dict:
    """Nur nicht-None-Werte ueberschreiben den bestehenden Selektor-Stand."""
    merged = dict(get_selectors())
    for key, value in found.items():
        if value is not None:
            merged[key] = value
    return merged


@app.route("/api/discovery/run", methods=["POST"])
def api_run_discovery():
    """Starte Selektor-Discovery."""
    data = request.get_json() or {}
    env_name = data.get("environment")
    url = (data.get("url") or "").strip() or None
    login_url = (data.get("login_url") or "").strip() or None
    username = (data.get("username") or "").strip() or None
    password = (data.get("password") or "").strip() or None

    try:
        from utils.discovery import discover_selectors, discover_selectors_by_url

        if url:
            result = discover_selectors_by_url(
                url,
                login_url=login_url,
                username=username,
                password=password,
            )
        else:
            result = discover_selectors(env_name)

        if result and result.get("selectors"):
            merged = _merge_discovered_selectors(result["selectors"])
            save_selectors(merged)
            result["selectors"] = merged
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/jira/config", methods=["GET"])
def api_jira_config_get():
    """Jira-Konfiguration lesen (api_token wird maskiert)."""
    config = get_jira_config()
    safe = dict(config)
    if safe.get("api_token"):
        safe["api_token"] = "***"
    return jsonify(safe)


@app.route("/api/jira/config", methods=["POST"])
def api_jira_config_save():
    """Jira-Konfiguration speichern."""
    data = request.get_json() or {}
    existing = get_jira_config()

    # api_token nur aktualisieren wenn ein echter Wert gesendet wurde
    new_token = (data.get("api_token") or "").strip()
    config = {
        "base_url": (data.get("base_url") or "").strip() or None,
        "email": (data.get("email") or "").strip() or None,
        "api_token": new_token if new_token and new_token != "***" else existing.get("api_token"),
        "project_key": (data.get("project_key") or "").strip() or None,
        "issue_type": (data.get("issue_type") or "Bug").strip(),
    }
    save_jira_config(config)
    return jsonify({"ok": True})


@app.route("/api/jira/test-connection", methods=["GET"])
def api_jira_test_connection():
    """Testet ob Jira erreichbar und Zugangsdaten korrekt sind."""
    from utils.jira_helper import test_connection
    return jsonify(test_connection())


@app.route("/api/jira/projects", methods=["GET"])
def api_jira_projects():
    """Gibt alle zugaenglichen Jira-Projekte zurueck."""
    from utils.jira_helper import get_projects
    try:
        projects = get_projects()
        return jsonify({"ok": True, "projects": projects})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/jira/create-tickets", methods=["POST"])
def api_jira_create_tickets():
    """Erstellt Jira-Tickets fuer fehlgeschlagene Tests eines Testlaufs."""
    from utils.jira_helper import create_tickets_for_failures
    data = request.get_json() or {}
    run_id = data.get("run_id")
    project_key = (data.get("project_key") or "").strip() or None
    issue_type = (data.get("issue_type") or "").strip() or None
    environment_url = (data.get("url") or "").strip()

    if not run_id:
        return jsonify({"ok": False, "error": "run_id fehlt"}), 400

    run = test_runs.get(run_id)
    if not run:
        return jsonify({"ok": False, "error": _TESTRUN_NOT_FOUND}), 404

    results = run.get("results", [])
    selected_tests = data.get("selected_tests")  # Liste von Display-Namen oder None
    if not environment_url:
        environment_url = run.get("url") or ""

    # Falls nur bestimmte Tests ausgewaehlt: filtern
    if selected_tests:
        def _display_name(name: str) -> str:
            return name.replace("test_", "").replace("_", " ").capitalize()
        selected_set = set(selected_tests)
        results = [r for r in results if _display_name(r.get("name", "")) in selected_set]

    try:
        created = create_tickets_for_failures(
            results=results,
            environment_url=environment_url,
            project_key=project_key,
            issue_type=issue_type,
        )
        return jsonify({"ok": True, "tickets": created})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ──────────────────────────────────────────────────────────────
# Website-Scan Endpoints
# ──────────────────────────────────────────────────────────────

# Aktive Website-Scans (getrennt von Chatbot test_runs)
website_scans: dict[str, dict] = {}


def _run_website_scan_worker(
    run_id: str, url: str, checks: list[str],
    login_url: str | None = None, username: str | None = None, password: str | None = None,
    pre_actions: list[dict] | None = None,
):
    """Worker-Thread für Website-Scan."""
    from utils.website_scanner import WebsiteScanner

    run = website_scans[run_id]
    run["status"] = "running"
    run["started_at"] = datetime.now().isoformat()

    scanner = WebsiteScanner(url, checks, login_url=login_url, username=username, password=password, pre_actions=pre_actions)
    run["_scanner"] = scanner

    try:
        scanner.run()
        run["results"] = scanner.results
        run["status"] = scanner.status
        # Report generieren wenn erfolgreich
        if scanner.results:
            try:
                from utils.report_generator import generate_website_scan_report
                report_path = generate_website_scan_report(
                    results=scanner.results,
                    url=url,
                    checks=checks,
                )
                run["report"] = report_path.name
            except Exception as e:
                run["report_error"] = str(e)
    except Exception as e:
        run["status"] = "error"
        run["error"] = str(e)
    finally:
        run["finished_at"] = datetime.now().isoformat()
        run.pop("_scanner", None)


@app.route("/api/website-scan/run", methods=["POST"])
def api_website_scan_run():
    """Starte einen Website-Scan."""
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()
    checks = data.get("checks") or ["accessibility", "performance", "links", "responsive", "seo"]
    login_url = (data.get("login_url") or "").strip() or None
    username = (data.get("username") or "").strip() or None
    password = (data.get("password") or "").strip() or None
    pre_actions = data.get("pre_actions") or []

    if not url:
        return jsonify({"error": "URL ist erforderlich"}), 400

    run_id = str(uuid.uuid4())[:8]
    website_scans[run_id] = {
        "id": run_id,
        "url": url,
        "checks": checks,
        "status": "starting",
        "results": [],
        "output": [],
    }

    thread = threading.Thread(
        target=_run_website_scan_worker,
        args=(run_id, url, checks, login_url, username, password, pre_actions),
        daemon=True,
    )
    thread.start()
    return jsonify({"run_id": run_id})


def _website_scan_current_results(run: dict) -> list:
    scanner = run.get("_scanner")
    if scanner:
        return scanner.results
    return run.get("results", [])


def _website_scan_done_payload(run: dict) -> str:
    results = _website_scan_current_results(run)
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    warnings = sum(1 for r in results if r["status"] == "warning")
    return json.dumps({
        "type": "done",
        "data": {
            "status": run["status"],
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "total": len(results),
            "report": run.get("report"),
        },
    })


@app.route("/api/website-scan/stream/<run_id>", methods=["GET"])
def api_website_scan_stream(run_id):
    """SSE-Stream für Website-Scan Live-Updates."""
    def generate():
        last_count = 0
        while True:
            run = website_scans.get(run_id)
            if not run:
                yield f"data: {json.dumps({'error': 'not found'})}\n\n"
                break

            results = _website_scan_current_results(run)
            if len(results) > last_count:
                for r in results[last_count:]:
                    yield f"data: {json.dumps({'type': 'result', 'data': r})}\n\n"
                last_count = len(results)

            if run["status"] in ("completed", "error", "cancelled"):
                yield f"data: {_website_scan_done_payload(run)}\n\n"
                break

            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/website-scan/detect", methods=["POST"])
def api_website_scan_detect():
    """Erkennt interaktive Elemente auf einer Seite (Inputs, Buttons)."""
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "URL ist erforderlich"}), 400

    try:
        from playwright.sync_api import sync_playwright
        from config.settings import HEADLESS, SLOW_MO

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
            page = browser.new_page(viewport={"width": 1440, "height": 900}, locale="de-DE")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass  # Seite hat offene Verbindungen, DOM reicht fuer Detect
            page.wait_for_timeout(1000)

            elements = page.evaluate("""() => {
                const inputs = [];
                document.querySelectorAll('input:not([type="hidden"]), textarea').forEach(el => {
                    if (!el.offsetParent && el.type !== 'hidden') return;
                    inputs.push({
                        placeholder: el.placeholder || '',
                        label: el.labels?.[0]?.textContent?.trim() || '',
                        name: el.name || '',
                        type: el.type || 'text',
                    });
                });
                const buttons = [];
                document.querySelectorAll('button, a[role="button"], input[type="submit"]').forEach(el => {
                    const text = el.textContent?.trim() || el.value || '';
                    if (text && el.offsetParent) buttons.push({text});
                });
                return {inputs, buttons};
            }""")
            browser.close()
            return jsonify(elements)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/website-scan/cancel/<run_id>", methods=["POST"])
def api_website_scan_cancel(run_id):
    """Laufenden Website-Scan abbrechen."""
    run = website_scans.get(run_id)
    if not run:
        return jsonify({"error": "Scan nicht gefunden"}), 404
    scanner = run.get("_scanner")
    if scanner:
        scanner.cancel()
    return jsonify({"status": "ok"})


def main():
    """Starte den Web-Server."""
    print("=" * 60)
    print("  UI/UX-Testing-Tool: Web-Frontend")
    print("  http://localhost:5000")
    print("=" * 60)
    debug = os.environ.get("FLASK_ENV") != "production"
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(debug=debug, host=host, port=5000)


if __name__ == "__main__":
    main()
