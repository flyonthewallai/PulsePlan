"""
Export Production Prompts for Retraining

Fetches logged prompts from production database and exports them in training format.
Includes both corrected prompts and high-confidence predictions.
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.database.nlu_repository import create_nlu_repository


async def export_production_prompts(
    output_path: str,
    min_date: datetime = None,
    limit: int = 10000
) -> int:
    """
    Export production prompts for retraining.

    Args:
        output_path: Path to export JSONL file
        min_date: Only include prompts after this date
        limit: Maximum prompts to export

    Returns:
        Number of prompts exported
    """
    print(f"📊 Exporting production prompts...")
    print(f"   Min date: {min_date or 'all time'}")
    print(f"   Limit: {limit}")
    print()

    # Initialize repository
    repo = create_nlu_repository()

    # Fetch prompts for retraining
    prompts = await repo.get_prompts_for_retraining(
        min_date=min_date,
        limit=limit
    )

    if not prompts:
        print("❌ No prompts found for retraining")
        return 0

    # Convert to training format
    training_examples = []
    corrected_count = 0
    high_conf_count = 0

    for log in prompts:
        # Use corrected intent if available, otherwise predicted
        label = log.get("corrected_intent") or log.get("predicted_intent")
        prompt = log.get("prompt")
        confidence = log.get("confidence", 0.0)

        if not prompt or not label:
            continue

        # Track statistics
        if log.get("corrected_intent"):
            corrected_count += 1
        else:
            high_conf_count += 1

        training_examples.append({
            "text": prompt,
            "label": label,
            "confidence": confidence,
            "source": "production",
            "corrected": bool(log.get("corrected_intent"))
        })

    # Write to JSONL
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for example in training_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    # Print statistics
    print(f"✅ Exported {len(training_examples)} production prompts")
    print()
    print("📈 Statistics:")
    print(f"   - Manually corrected: {corrected_count}")
    print(f"   - High confidence (>0.85): {high_conf_count}")
    print(f"   - Output: {output_file}")
    print()

    return len(training_examples)


async def export_low_confidence_for_review(
    output_path: str,
    threshold: float = 0.7,
    limit: int = 100
) -> int:
    """
    Export low-confidence prompts for manual review.

    Args:
        output_path: Path to export JSONL file
        threshold: Confidence threshold
        limit: Maximum prompts to export

    Returns:
        Number of prompts exported
    """
    print(f"🔍 Exporting low-confidence prompts for review...")
    print(f"   Threshold: {threshold}")
    print(f"   Limit: {limit}")
    print()

    repo = create_nlu_repository()
    prompts = await repo.get_low_confidence_prompts(
        threshold=threshold,
        limit=limit
    )

    if not prompts:
        print("✅ No low-confidence prompts found")
        return 0

    # Write to JSONL for review
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for log in prompts:
            review_record = {
                "id": log.get("id"),
                "prompt": log.get("prompt"),
                "predicted_intent": log.get("predicted_intent"),
                "confidence": log.get("confidence"),
                "created_at": log.get("created_at"),
                # Fields to fill in during review:
                "corrected_intent": "",
                "notes": ""
            }
            f.write(json.dumps(review_record, ensure_ascii=False, indent=2) + '\n')

    print(f"✅ Exported {len(prompts)} prompts for review")
    print(f"   Output: {output_file}")
    print()
    print("📝 Next steps:")
    print("   1. Review the exported file")
    print("   2. Fill in 'corrected_intent' for misclassified prompts")
    print("   3. Add notes explaining why correction was needed")
    print("   4. Run import script to save corrections back to database")
    print()

    return len(prompts)


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Export production prompts for retraining")
    parser.add_argument(
        "--mode",
        choices=["retraining", "review"],
        default="retraining",
        help="Export mode: 'retraining' for model updates, 'review' for manual labeling"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: data/production_prompts.jsonl or data/review_prompts.jsonl)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Only include prompts from last N days (default: all time)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10000,
        help="Maximum prompts to export (default: 10000)"
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.7,
        help="Confidence threshold for review mode (default: 0.7)"
    )

    args = parser.parse_args()

    # Calculate min_date if days specified
    min_date = None
    if args.days:
        min_date = datetime.utcnow() - timedelta(days=args.days)

    # Determine output path
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent

    if args.mode == "retraining":
        output_path = args.output or str(base_dir / "data/production_prompts.jsonl")
        count = await export_production_prompts(
            output_path=output_path,
            min_date=min_date,
            limit=args.limit
        )
    else:  # review mode
        output_path = args.output or str(base_dir / "data/review_prompts.jsonl")
        count = await export_low_confidence_for_review(
            output_path=output_path,
            threshold=args.confidence_threshold,
            limit=args.limit
        )

    if count > 0:
        print("✨ Export complete!")
    else:
        print("⚠️ No data exported")

    return count


if __name__ == "__main__":
    asyncio.run(main())
