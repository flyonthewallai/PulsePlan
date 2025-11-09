"""
Contrastive Learning Training Script for Intent Classifier

Trains MiniLM model using pair-based contrastive learning with CosineSimilarityLoss.
This replaces the classification-based approach for better semantic understanding.
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple
import torch
from sentence_transformers import (
    SentenceTransformer,
    InputExample,
    losses,
    evaluation
)
from torch.utils.data import DataLoader

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils_logging import setup_logger, load_config


def load_pairs(filepath: Path) -> List[InputExample]:
    """
    Load contrastive pairs from JSONL file.

    Args:
        filepath: Path to pairs JSONL file

    Returns:
        List of InputExample objects for sentence-transformers
    """
    examples = []
    with open(filepath, "r") as f:
        for line in f:
            data = json.loads(line.strip())
            examples.append(
                InputExample(
                    texts=[data["sentence1"], data["sentence2"]],
                    label=float(data["label"])
                )
            )
    return examples


def create_evaluators(intent_specs_path: Path, model: SentenceTransformer):
    """
    Create evaluation datasets for monitoring training.

    Uses intent descriptions as anchors and measures retrieval accuracy.

    Args:
        intent_specs_path: Path to intent_specs.json
        model: SentenceTransformer model instance

    Returns:
        Evaluator for sentence-transformers Trainer
    """
    with open(intent_specs_path, "r") as f:
        intent_data = json.load(f)

    intents = intent_data["intents"]

    # Create queries (example utterances) and corpus (intent descriptions)
    queries = {}
    corpus = {}
    relevant_docs = {}

    for idx, intent in enumerate(intents):
        # Corpus: intent descriptions
        corpus[str(idx)] = intent["description"]

        # Queries: sample examples from each intent
        for ex_idx, example in enumerate(intent["examples"][:3]):  # Use 3 examples per intent
            query_id = f"{intent['label']}_{ex_idx}"
            queries[query_id] = example
            relevant_docs[query_id] = {str(idx)}  # Relevant doc is the intent description

    # Create information retrieval evaluator
    evaluator = evaluation.InformationRetrievalEvaluator(
        queries=queries,
        corpus=corpus,
        relevant_docs=relevant_docs,
        name="intent_classification_eval"
    )

    return evaluator


def train_contrastive_classifier(config_path: Path) -> None:
    """
    Main training function for contrastive learning.

    Args:
        config_path: Path to YAML configuration file
    """
    # Load config
    config = load_config(config_path)

    # Setup logging
    logger = setup_logger(
        "intent_classifier_contrastive",
        log_file_path=Path("ml/intent_classifier/training_contrastive.log"),
        log_level=config["logging"]["level"],
        log_format=config["logging"]["format"]
    )

    logger.info("=" * 60)
    logger.info("Starting Contrastive Intent Classifier Training")
    logger.info("=" * 60)

    # Load base model
    base_model_name = config["model"]["base_model_name"]
    logger.info(f"Loading base model: {base_model_name}")

    model = SentenceTransformer(base_model_name)

    # Device setup
    device = "cuda" if torch.cuda.is_available() and config["training"]["device_preference_train"] == "cuda" else "cpu"
    logger.info(f"Training device: {device}")
    model.to(device)

    # Load training pairs (relative to script directory)
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    pairs_path = base_dir / "data/train_pairs.jsonl"
    logger.info(f"Loading training pairs from {pairs_path}")
    train_examples = load_pairs(pairs_path)
    logger.info(f"Loaded {len(train_examples)} training pairs")

    # Count positive/negative
    pos_count = sum(1 for ex in train_examples if ex.label == 1.0)
    neg_count = len(train_examples) - pos_count
    logger.info(f"Positive pairs: {pos_count}, Negative pairs: {neg_count}")

    # Create DataLoader
    train_dataloader = DataLoader(
        train_examples,
        shuffle=True,
        batch_size=config["training"]["batch_size_train"]
    )

    # Define loss function: CosineSimilarityLoss for contrastive learning
    train_loss = losses.CosineSimilarityLoss(model)
    logger.info("Using CosineSimilarityLoss for contrastive training")

    # Create evaluator
    intent_specs_path = base_dir / "data/intent_specs.json"
    evaluator = create_evaluators(intent_specs_path, model)

    # Training parameters
    num_epochs = config["training"]["num_epochs"]
    warmup_steps = config["training"]["warmup_steps"]
    output_dir = base_dir / "outputs" / "contrastive_model"

    logger.info(f"Training for {num_epochs} epochs with {warmup_steps} warmup steps")

    # Check if model already exists
    if output_dir.exists() and (output_dir / "model.safetensors").exists():
        logger.info(f"✅ Model already exists at {output_dir}, skipping training")
        model = SentenceTransformer(str(output_dir))
    else:
        # Train the model
        model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            evaluator=evaluator,
            epochs=num_epochs,
            warmup_steps=warmup_steps,
            output_path=str(output_dir),
            evaluation_steps=config["training"]["eval_steps"],
            save_best_model=True,
            show_progress_bar=True
        )

        logger.info(f"Model saved to {output_dir}")

    # Generate and cache intent embeddings for inference
    logger.info("Generating intent description embeddings...")
    with open(intent_specs_path, "r") as f:
        intent_data = json.load(f)

    intents = intent_data["intents"]
    descriptions = [intent["description"] for intent in intents]

    embeddings = model.encode(descriptions, convert_to_tensor=False, show_progress_bar=True)

    # Save embeddings alongside specs
    for idx, intent in enumerate(intents):
        intent["embedding"] = embeddings[idx].tolist()

    embedded_specs_path = base_dir / "data/intent_specs_embedded.json"
    with open(embedded_specs_path, "w") as f:
        json.dump({"intents": intents}, f, indent=2)

    logger.info(f"Cached intent embeddings to {embedded_specs_path}")

    # Test inference
    logger.info("Testing inference on sample queries...")
    test_queries = [
        "move my 3pm meeting to tomorrow",
        "add task to finish homework",
        "what's on my calendar today?",
        "send email to professor"
    ]

    for query in test_queries:
        query_emb = model.encode(query, convert_to_tensor=False)

        # Compute similarities
        similarities = []
        for intent in intents:
            intent_emb = intent["embedding"]
            similarity = torch.nn.functional.cosine_similarity(
                torch.tensor(query_emb).unsqueeze(0),
                torch.tensor(intent_emb).unsqueeze(0)
            ).item()
            similarities.append((intent["label"], similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: -x[1])
        top_intent, top_score = similarities[0]

        logger.info(f"Query: '{query}' -> Predicted: {top_intent} (score: {top_score:.3f})")

    logger.info("=" * 60)
    logger.info("Contrastive training completed successfully!")
    logger.info("=" * 60)


def main():
    """Entry point for contrastive training script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Train intent classifier with contrastive learning"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config YAML file"
    )

    args = parser.parse_args()

    # Auto-detect config location
    if args.config is None:
        script_dir = Path(__file__).parent
        config_path = script_dir.parent / "config.yaml"
    else:
        config_path = args.config

    train_contrastive_classifier(config_path)


if __name__ == "__main__":
    main()
