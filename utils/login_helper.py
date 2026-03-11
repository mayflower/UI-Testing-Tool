"""Login-Automatisierung fuer authentifizierte Chatbot-Seiten."""

from __future__ import annotations

from playwright.sync_api import Page

from config.settings import SCREENSHOTS_DIR

_LIVE_SCREENSHOT_PATH = str(SCREENSHOTS_DIR / "_live.png")


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

# Auth.js / NextAuth Provider-Button (z.B. "Mit Microsoft anmelden")
_AUTHJS_MICROSOFT_BUTTON = [
    "button:has-text('Microsoft')",
    "a:has-text('Microsoft')",
    "button:has-text('Azure')",
    "button:has-text('Entra')",
    "[data-provider='azure-ad']",
    "[data-provider='microsoft-entra-id']",
    "form[action*='azure-ad'] button",
    "form[action*='microsoft'] button",
    "form[action*='entra'] button",
]

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

    Navigiert zur login_url. Falls die App eine Auth.js Provider-Seite zeigt
    (z.B. "Mit Microsoft anmelden" Button), wird dieser automatisch geklickt
    bevor der Entra ID Flow startet.
    """
    page.goto(login_url, wait_until="networkidle", timeout=timeout)
    page.wait_for_timeout(1500)

    # Bereits eingeloggt (kein Login-Formular, kein Provider-Button)?
    if not has_login_form(page, wait_seconds=3) and not _find_login_element(page, _AUTHJS_MICROSOFT_BUTTON):
        return True

    # Auth.js Provider-Seite: "Mit Microsoft anmelden" Button klicken
    if not _is_entra_page(page):
        provider_btn = _find_login_element(page, _AUTHJS_MICROSOFT_BUTTON)
        if provider_btn:
            page.locator(provider_btn).click()
            # Warten bis Redirect zu login.microsoftonline.com abgeschlossen
            try:
                page.wait_for_url("**/login.microsoftonline.com/**", timeout=10000)
            except Exception:
                page.wait_for_load_state("networkidle", timeout=timeout)

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
    """Microsoft Entra ID Login-Flow mit MFA-Unterstuetzung.

    Schritt 1: E-Mail eingeben → Weiter
    Schritt 2: Passwort eingeben → Anmelden
    Schritt 3: MFA-Freigabe abwarten (falls aktiv)
    Schritt 4: "Angemeldet bleiben?" → Nein
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
        error = _detect_entra_error(page)
        raise ValueError(f"Entra ID Login: Passwort-Feld nicht erschienen. {error or ''}")

    pass_loc = page.locator(_ENTRA_PASSWORD_INPUT)
    pass_loc.click()
    pass_loc.fill(password)
    page.locator(_ENTRA_SIGNIN_BUTTON).click()

    page.wait_for_load_state("networkidle", timeout=timeout)
    page.wait_for_timeout(1000)

    # Fehlerpruefung vor MFA
    if _is_entra_page(page):
        error = _detect_entra_error(page)
        if error:
            raise ValueError(f"Entra ID Login fehlgeschlagen: {error}")

    # --- Schritt 3: MFA ---
    if _is_entra_page(page):
        _handle_entra_mfa(page)

    # --- Schritt 4: "Angemeldet bleiben?" ---
    try:
        page.wait_for_selector(_ENTRA_STAY_SIGNED_IN_NO, state="visible", timeout=5000)
        page.locator(_ENTRA_STAY_SIGNED_IN_NO).click()
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass  # Dialog erscheint nicht immer

    return True


def _handle_entra_mfa(page: Page, mfa_timeout: int = 120000) -> None:
    """Wartet auf MFA-Freigabe, speichert Live-Screenshots und gibt Hinweise aus.

    Unterstuetzt:
    - Number Matching (Zahl im Browser → in Authenticator App bestaetigen)
    - TOTP / SMS (Code-Eingabe im Browser)
    - Push-Benachrichtigung (einfaches Warten)

    Waehrend des Wartens wird alle 500ms ein Screenshot nach
    SCREENSHOTS_DIR/_live.png gespeichert (fuer die Web-UI Live-Ansicht).
    """
    import time as _time

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Number Matching: Zahl anzeigen die in der Authenticator App bestaetigt werden muss
    number_el = page.query_selector("#idRichContext_DisplaySign")
    if number_el and number_el.is_visible():
        number = number_el.inner_text().strip()
        print(f"\n{'='*50}")
        print(f"  MFA ERFORDERLICH - Number Matching")
        print(f"  Bitte die Zahl  >>{number}<<  in der")
        print(f"  Microsoft Authenticator App bestaetigen.")
        print(f"  (Live-Ansicht im Browser verfuegbar)")
        print(f"{'='*50}\n")
    elif page.query_selector("input[name='otc']"):
        print(f"\n{'='*50}")
        print(f"  MFA ERFORDERLICH - Einmal-Code")
        print(f"  Bitte den Code im Browser eingeben.")
        print(f"  (Live-Ansicht im Browser verfuegbar)")
        print(f"{'='*50}\n")
    else:
        print(f"\n{'='*50}")
        print(f"  MFA ERFORDERLICH")
        print(f"  Bitte Anforderung in der Authenticator App bestaetigen.")
        print(f"  (Live-Ansicht im Browser verfuegbar)")
        print(f"{'='*50}\n")

    # Polling-Loop: Screenshot alle 500ms + MFA-Abschluss pruefen
    deadline = _time.time() + mfa_timeout / 1000
    while _time.time() < deadline:
        try:
            page.screenshot(path=_LIVE_SCREENSHOT_PATH)
        except Exception:
            pass
        if "login.microsoftonline.com" not in page.url:
            return
        page.wait_for_timeout(500)

    raise ValueError(
        f"MFA-Timeout: Keine Freigabe innerhalb von {mfa_timeout // 1000} Sekunden."
    )


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
