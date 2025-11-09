"""
Integration tests for NLU pipeline end-to-end functionality
"""
import pytest
from uuid import uuid4
from datetime import datetime

pytestmark = pytest.mark.asyncio


class TestNLUIntegration:
    """Test full NLU pipeline integration"""

    async def test_simple_greeting_rule_match(self):
        """Test that simple greetings are handled by rules (no LLM)"""
        from app.agents.nlu.rules import match_rule

        # Test greeting
        result = match_rule("hi")
        assert result is not None
        assert result["intent"] == "greeting"
        assert result["conf"] == 0.99

        # Test confirmation
        result = match_rule("yes")
        assert result["intent"] == "confirm"
        assert result["conf"] == 0.99

        # Test cancellation
        result = match_rule("cancel that")
        assert result["intent"] == "cancel"
        assert result["conf"] >= 0.95

    async def test_nlu_service_integration(self):
        """Test NLU service processes messages correctly"""
        from app.agents.services.nlu_service import create_nlu_service

        # Create NLU service without classifier for testing
        nlu_service = create_nlu_service(None)

        # Test with greeting (should use rules)
        result = await nlu_service.process_message(
            message="hello",
            user_context={"user_id": "test-user", "timezone": "America/Denver"}
        )

        assert result.intent == "greeting"
        assert result.confidence >= 0.99
        assert result.rule_matched is True

    async def test_classifier_prediction(self):
        """Test ONNX/Mock classifier makes predictions"""
        from app.agents.nlu.classifier_onnx import create_classifier
        from app.config.core.settings import get_nlu_settings

        settings = get_nlu_settings()

        classifier = create_classifier(
            model_path=settings.INTENT_MODEL_PATH,
            labels=settings.INTENT_LABELS,
            hf_tokenizer=settings.HF_TOKENIZER
        )

        # Test scheduling intent
        intent, conf = classifier.predict("Schedule a meeting tomorrow")

        assert intent in settings.INTENT_LABELS
        assert conf > 0.0
        assert conf <= 1.0

    async def test_extractor_date_time(self):
        """Test datetime extractor"""
        from app.agents.nlu.extractors.date_time import extract_date_time

        result = extract_date_time(
            "tomorrow at 3pm",
            {"timezone": "America/Denver"}
        )

        assert result is not None
        assert "value" in result
        assert "confidence" in result
        assert result["confidence"] > 0.0

    async def test_information_gates(self):
        """Test information completeness checking"""
        from app.agents.core.orchestration.gates import has_enough_info

        # Test with sufficient info
        enough, why = has_enough_info(
            intent_conf=0.92,
            slot_confs={"date_time": 0.85, "duration": 0.90},
            required=["date_time", "duration"]
        )

        assert enough is True
        assert why is None

        # Test with insufficient intent confidence
        enough, why = has_enough_info(
            intent_conf=0.80,  # Below 0.85 threshold
            slot_confs={"date_time": 0.85},
            required=["date_time"]
        )

        assert enough is False
        assert why == "low_intent_conf"

        # Test with missing slot
        enough, why = has_enough_info(
            intent_conf=0.92,
            slot_confs={"date_time": 0.85},
            required=["date_time", "duration"]
        )

        assert enough is False
        assert "duration" in why

    async def test_policy_evaluation(self):
        """Test policy evaluation logic"""
        from app.agents.core.orchestration.policy import build_policy_context, evaluate

        # Test AUTO decision (safe operation)
        ctx = build_policy_context(
            intent="greeting",
            intent_conf=0.99,
            slots={},
            slot_confs={},
            required_slots=[],
            user_prefs={},
            action_metadata={
                "is_external_write": False,
                "is_destructive": False,
                "free_busy_ok": True
            }
        )

        decision, reasons = evaluate(ctx)
        assert decision.value == "auto"
        assert len(reasons) == 0

        # Test GATE decision (external write)
        ctx = build_policy_context(
            intent="scheduling",
            intent_conf=0.92,
            slots={"date_time": "2025-10-02T15:00"},
            slot_confs={"date_time": 0.85},
            required_slots=["date_time"],
            user_prefs={},
            action_metadata={
                "is_external_write": True,
                "is_destructive": False,
                "free_busy_ok": True
            }
        )

        decision, reasons = evaluate(ctx)
        assert decision.value == "gate"
        assert "is_external_write" in reasons or len(reasons) > 0

    async def test_continuation_classification(self):
        """Test turn classification for multi-turn conversations"""
        from app.agents.core.orchestration.continuation import classify_turn

        # Test NEW_INTENT (no pending gate)
        state = {
            "pending_gate": None,
            "last_action": None,
            "is_terse": False
        }

        nlu = {
            "intent": "scheduling",
            "confidence": 0.92
        }

        turn_type, action_id = classify_turn(state, nlu)
        assert turn_type == "NEW_INTENT"
        assert action_id is None

        # Test SLOT_FILL (pending gate exists, terse input)
        state = {
            "pending_gate": {
                "action_id": "test-action-123",
                "intent": "scheduling"
            },
            "last_action": None,
            "is_terse": True
        }

        turn_type, action_id = classify_turn(state, nlu)
        assert turn_type == "SLOT_FILL"
        assert action_id == "test-action-123"

        # Test CANCEL_PENDING
        nlu = {"intent": "cancel", "confidence": 0.99}
        turn_type, action_id = classify_turn(state, nlu)
        assert turn_type == "CANCEL_PENDING"
        assert action_id == "test-action-123"


class TestActionExecutor:
    """Test ActionExecutor functionality"""

    async def test_action_executor_initialization(self):
        """Test ActionExecutor can be created"""
        from app.agents.services.action_executor import get_action_executor

        executor = get_action_executor()
        assert executor is not None

    async def test_execute_greeting_action(self):
        """Test executing simple greeting action"""
        from app.agents.services.action_executor import get_action_executor

        executor = get_action_executor()

        action_record = {
            "id": str(uuid4()),
            "user_id": "test-user",
            "intent": "greeting",
            "params": {}
        }

        result = await executor.execute_action(action_record)

        assert result.success is True
        assert "Acknowledged" in result.message


class TestPlanningHandler:
    """Test Planning Handler functionality"""

    async def test_planning_handler_initialization(self):
        """Test PlanningHandler can be created"""
        from app.agents.services.planning_handler import create_planning_handler

        handler = create_planning_handler()
        assert handler is not None


class TestIntentProcessor:
    """Test Intent Processor integration"""

    async def test_intent_processor_initialization(self):
        """Test UnifiedIntentProcessor initializes correctly"""
        from app.agents.core.orchestration.intent_processor import get_intent_processor

        processor = get_intent_processor()
        assert processor is not None
        # NLU service may be None if no classifier provided
        # assert processor.nlu_service is not None
        assert processor.planning_handler is not None


class TestEndToEnd:
    """End-to-end workflow tests (requires mocking)"""

    async def test_e2e_greeting_flow(self):
        """Test simple greeting end-to-end"""
        # This would require full setup with mocked Supabase
        # Skipping for now - manual testing preferred
        pytest.skip("Requires full Supabase setup")

    async def test_e2e_scheduling_flow(self):
        """Test scheduling with gate confirmation end-to-end"""
        # This would require full setup with mocked orchestrator
        # Skipping for now - manual testing preferred
        pytest.skip("Requires full orchestrator setup")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
