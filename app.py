#!/usr/bin/env python3
"""EP-Testing-Tool: Web-Frontend für UI/UX Tests."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, jsonify, request, Response

from config.settings import (
    get_environments,
    get_environment,
    get_selectors,
    get_brand,
    save_selectors,
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


def _run_tests_worker(run_id: str, env_name: str, suite: str | None):
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

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(ROOT_DIR),
        )

        output_lines = []
        for line in proc.stdout:
            line = line.rstrip()
            output_lines.append(line)
            run["output"] = output_lines

            # Testergebnisse parsen
            if "PASSED" in line or "FAILED" in line or "SKIPPED" in line or "ERROR" in line:
                _parse_test_line(run, line)

        proc.wait()
        run["exit_code"] = proc.returncode
        run["status"] = "completed"
        run["finished_at"] = datetime.now().isoformat()

        # Report generieren
        _generate_report_for_run(run, env_name, suite)

    except Exception as e:
        run["status"] = "error"
        run["error"] = str(e)


def _parse_test_line(run: dict, line: str):
    """Parse eine pytest-Output-Zeile nach Testergebnissen."""
    result = None
    if " PASSED" in line:
        result = "passed"
    elif " FAILED" in line:
        result = "failed"
    elif " SKIPPED" in line:
        result = "skipped"
    elif " ERROR" in line:
        result = "error"

    if result:
        # Testname extrahieren
        parts = line.split("::")
        name = parts[-1].split(" ")[0] if parts else line
        suite = "unknown"
        if "tests/ui/" in line:
            suite = "ui"
        elif "tests/ux/" in line:
            suite = "ux"
        elif "tests/a11y/" in line:
            suite = "a11y"

        run.setdefault("results", []).append({
            "name": name,
            "outcome": result,
            "suite": suite,
            "raw": line.strip(),
        })


def _generate_report_for_run(run: dict, env_name: str, suite: str | None):
    """Generiere einen Report nach dem Testlauf."""
    try:
        results = run.get("results", [])
        if not results:
            return

        env = get_environment(env_name)

        # Ergebnisse fürs Report-Format aufbereiten
        report_results = []
        for r in results:
            report_results.append({
                "name": r["name"].replace("test_", "").replace("_", " ").capitalize(),
                "outcome": r["outcome"],
                "message": "",
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
    env_name = data.get("environment", "dev")
    suite = data.get("suite")  # None = alle

    run_id = str(uuid.uuid4())[:8]
    test_runs[run_id] = {
        "id": run_id,
        "environment": env_name,
        "suite": suite,
        "status": "starting",
        "results": [],
        "output": [],
    }

    thread = threading.Thread(
        target=_run_tests_worker,
        args=(run_id, env_name, suite),
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
    failed = sum(1 for r in results if r["outcome"] == "failed")
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

            if run["status"] in ("completed", "error"):
                passed = sum(1 for r in results if r["outcome"] == "passed")
                failed = sum(1 for r in results if r["outcome"] == "failed")
                skipped = sum(1 for r in results if r["outcome"] == "skipped")
                yield f"data: {json.dumps({'type': 'done', 'data': {'status': run['status'], 'passed': passed, 'failed': failed, 'skipped': skipped, 'report_name': run.get('report_name')}})}\n\n"
                break

            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/discovery/run", methods=["POST"])
def api_run_discovery():
    """Starte Selektor-Discovery."""
    data = request.get_json() or {}
    env_name = data.get("environment", "dev")

    try:
        from utils.discovery import discover_selectors
        result = discover_selectors(env_name)
        if result and result.get("selectors"):
            save_selectors(result["selectors"])
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
