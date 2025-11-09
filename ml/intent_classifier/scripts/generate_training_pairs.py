#!/usr/bin/env python3
"""
Generate contrastive training pairs for intent classification.

Creates positive pairs (same intent) and negative pairs (different intents)
from the training JSONL data with a 1:3 positive:negative ratio.
"""

import json
import random
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple


def load_intent_specs(specs_path: Path) -> Dict:
    """Load intent specifications including descriptions and keywords."""
    with open(specs_path, "r") as f:
        return json.load(f)


def load_training_data(data_path: Path) -> Dict[str, List[str]]:
    """Load training examples grouped by intent label."""
    intent_examples = defaultdict(list)

    with open(data_path, "r") as f:
        for line in f:
            item = json.loads(line.strip())
            intent_examples[item["label"]].append(item["text"])

    return dict(intent_examples)


def generate_positive_pairs(intent_examples: Dict[str, List[str]],
                            intent_specs: Dict) -> List[Tuple[str, str, int]]:
    """
    Generate positive pairs (label=1) by pairing:
    1. Examples from same intent
    2. Examples with intent description
    3. Examples with intent keywords
    """
    pairs = []

    # Get intent descriptions and keywords
    descriptions = {
        intent["label"]: intent["description"]
        for intent in intent_specs["intents"]
    }

    keywords_map = {
        intent["label"]: intent.get("keywords", [])
        for intent in intent_specs["intents"]
    }

    for intent_label, examples in intent_examples.items():
        description = descriptions.get(intent_label, "")
        keywords = keywords_map.get(intent_label, [])

        # Pair each example with description (multiple times for diversity)
        for example in examples:
            if description:
                pairs.append((example, description, 1))
                # Add reverse pairing for bidirectional learning
                pairs.append((description, example, 1))

        # Pair examples with keywords
        for example in examples:
            for keyword in keywords[:3]:  # Use top 3 keywords
                pairs.append((example, keyword, 1))

        # ALL combinatorial pairs within same intent (not limited)
        for i in range(len(examples)):
            for j in range(i + 1, len(examples)):
                pairs.append((examples[i], examples[j], 1))

    return pairs


def generate_negative_pairs(intent_examples: Dict[str, List[str]],
                            intent_specs: Dict,
                            target_count: int) -> List[Tuple[str, str, int]]:
    """
    Generate negative pairs (label=0) by pairing examples from different intents.

    Prioritizes hard negatives based on similar domains or keywords.
    """
    pairs = []
    intent_labels = list(intent_examples.keys())

    # Get intent metadata for hard negative generation
    intent_meta = {
        intent["label"]: intent
        for intent in intent_specs["intents"]
    }

    # Build hard negative mappings based on domain similarity
    hard_negative_candidates = defaultdict(list)
    for intent_label in intent_labels:
        domain = intent_meta[intent_label].get("domain", "")

        # Find intents in same domain (hard negatives)
        for other_label in intent_labels:
            if other_label != intent_label:
                if intent_meta[other_label].get("domain") == domain:
                    hard_negative_candidates[intent_label].append(other_label)

        # If no domain matches, use all others
        if not hard_negative_candidates[intent_label]:
            hard_negative_candidates[intent_label] = [
                l for l in intent_labels if l != intent_label
            ]

    # Generate negative pairs
    attempts = 0
    max_attempts = target_count * 10

    while len(pairs) < target_count and attempts < max_attempts:
        attempts += 1

        # Pick random intent
        intent1 = random.choice(intent_labels)

        # Pick hard negative intent (70% of time) or random (30%)
        if random.random() < 0.7:
            intent2 = random.choice(hard_negative_candidates[intent1])
        else:
            intent2 = random.choice([l for l in intent_labels if l != intent1])

        # Pick random examples from each
        example1 = random.choice(intent_examples[intent1])
        example2 = random.choice(intent_examples[intent2])

        # Avoid duplicates
        if (example1, example2, 0) not in pairs and (example2, example1, 0) not in pairs:
            pairs.append((example1, example2, 0))

    return pairs


def main():
    """Generate contrastive training pairs."""
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent.parent
    ml_dir = base_dir / "ml" / "intent_classifier"

    # Paths
    specs_path = ml_dir / "data" / "intent_specs.json"
    train_path = base_dir / "data" / "intents" / "train.jsonl"
    output_path = ml_dir / "data" / "train_pairs.jsonl"

    print("🔧 Generating contrastive training pairs...")
    print(f"\nIntent specs: {specs_path}")
    print(f"Training data: {train_path}")
    print(f"Output: {output_path}\n")

    # Load data
    intent_specs = load_intent_specs(specs_path)
    intent_examples = load_training_data(train_path)

    print(f"Loaded {len(intent_examples)} intent classes")
    total_examples = sum(len(exs) for exs in intent_examples.values())
    print(f"Total training examples: {total_examples}\n")

    # Generate positive pairs
    print("Generating positive pairs...")
    positive_pairs = generate_positive_pairs(intent_examples, intent_specs)
    print(f"  Generated {len(positive_pairs)} positive pairs")

    # Generate negative pairs (1:3 ratio)
    target_negatives = len(positive_pairs) * 3
    print(f"\nGenerating negative pairs (target: {target_negatives})...")
    negative_pairs = generate_negative_pairs(
        intent_examples,
        intent_specs,
        target_negatives
    )
    print(f"  Generated {len(negative_pairs)} negative pairs")

    # Combine and shuffle
    all_pairs = positive_pairs + negative_pairs
    random.shuffle(all_pairs)

    print(f"\nTotal pairs: {len(all_pairs)}")
    print(f"  Positive: {len(positive_pairs)} ({len(positive_pairs)/len(all_pairs)*100:.1f}%)")
    print(f"  Negative: {len(negative_pairs)} ({len(negative_pairs)/len(all_pairs)*100:.1f}%)")
    print(f"  Ratio: 1:{len(negative_pairs)/len(positive_pairs):.2f}")

    # Write to JSONL
    print(f"\nWriting to {output_path}...")
    with open(output_path, "w") as f:
        for sentence1, sentence2, label in all_pairs:
            pair = {
                "sentence1": sentence1,
                "sentence2": sentence2,
                "label": label
            }
            f.write(json.dumps(pair) + "\n")

    print(f"✅ Done! Generated {len(all_pairs)} training pairs.")


if __name__ == "__main__":
    random.seed(42)  # For reproducibility
    main()
