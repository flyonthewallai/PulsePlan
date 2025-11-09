#!/usr/bin/env python3
"""Remove vague status examples that overlap with user_data_query."""

import json
from pathlib import Path

# Examples to remove - these are too vague and overlap with other intents
VAGUE_STATUS_EXAMPLES = {
    "Give me an update",
    "What's my current status?",
    "Where am I on the project?",
    "Show my progress",
    "Am I on track with my goals?",
    "Dashboard",
    "Progress report",
    "Productivity summary",
    "How am I doing on my tasks?",
    "Stats",
    "Metrics",
    "Performance check",
    "Score",
}

# Normalize for comparison (lowercase, strip)
VAGUE_NORMALIZED = {s.lower().strip() for s in VAGUE_STATUS_EXAMPLES}


def should_remove(text: str) -> bool:
    """Check if this status example should be removed."""
    return text.lower().strip() in VAGUE_NORMALIZED


def filter_dataset(input_path: Path, output_path: Path):
    """Filter out vague status examples from a JSONL dataset."""
    lines_read = 0
    lines_kept = 0
    lines_removed = 0

    with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
        for line in f_in:
            lines_read += 1
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)

                # Only filter status intent examples
                if obj.get("label") == "status" and should_remove(obj.get("text", "")):
                    lines_removed += 1
                    print(f"  Removing: {obj['text']}")
                else:
                    f_out.write(json.dumps(obj) + '\n')
                    lines_kept += 1
            except json.JSONDecodeError as e:
                print(f"  ⚠️  Skipping malformed line {lines_read}: {e}")

    return lines_read, lines_kept, lines_removed


def main():
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent.parent
    data_dir = base_dir / "data" / "intents"

    print("🔍 Refining status intent examples...\n")
    print(f"Data directory: {data_dir}\n")
    print(f"Will remove {len(VAGUE_STATUS_EXAMPLES)} vague examples:\n")
    for ex in sorted(VAGUE_STATUS_EXAMPLES):
        print(f"  - {ex}")
    print()

    for dataset_name in ["train", "dev", "test"]:
        input_path = data_dir / f"{dataset_name}.jsonl"
        output_path = data_dir / f"{dataset_name}_refined.jsonl"

        print(f"\n📝 Processing {dataset_name}.jsonl...")
        read, kept, removed = filter_dataset(input_path, output_path)

        print(f"  Lines read: {read}")
        print(f"  Lines kept: {kept}")
        print(f"  Lines removed: {removed}")

        # Replace original with refined
        output_path.replace(input_path)
        print(f"  ✅ Updated {dataset_name}.jsonl")

    print("\n✅ Done! Status intent examples refined.")
    print("\nNext steps:")
    print("  1. Regenerate training pairs")
    print("  2. Retrain model")
    print("  3. Run inference validation")


if __name__ == "__main__":
    main()
