#!/usr/bin/env python3
"""
EP-Testing-Tool: CLI-Einstiegspunkt.


Nutzung:
    python run.py                    # Alle Tests, Standard-Umgebung
    python run.py --env staging      # Alle Tests, Staging
    python run.py --suite ui         # Nur UI-Tests
    python run.py --suite ux         # Nur UX-Tests
    python run.py --suite a11y       # Nur Accessibility-Tests
    python run.py --discover         # CSS-Selektoren erkennen
    python run.py --list-envs        # Verfügbare Umgebungen anzeigen
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

from config.settings import (
    get_environment,
    get_environments,
    REPORTS_DIR,
    SCREENSHOTS_DIR,
)


class ResultCollector:
    """Sammelt pytest-Ergebnisse für die Report-Generierung."""

    def __init__(self):
        self.results = []

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            # Suite aus dem Testpfad ableiten
            suite = "unknown"
            nodeid = report.nodeid
            if "tests/ui/" in nodeid:
                suite = "ui"
            elif "tests/ux/" in nodeid:
                suite = "ux"
            elif "tests/a11y/" in nodeid:
                suite = "a11y"

            # Testname bereinigen
            name = report.nodeid.split("::")[-1]
            if name.startswith("test_"):
                name = name[5:]
            name = name.replace("_", " ").capitalize()

            self.results.append({
                "name": name,
                "outcome": report.outcome,
                "message": str(report.longrepr) if report.failed else "",
                "duration": report.duration,
                "suite": suite,
                "nodeid": report.nodeid,
            })


def run_discovery(env_name: str | None) -> None:
    """Führe Selektor-Discovery durch."""
    from utils.discovery import run_discovery_interactive
    run_discovery_interactive(env_name)


def list_environments() -> None:
    """Zeige alle konfigurierten Umgebungen."""
    envs = get_environments()
    if not envs:
        print("Keine Umgebungen konfiguriert.")
        print("Bearbeite config/environments.yaml")
        return

    print("\nVerfügbare Umgebungen:\n")
    for name, config in envs.items():
        print(f"  {name:12s} {config.get('url', '?')}")
        if config.get("description"):
            print(f"  {' ':12s} {config['description']}")
        print()


def run_tests(env_name: str | None, suite: str | None) -> list[dict]:
    """Führe Tests aus und gib Ergebnisse zurück."""
    args = ["-v", "--tb=short"]

    # Umgebung
    if env_name:
        args.extend(["--env", env_name])

    # Suite-Filter
    if suite:
        suite_map = {
            "ui": "tests/ui/",
            "ux": "tests/ux/",
            "a11y": "tests/a11y/",
        }
        if suite not in suite_map:
            print(f"Unbekannte Suite: {suite}")
            print(f"Verfügbar: {', '.join(suite_map.keys())}")
            sys.exit(1)
        args.append(suite_map[suite])

    # Ergebnis-Collector
    collector = ResultCollector()
    args.append("--override-ini=addopts=")

    # pytest ausführen
    exit_code = pytest.main(args, plugins=[collector])

    return collector.results


def generate_report(results: list[dict], env_name: str | None, suite: str | None) -> None:
    """Generiere Testbericht aus Ergebnissen."""
    if not results:
        print("\nKeine Testergebnisse zum Reporten.")
        return

    from utils.report_generator import generate_report as gen_report
    from utils.report_generator import generate_suite_report

    env = get_environment(env_name)

    if suite:
        path = generate_suite_report(suite, results, env)
    else:
        path = gen_report(results, env)

    print(f"\nReport generiert: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="EP-Testing-Tool: UI/UX Tests für den Europa-Park Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python run.py                    Alle Tests ausführen
  python run.py --env staging      Tests auf Staging ausführen
  python run.py --suite ui         Nur UI-Tests
  python run.py --suite a11y       Nur Accessibility-Tests
  python run.py --discover         CSS-Selektoren erkennen
  python run.py --list-envs        Umgebungen anzeigen
        """,
    )

    parser.add_argument(
        "--env",
        help="Umgebung (dev, staging, prod)",
        default=None,
    )
    parser.add_argument(
        "--suite",
        help="Testsuite (ui, ux, a11y)",
        choices=["ui", "ux", "a11y"],
        default=None,
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="CSS-Selektoren automatisch erkennen",
    )
    parser.add_argument(
        "--list-envs",
        action="store_true",
        help="Verfügbare Umgebungen anzeigen",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Keinen Report generieren",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Browser sichtbar starten (nicht headless)",
    )

    args = parser.parse_args()

    # Headed-Modus überschreiben
    if args.headed:
        import os
        os.environ["HEADLESS"] = "false"

    # Verzeichnisse sicherstellen
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  EP-Testing-Tool: Europa-Park Chatbot UI/UX Tests")
    print("=" * 60)

    if args.list_envs:
        list_environments()
        return

    if args.discover:
        run_discovery(args.env)
        return

    # Tests ausführen
    env = get_environment(args.env)
    print(f"\n  Umgebung: {env['name']} ({env['url']})")
    if args.suite:
        print(f"  Suite:    {args.suite}")
    print()

    results = run_tests(args.env, args.suite)

    # Report generieren
    if not args.no_report and results:
        generate_report(results, args.env, args.suite)

    # Zusammenfassung
    passed = sum(1 for r in results if r["outcome"] == "passed")
    failed = sum(1 for r in results if r["outcome"] == "failed")
    skipped = sum(1 for r in results if r["outcome"] == "skipped")

    print(f"\n{'='*60}")
    print(f"  Ergebnis: {passed} bestanden, {failed} fehlgeschlagen, {skipped} übersprungen")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
