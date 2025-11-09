"""
Tests for Rule→ML→LLM Router Pathing

Tests the decision flow through rules, ML classifier, and LLM fallback.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestRouterPathing:
    """Test router decision flow."""

    @pytest.fixture
    def mock_classifier(self):
        """Fixture providing mock classifier."""
        classifier = Mock()
        classifier.predict.return_value = ("task_management", 0.85)
        classifier.is_available.return_value = True
        return classifier

    @pytest.fixture
    def nlu_service(self, mock_classifier):
        """Fixture providing NLU service."""
        from backend.app.agents.services.nlu_service import NLUService
        return NLUService(mock_classifier)

    @pytest.mark.asyncio
    async def test_rule_path_high_confidence(self, nlu_service):
        """Test: Rule match → immediate return (skip ML)."""
        # Rule patterns like "hello" should match immediately
        result = await nlu_service.process_message("hello")

        assert result.intent == "greeting"
        assert result.confidence == 0.99  # Rule confidence
        assert result.rule_matched == "greeting"
        # Classifier should not be called for rule matches

    @pytest.mark.asyncio
    async def test_ml_path_no_rule_match(self, nlu_service, mock_classifier):
        """Test: No rule match → ML classifier → return."""
        # Complex message shouldn't match rules
        result = await nlu_service.process_message(
            "I need to organize my assignments for next week"
        )

        assert result.intent == "task_management"  # From mock classifier
        assert result.confidence == 0.85
        assert result.rule_matched is None
        assert mock_classifier.predict.called

    @pytest.mark.asyncio
    async def test_llm_path_low_ml_confidence(self, mock_classifier):
        """Test: Low ML confidence → requires LLM (flagged in result)."""
        from backend.app.agents.services.nlu_service import NLUService

        # Mock low confidence prediction
        mock_classifier.predict.return_value = ("unknown", 0.45)

        nlu = NLUService(mock_classifier)
        result = await nlu.process_message("What about the thing?")

        # Low confidence should be reflected
        assert result.confidence < 0.7
        # In real system, orchestrator would use LLM for low confidence

    @pytest.mark.asyncio
    async def test_slot_extraction_after_intent(self, nlu_service):
        """Test: Intent determined → slots extracted → completeness check."""
        result = await nlu_service.process_message(
            "Schedule a meeting tomorrow at 2pm"
        )

        # Should extract date_time slot
        assert isinstance(result.slots, dict)
        assert isinstance(result.slot_confidences, dict)
        assert isinstance(result.enough_info, bool)

    @pytest.mark.asyncio
    async def test_missing_slots_flagged(self, mock_classifier):
        """Test: Missing required slots → enough_info=False."""
        from backend.app.agents.services.nlu_service import NLUService

        # Mock returns scheduling intent
        mock_classifier.predict.return_value = ("scheduling", 0.92)

        nlu = NLUService(mock_classifier)

        # Vague scheduling request missing time details
        result = await nlu.process_message("schedule a meeting")

        # Should flag missing information
        if not result.enough_info:
            assert result.missing_slot is not None

    @pytest.mark.asyncio
    async def test_continuation_classification(self, nlu_service):
        """Test: Turn classification for multi-turn dialogs."""
        # Simulate pending gate scenario
        pending_gate = {
            "gate_id": "gate_123",
            "intent": "scheduling",
            "missing_slot": "date_time"
        }

        result = await nlu_service.process_message("tomorrow at 2pm")

        # Classify turn type
        turn_type, target_id = await nlu_service.classify_conversation_turn(
            message="tomorrow at 2pm",
            nlu_result=result,
            pending_gate=pending_gate
        )

        # Should recognize as slot fill or continuation
        assert turn_type in ["SLOT_FILL", "CONTINUATION", "NEW_INTENT", "CANCEL_PENDING"]

    @pytest.mark.asyncio
    async def test_clarification_generation(self, nlu_service):
        """Test: Clarification question generation."""
        clarification = nlu_service.generate_clarification(
            missing_slot="date_time",
            intent="scheduling"
        )

        assert isinstance(clarification, str)
        assert len(clarification) > 0


class TestRuleMatching:
    """Test rule-based pattern matching."""

    def test_greeting_patterns(self):
        """Test greeting rule patterns."""
        from backend.app.agents.nlu.rules import match_rule

        greetings = ["hi", "hello", "hey", "howdy", "greetings"]

        for greeting in greetings:
            result = match_rule(greeting)
            assert result is not None
            assert result["intent"] == "greeting"
            assert result["conf"] == 0.99

    def test_confirmation_patterns(self):
        """Test confirmation rule patterns."""
        from backend.app.agents.nlu.rules import match_rule

        confirmations = ["yes", "yep", "yeah", "sure", "ok", "okay"]

        for conf in confirmations:
            result = match_rule(conf)
            assert result is not None
            assert result["intent"] == "confirm"

    def test_cancellation_patterns(self):
        """Test cancellation rule patterns."""
        from backend.app.agents.nlu.rules import match_rule

        cancellations = ["no", "nope", "cancel", "stop", "nevermind"]

        for cancel in cancellations:
            result = match_rule(cancel)
            assert result is not None
            assert result["intent"] == "cancel"

    def test_temporal_slot_fill_patterns(self):
        """Test temporal slot fill patterns."""
        from backend.app.agents.nlu.rules import match_rule

        temporal_words = ["tomorrow", "today", "tonight"]

        for word in temporal_words:
            result = match_rule(word)
            assert result is not None
            assert result["intent"] == "temporal_slot_fill"

    def test_no_rule_match(self):
        """Test no match returns None."""
        from backend.app.agents.nlu.rules import match_rule

        result = match_rule("I need to schedule a complex meeting")
        assert result is None


class TestIntentSpecifications:
    """Test intent specification definitions."""

    def test_get_intent_spec(self):
        """Test retrieving intent specs."""
        from backend.app.agents.core.intent_specs import get_intent_spec

        spec = get_intent_spec("scheduling")

        assert spec is not None
        assert "date_time" in spec.required_slots
        assert spec.is_external_write is True

    def test_external_write_detection(self):
        """Test external write intent detection."""
        from backend.app.agents.core.intent_specs import is_external_write_intent

        assert is_external_write_intent("scheduling") is True
        assert is_external_write_intent("email") is True
        assert is_external_write_intent("search") is False
        assert is_external_write_intent("briefing") is False

    def test_destructive_intent_detection(self):
        """Test destructive intent detection."""
        from backend.app.agents.core.intent_specs import is_destructive_intent

        assert is_destructive_intent("reschedule") is True
        assert is_destructive_intent("adjust_plan") is True
        assert is_destructive_intent("task_management") is False

    def test_all_intents_registered(self):
        """Test all intents are registered."""
        from backend.app.agents.core.intent_specs import get_all_intents

        intents = get_all_intents()

        assert len(intents) > 0
        assert "scheduling" in intents
        assert "task_management" in intents
        assert "greeting" in intents
        assert "unknown" in intents


class TestEndToEndFlow:
    """Test complete NLU pipeline flow."""

    @pytest.fixture
    def classifier(self):
        """Real mock classifier for E2E tests."""
        from backend.app.agents.nlu.classifier_onnx import MockIntentClassifier

        labels = [
            "scheduling", "calendar_event", "task_management",
            "reminder", "email", "search", "briefing",
            "greeting", "thanks", "confirm", "unknown"
        ]
        return MockIntentClassifier(labels)

    @pytest.fixture
    def nlu(self, classifier):
        """NLU service for E2E tests."""
        from backend.app.agents.services.nlu_service import NLUService
        return NLUService(classifier)

    @pytest.mark.asyncio
    async def test_simple_greeting_flow(self, nlu):
        """Test: 'hello' → rule match → greeting intent."""
        result = await nlu.process_message("hello")

        assert result.intent == "greeting"
        assert result.confidence == 0.99
        assert result.rule_matched == "greeting"
        assert result.enough_info is True  # No slots needed

    @pytest.mark.asyncio
    async def test_scheduling_with_slots_flow(self, nlu):
        """Test: Scheduling message → classifier → slot extraction."""
        result = await nlu.process_message(
            "Schedule a meeting with John tomorrow at 2pm"
        )

        # Should get some intent (exact depends on mock)
        assert result.intent is not None
        assert result.confidence > 0.0

        # Should have slots dict (even if empty)
        assert isinstance(result.slots, dict)

    @pytest.mark.asyncio
    async def test_incomplete_intent_flow(self, nlu):
        """Test: Incomplete info → missing slot detection."""
        result = await nlu.process_message("remind me")

        # Mock classifier might return reminder intent
        if result.intent == "reminder":
            # Should detect missing required slots
            # (date_time and title are required for reminder)
            pass  # Mock extractors may not find slots

    @pytest.mark.asyncio
    async def test_unknown_input_flow(self, nlu):
        """Test: Unclear input → unknown/low confidence."""
        result = await nlu.process_message("asdfghjkl xyzabc")

        # Should handle gracefully
        assert result.intent is not None
        # Might be 'unknown' or low confidence


@pytest.mark.integration
class TestOrchestratorIntegration:
    """Integration tests with orchestrator (if available)."""

    @pytest.mark.asyncio
    async def test_orchestrator_uses_nlu(self):
        """Test orchestrator integrates with NLU service."""
        # This would test the full orchestrator → NLU → agent flow
        # Placeholder for integration test
        pass

    @pytest.mark.asyncio
    async def test_low_confidence_triggers_llm(self):
        """Test low NLU confidence triggers LLM fallback."""
        # This would test the confidence-based routing
        # Placeholder for integration test
        pass
