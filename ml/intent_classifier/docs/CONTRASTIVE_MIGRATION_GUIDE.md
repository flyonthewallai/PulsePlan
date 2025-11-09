# Contrastive Learning Migration Guide

## Overview

This guide documents the migration from **classification-based** intent detection to **contrastive learning** with similarity search.

### Key Changes

| Aspect | Old Approach (Classification) | New Approach (Contrastive) |
|--------|------------------------------|----------------------------|
| **Training Data** | `train.jsonl` (text + label) | `train_pairs.jsonl` (sentence pairs + similarity label) |
| **Loss Function** | CrossEntropyLoss | CosineSimilarityLoss |
| **Model Output** | Logits over N classes | Dense embedding vector |
| **Inference** | Argmax over logits | Cosine similarity to intent descriptions |
| **Multi-intent** | Not supported | Native support via threshold |
| **Training Script** | `train.py` (Transformers Trainer) | `train_contrastive.py` (sentence-transformers) |

## Files Created

### Data Files

1. **`intent_specs.json`** (23 intents)
   - Canonical intent definitions with descriptions, domains, keywords, hard negatives
   - Generated from existing train/dev/test data + manually curated new intents
   - **23 intents** across 8 domains:
     - **Scheduling** (3): scheduling, calendar_event, reschedule
     - **Tasks** (1): task_management
     - **Communication** (2): email, reminder
     - **Information** (4): search, briefing, status, user_data_query
     - **System** (7): greeting, thanks, confirm, cancel, help, app_info_query, adjust_preferences
     - **Planning** (1): adjust_plan
     - **Slots** (2): temporal_slot_fill, time_slot_fill
     - **Fallback** (3): chitchat, unknown, clarification_request
   - Placeholder normalization ({person}, {date}, {time}, {task}, {event}, {course})

2. **`train_pairs.jsonl`** (2,316 pairs)
   - Positive pairs: utterance ↔ correct intent description (579)
   - Negative pairs: utterance ↔ incorrect intent descriptions (1,737)
   - **Ratio: 1:3.00** (optimal for contrastive learning)
   - **Hard negatives** from same domain (e.g., "scheduling" vs "reschedule")
   - **Medium negatives** from adjacent domains (e.g., "scheduling" vs "task_management")
   - **Easy negatives** from different domains (e.g., "scheduling" vs "greeting")
   - Semantic validation to remove false positives/negatives

3. **`multi_intent_examples.jsonl`** (74 examples)
   - Compound queries with multiple intents
   - 21 unique intent combinations
   - Clause-level decomposition for evaluation
   - Includes new meta-intents (app_info_query, adjust_preferences, user_data_query)

### Training & Inference

4. **`train_contrastive.py`**
   - Trains MiniLM with CosineSimilarityLoss
   - Uses sentence-transformers library
   - Caches intent embeddings for fast inference
   - Generates `intent_specs_embedded.json`

5. **`inference_contrastive.py`**
   - `ContrastiveIntentClassifier` class
   - Single-intent, multi-intent, and batch prediction
   - Similarity-based classification

6. **`export_to_onnx_contrastive.py`**
   - Exports embedding model (not classification head)
   - Creates quantized version for CPU inference
   - Generates `inference_config.json`

## Migration Steps

### 1. Train Contrastive Model

```bash
cd /Users/admin/PulsePlan

# Train the model (uses train_pairs.jsonl)
python ml/intent_classifier/train_contrastive.py --config ml/intent_classifier/config.yaml
```

**Expected Output:**
- Model saved to: `ml/intent_classifier/outputs/contrastive_model/`
- Cached embeddings: `ml/intent_classifier/intent_specs_embedded.json`
- Training log: `ml/intent_classifier/training_contrastive.log`

**Training Time:** ~10-15 minutes on GPU (3060 Ti), ~45-60 minutes on CPU

### 2. Test Inference

```bash
# Test with sample query
python ml/intent_classifier/inference_contrastive.py \
    --model ml/intent_classifier/outputs/contrastive_model \
    --query "move my 3pm meeting to tomorrow"

# Run batch test
python ml/intent_classifier/inference_contrastive.py
```

**Expected Output:**
```
Query: move my 3pm meeting to tomorrow
Predicted Intent: reschedule (confidence: 0.847)

Top-3 predictions:
  reschedule: 0.847
  scheduling: 0.623
  calendar_event: 0.512
```

### 3. Export to ONNX

```bash
# Export and quantize
python ml/intent_classifier/export_to_onnx_contrastive.py \
    --model ml/intent_classifier/outputs/contrastive_model \
    --output-dir ml/intent_classifier/onnx \
    --quantize
```

**Expected Output:**
- ONNX model: `ml/intent_classifier/onnx/model.onnx` (~90 MB)
- Quantized: `ml/intent_classifier/onnx/model_quantized.onnx` (~23 MB)
- Config: `ml/intent_classifier/onnx/inference_config.json`

### 4. Deploy to Production

The ONNX model can be integrated into the backend NLU service:

```python
from ml.intent_classifier.inference_contrastive import ContrastiveIntentClassifier

# Initialize classifier
classifier = ContrastiveIntentClassifier(
    model_path="ml/intent_classifier/onnx",  # Can use ONNX path
    intent_specs_path="ml/intent_classifier/intent_specs_embedded.json",
    confidence_threshold=0.5
)

# Single prediction
intent, confidence = classifier.predict_single("check my tasks and email them to my advisor")

# Multi-intent detection
intents = classifier.predict_multi_intent("check my tasks and email them to my advisor", threshold=0.55)
# Returns: [('search', 0.72), ('email', 0.68)]
```

## Advantages of Contrastive Approach

### 1. **Better Semantic Understanding**
- Model learns **semantic similarity** rather than memorizing patterns
- Generalizes better to unseen phrasings
- Works well with paraphrases

### 2. **Multi-Intent Support**
- Native multi-intent detection via similarity threshold
- Example: "check my calendar and send an email" → `['event_query', 'email']`

### 3. **Easier to Update**
- Adding new intent: just add description and re-embed (no retraining)
- Updating intent definition: re-embed only (fast)

### 4. **Confidence Calibration**
- Similarity scores are more interpretable than softmax probabilities
- Natural threshold for "unknown" intent

### 5. **Hard Negative Mining**
- Explicit hard negatives improve discrimination between similar intents
- Example: `scheduling` vs `reschedule` vs `calendar_event`

## Data Quality Metrics

### Intent Balance

| Intent | Train Examples | Dev Examples | Test Examples | Total |
|--------|---------------|--------------|---------------|-------|
| scheduling | 37 | 14 | 14 | 65 |
| task_management | 36 | 14 | 13 | 63 |
| calendar_event | 32 | 11 | 11 | 54 |
| reschedule | 30 | 10 | 10 | 50 |
| briefing | 30 | 10 | 10 | 50 |
| email | 30 | 10 | 10 | 50 |
| reminder | 30 | 10 | 10 | 50 |
| search | 30 | 10 | 10 | 50 |
| confirm | 29 | 10 | 9 | 48 |
| greeting | 28 | 9 | 9 | 46 |
| status | 28 | 9 | 9 | 46 |
| cancel | 28 | 9 | 9 | 46 |
| adjust_plan | 27 | 9 | 9 | 45 |
| help | 27 | 9 | 9 | 45 |
| thanks | 27 | 9 | 9 | 45 |
| temporal_slot_fill | 26 | 9 | 8 | 43 |
| time_slot_fill | 26 | 9 | 8 | 43 |
| chitchat | 25 | 8 | 8 | 41 |
| unknown | 25 | 8 | 8 | 41 |

**Total:** 551 examples across 19 intents

### Pair Statistics

- **Total pairs:** 3,018
- **Positive pairs:** 551 (18.3%)
- **Negative pairs:** 2,467 (81.7%)
- **Ratio:** 1:4.5 (optimal for contrastive learning)
- **Hard negatives:** ~40% of negative pairs (same domain)

## Validation Checklist

- [ ] Training completes without errors
- [ ] Model achieves >90% accuracy on evaluation
- [ ] Inference script correctly predicts test queries
- [ ] Multi-intent detection works for compound queries
- [ ] ONNX export succeeds and model size is reasonable
- [ ] Quantized model maintains >95% of full model accuracy
- [ ] Inference latency <100ms per query on CPU

## Troubleshooting

### Issue: Low Similarity Scores

**Symptoms:** All predictions have scores <0.5

**Fix:**
1. Check that intent descriptions are semantic (not just labels)
2. Ensure model training completed (check logs)
3. Verify intent_specs_embedded.json has embeddings

### Issue: Can't Distinguish Similar Intents

**Symptoms:** `scheduling` and `reschedule` always confused

**Fix:**
1. Add more hard negatives in `train_pairs.jsonl`
2. Improve intent descriptions to highlight differences
3. Increase training epochs or use larger model

### Issue: Multi-Intent Not Working

**Symptoms:** Only one intent detected for compound queries

**Fix:**
1. Lower the threshold in `predict_multi_intent()`
2. Check multi_intent_examples.jsonl for training data
3. Ensure intent descriptions are distinct

## Rollback Plan

If contrastive approach doesn't work, you can rollback to classification:

1. Old files are preserved in `data/intents/`
2. Use `train.py` instead of `train_contrastive.py`
3. Old ONNX export: `export_to_onnx.py`

## Next Steps

1. **Train the model** using `train_contrastive.py`
2. **Validate performance** on test set
3. **Export to ONNX** with quantization
4. **Integrate** into `backend/app/agents/nlu/` service
5. **Monitor** production performance via PostHog
6. **Iterate** on intent descriptions based on user queries

## References

- **Sentence-Transformers:** https://www.sbert.net/
- **Contrastive Learning:** https://arxiv.org/abs/2104.08821
- **ONNX Runtime:** https://onnxruntime.ai/
