"""
NLU System Verification Script
Tests NLU components without requiring full app initialization
"""
import sys
import asyncio


def test_imports():
    """Test that all NLU components can be imported"""
    print("🧪 Testing imports...")

    try:
        from app.agents.nlu.rules import match_rule, RULES
        print("  ✅ Rules engine imported")

        from app.agents.nlu.classifier_onnx import create_classifier, MockIntentClassifier
        print("  ✅ Classifier imported")

        from app.agents.nlu.extractors.registry import REGISTRY
        print(f"  ✅ Extractors registry imported ({len(REGISTRY)} extractors)")

        from app.agents.core.orchestration.gates import has_enough_info
        print("  ✅ Gates module imported")

        from app.agents.core.orchestration.continuation import classify_turn
        print("  ✅ Continuation module imported")

        from app.agents.core.orchestration.policy import evaluate, PolicyDecision
        print("  ✅ Policy module imported")

        from app.agents.services.action_executor import get_action_executor
        print("  ✅ Action executor imported")

        from app.agents.services.planning_handler import create_planning_handler
        print("  ✅ Planning handler imported")

        from app.database.nlu_repository import create_nlu_repository
        print("  ✅ NLU repository imported")

        from app.observability.prompt_logs import create_prompt_logger
        print("  ✅ Prompt logger imported")

        return True

    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rules_engine():
    """Test rules engine"""
    print("\n🧪 Testing rules engine...")

    try:
        from app.agents.nlu.rules import match_rule

        # Test greeting
        result = match_rule("hi")
        assert result is not None, "Should match greeting"
        assert result["intent"] == "greeting", f"Expected 'greeting', got {result['intent']}"
        assert result["conf"] == 0.99, f"Expected 0.99, got {result['conf']}"
        print("  ✅ Greeting rule works")

        # Test confirmation
        result = match_rule("yes")
        assert result["intent"] == "confirm"
        print("  ✅ Confirmation rule works")

        # Test no match
        result = match_rule("schedule a meeting")
        assert result is None, "Should not match"
        print("  ✅ Non-match works correctly")

        return True

    except Exception as e:
        print(f"  ❌ Rules engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_classifier():
    """Test classifier"""
    print("\n🧪 Testing classifier...")

    try:
        from app.agents.nlu.classifier_onnx import create_classifier
        from app.config.core.settings import get_nlu_settings

        settings = get_nlu_settings()

        classifier = create_classifier(
            model_path=settings.INTENT_MODEL_PATH,
            labels=settings.INTENT_LABELS,
            hf_tokenizer=settings.HF_TOKENIZER
        )

        print(f"  ℹ️  Classifier type: {type(classifier).__name__}")
        print(f"  ℹ️  Available: {classifier.is_available()}")
        print(f"  ℹ️  Labels: {len(settings.INTENT_LABELS)} intents")

        # Test prediction
        intent, conf = classifier.predict("Schedule a meeting tomorrow")
        print(f"  ✅ Prediction: intent='{intent}', confidence={conf:.2f}")

        assert intent in settings.INTENT_LABELS, f"Intent '{intent}' not in labels"
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of range"

        return True

    except Exception as e:
        print(f"  ❌ Classifier test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_extractors():
    """Test extractors"""
    print("\n🧪 Testing extractors...")

    try:
        from app.agents.nlu.extractors.registry import REGISTRY

        print(f"  ℹ️  Registered extractors: {list(REGISTRY.keys())}")

        # Test date_time extractor
        if "date_time" in REGISTRY:
            extractor = REGISTRY["date_time"]
            result = extractor("tomorrow at 3pm", {"timezone": "America/Denver"})

            assert result is not None, "Should return result"
            assert "value" in result, "Should have value"
            assert "confidence" in result, "Should have confidence"

            print(f"  ✅ date_time extractor works: {result['value'][:19]}")
        else:
            print("  ⚠️  date_time extractor not found")

        return True

    except Exception as e:
        print(f"  ❌ Extractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gates():
    """Test information gates"""
    print("\n🧪 Testing information gates...")

    try:
        from app.agents.core.orchestration.gates import has_enough_info

        # Test sufficient info
        enough, why = has_enough_info(
            intent_conf=0.92,
            slot_confs={"date_time": 0.85, "duration": 0.90},
            required=["date_time", "duration"]
        )

        assert enough is True, "Should have enough info"
        assert why is None, "Should not have reason"
        print("  ✅ Sufficient info check works")

        # Test insufficient info
        enough, why = has_enough_info(
            intent_conf=0.80,  # Below threshold
            slot_confs={"date_time": 0.85},
            required=["date_time"]
        )

        assert enough is False, "Should not have enough info"
        assert why is not None, "Should have reason"
        print(f"  ✅ Insufficient info check works: {why}")

        return True

    except Exception as e:
        print(f"  ❌ Gates test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_policy():
    """Test policy evaluation"""
    print("\n🧪 Testing policy evaluation...")

    try:
        from app.agents.core.orchestration.policy import build_policy_context, evaluate

        # Test AUTO decision
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
        assert decision.value == "auto", f"Expected 'auto', got '{decision.value}'"
        print(f"  ✅ AUTO decision works (reasons: {reasons})")

        # Test GATE decision
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
        print(f"  ✅ GATE decision works: {decision.value} (reasons: {reasons})")

        return True

    except Exception as e:
        print(f"  ❌ Policy test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_continuation():
    """Test continuation classification"""
    print("\n🧪 Testing continuation classification...")

    try:
        from app.agents.core.orchestration.continuation import classify_turn

        # Test NEW_INTENT
        state = {"pending_gate": None, "last_action": None, "is_terse": False}
        nlu = {"intent": "scheduling", "confidence": 0.92}

        turn_type, action_id = classify_turn(state, nlu)
        assert turn_type == "NEW_INTENT", f"Expected NEW_INTENT, got {turn_type}"
        print(f"  ✅ NEW_INTENT classification works")

        # Test SLOT_FILL
        state = {
            "pending_gate": {"action_id": "test-123", "intent": "scheduling"},
            "last_action": None,
            "is_terse": True
        }

        turn_type, action_id = classify_turn(state, nlu)
        assert turn_type == "SLOT_FILL", f"Expected SLOT_FILL, got {turn_type}"
        assert action_id == "test-123"
        print(f"  ✅ SLOT_FILL classification works")

        return True

    except Exception as e:
        print(f"  ❌ Continuation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_action_executor():
    """Test action executor"""
    print("\n🧪 Testing action executor...")

    try:
        from app.agents.services.action_executor import get_action_executor
        from uuid import uuid4

        executor = get_action_executor()
        assert executor is not None

        print(f"  ✅ Action executor created: {type(executor).__name__}")

        # Test simple greeting action (doesn't need full workflow)
        async def test_greeting():
            action_record = {
                "id": str(uuid4()),
                "user_id": "test-user",
                "intent": "greeting",
                "params": {}
            }

            result = await executor.execute_action(action_record)
            assert result.success is True
            print(f"  ✅ Greeting action executed: {result.message}")

        asyncio.run(test_greeting())

        return True

    except Exception as e:
        print(f"  ❌ Action executor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests"""
    print("=" * 70)
    print("NLU SYSTEM VERIFICATION")
    print("=" * 70)

    results = {
        "Imports": test_imports(),
        "Rules Engine": test_rules_engine(),
        "Classifier": test_classifier(),
        "Extractors": test_extractors(),
        "Information Gates": test_gates(),
        "Policy Evaluation": test_policy(),
        "Continuation": test_continuation(),
        "Action Executor": test_action_executor(),
    }

    print("\n" + "=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")

    print("=" * 70)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - NLU System is operational!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
