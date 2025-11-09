#!/usr/bin/env python3
"""
Batch Inference Script for Intent Classifier

Runs inference on a test dataset and reports accuracy, confusion, and errors.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from sentence_transformers import SentenceTransformer

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils_logging import setup_logger

logger = setup_logger(__name__)


def load_intent_embeddings(specs_path: Path):
    """Load pre-computed intent embeddings."""
    with open(specs_path, "r") as f:
        data = json.load(f)

    intents = data["intents"]
    labels = [intent["label"] for intent in intents]
    embeddings = np.array([intent["embedding"] for intent in intents])

    return labels, embeddings


def classify_query(query: str, model: SentenceTransformer,
                   intent_labels: list, intent_embeddings: np.ndarray):
    """Classify a single query."""
    query_embedding = model.encode(query, convert_to_numpy=True)

    # Compute cosine similarity with all intent embeddings
    similarities = np.dot(intent_embeddings, query_embedding) / (
        np.linalg.norm(intent_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )

    # Get top prediction
    top_idx = np.argmax(similarities)
    top_intent = intent_labels[top_idx]
    top_confidence = float(similarities[top_idx])

    # Get top 3 for secondary intents
    top3_indices = np.argsort(similarities)[-3:][::-1]
    secondary_intents = [
        {"intent": intent_labels[idx], "confidence": float(similarities[idx])}
        for idx in top3_indices[1:]  # Skip the top one
    ]

    return {
        "intent": top_intent,
        "confidence": top_confidence,
        "secondary": secondary_intents
    }


def main():
    """Run batch inference on test set."""
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent.parent
    ml_dir = base_dir / "ml" / "intent_classifier"

    # Paths
    model_path = ml_dir / "outputs" / "contrastive_model"
    specs_path = ml_dir / "data" / "intent_specs_embedded.json"
    test_path = base_dir / "data" / "intents" / "test.jsonl"

    print("🧪 Running Batch Inference on Test Set\n")
    print("=" * 80)
    print(f"\nModel: {model_path}")
    print(f"Specs: {specs_path}")
    print(f"Test data: {test_path}\n")

    # Load model and embeddings
    logger.info("Loading model...")
    model = SentenceTransformer(str(model_path))

    logger.info("Loading intent embeddings...")
    intent_labels, intent_embeddings = load_intent_embeddings(specs_path)
    print(f"Loaded {len(intent_labels)} intent classes\n")

    # Load test data
    test_examples = []
    with open(test_path, "r") as f:
        for line in f:
            test_examples.append(json.loads(line.strip()))

    print(f"Loaded {len(test_examples)} test examples\n")
    print("=" * 80)
    print("\nRunning inference...\n")

    # Run inference
    results = []
    correct = 0
    errors_by_intent = defaultdict(list)
    confusion = defaultdict(lambda: defaultdict(int))
    confidence_scores = []

    for i, example in enumerate(test_examples, 1):
        query = example["text"]
        true_label = example["label"]

        result = classify_query(query, model, intent_labels, intent_embeddings)
        predicted = result["intent"]
        confidence = result["confidence"]

        is_correct = predicted == true_label
        if is_correct:
            correct += 1
        else:
            errors_by_intent[true_label].append({
                "query": query,
                "predicted": predicted,
                "confidence": confidence,
                "secondary": result["secondary"]
            })

        confusion[true_label][predicted] += 1
        confidence_scores.append(confidence)

        results.append({
            "query": query,
            "true": true_label,
            "predicted": predicted,
            "confidence": confidence,
            "correct": is_correct
        })

        # Progress indicator
        if i % 20 == 0:
            print(f"  Processed {i}/{len(test_examples)} examples...")

    # Calculate metrics
    accuracy = correct / len(test_examples)
    avg_confidence = np.mean(confidence_scores)

    print("\n" + "=" * 80)
    print("📊 RESULTS")
    print("=" * 80)
    print(f"\n✅ Overall Accuracy: {accuracy*100:.2f}% ({correct}/{len(test_examples)})")
    print(f"📈 Average Confidence: {avg_confidence:.3f}")
    print(f"📉 Confidence Std Dev: {np.std(confidence_scores):.3f}")

    # Per-intent accuracy
    print("\n📋 Per-Intent Accuracy:")
    intent_accuracies = {}
    for intent in sorted(set(ex["label"] for ex in test_examples)):
        total = sum(confusion[intent].values())
        correct_count = confusion[intent][intent]
        acc = correct_count / total if total > 0 else 0
        intent_accuracies[intent] = acc
        status = "✅" if acc >= 0.8 else "⚠️" if acc >= 0.6 else "❌"
        print(f"  {status} {intent:<25} {acc*100:>5.1f}% ({correct_count}/{total})")

    # Show worst performing intents
    worst_intents = sorted(intent_accuracies.items(), key=lambda x: x[1])[:5]
    print("\n⚠️  Worst Performing Intents:")
    for intent, acc in worst_intents:
        print(f"  {intent:<25} {acc*100:.1f}%")

    # Show errors
    if errors_by_intent:
        print("\n❌ Classification Errors (showing up to 3 per intent):")
        for intent in sorted(errors_by_intent.keys()):
            errors = errors_by_intent[intent]
            print(f"\n  {intent} ({len(errors)} errors):")
            for err in errors[:3]:
                print(f"    Query: \"{err['query']}\"")
                print(f"    Predicted: {err['predicted']} (conf: {err['confidence']:.3f})")
                if err['secondary']:
                    sec = err['secondary'][0]
                    print(f"    2nd choice: {sec['intent']} (conf: {sec['confidence']:.3f})")

    # Confusion matrix (most confused pairs)
    print("\n🔀 Most Confused Intent Pairs:")
    confused_pairs = []
    for true_intent, preds in confusion.items():
        for pred_intent, count in preds.items():
            if true_intent != pred_intent and count > 0:
                confused_pairs.append((true_intent, pred_intent, count))

    confused_pairs.sort(key=lambda x: x[2], reverse=True)
    for true_i, pred_i, count in confused_pairs[:10]:
        print(f"  {true_i:<25} → {pred_i:<25} ({count} times)")

    # Low confidence predictions
    low_conf = [r for r in results if r["confidence"] < 0.5]
    if low_conf:
        print(f"\n⚠️  Low Confidence Predictions (<0.5): {len(low_conf)}")
        for r in low_conf[:5]:
            status = "✅" if r["correct"] else "❌"
            print(f"  {status} \"{r['query'][:60]}\" → {r['predicted']} (conf: {r['confidence']:.3f}, true: {r['true']})")

    print("\n" + "=" * 80)
    print("✅ Inference complete!")

    return accuracy


if __name__ == "__main__":
    main()
