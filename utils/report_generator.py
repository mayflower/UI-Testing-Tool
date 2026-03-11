"""Report-Generator: Erzeugt Markdown-Checklisten aus Testergebnissen."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config.settings import TEMPLATES_DIR, REPORTS_DIR, TESTER_NAME


# Verständliche Beschreibungen und Handlungsempfehlungen pro Test
TEST_DESCRIPTIONS = {
    # === UI-Tests ===
    "widget_is_visible": {
        "label": "Chat-Widget sichtbar",
        "description": "Das Chat-Widget wird auf der Seite angezeigt",
        "action": "Pruefen, ob das Widget korrekt eingebunden ist und nicht durch CSS verdeckt wird",
    },
    "widget_has_reasonable_dimensions": {
        "label": "Widget-Groesse angemessen",
        "description": "Das Chat-Widget hat eine Mindestgroesse von 300x400 Pixeln",
        "action": "CSS-Dimensionen des Widgets anpassen (min-width: 300px, min-height: 400px)",
    },
    "input_field_is_visible": {
        "label": "Eingabefeld sichtbar",
        "description": "Das Texteingabefeld ist sichtbar und aktiviert",
        "action": "Eingabefeld im HTML pruefen, ggf. display/visibility CSS korrigieren",
    },
    "send_button_is_visible": {
        "label": "Senden-Button sichtbar",
        "description": "Der Button zum Absenden von Nachrichten ist sichtbar",
        "action": "Senden-Button im HTML pruefen, ggf. Styling korrigieren",
    },
    "message_area_exists": {
        "label": "Nachrichtenbereich vorhanden",
        "description": "Es gibt einen Bereich fuer den Chatverlauf",
        "action": "Message-Container im HTML pruefen",
    },
    "header_exists": {
        "label": "Chat-Header vorhanden",
        "description": "Das Widget hat einen Header-Bereich (z.B. mit Titel/Logo)",
        "action": "Header-Element zum Widget hinzufuegen",
    },
    "widget_not_overlapping_page_content": {
        "label": "Widget ueberlagert Seite nicht",
        "description": "Das Widget nimmt nicht mehr als 80% des Bildschirms ein",
        "action": "Widget-Groesse und Positionierung (CSS) ueberpruefen",
    },
    "screenshot_initial_state": {
        "label": "Screenshot Anfangsansicht",
        "description": "Screenshot der initialen Darstellung wurde erstellt",
        "action": "Siehe screenshots/ui_initial_state.png",
    },
    "primary_color": {
        "label": "Primaerfarbe korrekt",
        "description": "Die Hintergrundfarbe entspricht dem Corporate Design",
        "action": "Hintergrundfarbe im CSS an die Markenfarbe anpassen (siehe brand.yaml)",
    },
    "accent_color_on_send_button": {
        "label": "Akzentfarbe auf Button",
        "description": "Der Senden-Button nutzt die richtige Akzentfarbe",
        "action": "Button-Hintergrundfarbe an die Marken-Akzentfarbe anpassen",
    },
    "text_color": {
        "label": "Textfarbe korrekt",
        "description": "Die Textfarbe entspricht den Markenvorgaben",
        "action": "CSS-Textfarbe an die Markenvorgabe anpassen",
    },
    "primary_font": {
        "label": "Schriftart korrekt",
        "description": "Die verwendete Schriftart entspricht dem Corporate Design",
        "action": "font-family im CSS pruefen und die richtige Schriftart einbinden",
    },
    "font_size_readable": {
        "label": "Schriftgroesse lesbar",
        "description": "Der Text hat mindestens 14px Schriftgroesse",
        "action": "font-size im CSS auf mindestens 14px erhoehen",
    },
    "logo_present": {
        "label": "Logo vorhanden",
        "description": "Ein Logo mit korrektem Alt-Text ist im Header sichtbar",
        "action": "Logo-Bild im Header einbinden und Alt-Text setzen",
    },
    "bot_user_messages_distinguishable": {
        "label": "Nachrichten unterscheidbar",
        "description": "Bot- und Nutzer-Nachrichten sind visuell unterschiedlich dargestellt",
        "action": "Unterschiedliche Hintergrundfarben fuer Bot- und Nutzer-Nachrichten verwenden",
    },
    "screenshot_desktop": {
        "label": "Screenshot Desktop",
        "description": "Screenshot in Desktop-Aufloesung (1280x720) erstellt",
        "action": "Siehe screenshots/visual_desktop.png",
    },
    "screenshot_tablet": {
        "label": "Screenshot Tablet",
        "description": "Screenshot in Tablet-Aufloesung (768x1024) erstellt",
        "action": "Siehe screenshots/visual_tablet.png",
    },
    "screenshot_mobile": {
        "label": "Screenshot Mobile",
        "description": "Screenshot in Mobile-Aufloesung (375x812) erstellt",
        "action": "Siehe screenshots/visual_mobile.png",
    },
    "screenshot_after_message": {
        "label": "Screenshot nach Nachricht",
        "description": "Screenshot nach dem Senden einer Testnachricht erstellt",
        "action": "Siehe screenshots/visual_after_message.png",
    },
    "widget_responsive_desktop": {
        "label": "Responsive: Desktop",
        "description": "Das Widget wird auf Desktop-Bildschirmen korrekt dargestellt",
        "action": "Responsive CSS fuer Desktop-Viewports pruefen",
    },
    "widget_responsive_mobile": {
        "label": "Responsive: Mobile",
        "description": "Das Widget passt sich an mobile Bildschirme an",
        "action": "Responsive CSS fuer Mobile-Viewports pruefen, ggf. Media Queries anpassen",
    },

    # === UX-Tests ===
    "welcome_message_present": {
        "label": "Begruessung vorhanden",
        "description": "Der Bot zeigt beim Oeffnen eine Willkommensnachricht an",
        "action": "Eine initiale Begruessung konfigurieren, die Nutzer willkommen heisst",
    },
    "welcome_message_is_german": {
        "label": "Begruessung auf Deutsch",
        "description": "Die Willkommensnachricht ist in deutscher Sprache",
        "action": "Begruessung auf Deutsch umstellen (Zielgruppe: deutschsprachige Besucher)",
    },
    "simple_question": {
        "label": "Einfache Frage beantwortet",
        "description": "Bot beantwortet die Frage 'Was sind die Oeffnungszeiten?' sinnvoll",
        "action": "Wissensbasis pruefen und sicherstellen, dass Oeffnungszeiten hinterlegt sind",
    },
    "greeting_response": {
        "label": "Begruessung erwidert",
        "description": "Bot reagiert freundlich auf ein 'Hallo!'",
        "action": "Small-Talk-Faehigkeit pruefen und ggf. Begruessung-Antworten konfigurieren",
    },
    "followup_question": {
        "label": "Folgefragen im Kontext",
        "description": "Bot kann Folgefragen im Gespraechskontext beantworten",
        "action": "Kontext-Management (Memory) des Chatbots pruefen und verbessern",
    },
    "input_field_clears_after_send": {
        "label": "Eingabefeld wird geleert",
        "description": "Nach dem Absenden wird das Eingabefeld automatisch geleert",
        "action": "JavaScript-Logik pruefen: Eingabefeld nach dem Senden zuruecksetzen",
    },
    "input_placeholder_text": {
        "label": "Platzhaltertext vorhanden",
        "description": "Das Eingabefeld zeigt einen hilfreichen Platzhaltertext",
        "action": "placeholder-Attribut am Input-Feld setzen (z.B. 'Stelle mir eine Frage...')",
    },
    "empty_message": {
        "label": "Leere Nachrichten abgefangen",
        "description": "Leere Nachrichten werden verhindert oder korrekt behandelt",
        "action": "Validierung einbauen: Leere Nachrichten nicht absenden lassen",
    },
    "very_long_message": {
        "label": "Langer Text verarbeitet",
        "description": "Sehr lange Nachrichten (~1900 Zeichen) fuehren nicht zum Absturz",
        "action": "Maximale Eingabelaenge pruefen und ggf. Fehlermeldung anzeigen",
    },
    "special_characters": {
        "label": "Sonderzeichen verarbeitet",
        "description": "Emojis, HTML-Tags und Sonderzeichen werden korrekt behandelt",
        "action": "Input-Sanitierung pruefen, alle Sonderzeichen muessen escaped werden",
    },
    "html_injection": {
        "label": "HTML-Injection verhindert",
        "description": "Eingeschleuster HTML-Code wird nicht ausgefuehrt (XSS-Schutz)",
        "action": "SICHERHEITSKRITISCH: HTML-Eingaben muessen escaped werden, XSS-Schutz einbauen",
    },
    "rapid_messages": {
        "label": "Schnelle Folgefragen stabil",
        "description": "Mehrere schnelle Nachrichten hintereinander fuehren nicht zum Absturz",
        "action": "Rate-Limiting oder Nachrichtenwarteschlange pruefen",
    },
    "only_whitespace_message": {
        "label": "Leerzeichen-Nachrichten abgefangen",
        "description": "Nachrichten mit nur Leerzeichen werden verhindert",
        "action": "Input-Validierung: Whitespace-only Eingaben abfangen",
    },
    "simple_question_response_time": {
        "label": "Antwortzeit: Einfache Frage",
        "description": "Einfache Fragen werden in unter 5 Sekunden beantwortet",
        "action": "Backend-Performance optimieren, ggf. Caching einsetzen",
    },
    "greeting_response_time": {
        "label": "Antwortzeit: Begruessung",
        "description": "Eine Begruessung wird in unter 3 Sekunden beantwortet",
        "action": "Begruessung-Antworten vorhalten (Caching) fuer schnellere Reaktion",
    },
    "complex_question_response_time": {
        "label": "Antwortzeit: Komplexe Frage",
        "description": "Komplexe Fragen werden in unter 10 Sekunden beantwortet",
        "action": "LLM-Timeout und Streaming pruefen, ggf. Antwort-Streaming aktivieren",
    },
    "multiple_questions_average_time": {
        "label": "Durchschnittliche Antwortzeit",
        "description": "Die durchschnittliche Antwortzeit ueber mehrere Fragen liegt unter 5 Sekunden",
        "action": "Gesamtperformance des Backends analysieren und Engpaesse beseitigen",
    },
    "page_load_time": {
        "label": "Seitenladezeit",
        "description": "Die Seite laedt vollstaendig in unter 10 Sekunden",
        "action": "Seitenladezeit optimieren: Assets komprimieren, Lazy Loading pruefen",
    },

    # === Accessibility-Tests ===
    "axe_full_page_audit": {
        "label": "WCAG-Audit: Gesamte Seite",
        "description": "Automatischer WCAG 2.1 AA Audit der gesamten Seite (axe-core)",
        "action": "Alle gefundenen WCAG-Violations beheben (siehe Details im Report)",
    },
    "axe_chat_widget_audit": {
        "label": "WCAG-Audit: Chat-Widget",
        "description": "WCAG 2.1 AA Audit nur fuer das Chat-Widget",
        "action": "Kritische Accessibility-Probleme im Chat-Widget zuerst beheben",
    },
    "color_contrast": {
        "label": "Farbkontraste ausreichend",
        "description": "Text/Hintergrund-Kontrast erfuellt WCAG AA (mindestens 4.5:1)",
        "action": "Textfarben und Hintergruende anpassen fuer ausreichenden Kontrast (min. 4.5:1)",
    },
    "images_have_alt_text": {
        "label": "Bilder haben Alt-Texte",
        "description": "Alle Bilder haben beschreibende Alternativtexte",
        "action": "Allen <img>-Elementen sinnvolle alt-Attribute hinzufuegen",
    },
    "save_axe_report": {
        "label": "Detaillierter axe-Report",
        "description": "Vollstaendiger axe-core Audit-Report als JSON gespeichert",
        "action": "Siehe reports/axe_report.json fuer den vollstaendigen Report",
    },
    "input_focusable_by_tab": {
        "label": "Eingabefeld per Tab erreichbar",
        "description": "Das Eingabefeld kann mit der Tab-Taste erreicht werden",
        "action": "Tab-Reihenfolge (tabindex) pruefen, Eingabefeld muss fokussierbar sein",
    },
    "send_message_with_enter": {
        "label": "Senden per Enter-Taste",
        "description": "Nachrichten koennen mit der Enter-Taste gesendet werden",
        "action": "KeyDown-Event auf Enter im Eingabefeld implementieren",
    },
    "no_keyboard_trap": {
        "label": "Kein Keyboard-Trap",
        "description": "Der Fokus bleibt nicht im Widget gefangen, Nutzer kann per Tab weiternavigieren",
        "action": "KRITISCH: Keyboard-Trap beseitigen, Nutzer muss Widget per Tab verlassen koennen",
    },
    "escape_closes_or_defocuses": {
        "label": "Escape-Taste funktioniert",
        "description": "Escape schliesst das Widget oder entfernt den Fokus",
        "action": "Optional: Escape-Handler implementieren zum Schliessen/Defokussieren",
    },
    "input_has_aria_label": {
        "label": "Eingabefeld hat Label",
        "description": "Das Eingabefeld hat ein ARIA-Label oder sichtbares Label fuer Screenreader",
        "action": "aria-label oder <label>-Element zum Eingabefeld hinzufuegen",
    },
    "send_button_has_aria_label": {
        "label": "Button hat Label",
        "description": "Der Senden-Button hat ein ARIA-Label oder sichtbaren Text",
        "action": "aria-label oder sichtbaren Text zum Button hinzufuegen",
    },
    "message_area_has_role": {
        "label": "Nachrichtenbereich hat ARIA-Rolle",
        "description": "Der Chatverlauf hat role='log' oder aria-live fuer Screenreader",
        "action": "role='log' und aria-live='polite' zum Nachrichtencontainer hinzufuegen",
    },
    "live_region_for_new_messages": {
        "label": "Neue Nachrichten angekuendigt",
        "description": "Screenreader kuendigen neue Bot-Nachrichten automatisch an",
        "action": "ARIA Live-Region (aria-live='polite') fuer neue Nachrichten einrichten",
    },
    "focus_visible_on_interactive_elements": {
        "label": "Fokus-Indikator sichtbar",
        "description": "Interaktive Elemente zeigen einen sichtbaren Fokus-Rahmen",
        "action": "CSS :focus-visible Styles hinzufuegen (outline oder box-shadow)",
    },
    "heading_structure": {
        "label": "Ueberschriften-Hierarchie",
        "description": "Ueberschriften im Widget folgen einer logischen Hierarchie (h1 > h2 > h3)",
        "action": "Ueberschriften-Ebenen korrigieren, keine Spruenge (z.B. h2 direkt nach h4)",
    },
}


def _get_jinja_env() -> Environment:
    """Erstelle Jinja2-Umgebung mit Templates-Verzeichnis."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _enrich_result(result: dict) -> dict:
    """Reichere ein Testergebnis mit verstaendlichen Beschreibungen an."""
    raw_name = result.get("name", "")

    # Testname normalisieren (test_ Praefix entfernen, Klassennamen entfernen)
    clean_name = raw_name
    for prefix in ("test_", "Test"):
        clean_name = clean_name.replace(prefix, "")
    clean_name = clean_name.strip("_").strip()

    info = TEST_DESCRIPTIONS.get(clean_name, {})

    outcome = result.get("outcome", "unknown")
    return {
        "test_id": clean_name,
        "label": info.get("label", clean_name.replace("_", " ").capitalize()),
        "description": info.get("description", ""),
        "action": info.get("action", ""),
        "passed": outcome == "passed",
        "failed": outcome in ("failed", "error"),
        "skipped": outcome == "skipped",
        "outcome": outcome,
        "message": result.get("message", ""),
        "duration_ms": round(result.get("duration", 0) * 1000),
    }


def _parse_pytest_results(results: list[dict]) -> dict:
    """Parse und reichere pytest-Ergebnisse an."""
    suites = {"ui": [], "ux": [], "a11y": []}

    for result in results:
        suite = result.get("suite", "unknown")
        if suite in suites:
            suites[suite].append(_enrich_result(result))

    return suites


def generate_report(
    results: list[dict],
    environment: dict,
    output_name: str | None = None,
) -> Path:
    """Generiere einen vollstaendigen Testbericht als Markdown."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    env = _get_jinja_env()
    template = env.get_template("checklist_full.md.j2")

    suites = _parse_pytest_results(results)

    total = len(results)
    passed = sum(1 for r in results if r["outcome"] == "passed")
    failed = sum(1 for r in results if r["outcome"] in ("failed", "error"))
    skipped = sum(1 for r in results if r["outcome"] == "skipped")

    # Handlungsempfehlungen sammeln (nur fuer fehlgeschlagene Tests)
    actions = []
    for suite_name, suite_results in suites.items():
        for r in suite_results:
            if r["failed"] and r["action"]:
                actions.append({
                    "suite": suite_name,
                    "label": r["label"],
                    "action": r["action"],
                    "message": r["message"],
                })

    now = datetime.now()
    report_name = output_name or f"testbericht_{now.strftime('%Y%m%d_%H%M%S')}"

    content = template.render(
        date=now.strftime("%Y-%m-%d %H:%M"),
        environment_name=environment.get("name", "unbekannt"),
        environment_url=environment.get("url", ""),
        environment_description=environment.get("description", ""),
        tester=TESTER_NAME,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        pass_rate=round(passed / total * 100) if total > 0 else 0,
        ui_results=suites["ui"],
        ux_results=suites["ux"],
        a11y_results=suites["a11y"],
        actions=actions,
    )

    output_path = REPORTS_DIR / f"{report_name}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def generate_suite_report(
    suite_name: str,
    results: list[dict],
    environment: dict,
) -> Path:
    """Generiere einen Report fuer eine einzelne Suite."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    env = _get_jinja_env()
    template_name = f"checklist_{suite_name}.md.j2"
    template = env.get_template(template_name)

    enriched = [_enrich_result(r) for r in results]
    actions = [r for r in enriched if r["failed"] and r["action"]]

    now = datetime.now()

    content = template.render(
        date=now.strftime("%Y-%m-%d %H:%M"),
        environment_name=environment.get("name", "unbekannt"),
        environment_url=environment.get("url", ""),
        tester=TESTER_NAME,
        results=enriched,
        actions=actions,
    )

    output_path = REPORTS_DIR / f"checklist_{suite_name}_{now.strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path
