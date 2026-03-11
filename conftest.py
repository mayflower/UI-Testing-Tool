"""Pytest-Konfiguration und Browser-Fixtures fuer das UI/UX-Testing-Tool."""

import time

import pytest
from playwright.sync_api import sync_playwright

from utils.login_helper import (
    perform_login,
    perform_login_on_page,
    has_login_form,
    needs_login,
)
from config.settings import (
    HEADLESS,
    SLOW_MO,
    BROWSER,
    NAVIGATION_TIMEOUT,
    SCREENSHOTS_DIR,
    AUTH_DIR,
    get_environment,
    get_selectors,
    get_brand,
)

# Gespeicherte Session gilt fuer 8 Stunden
_AUTH_STATE_MAX_AGE = 8 * 3600


def pytest_addoption(parser):
    """CLI-Optionen für pytest."""
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="Umgebung: dev, staging, prod",
    )
    parser.addoption(
        "--suite",
        action="store",
        default=None,
        help="Testsuite: ui, ux, a11y",
    )


@pytest.fixture(scope="session")
def environment(request):
    """Aktive Umgebung als Fixture."""
    env_name = request.config.getoption("--env")
    return get_environment(env_name)


@pytest.fixture(scope="session")
def selectors():
    """CSS-Selektoren als Fixture."""
    sels = get_selectors()
    # Prüfe ob mindestens die wichtigsten Selektoren konfiguriert sind
    missing = [k for k, v in sels.items() if v is None and k in ("container", "input_field", "send_button")]
    if missing:
        pytest.skip(
            f"CSS-Selektoren nicht konfiguriert: {missing}. "
            "Führe zuerst 'python run.py --discover' aus."
        )
    return sels


@pytest.fixture(scope="session")
def brand():
    """Branding-Konfiguration als Fixture."""
    return get_brand()


def _get_auth_state_path(environment: dict) -> str:
    """Pfad zur gespeicherten Session-Datei fuer diese Umgebung."""
    # Dateiname basiert auf der URL, damit verschiedene Umgebungen
    # eigene State-Dateien haben.
    safe_name = environment.get("url", "default").replace("https://", "").replace("/", "_").strip("_")
    return str(AUTH_DIR / f"state_{safe_name}.json")


def _auth_state_is_fresh(state_path: str) -> bool:
    """Prueft ob eine gespeicherte Session noch gueltig (nicht abgelaufen) ist."""
    from pathlib import Path
    p = Path(state_path)
    if not p.exists():
        return False
    age = time.time() - p.stat().st_mtime
    return age < _AUTH_STATE_MAX_AGE


@pytest.fixture(scope="session")
def browser_context(environment):
    """Playwright-Browser-Context fuer die gesamte Test-Session.

    Laedt eine gespeicherte Session (Storage State) falls vorhanden und
    aktuell, um SSO/Login bei Folgelaeufen zu ueberspringen.
    """
    login_url = environment.get("login_url", "")
    username = environment.get("username", "")
    password = environment.get("password", "")
    state_path = _get_auth_state_path(environment)

    with sync_playwright() as p:
        browser_type = getattr(p, BROWSER)
        browser = browser_type.launch(headless=HEADLESS, slow_mo=SLOW_MO)

        context_kwargs = {
            "viewport": {"width": 1280, "height": 720},
            "locale": "de-DE",
        }

        # Gespeicherte Session laden falls frisch genug
        if _auth_state_is_fresh(state_path):
            context_kwargs["storage_state"] = state_path

        context = browser.new_context(**context_kwargs)
        context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)

        # Einmalig einloggen falls keine gespeicherte Session vorhanden
        if not _auth_state_is_fresh(state_path) and needs_login(username, password):
            setup_page = context.new_page()
            try:
                if login_url:
                    perform_login(setup_page, login_url, username, password)
                setup_page.goto(environment["url"], wait_until="networkidle")
                if has_login_form(setup_page, wait_seconds=10):
                    perform_login_on_page(setup_page, username, password)
                    setup_page.wait_for_load_state("networkidle")
                # Nur speichern wenn wirklich eingeloggt (kein Login-Formular mehr)
                if not has_login_form(setup_page, wait_seconds=3):
                    AUTH_DIR.mkdir(parents=True, exist_ok=True)
                    context.storage_state(path=state_path)
                else:
                    raise ValueError("Login scheinbar fehlgeschlagen – Login-Formular noch sichtbar.")
            except Exception as e:
                setup_page.close()
                context.close()
                browser.close()
                pytest.fail(f"Login fehlgeschlagen: {e}")
            setup_page.close()

        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context, environment):
    """Frische Seite fuer jeden Test, navigiert zum Chatbot."""
    page = browser_context.new_page()

    # Zur Chatbot-URL navigieren (Session-Cookies aus Storage State aktiv)
    page.goto(environment["url"], wait_until="networkidle")

    # Sicherheitsnetz: falls doch auf Login-Seite gelandet (z.B. Session abgelaufen)
    username = environment.get("username", "")
    password = environment.get("password", "")
    if needs_login(username, password) and has_login_form(page, wait_seconds=5):
        try:
            perform_login_on_page(page, username, password)
            page.wait_for_load_state("networkidle")
            # Abgelaufene Session-Datei loeschen damit naechster Lauf neu einloggt
            from pathlib import Path
            state_path = _get_auth_state_path(environment)
            Path(state_path).unlink(missing_ok=True)
        except Exception as e:
            page.close()
            pytest.fail(f"Login fehlgeschlagen: {e}")

    yield page
    page.close()


@pytest.fixture
def screenshot_path():
    """Hilfsfunktion für Screenshot-Pfade."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def _path(name: str) -> str:
        return str(SCREENSHOTS_DIR / f"{name}.png")

    return _path
