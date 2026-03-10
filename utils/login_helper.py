"""Login-Automatisierung fuer authentifizierte Chatbot-Seiten."""

from __future__ import annotations

from playwright.sync_api import Page


# Generische Login-Formular-Selektoren
LOGIN_FORM_PATTERNS = {
    "username_field": [
        "input[type='email']",
        "input[type='text'][name*='user']",
        "input[type='text'][name*='email']",
        "input[name='username']",
        "input[name='email']",
        "input[autocomplete='username']",
        "input[autocomplete='email']",
    ],
    "password_field": [
        "input[type='password']",
        "input[name='password']",
        "input[name='passwd']",
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

# Entra ID (Microsoft/Azure AD) spezifische Selektoren
_ENTRA_EMAIL_INPUT = "input[name='loginfmt']"
_ENTRA_NEXT_BUTTON = "input[id='idSIButton9'], input[type='submit']"
_ENTRA_PASSWORD_INPUT = "input[name='passwd']"
_ENTRA_SIGNIN_BUTTON = "input[id='idSIButton9']"
_ENTRA_STAY_SIGNED_IN_NO = "#idBtn_Back"    # "Nein" bei "Angemeldet bleiben?"
_ENTRA_ERROR = "#passwordError, #usernameError, [id$='Error'][role='alert'], .alert-error"

# Typische Fehlermeldungs-Patterns
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


def _is_entra_page(page: Page) -> bool:
    """Prueft ob die aktuelle Seite ein Microsoft Entra ID Login ist."""
    return "login.microsoftonline.com" in page.url or "login.microsoft.com" in page.url


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
    """Pruefe ob die aktuelle Seite ein Login-Formular zeigt."""
    # Entra ID: E-Mail-Feld ist der Einstieg (noch kein Passwort-Feld sichtbar)
    entra_selectors = f"{_ENTRA_EMAIL_INPUT}, {_ENTRA_PASSWORD_INPUT}"
    generic_selectors = ", ".join(LOGIN_FORM_PATTERNS["password_field"])
    combined = f"{entra_selectors}, {generic_selectors}"
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
    """Fuehre Login durch. Unterstuetzt Entra ID (OAuth) und generische Formulare.

    Navigiert zur login_url. Falls bereits eingeloggt (kein Login-Formular),
    wird der Login uebersprungen.
    """
    page.goto(login_url, wait_until="networkidle", timeout=timeout)

    # Kurz warten auf moegliche JS-Redirects (z.B. OAuth-Weiterleitung)
    page.wait_for_timeout(1500)

    if not has_login_form(page, wait_seconds=10):
        return True  # Bereits eingeloggt

    if _is_entra_page(page):
        return _perform_entra_login(page, username, password, timeout)

    return _fill_and_submit_login(page, username, password, timeout)


def perform_login_on_page(
    page: Page,
    username: str,
    password: str,
    timeout: int = 30000,
) -> bool:
    """Fuehre Login auf der aktuell geladenen Seite durch."""
    if _is_entra_page(page):
        return _perform_entra_login(page, username, password, timeout)
    return _fill_and_submit_login(page, username, password, timeout)


def _perform_entra_login(
    page: Page,
    username: str,
    password: str,
    timeout: int = 30000,
) -> bool:
    """Microsoft Entra ID zweistufiger Login-Flow.

    Schritt 1: E-Mail eingeben → Weiter
    Schritt 2: Passwort eingeben → Anmelden
    Schritt 3: "Angemeldet bleiben?" → Nein
    """
    # --- Schritt 1: E-Mail ---
    try:
        page.wait_for_selector(_ENTRA_EMAIL_INPUT, state="visible", timeout=10000)
    except Exception:
        raise ValueError("Entra ID Login: E-Mail-Feld nicht gefunden.")

    email_loc = page.locator(_ENTRA_EMAIL_INPUT)
    email_loc.click()
    email_loc.fill(username)
    page.locator(_ENTRA_NEXT_BUTTON).first.click()

    # --- Schritt 2: Passwort ---
    try:
        page.wait_for_selector(_ENTRA_PASSWORD_INPUT, state="visible", timeout=15000)
    except Exception:
        # Pruefen ob Fehlermeldung sichtbar (z.B. Konto nicht gefunden)
        error = _detect_entra_error(page)
        raise ValueError(f"Entra ID Login: Passwort-Feld nicht erschienen. {error or ''}")

    pass_loc = page.locator(_ENTRA_PASSWORD_INPUT)
    pass_loc.click()
    pass_loc.fill(password)
    page.locator(_ENTRA_SIGNIN_BUTTON).click()

    # Warten bis Seite geladen ist
    page.wait_for_load_state("networkidle", timeout=timeout)
    page.wait_for_timeout(1000)

    # Fehlerpruefung
    if _is_entra_page(page):
        error = _detect_entra_error(page)
        if error:
            raise ValueError(f"Entra ID Login fehlgeschlagen: {error}")

    # --- Schritt 3: "Angemeldet bleiben?" dialog ---
    try:
        page.wait_for_selector(_ENTRA_STAY_SIGNED_IN_NO, state="visible", timeout=5000)
        page.locator(_ENTRA_STAY_SIGNED_IN_NO).click()
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass  # Dialog erscheint nicht immer

    return True


def _detect_entra_error(page: Page) -> str | None:
    """Liest Fehlermeldungen von Entra ID Seiten."""
    try:
        el = page.query_selector(_ENTRA_ERROR)
        if el and el.is_visible():
            return el.inner_text().strip() or None
    except Exception:
        pass
    return None


def _fill_and_submit_login(
    page: Page,
    username: str,
    password: str,
    timeout: int = 30000,
) -> bool:
    """Generischer Login: Erkenne Formular, fuelle es aus und submitte."""
    user_sel = _find_login_element(page, LOGIN_FORM_PATTERNS["username_field"])
    pass_sel = _find_login_element(page, LOGIN_FORM_PATTERNS["password_field"])
    submit_sel = _find_login_element(page, LOGIN_FORM_PATTERNS["submit_button"])

    if not user_sel or not pass_sel:
        raise ValueError(
            "Login-Formular konnte nicht erkannt werden. "
            "Username- oder Passwort-Feld nicht gefunden."
        )

    user_loc = page.locator(user_sel)
    user_loc.click()
    user_loc.fill("")
    user_loc.press_sequentially(username, delay=50)

    pass_loc = page.locator(pass_sel)
    pass_loc.click()
    pass_loc.fill("")
    pass_loc.press_sequentially(password, delay=50)

    url_before = page.url

    if submit_sel:
        page.locator(submit_sel).click()
    else:
        pass_loc.press("Enter")

    page.wait_for_load_state("networkidle", timeout=timeout)
    page.wait_for_timeout(1000)

    error = _detect_login_error(page)
    if error:
        raise ValueError(f"Login fehlgeschlagen: {error}")

    still_on_login = _find_login_element(page, LOGIN_FORM_PATTERNS["password_field"])
    if still_on_login and page.url == url_before:
        raise ValueError(
            "Login fehlgeschlagen: Seite hat sich nach Submit nicht geaendert."
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
    username: str | None,
    password: str | None,
) -> bool:
    """Pruefe ob Login-Credentials vorhanden sind."""
    return bool(username and password)
