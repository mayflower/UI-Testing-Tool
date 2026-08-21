"""UX-Tests: Conversation-Flows eines Chatbots.

Geprueft wird domaenenspezifisches Verhalten — Fachwissen, Mehrfach-Turn-Kontext,
Off-Topic-Verweigerung, Halluzinationssicherheit, Sprachverhalten. Die Testlogik
selbst kennt keine Domaene: Fragen, erwartete Begriffe und Bewertungsindikatoren
kommen aus `config/prompts.yaml` (Vorlage: `config/prompts.example.yaml`).

Antworten eines Sprachmodells sind probabilistisch, deshalb wird auf
Keyword-Mengen statt auf exakte Strings geprueft. Fehlt ein Eintrag in der
Konfiguration, ueberspringt sich der betroffene Test.
"""

import pytest

from utils.chat_helpers import ChatHelper
from config.settings import get_prompts
from tests.prompt_helpers import (
    case_ids,
    case_or_skip,
    contains_any,
    require_indicators,
    value_or_skip,
)


pytestmark = pytest.mark.ux


# Die Parametrisierung braucht die Fallnamen bereits beim Einsammeln der Tests,
# also vor dem Greifen der Fixture. Deshalb hier einmalig geladen.
_CONFIG = get_prompts()


class TestDomainKnowledge:
    """Prueft, ob der Bot fachliche Fragen mit relevanten Inhalten beantwortet."""

    @pytest.mark.parametrize("case_name", case_ids(_CONFIG, "domain_knowledge"))
    def test_domain_question(self, page, selectors, prompts, case_name):
        """Fachfrage wird beantwortet und enthaelt einen erwarteten Begriff."""
        case = case_or_skip(prompts, case_name, "domain_knowledge")
        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait(case["prompt"])

        assert result["success"], "Bot hat nicht geantwortet"

        expected = case.get("expect_any") or []
        if not expected:
            # Kein Erwartungswert konfiguriert: dann gilt nur, dass eine
            # inhaltliche Antwort kam.
            assert len(result["response"]) > 10, (
                f"Antwort zu kurz: '{result['response']}'"
            )
            return

        assert contains_any(result["response"], expected), (
            f"Antwort enthaelt keinen der erwarteten Begriffe {expected}: "
            f"'{result['response'][:200]}'"
        )


class TestConversationContext:
    """Prueft, ob der Bot Kontext aus vorherigen Nachrichten bewahrt."""

    def test_followup_uses_prior_context(self, page, selectors, prompts):
        """Die Folgefrage ist nur mit dem Kontext der ersten Frage beantwortbar."""
        first_prompt = value_or_skip(prompts, "context", "followup", "first")
        second_prompt = value_or_skip(prompts, "context", "followup", "second")
        expected = value_or_skip(prompts, "context", "followup", "expect_any")

        chat = ChatHelper(page, selectors)

        first = chat.send_and_wait(first_prompt)
        assert first["success"], "Erste Frage unbeantwortet"

        followup = chat.send_and_wait(second_prompt)
        assert followup["success"], "Folgefrage unbeantwortet"

        assert contains_any(followup["response"], expected), (
            f"Folgeantwort wirkt kontextlos: '{followup['response'][:200]}'"
        )

    def test_multi_turn_conversation_stable(self, page, selectors, prompts):
        """Alle Fragen einer Folge liefern eine Antwort."""
        questions = value_or_skip(prompts, "context", "multi_turn")
        chat = ChatHelper(page, selectors)

        responses = []
        for question in questions:
            responses.append(chat.send_and_wait(question, timeout=30000))
            page.wait_for_timeout(500)

        successes = [r for r in responses if r["success"]]
        assert len(successes) == len(questions), (
            f"Nicht alle Folgefragen beantwortet "
            f"({len(successes)}/{len(questions)})"
        )


class TestOffTopicHandling:
    """Prueft, ob der Bot Off-Topic-Fragen freundlich auf seinen Bereich zurueckfuehrt."""

    @pytest.mark.parametrize("case_name", case_ids(_CONFIG, "off_topic"))
    def test_off_topic_refused(self, page, selectors, prompts, case_name):
        """Frage ausserhalb des Zustaendigkeitsbereichs wird nicht inhaltlich beantwortet."""
        case = case_or_skip(prompts, case_name, "off_topic")
        refusal = require_indicators(prompts, "refusal")

        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait(case["prompt"])

        assert result["success"], "Bot hat nicht geantwortet"

        # Verbotene Begriffe beweisen, dass inhaltlich geantwortet wurde.
        forbidden = case.get("forbidden_any") or []
        if forbidden and contains_any(result["response"], forbidden):
            pytest.fail(
                f"Bot antwortet inhaltlich statt zu verweisen (Treffer aus "
                f"{forbidden}): '{result['response'][:200]}'"
            )

        assert contains_any(result["response"], refusal), (
            f"Keine erkennbare Off-Topic-Verweigerung: '{result['response'][:200]}'"
        )


class TestHallucinationGuard:
    """Prueft, ob der Bot bei erfundenen Begriffen nicht halluziniert."""

    def test_invented_entity_not_confirmed(self, page, selectors, prompts):
        """Frage nach einer erfundenen Sache wird nicht bestaetigt."""
        prompt = value_or_skip(prompts, "hallucination", "invented_entity", "prompt")
        markers = value_or_skip(prompts, "hallucination", "invented_entity", "markers")
        refusal = require_indicators(prompts, "refusal")
        confirmation = require_indicators(prompts, "confirmation")
        negation = require_indicators(prompts, "negation")

        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait(prompt)

        assert result["success"], "Bot hat nicht geantwortet"

        # Uebernimmt der Bot den erfundenen Namen UND bestaetigt er ihn,
        # ist das eine Halluzination.
        mentions_invented = contains_any(result["response"], markers)
        confirms = contains_any(result["response"], confirmation)
        if mentions_invented and confirms:
            pytest.fail(
                f"Bot bestaetigt eine erfundene Sache (moegliche Halluzination): "
                f"'{result['response'][:300]}'"
            )

        acceptable = (
            contains_any(result["response"], refusal)
            or contains_any(result["response"], negation)
        )
        assert acceptable, (
            f"Antwort weder Refusal noch klare Negierung: '{result['response'][:300]}'"
        )


class TestLanguageHandling:
    """Prueft die Sprachfaehigkeit des Bots."""

    def test_foreign_language_question_gets_response(self, page, selectors, prompts):
        """Fremdsprachige Frage wird beantwortet — in welcher Sprache, ist offen."""
        prompt = value_or_skip(prompts, "language", "foreign_question")

        chat = ChatHelper(page, selectors)
        result = chat.send_and_wait(prompt)

        assert result["success"], "Bot hat nicht auf fremdsprachige Frage geantwortet"
        assert len(result["response"]) > 10, (
            f"Antwort zu kurz: '{result['response']}'"
        )
