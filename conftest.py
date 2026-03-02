"""Pytest-Konfiguration und Browser-Fixtures für das EP-Testing-Tool."""

import pytest
from playwright.sync_api import sync_playwright

from config.settings import (
    HEADLESS,
    SLOW_MO,
    BROWSER,
    NAVIGATION_TIMEOUT,
    SCREENSHOTS_DIR,
    get_environment,
    get_selectors,
    get_brand,
)


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


@pytest.fixture(scope="session")
def browser_context(environment):
    """Playwright-Browser-Context für die gesamte Test-Session."""
    with sync_playwright() as p:
        browser_type = getattr(p, BROWSER)
        browser = browser_type.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="de-DE",
        )
        context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context, environment):
    """Frische Seite für jeden Test, navigiert zum Chatbot."""
    page = browser_context.new_page()
    page.goto(environment["url"], wait_until="networkidle")
    yield page
    page.close()


@pytest.fixture
def screenshot_path():
    """Hilfsfunktion für Screenshot-Pfade."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def _path(name: str) -> str:
        return str(SCREENSHOTS_DIR / f"{name}.png")

    return _path
