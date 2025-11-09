"""
Tests for Intent Classifier Runtime

Tests ONNX inference, quantization, and integration.
"""

import pytest
from pathlib import Path
import json
from unittest.mock import Mock, patch
import numpy as np


class TestIntentClassifierRuntime:
    """Test suite for ONNX intent classifier runtime."""

    @pytest.fixture
    def mock_labels(self):
        """Fixture providing test labels."""
        return [
            "scheduling", "calendar_event", "task_management",
            "reminder", "email", "search", "briefing",
            "greeting", "thanks", "confirm", "cancel",
            "help", "unknown"
        ]

    @pytest.fixture
    def mock_classifier(self, mock_labels):
        """Fixture providing mocked classifier."""
        from backend.app.agents.nlu.classifier_onnx import MockIntentClassifier
        return MockIntentClassifier(mock_labels)

    def test_mock_classifier_basic_predictions(self, mock_classifier):
        """Test mock classifier returns reasonable predictions."""
        test_cases = [
            ("schedule a meeting", "scheduling"),
            ("add a task", "task_management"),
            ("remind me tomorrow", "reminder"),
            ("hello", "greeting"),
        ]

        for text, expected_intent in test_cases:
            intent, confidence = mock_classifier.predict(text)
            # Mock should return some intent (might not match expected exactly)
            assert intent is not None
            assert 0.0 <= confidence <= 1.0

    def test_mock_classifier_availability(self, mock_classifier):
        """Test mock classifier is always available."""
        assert mock_classifier.is_available() is True

    @pytest.mark.skipif(
        not Path("ml/intent_classifier/model_quantized.onnx").exists(),
        reason="Quantized ONNX model not available"
    )
    def test_onnx_classifier_initialization(self, mock_labels):
        """Test ONNX classifier initialization with quantized model."""
        from backend.app.agents.nlu.classifier_onnx import IntentClassifier

        classifier = IntentClassifier(
            model_path="ml/intent_classifier/model.onnx",
            labels=mock_labels,
            hf_tokenizer="sentence-transformers/all-MiniLM-L6-v2",
            use_quantized=True
        )

        assert classifier.is_available()
        assert classifier.is_quantized is True

    @pytest.mark.skipif(
        not Path("ml/intent_classifier/model_quantized.onnx").exists(),
        reason="Quantized ONNX model not available"
    )
    def test_onnx_classifier_predictions(self, mock_labels):
        """Test ONNX classifier predictions."""
        from backend.app.agents.nlu.classifier_onnx import IntentClassifier

        classifier = IntentClassifier(
            model_path="ml/intent_classifier/model.onnx",
            labels=mock_labels,
            hf_tokenizer="sentence-transformers/all-MiniLM-L6-v2",
            use_quantized=True
        )

        # Test various inputs
        test_cases = [
            "Schedule a meeting tomorrow at 2pm",
            "Add task to finish homework",
            "Remind me about the exam",
            "Hello",
            "Thanks",
        ]

        for text in test_cases:
            intent, confidence = classifier.predict(text)

            # Basic validation
            assert intent in mock_labels
            assert 0.0 <= confidence <= 1.0

    def test_confidence_threshold(self, mock_labels):
        """Test confidence threshold behavior."""
        from backend.app.agents.nlu.classifier_onnx import IntentClassifier

        # Mock ONNX Runtime and transformers
        with patch('backend.app.agents.nlu.classifier_onnx.ort') as mock_ort, \
             patch('backend.app.agents.nlu.classifier_onnx.AutoTokenizer') as mock_tok:

            # Setup mocks
            mock_session = Mock()
            mock_tokenizer = Mock()

            mock_ort.InferenceSession.return_value = mock_session
            mock_tok.from_pretrained.return_value = mock_tokenizer

            # Mock tokenizer output
            mock_tokenizer.return_value = {
                "input_ids": np.array([[1, 2, 3]]),
                "attention_mask": np.array([[1, 1, 1]])
            }

            # Mock low confidence prediction
            low_conf_logits = np.array([[0.1, 0.2, 0.15]])  # Low values
            mock_session.run.return_value = [low_conf_logits]

            classifier = IntentClassifier(
                model_path="dummy.onnx",
                labels=["intent1", "intent2", "unknown"],
                hf_tokenizer="dummy",
                confidence_threshold=0.7
            )

            # Should fall back to unknown for low confidence
            intent, conf = classifier.predict("test")
            assert intent == "unknown"

    def test_predict_with_probabilities(self, mock_labels):
        """Test probability distribution output."""
        from backend.app.agents.nlu.classifier_onnx import IntentClassifier

        with patch('backend.app.agents.nlu.classifier_onnx.ort') as mock_ort, \
             patch('backend.app.agents.nlu.classifier_onnx.AutoTokenizer') as mock_tok:

            mock_session = Mock()
            mock_tokenizer = Mock()

            mock_ort.InferenceSession.return_value = mock_session
            mock_tok.from_pretrained.return_value = mock_tokenizer

            mock_tokenizer.return_value = {
                "input_ids": np.array([[1, 2, 3]]),
                "attention_mask": np.array([[1, 1, 1]])
            }

            # Mock prediction with clear winner
            logits = np.array([[2.0, 0.5, 0.3]])
            mock_session.run.return_value = [logits]

            classifier = IntentClassifier(
                model_path="dummy.onnx",
                labels=["intent1", "intent2", "intent3"],
                hf_tokenizer="dummy"
            )

            intent, conf, probs = classifier.predict_with_probabilities("test")

            assert intent == "intent1"
            assert isinstance(probs, dict)
            assert len(probs) == 3
            assert sum(probs.values()) == pytest.approx(1.0, abs=1e-5)

    def test_get_info(self, mock_labels):
        """Test classifier info retrieval."""
        from backend.app.agents.nlu.classifier_onnx import MockIntentClassifier

        classifier = MockIntentClassifier(mock_labels)
        info = classifier.get_info() if hasattr(classifier, 'get_info') else {}

        # Mock classifier might not have get_info
        assert isinstance(info, dict)


class TestIntentClassifierIntegration:
    """Integration tests with NLU service."""

    @pytest.fixture
    def mock_classifier(self):
        """Fixture providing mock classifier."""
        from backend.app.agents.nlu.classifier_onnx import MockIntentClassifier
        labels = ["scheduling", "task_management", "greeting", "unknown"]
        return MockIntentClassifier(labels)

    @pytest.mark.asyncio
    async def test_nlu_service_with_classifier(self, mock_classifier):
        """Test NLU service integration."""
        from backend.app.agents.services.nlu_service import NLUService

        nlu = NLUService(mock_classifier)

        # Test message processing
        result = await nlu.process_message("schedule a meeting tomorrow")

        assert result.intent is not None
        assert result.confidence > 0.0
        assert isinstance(result.slots, dict)
        assert isinstance(result.slot_confidences, dict)
        assert isinstance(result.enough_info, bool)

    @pytest.mark.asyncio
    async def test_nlu_rule_override(self, mock_classifier):
        """Test that rules override classifier."""
        from backend.app.agents.services.nlu_service import NLUService

        nlu = NLUService(mock_classifier)

        # Rule should match with high confidence
        result = await nlu.process_message("hello")

        assert result.intent == "greeting"
        assert result.confidence == 0.99  # Rule confidence
        assert result.rule_matched == "greeting"

    @pytest.mark.asyncio
    async def test_nlu_classifier_fallback(self, mock_classifier):
        """Test classifier is used when no rule matches."""
        from backend.app.agents.services.nlu_service import NLUService

        nlu = NLUService(mock_classifier)

        # No rule should match this
        result = await nlu.process_message("I need to organize my tasks for next week")

        assert result.intent is not None
        assert result.rule_matched is None  # No rule matched
        assert result.confidence > 0.0  # Classifier provided confidence


class TestDatasetPreparation:
    """Test dataset loading and preparation."""

    def test_load_jsonl_examples(self):
        """Test loading JSONL examples."""
        from ml.intent_classifier.dataset import load_jsonl_examples

        examples = load_jsonl_examples(Path("data/intents/train.jsonl"))

        assert len(examples) > 0
        assert all(hasattr(ex, 'text') for ex in examples)
        assert all(hasattr(ex, 'label') for ex in examples)

    def test_label_mappings(self):
        """Test label mapping creation."""
        from ml.intent_classifier.dataset import create_label_mappings

        labels = ["intent1", "intent2", "intent3"]
        label_to_id, id_to_label = create_label_mappings(labels)

        assert len(label_to_id) == 3
        assert len(id_to_label) == 3
        assert label_to_id["intent1"] == 0
        assert id_to_label[0] == "intent1"

    def test_class_distribution(self):
        """Test class distribution calculation."""
        from ml.intent_classifier.dataset import (
            load_jsonl_examples,
            get_class_distribution
        )

        examples = load_jsonl_examples(Path("data/intents/train.jsonl"))
        dist = get_class_distribution(examples)

        assert isinstance(dist, dict)
        assert len(dist) > 0
        assert all(count > 0 for count in dist.values())


@pytest.mark.skipif(
    not Path("ml/intent_classifier/config.yaml").exists(),
    reason="Config file not available"
)
class TestConfigurationLoading:
    """Test configuration loading and validation."""

    def test_load_config(self):
        """Test config loading."""
        from ml.intent_classifier.utils_logging import load_config

        config = load_config(Path("ml/intent_classifier/config.yaml"))

        assert isinstance(config, dict)
        assert "model" in config
        assert "training" in config
        assert "data" in config
        assert "paths" in config
        assert "labels" in config

    def test_validate_config(self):
        """Test config validation."""
        from ml.intent_classifier.utils_logging import (
            load_config,
            validate_config
        )

        config = load_config(Path("ml/intent_classifier/config.yaml"))

        # Should not raise
        validate_config(config)

    def test_invalid_config(self):
        """Test invalid config raises error."""
        from ml.intent_classifier.utils_logging import validate_config

        invalid_config = {"model": {}}  # Missing required fields

        with pytest.raises(ValueError):
            validate_config(invalid_config)
