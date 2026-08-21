"""Unit-Tests fuer die Prompt-Konfiguration und ihre Testhelfer.

Geprueft wird das Verhalten, auf das sich die UX-Tests verlassen: fehlende
Eintraege fuehren zu einem Skip, nicht zu einem Fehler, und die Parametrisierung
liest genau die konfigurierten Faelle.
"""

import pytest
import yaml

from tests import prompt_helpers as ph


# --------------------------------------------------------------------------
# contains_any
# --------------------------------------------------------------------------

class TestContainsAny:
    def test_findet_keyword_unabhaengig_von_gross_klein(self):
        assert ph.contains_any("Wir haben ab 9 UHR geoeffnet", ["uhr"])

    def test_kein_treffer(self):
        assert not ph.contains_any("Keine Angabe", ["uhr", "preis"])

    def test_leerer_text_ist_kein_treffer(self):
        assert not ph.contains_any("", ["uhr"])

    def test_leere_keywordliste_ist_kein_treffer(self):
        # Wichtig: eine leere Erwartung darf nicht versehentlich als
        # "alles trifft zu" gelten.
        assert not ph.contains_any("beliebiger Text", [])


# --------------------------------------------------------------------------
# cases / case_ids — Grundlage der Parametrisierung
# --------------------------------------------------------------------------

_CONFIG = {
    "prompts": {
        "domain_knowledge": {
            "mit_prompt": {"prompt": "Frage?", "expect_any": ["antwort"]},
            "ohne_prompt": {"prompt": None, "expect_any": []},
            "leerer_prompt": {"prompt": "", "expect_any": []},
        },
        "generic": {"greeting": "Hallo!", "leer": None},
        "context": {"multi_turn": ["a", "b"], "leer": []},
    },
    "indicators": {"refusal": ["kann ich nicht"], "leer": []},
}


class TestCases:
    def test_nur_faelle_mit_prompt(self):
        found = ph.cases(_CONFIG, "domain_knowledge")
        assert list(found) == ["mit_prompt"]

    def test_unbekannter_abschnitt_ist_leer(self):
        assert ph.cases(_CONFIG, "gibt_es_nicht") == {}

    def test_case_ids_sortiert(self):
        config = {"prompts": {"x": {
            "b": {"prompt": "?"}, "a": {"prompt": "?"},
        }}}
        assert ph.case_ids(config, "x") == ["a", "b"]

    def test_case_ids_platzhalter_wenn_leer(self):
        # Ohne Platzhalter waere der Testfall in der Collection unsichtbar.
        assert ph.case_ids({"prompts": {}}, "domain_knowledge") == ["_nicht_konfiguriert"]


# --------------------------------------------------------------------------
# Skip-Verhalten
# --------------------------------------------------------------------------

class TestSkipVerhalten:
    def test_case_or_skip_liefert_fall(self):
        case = ph.case_or_skip(_CONFIG, "mit_prompt", "domain_knowledge")
        assert case["prompt"] == "Frage?"

    def test_case_or_skip_skippt_bei_fehlendem_fall(self):
        # pytest.skip() wirft Skipped -- eine BaseException. pytest.raises(Exception)
        # faengt sie NICHT: der Skip propagiert, und dieser Test gilt selbst als
        # "skipped", ohne etwas geprueft zu haben. Deshalb pytest.skip.Exception.
        with pytest.raises(pytest.skip.Exception):
            ph.case_or_skip(_CONFIG, "gibt_es_nicht", "domain_knowledge")

    def test_generic_liefert_wert(self):
        assert ph.generic(_CONFIG, "greeting") == "Hallo!"

    def test_generic_skippt_bei_leerem_wert(self):
        with pytest.raises(pytest.skip.Exception):
            ph.generic(_CONFIG, "leer")

    def test_value_or_skip_liefert_liste(self):
        assert ph.value_or_skip(_CONFIG, "context", "multi_turn") == ["a", "b"]

    def test_value_or_skip_skippt_bei_leerer_liste(self):
        with pytest.raises(pytest.skip.Exception):
            ph.value_or_skip(_CONFIG, "context", "leer")

    def test_require_indicators_liefert_liste(self):
        assert ph.require_indicators(_CONFIG, "refusal") == ["kann ich nicht"]

    def test_require_indicators_skippt_bei_leerer_liste(self):
        with pytest.raises(pytest.skip.Exception):
            ph.require_indicators(_CONFIG, "leer")

    def test_indicators_ohne_skip_gibt_leere_liste(self):
        assert ph.indicators(_CONFIG, "gibt_es_nicht") == []


# --------------------------------------------------------------------------
# get_prompts — Laden und Fallback
# --------------------------------------------------------------------------

class TestGetPrompts:
    def test_liest_prompts_yaml(self, tmp_path, monkeypatch):
        from config import settings

        (tmp_path / "prompts.yaml").write_text(
            yaml.safe_dump({"prompts": {"generic": {"greeting": "Moin"}},
                            "indicators": {"refusal": ["nein"]}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(settings, "CONFIG_DIR", tmp_path)

        config = settings.get_prompts()
        assert config["prompts"]["generic"]["greeting"] == "Moin"
        assert config["indicators"]["refusal"] == ["nein"]

    def test_fallback_auf_example(self, tmp_path, monkeypatch):
        from config import settings

        (tmp_path / "prompts.example.yaml").write_text(
            yaml.safe_dump({"prompts": {"generic": {"greeting": "aus Vorlage"}}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(settings, "CONFIG_DIR", tmp_path)

        config = settings.get_prompts()
        assert config["prompts"]["generic"]["greeting"] == "aus Vorlage"
        # Fehlender Abschnitt ist ein leeres Dict, kein None.
        assert config["indicators"] == {}

    def test_ohne_jede_datei_leere_struktur(self, tmp_path, monkeypatch):
        from config import settings

        monkeypatch.setattr(settings, "CONFIG_DIR", tmp_path)
        config = settings.get_prompts()
        assert config == {"prompts": {}, "indicators": {}}

    def test_leere_datei_ergibt_leere_struktur(self, tmp_path, monkeypatch):
        from config import settings

        (tmp_path / "prompts.yaml").write_text("", encoding="utf-8")
        monkeypatch.setattr(settings, "CONFIG_DIR", tmp_path)
        config = settings.get_prompts()
        assert config == {"prompts": {}, "indicators": {}}


# --------------------------------------------------------------------------
# Die ausgelieferte Vorlage muss ladbar und domaenenfrei sein
# --------------------------------------------------------------------------

class TestVorlage:
    def test_example_ist_gueltiges_yaml_und_domaenenfrei(self):
        from config.settings import CONFIG_DIR

        path = CONFIG_DIR / "prompts.example.yaml"
        assert path.exists(), "config/prompts.example.yaml fehlt"

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert "prompts" in data and "indicators" in data

        # Domaenenfrei: die Vorlage darf keine Fachfragen mitbringen.
        assert not (data["prompts"].get("domain_knowledge") or {}), (
            "Die Vorlage soll keine fachlichen Fragen enthalten"
        )

        # Die domaenenfreien Prompts sind dagegen vorbelegt.
        assert data["prompts"]["generic"]["greeting"]
        assert data["indicators"]["refusal"]
