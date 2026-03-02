"""Login-Automatisierung fuer authentifizierte Chatbot-Seiten."""

from __future__ import annotations

from playwright.sync_api import Page


# Typische Login-Formular-Selektoren (Auto-Detection)
LOGIN_FORM_PATTERNS = {
    "username_field": [
        "input[type='email']",
        "input[type='text'][name*='user']",
        "input[type='text'][name*='email']",
        "input[type='text'][name*='login']",
        "input[name='username']",
        "input[name='email']",
        "input[id*='user']",
        "input[id*='email']",
        "input[autocomplete='username']",
        "input[autocomplete='email']",
    ],
    "password_field": [
        "input[type='password']",
        "input[name='password']",
        "input[id*='password']",
        "input[autocomplete='current-password']",
    ],
    "submit_button": [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('Log in')",
        "button:has-text('Login')",
        "button:has-text('Anmelden')",
        "button:has-text('Sign in')",
    ],
}


def _find_login_element(page: Page, patterns: list[str]) -> str | None:
    """Finde ein Login-Formular-Element anhand typischer Patterns."""
    for selector in patterns:
        try:
            el = page.query_selector(selector)
            if el and el.is_visible():
                return selector
        except Exception:
            continue
    return None


def perform_login(
    page: Page,
    login_url: str,
    username: str,
    password: str,
    timeout: int = 30000,
) -> bool:
    """Fuehre Login auf einer separaten Login-Seite durch.

    Navigiert zur login_url, fuellt das Formular aus und submittet.
    """
    page.goto(login_url, wait_until="networkidle", timeout=timeout)
    return _fill_and_submit_login(page, username, password, timeout)


def perform_login_on_page(
    page: Page,
    username: str,
    password: str,
    timeout: int = 30000,
) -> bool:
    """Fuehre Login auf der aktuell geladenen Seite durch.

    Fuer den Fall, dass die Chatbot-URL selbst zur Login-Seite weiterleitet
    und keine separate Login-URL angegeben wurde.
    """
    return _fill_and_submit_login(page, username, password, timeout)


def _fill_and_submit_login(
    page: Page,
    username: str,
    password: str,
    timeout: int = 30000,
) -> bool:
    """Erkenne Login-Formular, fuelle es aus und submitte."""
    user_sel = _find_login_element(page, LOGIN_FORM_PATTERNS["username_field"])
    pass_sel = _find_login_element(page, LOGIN_FORM_PATTERNS["password_field"])
    submit_sel = _find_login_element(page, LOGIN_FORM_PATTERNS["submit_button"])

    if not user_sel or not pass_sel:
        raise ValueError(
            "Login-Formular konnte nicht erkannt werden. "
            "Username- oder Passwort-Feld nicht gefunden."
        )

    page.fill(user_sel, username)
    page.fill(pass_sel, password)

    if submit_sel:
        page.click(submit_sel)
    else:
        page.press(pass_sel, "Enter")

    page.wait_for_load_state("networkidle", timeout=timeout)

    return True


def needs_login(
    login_url: str | None,
    username: str | None,
    password: str | None,
) -> bool:
    """Pruefe ob Login-Credentials vorhanden sind.

    login_url ist optional – wenn leer, wird auf der Chatbot-Seite
    selbst nach einem Login-Formular gesucht.
    """
    return bool(username and password)
