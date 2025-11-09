#!/usr/bin/env python3
"""
Simple model export for production deployment.

Instead of ONNX (which has compatibility issues), we'll just copy the model
and create a lightweight Python inference wrapper.
"""

import json
import shutil
from pathlib import Path


def main():
    """Export model for production."""
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent

    # Paths
    model_dir = base_dir / "outputs" / "contrastive_model"
    specs_path = base_dir / "data" / "intent_specs_embedded.json"
    output_dir = base_dir / "production_model"

    print("📦 Preparing model for production deployment\n")
    print("=" * 80)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy model files
    print(f"\n📁 Copying model from {model_dir}")
    model_output = output_dir / "model"
    if model_output.exists():
        shutil.rmtree(model_output)
    shutil.copytree(model_dir, model_output)
    print(f"   ✅ Model copied to {model_output}")

    # Copy intent specs
    print(f"\n📋 Copying intent specs from {specs_path}")
    specs_output = output_dir / "intent_specs_embedded.json"
    shutil.copy(specs_path, specs_output)
    print(f"   ✅ Specs copied to {specs_output}")

    # Create inference config
    config = {
        "model_path": "model",  # Relative path
        "intent_specs_path": "intent_specs_embedded.json",  # Relative path
        "confidence_threshold": 0.5,
        "max_sequence_length": 128,
        "similarity_metric": "cosine",
        "model_type": "sentence-transformers",
        "pooling_strategy": "mean"
    }

    config_path = output_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\n⚙️  Config saved to {config_path}")

    # Create README
    readme_content = """# Intent Classifier Production Model

This directory contains the trained intent classifier model ready for production deployment.

## Contents

- `model/`: Sentence-transformers model (MiniLM-L6-v2 fine-tuned with contrastive learning)
- `intent_specs_embedded.json`: Intent definitions with pre-computed embeddings
- `config.json`: Inference configuration

## Usage in Python

```python
from sentence_transformers import SentenceTransformer
import json
import numpy as np

# Load model
model = SentenceTransformer('production_model/model')

# Load intent specs
with open('production_model/intent_specs_embedded.json') as f:
    data = json.load(f)

intents = data['intents']
labels = [intent['label'] for intent in intents]
embeddings = np.array([intent['embedding'] for intent in intents])

# Classify query
query = "what's on my calendar today?"
query_embedding = model.encode(query, convert_to_numpy=True)

# Compute cosine similarity
similarities = np.dot(embeddings, query_embedding) / (
    np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
)

# Get top prediction
top_idx = np.argmax(similarities)
predicted_intent = labels[top_idx]
confidence = float(similarities[top_idx])

print(f"Intent: {predicted_intent} (confidence: {confidence:.3f})")
```

## Model Stats

- **Model**: sentence-transformers/all-MiniLM-L6-v2 (fine-tuned)
- **Intents**: 22 classes
- **Test Accuracy**: 88%
- **Avg Confidence**: 0.922
- **Model Size**: ~80MB
- **Inference Speed**: ~10-20ms on CPU

## Deployment

1. Copy this entire directory to your backend
2. Install dependencies: `pip install sentence-transformers numpy`
3. Load model using the code above
4. Integrate with NLU service

## Notes

- Model runs efficiently on CPU (no GPU required)
- Pre-computed intent embeddings speed up inference
- Confidence threshold of 0.5 recommended for production
"""

    readme_path = output_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)
    print(f"\n📄 README created at {readme_path}")

    # Print summary
    print("\n" + "=" * 80)
    print("✅ MODEL EXPORT COMPLETE!")
    print("=" * 80)
    print(f"\n📦 Production model ready at: {output_dir.absolute()}")
    print(f"\n📊 Model size: {get_dir_size(model_output):.1f} MB")
    print(f"\n🚀 Next steps:")
    print(f"   1. Copy {output_dir.name}/ to backend/app/agents/nlu/")
    print(f"   2. Update NLU service to load from this directory")
    print(f"   3. Test integration with orchestrator")
    print()


def get_dir_size(path: Path) -> float:
    """Get directory size in MB."""
    total = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    return total / (1024 * 1024)


if __name__ == "__main__":
    main()
