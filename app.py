#!/usr/bin/env python3
"""EP-Testing-Tool: Web-Frontend für UI/UX Tests."""

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

from config.settings import (
    get_environments,
    get_environment,
    get_selectors,
    get_brand,
    save_selectors,
    add_environment,
    remove_environment,
    REPORTS_DIR,
    SCREENSHOTS_DIR,
    ROOT_DIR,
)

app = Flask(
    __name__,
    template_folder="templates/web",
    static_folder="static",
)

# Aktive Testläufe speichern
test_runs: dict[str, dict] = {}


@app.route("/")
def index():
    """Dashboard-Startseite."""
    return render_template("index.html")


@app.route("/api/environments")
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


@app.route("/api/selectors")
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


@app.route("/api/brand")
def api_brand():
    """Branding-Konfiguration."""
    return jsonify(get_brand())


@app.route("/api/reports")
def api_reports():
    """Liste aller generierten Reports."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    for f in sorted(REPORTS_DIR.glob("*.md"), reverse=True):
        reports.append({
            "name": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
    return jsonify(reports)


@app.route("/api/reports/<name>")
def api_report_content(name):
    """Inhalt eines Reports."""
    path = REPORTS_DIR / name
    if not path.exists() or not path.is_file():
        return jsonify({"error": "Report nicht gefunden"}), 404
    return jsonify({"content": path.read_text(encoding="utf-8")})


@app.route("/api/screenshots")
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


@app.route("/static_screenshots/<name>")
def serve_screenshot(name):
    """Screenshot-Dateien ausliefern."""
    from flask import send_from_directory
    return send_from_directory(str(SCREENSHOTS_DIR), name)


@app.route("/live-browser")
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

    cmd = [
        sys.executable, "-m", "pytest",
        "-v", "--tb=short",
        "--override-ini=addopts=",
    ]

    if env_name:
        cmd.extend(["--env", env_name])

    if suite:
        suite_map = {"ui": "tests/ui/", "ux": "tests/ux/", "a11y": "tests/a11y/"}
        if suite in suite_map:
            cmd.append(suite_map[suite])

    # Umgebungsvariablen für den Subprozess
    env = dict(os.environ)
    if url:
        env["CHATBOT_URL"] = url
    if login_url:
        env["CHATBOT_LOGIN_URL"] = login_url
    if username:
        env["CHATBOT_USERNAME"] = username
    if password:
        env["CHATBOT_PASSWORD"] = password

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

        output_lines = []
        for line in proc.stdout:
            # Abbruch prüfen
            if run.get("_cancel"):
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                run["status"] = "cancelled"
                run["finished_at"] = datetime.now().isoformat()
                return

            line = line.rstrip()
            output_lines.append(line)
            run["output"] = output_lines

            # Testergebnisse parsen (Regex in _parse_test_line filtert selbst)
            if "::" in line:
                _parse_test_line(run, line)

        proc.wait()
        run["exit_code"] = proc.returncode
        run["status"] = "completed"
        run["finished_at"] = datetime.now().isoformat()

        # Report generieren
        _generate_report_for_run(run, env_name, suite, url)

    except Exception as e:
        run["status"] = "error"
        run["error"] = str(e)
    finally:
        run.pop("_proc", None)


_TEST_LINE_RE = re.compile(
    r"^(tests/.+?::.+?)\s+(PASSED|FAILED|SKIPPED|ERROR)"
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


def _extract_error_messages(output_lines: list[str]) -> dict[str, str]:
    """Extrahiere Fehlermeldungen aus dem pytest-Output.

    Sucht nach FAILURES/ERRORS Sektionen und ordnet die Fehlerdetails
    den jeweiligen Testnamen zu.

    Returns:
        Dict {test_name: fehlermeldung}
    """
    errors: dict[str, str] = {}
    current_test = None
    current_lines: list[str] = []
    in_failures = False

    for line in output_lines:
        # Beginn der FAILURES/ERRORS Sektion
        if line.strip().startswith("=") and ("FAILURES" in line or "ERRORS" in line):
            in_failures = True
            continue

        # Ende der Sektion (naechste ===... Zeile)
        if in_failures and line.strip().startswith("=") and "short test summary" in line:
            # Letzten Test speichern
            if current_test and current_lines:
                errors[current_test] = _clean_error_block(current_lines)
            break

        if not in_failures:
            continue

        # Neuer Test-Header: ___ TestClass.test_name ___
        header_match = re.match(r"^_+ (.+?) _+$", line.strip())
        if header_match:
            # Vorherigen Test speichern
            if current_test and current_lines:
                errors[current_test] = _clean_error_block(current_lines)
            # Neuen Test starten
            header_text = header_match.group(1)
            # "ERROR at setup of TestClass.test_name" oder "TestClass.test_name"
            header_text = re.sub(r"^ERROR at (?:setup|teardown) of ", "", header_text)
            # Testname ist der letzte Teil nach dem Punkt
            current_test = header_text.split(".")[-1] if "." in header_text else header_text
            current_lines = []
        elif current_test:
            current_lines.append(line)

    # Letzten Block speichern falls Schleife ohne break endet
    if current_test and current_lines:
        errors[current_test] = _clean_error_block(current_lines)

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

        # Fehlermeldungen aus dem gesamten Output extrahieren
        error_messages = _extract_error_messages(run.get("output", []))

        # Ergebnisse fürs Report-Format aufbereiten
        report_results = []
        for r in results:
            test_name = r["name"]
            message = error_messages.get(test_name, "")
            report_results.append({
                "name": test_name,
                "outcome": r["outcome"],
                "message": message,
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
    suite = data.get("suite")  # None = alle
    url = (data.get("url") or "").strip() or None  # Direkte URL
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


@app.route("/api/tests/status/<run_id>")
def api_test_status(run_id):
    """Status eines Testlaufs abfragen."""
    run = test_runs.get(run_id)
    if not run:
        return jsonify({"error": "Testlauf nicht gefunden"}), 404

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
        return jsonify({"error": "Testlauf nicht gefunden"}), 404

    if run["status"] != "running":
        return jsonify({"error": "Testlauf laeuft nicht"}), 400

    # Signal an den Worker-Thread
    run["_cancel"] = True

    # Prozess direkt beenden falls vorhanden
    proc = run.get("_proc")
    if proc and proc.poll() is None:
        proc.terminate()

    return jsonify({"status": "ok", "message": "Abbruch angefordert"})


@app.route("/api/tests/stream/<run_id>")
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
            # Merge: nur gefundene Selektoren ueberschreiben, null-Werte behalten
            existing = get_selectors()
            merged = dict(existing)
            for key, value in result["selectors"].items():
                if value is not None:
                    merged[key] = value
            save_selectors(merged)
            result["selectors"] = merged
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    """Starte den Web-Server."""
    print("=" * 60)
    print("  EP-Testing-Tool: Web-Frontend")
    print("  http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
