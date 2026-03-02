"""Report-Generator: Erzeugt Markdown-Checklisten aus Testergebnissen."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config.settings import TEMPLATES_DIR, REPORTS_DIR, TESTER_NAME


def _get_jinja_env() -> Environment:
    """Erstelle Jinja2-Umgebung mit Templates-Verzeichnis."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )


def _parse_pytest_results(results: list[dict]) -> dict:
    """
    Parse pytest-Ergebnisse in ein strukturiertes Format.

    Args:
        results: Liste von Test-Ergebnissen mit keys:
            - name: Testname
            - outcome: 'passed', 'failed', 'skipped'
            - message: Fehlermeldung (bei failed)
            - duration: Testdauer in Sekunden
            - suite: 'ui', 'ux', 'a11y'

    Returns:
        Strukturiertes Dict pro Suite.
    """
    suites = {"ui": [], "ux": [], "a11y": []}

    for result in results:
        suite = result.get("suite", "unknown")
        if suite in suites:
            suites[suite].append({
                "name": result["name"],
                "passed": result["outcome"] == "passed",
                "skipped": result["outcome"] == "skipped",
                "failed": result["outcome"] == "failed",
                "message": result.get("message", ""),
                "duration_ms": round(result.get("duration", 0) * 1000),
            })

    return suites


def generate_report(
    results: list[dict],
    environment: dict,
    output_name: str | None = None,
) -> Path:
    """
    Generiere einen vollständigen Testbericht als Markdown.

    Args:
        results: Liste von Test-Ergebnissen.
        environment: Aktive Umgebungskonfiguration.
        output_name: Dateiname für den Report (ohne .md).

    Returns:
        Pfad zur generierten Report-Datei.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    env = _get_jinja_env()
    template = env.get_template("checklist_full.md.j2")

    suites = _parse_pytest_results(results)

    # Statistiken
    total = len(results)
    passed = sum(1 for r in results if r["outcome"] == "passed")
    failed = sum(1 for r in results if r["outcome"] == "failed")
    skipped = sum(1 for r in results if r["outcome"] == "skipped")

    now = datetime.now()
    report_name = output_name or f"testbericht_{now.strftime('%Y%m%d_%H%M%S')}"

    content = template.render(
        date=now.strftime("%Y-%m-%d %H:%M"),
        environment_name=environment.get("name", "unbekannt"),
        environment_url=environment.get("url", ""),
        environment_description=environment.get("description", ""),
        tester=TESTER_NAME,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        pass_rate=round(passed / total * 100) if total > 0 else 0,
        ui_results=suites["ui"],
        ux_results=suites["ux"],
        a11y_results=suites["a11y"],
    )

    output_path = REPORTS_DIR / f"{report_name}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def generate_suite_report(
    suite_name: str,
    results: list[dict],
    environment: dict,
) -> Path:
    """Generiere einen Report für eine einzelne Suite."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    env = _get_jinja_env()
    template_name = f"checklist_{suite_name}.md.j2"
    template = env.get_template(template_name)

    now = datetime.now()

    content = template.render(
        date=now.strftime("%Y-%m-%d %H:%M"),
        environment_name=environment.get("name", "unbekannt"),
        environment_url=environment.get("url", ""),
        tester=TESTER_NAME,
        results=results,
    )

    output_path = REPORTS_DIR / f"checklist_{suite_name}_{now.strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path
