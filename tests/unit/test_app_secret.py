"""Unit-Tests fuer _load_app_secret() in app.py (fail-closed in Production)."""

from __future__ import annotations

import os

import pytest

from app import _load_app_secret


def test_secret_gesetzt_wird_zurueckgegeben(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "mein-geheimer-wert")
    monkeypatch.delenv("FLASK_ENV", raising=False)

    assert _load_app_secret() == "mein-geheimer-wert"


def test_secret_gesetzt_wird_auch_in_production_zurueckgegeben(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "mein-geheimer-wert")
    monkeypatch.setenv("FLASK_ENV", "production")

    assert _load_app_secret() == "mein-geheimer-wert"


def test_fehlender_secret_in_production_wirft_runtime_error(monkeypatch):
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")

    with pytest.raises(RuntimeError):
        _load_app_secret()


def test_leerer_secret_in_production_wirft_runtime_error(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "")
    monkeypatch.setenv("FLASK_ENV", "production")

    with pytest.raises(RuntimeError):
        _load_app_secret()


def test_fehlermeldung_enthaelt_secret_wert_nicht(monkeypatch):
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")

    with pytest.raises(RuntimeError) as exc_info:
        _load_app_secret()

    fehlermeldung = str(exc_info.value)
    # Die Meldung darf keinerlei Secret-Rohwert enthalten, sondern nur
    # den Namen der Umgebungsvariable und einen Hinweistext.
    assert "FLASK_SECRET_KEY" in fehlermeldung
    assert os.environ.get("FLASK_SECRET_KEY") is None


def test_fehlender_secret_ohne_production_faellt_auf_zufallswert_zurueck(monkeypatch):
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)

    wert1 = _load_app_secret()
    wert2 = _load_app_secret()

    assert wert1 != wert2
    assert len(wert1) > 0
