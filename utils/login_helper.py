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

# Typische Fehlermeldungs-Patterns auf Login-Seiten
_ERROR_PATTERNS = [
    "[role='alert']",
    ".error",
    ".error-message",
    ".alert-error",
    ".alert-danger",
    "[class*='error']",
    "[class*='Error']",
    "[data-testid*='error']",
]


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


def has_login_form(page: Page, wait_seconds: int = 5) -> bool:
    """Pruefe ob die aktuelle Seite ein Login-Formular zeigt.

    Wartet kurz auf moegliche JS-Redirects und Hydration.
    Gibt True zurueck wenn ein Passwort-Feld sichtbar ist.
    """
    combined = ", ".join(LOGIN_FORM_PATTERNS["password_field"])
    try:
        page.wait_for_selector(combined, state="visible", timeout=wait_seconds * 1000)
        return True
    except Exception:
        return False


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

    # Felder per Klick fokussieren, leeren, dann Zeichen einzeln tippen
    # (zuverlaessiger als fill() bei React/Next.js Server Actions)
    user_loc = page.locator(user_sel)
    user_loc.click()
    user_loc.fill("")
    user_loc.press_sequentially(username, delay=50)

    pass_loc = page.locator(pass_sel)
    pass_loc.click()
    pass_loc.fill("")
    pass_loc.press_sequentially(password, delay=50)

    # URL vor Submit merken, um Redirect zu erkennen
    url_before = page.url

    if submit_sel:
        page.locator(submit_sel).click()
    else:
        pass_loc.press("Enter")

    page.wait_for_load_state("networkidle", timeout=timeout)

    # Kurz warten, damit Fehlermeldungen gerendert werden
    page.wait_for_timeout(1000)

    # Pruefen ob Login fehlgeschlagen ist
    error = _detect_login_error(page)
    if error:
        raise ValueError(f"Login fehlgeschlagen: {error}")

    # Pruefen ob Passwort-Feld noch sichtbar ist (= Login-Seite noch offen)
    still_on_login = _find_login_element(page, LOGIN_FORM_PATTERNS["password_field"])
    if still_on_login and page.url == url_before:
        raise ValueError(
            "Login fehlgeschlagen: Seite hat sich nach Submit nicht geaendert. "
            "Credentials pruefen."
        )

    return True


def _detect_login_error(page: Page) -> str | None:
    """Pruefe ob eine Fehlermeldung auf der Seite sichtbar ist."""
    for selector in _ERROR_PATTERNS:
        try:
            el = page.query_selector(selector)
            if el and el.is_visible():
                text = el.inner_text().strip()
                if text:
                    return text
        except Exception:
            continue
    return None


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
