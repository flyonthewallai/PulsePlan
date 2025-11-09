"""
Dataset Validation Script for Contrastive Intent Classifier

Validates the quality and completeness of the training data before training.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict


def validate_intent_specs(specs_path: Path) -> dict:
    """Validate intent_specs.json structure and completeness."""
    with open(specs_path, "r") as f:
        data = json.load(f)

    print("=" * 60)
    print("INTENT SPECS VALIDATION")
    print("=" * 60)

    intents = data["intents"]
    metadata = data.get("metadata", {})

    print(f"\nMetadata:")
    print(f"  Source: {metadata.get('source', 'N/A')}")
    print(f"  Version: {metadata.get('version', 'N/A')}")
    print(f"  Total intents: {metadata.get('total_intents', len(intents))}")

    # Validate each intent
    issues = []
    domain_counts = Counter()

    for intent in intents:
        label = intent.get("label")
        description = intent.get("description")
        domain = intent.get("domain")
        examples = intent.get("examples", [])
        keywords = intent.get("keywords", [])
        hard_negatives = intent.get("hard_negatives", [])

        # Check required fields
        if not label:
            issues.append(f"Missing label in intent")
        if not description or len(description) < 20:
            issues.append(f"{label}: Description too short or missing")
        if not domain:
            issues.append(f"{label}: Missing domain")
        if len(examples) < 10:
            issues.append(f"{label}: Only {len(examples)} examples (min 10 recommended)")
        if not keywords:
            issues.append(f"{label}: No keywords defined")
        if not hard_negatives:
            issues.append(f"{label}: No hard negatives defined")

        domain_counts[domain] += 1

    print(f"\nIntent distribution by domain:")
    for domain, count in sorted(domain_counts.items()):
        print(f"  {domain:<15} {count:>3} intents")

    if issues:
        print(f"\n⚠️  Found {len(issues)} issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")
    else:
        print("\n✅ All intent specs valid!")

    return {
        "total_intents": len(intents),
        "domains": len(domain_counts),
        "issues": len(issues)
    }


def validate_training_data(data_dir: Path) -> dict:
    """Validate train/dev/test JSONL files."""
    print("\n" + "=" * 60)
    print("TRAINING DATA VALIDATION")
    print("=" * 60)

    stats = {}
    all_labels = set()

    for split in ["train", "dev", "test"]:
        filepath = data_dir / f"{split}.jsonl"

        if not filepath.exists():
            print(f"\n❌ {split}.jsonl not found!")
            continue

        examples = []
        errors = 0

        with open(filepath, "r") as f:
            for i, line in enumerate(f, 1):
                try:
                    item = json.loads(line.strip())
                    if "text" in item and "label" in item:
                        examples.append(item)
                        all_labels.add(item["label"])
                    else:
                        errors += 1
                except:
                    errors += 1

        # Count per label
        label_counts = Counter([ex["label"] for ex in examples])

        stats[split] = {
            "total": len(examples),
            "errors": errors,
            "unique_labels": len(label_counts),
            "label_counts": label_counts
        }

        print(f"\n{split.upper()}:")
        print(f"  Total examples: {len(examples)}")
        print(f"  Errors: {errors}")
        print(f"  Unique labels: {len(label_counts)}")

        # Show labels with < 5 examples
        sparse = {label: count for label, count in label_counts.items() if count < 5}
        if sparse:
            print(f"  ⚠️  Sparse labels (< 5 examples):")
            for label, count in sparse.items():
                print(f"    - {label}: {count}")

    print(f"\n✅ Found {len(all_labels)} unique intent labels across all splits")

    return stats


def validate_pairs(pairs_path: Path) -> dict:
    """Validate train_pairs.jsonl."""
    print("\n" + "=" * 60)
    print("CONTRASTIVE PAIRS VALIDATION")
    print("=" * 60)

    if not pairs_path.exists():
        print(f"❌ {pairs_path} not found!")
        return {}

    pairs = []
    errors = 0

    with open(pairs_path, "r") as f:
        for i, line in enumerate(f, 1):
            try:
                pair = json.loads(line.strip())
                if all(k in pair for k in ["sentence1", "sentence2", "label"]):
                    pairs.append(pair)
                else:
                    errors += 1
            except:
                errors += 1

    pos_count = sum(1 for p in pairs if p["label"] == 1)
    neg_count = len(pairs) - pos_count

    print(f"\nTotal pairs: {len(pairs)}")
    print(f"Errors: {errors}")
    print(f"Positive pairs: {pos_count} ({pos_count/len(pairs)*100:.1f}%)")
    print(f"Negative pairs: {neg_count} ({neg_count/len(pairs)*100:.1f}%)")
    print(f"Ratio: 1:{neg_count/pos_count:.2f}")

    # Quality checks
    issues = []

    if neg_count / pos_count > 4:
        issues.append(f"Negative ratio too high (1:{neg_count/pos_count:.1f}), prefer 1:3")
    elif neg_count / pos_count < 2:
        issues.append(f"Not enough negatives (1:{neg_count/pos_count:.1f}), prefer 1:3")

    # Check for very short examples
    short_s1 = sum(1 for p in pairs if len(p["sentence1"]) < 5)
    short_s2 = sum(1 for p in pairs if len(p["sentence2"]) < 20)

    if short_s1 > 0:
        issues.append(f"{short_s1} pairs have very short sentence1 (< 5 chars)")
    if short_s2 > 0:
        issues.append(f"{short_s2} pairs have very short sentence2 (< 20 chars)")

    if issues:
        print(f"\n⚠️  Quality issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ Pairs dataset looks good!")

    return {
        "total": len(pairs),
        "positive": pos_count,
        "negative": neg_count,
        "ratio": neg_count / pos_count if pos_count > 0 else 0,
        "issues": len(issues)
    }


def validate_multi_intent(multi_path: Path) -> dict:
    """Validate multi_intent_examples.jsonl."""
    print("\n" + "=" * 60)
    print("MULTI-INTENT EXAMPLES VALIDATION")
    print("=" * 60)

    if not multi_path.exists():
        print(f"❌ {multi_path} not found!")
        return {}

    examples = []
    errors = 0

    with open(multi_path, "r") as f:
        for line in f:
            try:
                ex = json.loads(line.strip())
                if "text" in ex and "intents" in ex and "decomposed" in ex:
                    examples.append(ex)
                else:
                    errors += 1
            except:
                errors += 1

    # Count intent combinations
    combo_counts = Counter()
    for ex in examples:
        combo = tuple(sorted(ex["intents"]))
        combo_counts[combo] += 1

    print(f"\nTotal examples: {len(examples)}")
    print(f"Errors: {errors}")
    print(f"Unique combinations: {len(combo_counts)}")

    print(f"\nTop 5 combinations:")
    for combo, count in combo_counts.most_common(5):
        print(f"  {' + '.join(combo):<40} {count:>3} examples")

    if len(examples) < 50:
        print(f"\n⚠️  Only {len(examples)} examples, recommend >= 50")
    else:
        print("\n✅ Multi-intent dataset looks good!")

    return {
        "total": len(examples),
        "combinations": len(combo_counts),
        "errors": errors
    }


def main():
    """Run all validations."""
    base_path = Path("ml/intent_classifier")

    print("\n" + "=" * 60)
    print("CONTRASTIVE INTENT CLASSIFIER - DATASET VALIDATION")
    print("=" * 60)

    # Validate intent specs
    specs_result = validate_intent_specs(base_path / "data/intent_specs.json")

    # Validate training data
    data_result = validate_training_data(Path("data/intents"))

    # Validate pairs
    pairs_result = validate_pairs(base_path / "data/train_pairs.jsonl")

    # Validate multi-intent
    multi_result = validate_multi_intent(base_path / "data/multi_intent_examples.jsonl")

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    total_issues = (
        specs_result.get("issues", 0) +
        pairs_result.get("issues", 0)
    )

    print(f"\n✅ Intent specs: {specs_result.get('total_intents', 0)} intents, {specs_result.get('domains', 0)} domains")
    print(f"✅ Training data: {data_result.get('train', {}).get('total', 0)} train, {data_result.get('dev', {}).get('total', 0)} dev, {data_result.get('test', {}).get('total', 0)} test")
    print(f"✅ Contrastive pairs: {pairs_result.get('total', 0)} pairs (1:{pairs_result.get('ratio', 0):.2f} ratio)")
    print(f"✅ Multi-intent: {multi_result.get('total', 0)} examples")

    if total_issues == 0:
        print("\n🎉 All validations passed! Ready to train.")
    else:
        print(f"\n⚠️  Found {total_issues} issues to address before training.")

    return total_issues == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
