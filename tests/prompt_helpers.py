"""Helfer fuer den Zugriff auf die fachlichen Testinhalte aus prompts.yaml.

Die Testlogik ist domaenenfrei: sie prueft Struktureigenschaften einer Antwort
(kommt eine, enthaelt sie erwartete Begriffe, wird verweigert, wird etwas
Erfundenes bestaetigt). Was gefragt wird und was in der Antwort stehen soll,
kommt aus der Konfiguration.

Fehlt ein Eintrag, wird der Test uebersprungen statt zu scheitern — dasselbe
Verhalten wie bei den Branding-Tests. Ein Werkzeug ohne konfigurierte Domaene
soll nicht rot sein, sondern schweigen.
"""

from __future__ import annotations

import pytest


def contains_any(text: str, keywords: list[str]) -> bool:
    """True wenn mindestens eines der Keywords im Text vorkommt (case-insensitive)."""
    if not text or not keywords:
        return False
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


def indicators(prompts_config: dict, name: str) -> list[str]:
    """Indikatorliste `name` — leere Liste wenn nicht konfiguriert."""
    return prompts_config.get("indicators", {}).get(name) or []


def require_indicators(prompts_config: dict, name: str) -> list[str]:
    """Wie `indicators`, ueberspringt den Test aber wenn die Liste leer ist."""
    values = indicators(prompts_config, name)
    if not values:
        pytest.skip(
            f"Indikatorliste '{name}' ist nicht konfiguriert "
            f"(config/prompts.yaml, Abschnitt 'indicators')."
        )
    return values


def _section(prompts_config: dict, *path: str) -> dict:
    """Abschnitt unter prompts.<path> — leeres Dict wenn nicht vorhanden."""
    node = prompts_config.get("prompts", {})
    for key in path:
        if not isinstance(node, dict):
            return {}
        node = node.get(key) or {}
    return node if isinstance(node, dict) else {}


def cases(prompts_config: dict, *path: str) -> dict:
    """Alle konfigurierten Faelle eines Abschnitts, nur die mit gesetztem Prompt.

    Wird fuer die Parametrisierung genutzt: jeder Eintrag in prompts.yaml wird
    zu einem eigenen Testfall, unabhaengig von ihrer Anzahl.
    """
    section = _section(prompts_config, *path)
    return {
        name: case for name, case in section.items()
        if isinstance(case, dict) and case.get("prompt")
    }


def case_ids(prompts_config: dict, *path: str) -> list[str]:
    """Namen der konfigurierten Faelle — Eingabe fuer pytest.mark.parametrize.

    Ist nichts konfiguriert, wird ein Platzhalter zurueckgegeben, damit
    pytest den Test einsammeln und mit einem Skip-Hinweis versehen kann.
    Ohne diesen Platzhalter waere der Testfall unsichtbar.
    """
    return sorted(cases(prompts_config, *path).keys()) or ["_nicht_konfiguriert"]


def case_or_skip(prompts_config: dict, name: str, *path: str) -> dict:
    """Einen einzelnen Fall holen, oder den Test ueberspringen."""
    found = cases(prompts_config, *path)
    if name not in found:
        pytest.skip(
            f"Kein Testfall '{name}' unter prompts.{'.'.join(path)} konfiguriert "
            f"(config/prompts.yaml). Vorlage: config/prompts.example.yaml."
        )
    return found[name]


def generic(prompts_config: dict, name: str):
    """Domaenenfreier Prompt aus dem Abschnitt 'generic'."""
    value = _section(prompts_config, "generic").get(name)
    if not value:
        pytest.skip(f"prompts.generic.{name} ist nicht konfiguriert.")
    return value


def value_or_skip(prompts_config: dict, *path: str):
    """Beliebigen Wert unter prompts.<path> holen, oder den Test ueberspringen.

    Der letzte Pfadbestandteil darf auf eine Liste oder einen String zeigen.
    """
    node = prompts_config.get("prompts", {})
    for key in path[:-1]:
        node = (node or {}).get(key) or {}
    value = (node or {}).get(path[-1])
    if not value:
        pytest.skip(f"prompts.{'.'.join(path)} ist nicht konfiguriert.")
    return value
