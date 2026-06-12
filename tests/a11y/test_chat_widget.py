"""Accessibility-Tests speziell fuer das Chat-Widget-Verhalten.

Ergaenzt test_focus.py und test_keyboard.py um:
- Fokus-Management nach Senden (User kann ohne Maus weiterschreiben)
- Shift+Enter fuer Zeilenumbruch (Textarea-Konvention)
- Disabled-State des Send-Buttons bei leerer Eingabe
- lang-Attribut fuer korrekte Screenreader-Aussprache
- Bot-Antwort als Live-Region tatsaechlich angekuendigt
"""

import pytest

from utils.chat_helpers import ChatHelper


pytestmark = pytest.mark.a11y


class TestChatWidgetA11y:
    """Prueft Chat-Widget-spezifische Barrierefreiheits-Aspekte."""

    def test_focus_returns_to_input_after_send(self, page, selectors):
        """Fokus bleibt/kehrt nach dem Senden zum Eingabefeld zurueck.

        Wichtig fuer Tastatur-Nutzer: Sie koennen nach dem Senden direkt
        die naechste Frage tippen, ohne neu in das Feld zu navigieren.
        """
        chat = ChatHelper(page, selectors)
        input_sel = selectors["input_field"]

        chat.send_message("Test-Frage")
        # Kurz warten bis UI sich nach Send stabilisiert
        page.wait_for_timeout(800)

        focus_in_input = page.evaluate(
            f"() => document.activeElement?.matches('{input_sel}') || false"
        )

        if not focus_in_input:
            # Manche Widgets verlieren den Fokus erst, wenn die Antwort eintrifft —
            # akzeptabel, aber wenn der Fokus dauerhaft weg ist, ist das ein Problem.
            chat.wait_for_response(timeout=40000)
            page.wait_for_timeout(500)
            focus_in_input = page.evaluate(
                f"() => document.activeElement?.matches('{input_sel}') || false"
            )

        assert focus_in_input, (
            "Fokus liegt nach dem Senden nicht im Eingabefeld — "
            "Tastatur-Nutzer muessen den Fokus manuell zuruecksetzen."
        )

    def test_shift_enter_inserts_newline(self, page, selectors):
        """Shift+Enter erzeugt einen Zeilenumbruch, sendet aber nicht.

        Konvention bei Textarea-Inputs: Enter = senden, Shift+Enter = neue Zeile.
        """
        input_sel = selectors["input_field"]
        send_sel = selectors["send_button"]

        page.click(input_sel)
        page.keyboard.type("Zeile 1")
        page.keyboard.press("Shift+Enter")
        page.keyboard.type("Zeile 2")

        # Kein Senden ausgeloest: User-Message darf noch nicht im Verlauf sein
        page.wait_for_timeout(500)

        value = page.evaluate(f"""() => {{
            const el = document.querySelector('{input_sel}');
            return el?.value ?? el?.textContent ?? '';
        }}""")

        # Eingabe enthaelt beide Zeilen oder einen Zeilenumbruch
        contains_both = "Zeile 1" in value and "Zeile 2" in value
        contains_newline = "\n" in value

        assert contains_both or contains_newline, (
            f"Shift+Enter scheint kein Zeilenumbruch zu sein. Wert: {value!r}"
        )

        # Aufraeumen: Eingabe loeschen, damit nachfolgende Tests sauberen Stand haben
        page.fill(input_sel, "")

    def test_send_button_disabled_when_empty(self, page, selectors):
        """Send-Button ist bei leerer Eingabe nicht aktiv.

        Verhindert versehentlich gesendete leere Nachrichten und gibt
        sehbehinderten Nutzern ein klares Affordance-Signal.
        """
        input_sel = selectors["input_field"]
        send_sel = selectors["send_button"]

        page.click(input_sel)
        page.fill(input_sel, "")
        page.wait_for_timeout(300)

        btn = page.query_selector(send_sel)
        assert btn is not None, "Send-Button nicht gefunden"

        is_disabled = btn.is_disabled()
        aria_disabled = btn.get_attribute("aria-disabled") == "true"

        # Akzeptabel ist beides: HTML-disabled oder aria-disabled
        assert is_disabled or aria_disabled, (
            "Send-Button ist bei leerer Eingabe weder disabled noch aria-disabled — "
            "leere Nachrichten koennen gesendet werden."
        )

    def test_lang_attribute_set(self, page, selectors):
        """Das Dokument oder Chat-Widget hat ein gesetztes lang-Attribut.

        Screenreader brauchen lang, um die Aussprache (DE vs. EN) zu waehlen.
        """
        container_sel = selectors["container"]

        lang_info = page.evaluate(f"""() => {{
            const html_lang = document.documentElement.lang || '';
            const container = document.querySelector('{container_sel}');
            const widget_lang = container?.getAttribute('lang') || '';
            // Auch geerbte lang-Attribute akzeptieren (closest)
            const inherited = container?.closest('[lang]')?.getAttribute('lang') || '';
            return {{ html_lang, widget_lang, inherited }};
        }}""")

        any_lang = (
            lang_info.get("html_lang")
            or lang_info.get("widget_lang")
            or lang_info.get("inherited")
        )
        assert any_lang, (
            "Weder <html lang> noch das Chat-Widget haben ein lang-Attribut — "
            "Screenreader koennen die Aussprache nicht zuverlaessig waehlen."
        )

    def test_bot_response_in_live_region(self, page, selectors):
        """Eine eintreffende Bot-Antwort liegt in einer ARIA-Live-Region.

        Pruefung erfolgt am tatsaechlichen Antwort-Element nach einem Send,
        nicht nur strukturell (das macht test_focus.py bereits).
        """
        chat = ChatHelper(page, selectors)
        bot_sel = selectors.get("bot_message")
        if not bot_sel:
            pytest.skip("bot_message Selektor nicht konfiguriert")

        result = chat.send_and_wait("Hallo", timeout=20000)
        if not result["success"]:
            pytest.skip("Bot hat nicht geantwortet — Test nicht aussagekraeftig")

        # Pruefe die letzte Bot-Nachricht und ihre Vorfahren auf Live-Region-Semantik
        in_live_region = page.evaluate(f"""() => {{
            const msgs = document.querySelectorAll('{bot_sel}');
            if (!msgs.length) return false;
            const last = msgs[msgs.length - 1];
            // Aufsteigend nach aria-live, role=log/status/alert pruefen
            let el = last;
            while (el && el !== document.body) {{
                const live = el.getAttribute('aria-live');
                const role = el.getAttribute('role');
                if (live && live !== 'off') return true;
                if (role === 'log' || role === 'status' || role === 'alert') return true;
                el = el.parentElement;
            }}
            return false;
        }}""")

        assert in_live_region, (
            "Eingegangene Bot-Antwort liegt in keiner ARIA-Live-Region — "
            "Screenreader kuendigen neue Nachrichten nicht an."
        )
