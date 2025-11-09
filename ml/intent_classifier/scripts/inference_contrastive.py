"""
Contrastive Inference Module for Intent Classification

Performs similarity-based intent classification using cached embeddings.
"""

import json
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class ContrastiveIntentClassifier:
    """
    Intent classifier using contrastive embeddings and similarity search.

    Instead of classification head, this uses cosine similarity between
    query embedding and cached intent description embeddings.
    """

    def __init__(
        self,
        model_path: str,
        intent_specs_path: str,
        confidence_threshold: float = 0.5
    ):
        """
        Initialize classifier with trained model and intent specs.

        Args:
            model_path: Path to trained SentenceTransformer model
            intent_specs_path: Path to intent_specs_embedded.json
            confidence_threshold: Minimum similarity score for classification
        """
        self.model = SentenceTransformer(model_path)
        self.confidence_threshold = confidence_threshold

        # Load cached embeddings
        with open(intent_specs_path, "r") as f:
            intent_data = json.load(f)

        self.intents = intent_data["intents"]
        self.intent_labels = [intent["label"] for intent in self.intents]
        self.intent_embeddings = np.array([intent["embedding"] for intent in self.intents])

        print(f"Loaded {len(self.intents)} intents with cached embeddings")

    def predict(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Predict intent for a query using similarity search.

        Args:
            query: Input text
            top_k: Number of top predictions to return

        Returns:
            List of (intent_label, similarity_score) tuples, sorted by score
        """
        # Encode query
        query_embedding = self.model.encode(query, convert_to_tensor=False)

        # Compute similarities
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1),
            self.intent_embeddings
        )[0]

        # Get top-k predictions
        top_indices = np.argsort(similarities)[::-1][:top_k]
        predictions = [
            (self.intent_labels[idx], float(similarities[idx]))
            for idx in top_indices
        ]

        return predictions

    def predict_single(self, query: str) -> Tuple[str, float]:
        """
        Predict single best intent with confidence score.

        Args:
            query: Input text

        Returns:
            Tuple of (predicted_intent, confidence_score)
        """
        predictions = self.predict(query, top_k=1)
        intent, score = predictions[0]

        # Apply threshold
        if score < self.confidence_threshold:
            return "unknown", score

        return intent, score

    def predict_multi_intent(
        self,
        query: str,
        threshold: float = 0.6
    ) -> List[Tuple[str, float]]:
        """
        Detect multiple intents in a single query.

        Useful for compound queries like "check my calendar and send an email".

        Args:
            query: Input text
            threshold: Minimum similarity for an intent to be included

        Returns:
            List of (intent_label, score) for all intents above threshold
        """
        query_embedding = self.model.encode(query, convert_to_tensor=False)

        similarities = cosine_similarity(
            query_embedding.reshape(1, -1),
            self.intent_embeddings
        )[0]

        # Filter by threshold and sort
        multi_intents = [
            (self.intent_labels[idx], float(similarities[idx]))
            for idx, score in enumerate(similarities)
            if score >= threshold
        ]

        multi_intents.sort(key=lambda x: -x[1])

        return multi_intents

    def batch_predict(self, queries: List[str]) -> List[Tuple[str, float]]:
        """
        Predict intents for multiple queries efficiently.

        Args:
            queries: List of input texts

        Returns:
            List of (predicted_intent, confidence_score) for each query
        """
        # Batch encode queries
        query_embeddings = self.model.encode(queries, convert_to_tensor=False, show_progress_bar=True)

        # Compute similarities
        similarities = cosine_similarity(query_embeddings, self.intent_embeddings)

        # Get best intent for each query
        predictions = []
        for query_sims in similarities:
            best_idx = np.argmax(query_sims)
            intent = self.intent_labels[best_idx]
            score = float(query_sims[best_idx])

            # Apply threshold
            if score < self.confidence_threshold:
                predictions.append(("unknown", score))
            else:
                predictions.append((intent, score))

        return predictions

    def get_intent_info(self, intent_label: str) -> Optional[dict]:
        """
        Get full intent specification for a label.

        Args:
            intent_label: Intent label to look up

        Returns:
            Intent specification dict or None if not found
        """
        for intent in self.intents:
            if intent["label"] == intent_label:
                return intent
        return None


def main():
    """Demo inference with test queries."""
    import argparse

    parser = argparse.ArgumentParser(description="Run contrastive intent classifier")
    parser.add_argument(
        "--model",
        type=str,
        default="ml/intent_classifier/outputs/contrastive_model",
        help="Path to trained model"
    )
    parser.add_argument(
        "--specs",
        type=str,
        default="ml/intent_classifier/data/intent_specs_embedded.json",
        help="Path to intent specs with embeddings"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Single query to classify"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Confidence threshold"
    )

    args = parser.parse_args()

    # Initialize classifier
    classifier = ContrastiveIntentClassifier(
        model_path=args.model,
        intent_specs_path=args.specs,
        confidence_threshold=args.threshold
    )

    if args.query:
        # Single query
        intent, score = classifier.predict_single(args.query)
        print(f"\nQuery: {args.query}")
        print(f"Predicted Intent: {intent} (confidence: {score:.3f})")

        # Show top-3
        print("\nTop-3 predictions:")
        for intent, score in classifier.predict(args.query, top_k=3):
            print(f"  {intent}: {score:.3f}")

        # Check for multi-intent
        multi = classifier.predict_multi_intent(args.query, threshold=0.55)
        if len(multi) > 1:
            print("\nMulti-intent detected:")
            for intent, score in multi:
                print(f"  {intent}: {score:.3f}")
    else:
        # Test queries
        test_queries = [
            "move my 3pm meeting to tomorrow",
            "add task to finish homework",
            "what's on my calendar today?",
            "send email to professor about the assignment",
            "check my tasks and schedule time to finish them",
            "hello",
            "thanks",
            "asdfasdf xyz"
        ]

        print("\nRunning test queries...")
        predictions = classifier.batch_predict(test_queries)

        for query, (intent, score) in zip(test_queries, predictions):
            print(f"{query:<50} -> {intent:<20} ({score:.3f})")


if __name__ == "__main__":
    main()
