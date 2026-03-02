"""Auto-Discovery für CSS-Selektoren des Chat-Widgets."""

from __future__ import annotations

from playwright.sync_api import sync_playwright, Page

from config.settings import (
    HEADLESS,
    BROWSER,
    NAVIGATION_TIMEOUT,
    get_environment,
    save_selectors,
)
from utils.login_helper import perform_login, perform_login_on_page, needs_login

# Typische Patterns für Chat-Widget-Elemente
DISCOVERY_PATTERNS = {
    "container": [
        "[class*='chat']",
        "[class*='Chat']",
        "[class*='widget']",
        "[class*='Widget']",
        "[class*='messenger']",
        "[class*='Messenger']",
        "[id*='chat']",
        "[id*='Chat']",
        "[role='dialog']",
        "[role='complementary']",
    ],
    "input_field": [
        "textarea[class*='chat']",
        "textarea[class*='input']",
        "textarea[class*='message']",
        "input[class*='chat']",
        "input[class*='message']",
        "input[type='text'][class*='chat']",
        "textarea[placeholder]",
        "[contenteditable='true']",
        "[role='textbox']",
    ],
    "send_button": [
        "button[class*='send']",
        "button[class*='Send']",
        "button[class*='submit']",
        "button[type='submit']",
        "button[aria-label*='send' i]",
        "button[aria-label*='Send' i]",
        "button[aria-label*='senden' i]",
        "button[aria-label*='Senden' i]",
    ],
    "message_list": [
        "[class*='message-list']",
        "[class*='messageList']",
        "[class*='messages']",
        "[class*='Messages']",
        "[class*='conversation']",
        "[role='log']",
        "[role='list'][class*='chat']",
    ],
    "bot_message": [
        "[class*='bot-message']",
        "[class*='botMessage']",
        "[class*='assistant']",
        "[class*='bot'][class*='message']",
        "[data-role='assistant']",
        "[data-sender='bot']",
    ],
    "user_message": [
        "[class*='user-message']",
        "[class*='userMessage']",
        "[class*='user'][class*='message']",
        "[data-role='user']",
        "[data-sender='user']",
    ],
    "header": [
        "[class*='chat-header']",
        "[class*='chatHeader']",
        "[class*='widget-header']",
        "[class*='Chat'][class*='header']",
    ],
    "close_button": [
        "button[class*='close']",
        "button[aria-label*='close' i]",
        "button[aria-label*='schließen' i]",
        "button[aria-label*='Schließen' i]",
    ],
}


def _find_element(page: Page, patterns: list[str]) -> dict | None:
    """Suche ein Element anhand einer Liste von CSS-Selektoren."""
    for selector in patterns:
        try:
            elements = page.query_selector_all(selector)
            if elements:
                el = elements[0]
                tag = el.evaluate("el => el.tagName.toLowerCase()")
                classes = el.evaluate("el => el.className")
                element_id = el.evaluate("el => el.id")
                text = el.evaluate("el => el.textContent?.trim()?.substring(0, 50) || ''")

                # Baue einen eindeutigen Selektor
                if element_id:
                    best_selector = f"#{element_id}"
                elif classes and isinstance(classes, str):
                    first_class = classes.split()[0]
                    best_selector = f"{tag}.{first_class}"
                else:
                    best_selector = selector

                return {
                    "selector": best_selector,
                    "matched_pattern": selector,
                    "tag": tag,
                    "id": element_id,
                    "classes": classes,
                    "text_preview": text,
                    "count": len(elements),
                }
        except Exception:
            continue
    return None


def discover_selectors_by_url(
    url: str,
    login_url: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> dict:
    """
    Discovery mit einer direkten URL (ohne environments.yaml).

    Returns:
        Dict mit erkannten Selektoren und Metadaten.
    """
    return _discover_selectors_core(
        url,
        environment_label="Direkte URL",
        login_url=login_url,
        username=username,
        password=password,
    )


def discover_selectors(env_name: str | None = None) -> dict:
    """
    Discovery über einen Umgebungsnamen aus environments.yaml.

    Returns:
        Dict mit erkannten Selektoren und Metadaten.
    """
    env = get_environment(env_name)
    return _discover_selectors_core(
        env["url"],
        environment_label=env.get("description", env_name),
        login_url=env.get("login_url"),
        username=env.get("username"),
        password=env.get("password"),
    )


def _discover_selectors_core(
    url: str,
    environment_label: str = "",
    login_url: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> dict:
    """
    Kern-Logik: Öffne eine URL und erkenne Chat-Widget-Selektoren.

    Returns:
        Dict mit erkannten Selektoren und Metadaten.
    """
    print(f"\n🔍 Discovery-Modus für: {url}")
    if environment_label:
        print(f"   Umgebung: {environment_label}\n")

    results = {}
    discovered_selectors = {}

    with sync_playwright() as p:
        browser_type = getattr(p, BROWSER)
        browser = browser_type.launch(headless=HEADLESS)
        page = browser.new_page()
        page.set_default_navigation_timeout(NAVIGATION_TIMEOUT)

        # Login durchfuehren, falls Credentials vorhanden
        if needs_login(login_url, username, password):
            try:
                if login_url:
                    # Separate Login-Seite: erst Login, dann Chatbot
                    print(f"   🔐 Login auf: {login_url}")
                    perform_login(page, login_url, username, password)
                    print("   ✅ Login erfolgreich\n")
                else:
                    # Chatbot-URL leitet selbst zur Login-Seite weiter
                    print(f"   🔐 Login auf: {url} (Redirect)")
                    page.goto(url, wait_until="networkidle")
                    perform_login_on_page(page, username, password)
                    print("   ✅ Login erfolgreich\n")
            except Exception as e:
                print(f"   ❌ Login fehlgeschlagen: {e}")
                browser.close()
                return {"error": f"Login fehlgeschlagen: {e}"}

        try:
            page.goto(url, wait_until="networkidle")
        except Exception as e:
            print(f"   ❌ Seite konnte nicht geladen werden: {e}")
            browser.close()
            return {}

        # Warte kurz, damit dynamische Inhalte laden
        page.wait_for_timeout(2000)

        for element_name, patterns in DISCOVERY_PATTERNS.items():
            result = _find_element(page, patterns)
            if result:
                results[element_name] = result
                discovered_selectors[element_name] = result["selector"]
                print(f"   ✅ {element_name}: {result['selector']}")
                print(f"      Tag: <{result['tag']}>, Klassen: {result['classes']}")
                if result["text_preview"]:
                    print(f"      Text: \"{result['text_preview']}\"")
                print(f"      Gefunden mit Pattern: {result['matched_pattern']}")
                print(f"      Anzahl Treffer: {result['count']}")
            else:
                discovered_selectors[element_name] = None
                print(f"   ⚠️  {element_name}: nicht gefunden")
            print()

        # Screenshot für manuelle Überprüfung
        from config.settings import SCREENSHOTS_DIR
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = str(SCREENSHOTS_DIR / "discovery.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"   📸 Screenshot gespeichert: {screenshot_path}")

        browser.close()

    return {
        "selectors": discovered_selectors,
        "details": results,
        "url": url,
        "environment": environment_label or "custom",
    }


def run_discovery_interactive(env_name: str | None = None) -> None:
    """
    Führe Discovery durch und frage den Nutzer, ob die Ergebnisse
    gespeichert werden sollen.
    """
    result = discover_selectors(env_name)

    if not result:
        print("\n❌ Discovery fehlgeschlagen. Prüfe die URL und Netzwerkverbindung.")
        return

    found = sum(1 for v in result["selectors"].values() if v is not None)
    total = len(result["selectors"])

    print(f"\n{'='*60}")
    print(f"   Ergebnis: {found}/{total} Elemente erkannt")
    print(f"{'='*60}\n")

    if found == 0:
        print("Keine Elemente erkannt. Mögliche Ursachen:")
        print("  - Der Chatbot nutzt ein iframe (prüfe manuell)")
        print("  - Die Seite benötigt eine Interaktion zum Öffnen")
        print("  - Ungewöhnliche CSS-Klassennamens-Konventionen")
        print("\nTipp: Trage die Selektoren manuell in config/selectors.yaml ein.")
        return

    answer = input("\nSelektoren in config/selectors.yaml speichern? [J/n]: ").strip()
    if answer.lower() in ("", "j", "ja", "y", "yes"):
        save_selectors(result["selectors"])
        print("✅ Selektoren gespeichert in config/selectors.yaml")
    else:
        print("Selektoren wurden NICHT gespeichert.")
        print("Du kannst sie manuell in config/selectors.yaml eintragen.")
