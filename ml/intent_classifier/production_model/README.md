# Intent Classifier Production Model

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
