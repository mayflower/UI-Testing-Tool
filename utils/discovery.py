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
from utils.login_helper import (
    perform_login,
    perform_login_on_page,
    has_login_form,
    needs_login,
)

# Typische Patterns für Chat-Widget-Elemente
DISCOVERY_PATTERNS = {
    "container": [
        # CopilotKit
        "div.copilotKitChat",
        "div.copilotKitInput",
        # Generic
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
        # CopilotKit
        "div.copilotKitInput textarea",
        # Generic
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
        # CopilotKit (Send-Button ist der letzte Button in der Controls-Leiste)
        "div.copilotKitInputControls button.copilotKitInputControlButton:last-child",
        "button.copilotKitInputControlButton:last-child",
        # Generic
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
        # CopilotKit
        "div.copilotKitMessages",
        # Generic
        "[class*='message-list']",
        "[class*='messageList']",
        "[class*='messages']",
        "[class*='Messages']",
        "[class*='conversation']",
        "[role='log']",
        "[role='list'][class*='chat']",
    ],
    "bot_message": [
        # CopilotKit
        "div.copilotKitAssistantMessage",
        "[data-message-role='assistant']",
        # ecki.ai / mAIstack custom patterns
        "[class*='assistant-message-content']",
        "[class*='assistant-message']:not([class*='feedback'])",
        # Generic (exclude feedback/control elements)
        "[class*='bot-message']",
        "[class*='botMessage']",
        "[class*='assistant']:not([class*='feedback']):not([class*='action']):not([class*='control'])",
        "[class*='bot'][class*='message']",
        "[data-role='assistant']",
        "[data-sender='bot']",
    ],
    "user_message": [
        # CopilotKit
        "div.copilotKitUserMessage",
        "[data-message-role='user']",
        # Generic
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


def _inspect_message_dom(page: Page, msg_list_sel: str | None) -> list[dict]:
    """Inspiziere die DOM-Struktur innerhalb des Nachrichtencontainers.

    Geht bis zu 2 Ebenen tief, damit auch verschachtelte Nachrichten
    (z.B. in copilotKitMessagesContainer) erkannt werden.
    """
    if not msg_list_sel:
        print("   ⚠️  Kein message_list-Selektor — DOM-Inspektion uebersprungen")
        return []

    try:
        # Sammle Elemente bis 2 Ebenen tief
        elements = page.evaluate(f"""() => {{
            const root = document.querySelector('{msg_list_sel}');
            if (!root) return [];
            const results = [];
            function inspect(el, depth, prefix) {{
                for (const child of el.children) {{
                    const attrs = {{}};
                    for (const a of child.attributes) {{
                        if (a.name.startsWith('data-') || a.name === 'role' || a.name === 'class')
                            attrs[a.name] = a.value;
                    }}
                    results.push({{
                        depth: depth,
                        prefix: prefix,
                        tag: child.tagName.toLowerCase(),
                        classes: child.className || '',
                        text: (child.textContent || '').trim().substring(0, 80),
                        attrs: attrs,
                        childCount: child.children.length,
                    }});
                    if (depth < 2 && child.children.length > 0) {{
                        inspect(child, depth + 1, prefix + '  ');
                    }}
                }}
            }}
            inspect(root, 1, '');
            return results;
        }}""")

        print(f"\n   🔎 DOM-Inspektion ({len(elements)} Elemente):")
        for el in elements:
            indent = "      " + el.get("prefix", "")
            print(f"{indent}<{el['tag']}> class=\"{el['classes']}\"")
            for k, v in el.get("attrs", {}).items():
                if k != "class":
                    print(f"{indent}  {k}=\"{v}\"")
            if el["text"]:
                text_preview = el['text'][:60].replace('\n', ' ')
                print(f"{indent}  Text: \"{text_preview}\"")
        print()
        return elements
    except Exception as e:
        print(f"   ⚠️  DOM-Inspektion fehlgeschlagen: {e}")
        return []


import re

# Muster fuer generierte/instabile CSS-Klassen die uebersprungen werden sollen
_GENERATED_CLASS_RE = re.compile(
    r"^(jsx-[a-f0-9]+|css-[a-z0-9]+|sc-[a-zA-Z]+|_[a-zA-Z0-9]{5,}|[a-f0-9]{8,})$"
)


def _pick_stable_class(classes: str) -> str | None:
    """Waehle eine stabile CSS-Klasse und ueberspringe generierte Hashes.

    Generierte Klassen (styled-jsx, CSS Modules, styled-components) aendern
    sich bei jedem Build und sind als Selektor ungeeignet.
    """
    for cls in classes.split():
        if not _GENERATED_CLASS_RE.match(cls):
            return cls
    return None


def _find_bot_message_by_content(page: Page, msg_list_sel: str | None) -> dict | None:
    """Fallback: Finde Bot-Nachrichten anhand von Textinhalt.

    Sucht innerhalb des Nachrichtencontainers nach Elementen mit
    substanziellem Text (>50 Zeichen), die keine UI-Kontrollelemente sind.
    """
    if not msg_list_sel:
        return None

    try:
        result = page.evaluate(f"""() => {{
            const root = document.querySelector('{msg_list_sel}');
            if (!root) return null;

            // Suche rekursiv nach Elementen mit langem Textinhalt
            const candidates = [];
            function scan(el, depth) {{
                if (depth > 6) return;
                const text = (el.textContent || '').trim();
                const directText = Array.from(el.childNodes)
                    .filter(n => n.nodeType === 3)
                    .map(n => n.textContent.trim())
                    .join('');
                const cls = el.className || '';

                // UI-Kontrollelemente ueberspringen
                if (/feedback|action|control|button|icon|thumb/i.test(cls)) return;
                if (el.tagName === 'BUTTON' || el.tagName === 'SVG') return;

                // Element mit substanziellem Text?
                if (text.length > 50 && el.children.length <= 10) {{
                    candidates.push({{
                        tag: el.tagName.toLowerCase(),
                        classes: cls,
                        id: el.id || '',
                        textLen: text.length,
                        text: text.substring(0, 80),
                        depth: depth,
                    }});
                }}
                for (const child of el.children) {{
                    scan(child, depth + 1);
                }}
            }}
            scan(root, 0);

            if (candidates.length === 0) return null;

            // Bevorzuge Elemente auf mittlerer Tiefe mit viel Text
            // (nicht zu flach = Container, nicht zu tief = Inline-Element)
            candidates.sort((a, b) => {{
                // Tiefe 2-4 bevorzugen
                const aScore = (a.depth >= 2 && a.depth <= 4 ? 100 : 0) + a.textLen;
                const bScore = (b.depth >= 2 && b.depth <= 4 ? 100 : 0) + b.textLen;
                return bScore - aScore;
            }});
            return candidates[0];
        }}""")

        if not result:
            return None

        # Baue Selektor
        tag = result["tag"]
        classes = result.get("classes", "")
        element_id = result.get("id", "")

        if element_id:
            best_selector = f"#{element_id}"
        elif classes:
            stable = _pick_stable_class(classes)
            if stable:
                best_selector = f"{tag}.{stable}"
            else:
                return None  # Nur generierte Klassen, kein stabiler Selektor
        else:
            return None

        return {
            "selector": best_selector,
            "matched_pattern": "content-based-fallback",
            "tag": tag,
            "id": element_id,
            "classes": classes,
            "text_preview": result.get("text", ""),
            "count": 1,
        }

    except Exception as e:
        print(f"   ⚠️  Content-basierte Suche fehlgeschlagen: {e}")
        return None


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
                    stable = _pick_stable_class(classes)
                    if stable:
                        best_selector = f"{tag}.{stable}"
                    else:
                        # Nur generierte Klassen — benutze das Suchmuster direkt
                        best_selector = selector
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

        # Separate Login-Seite zuerst, falls vorhanden
        if needs_login(username, password) and login_url:
            try:
                print(f"   🔐 Login auf: {login_url}")
                perform_login(page, login_url, username, password)
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

        # Falls wir auf einer Login-Seite gelandet sind (Redirect), einloggen
        if needs_login(username, password) and has_login_form(page, wait_seconds=15):
            try:
                print(f"   🔐 Login auf: {page.url} (Redirect)")
                perform_login_on_page(page, username, password)
                print("   ✅ Login erfolgreich\n")
                # Nach Login nochmal zur Ziel-URL
                page.goto(url, wait_until="networkidle")
            except Exception as e:
                print(f"   ❌ Login fehlgeschlagen: {e}")
                browser.close()
                return {"error": f"Login fehlgeschlagen: {e}"}
        elif needs_login(username, password):
            print(f"   ℹ️  Kein Login-Formular erkannt (URL: {page.url})")

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

        # Falls bot_message/user_message nicht gefunden: Testnachricht senden
        input_sel = discovered_selectors.get("input_field")
        send_sel = discovered_selectors.get("send_button")
        missing_msg = not discovered_selectors.get("bot_message") or not discovered_selectors.get("user_message")

        if input_sel and send_sel and missing_msg:
            print("   💬 Sende Testnachricht um Nachrichtenelemente zu finden...")
            try:
                page.locator(input_sel).click()
                page.locator(input_sel).fill("Hallo")
                page.click(send_sel)
                page.wait_for_timeout(8000)

                # DOM-Inspektion: alle Elemente im Message-Container ausgeben
                msg_list_sel = discovered_selectors.get("message_list")
                dom_info = _inspect_message_dom(page, msg_list_sel)
                results["_dom_inspection"] = dom_info

                # Nochmal nach Nachrichtenelementen suchen
                for msg_key in ("bot_message", "user_message"):
                    if not discovered_selectors.get(msg_key):
                        result = _find_element(page, DISCOVERY_PATTERNS[msg_key])
                        if result:
                            results[msg_key] = result
                            discovered_selectors[msg_key] = result["selector"]
                            print(f"   ✅ {msg_key}: {result['selector']}")
                        elif msg_key == "bot_message":
                            # Content-basierter Fallback fuer bot_message
                            print("   🔎 Versuche Content-basierte Erkennung...")
                            result = _find_bot_message_by_content(page, msg_list_sel)
                            if result:
                                results[msg_key] = result
                                discovered_selectors[msg_key] = result["selector"]
                                print(f"   ✅ {msg_key}: {result['selector']} (Content-Fallback)")
                                print(f"      Text: \"{result['text_preview']}\"")
                            else:
                                print(f"   ⚠️  {msg_key}: auch nach Testnachricht nicht gefunden")
                        else:
                            print(f"   ⚠️  {msg_key}: auch nach Testnachricht nicht gefunden")
            except Exception as e:
                print(f"   ⚠️  Testnachricht fehlgeschlagen: {e}")

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
