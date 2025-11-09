# Contrastive Intent Classifier - Dataset Summary

## Overview

Production-ready contrastive learning dataset for **23-intent** classification using MiniLM embeddings and similarity search.

## Intent Coverage (23 Total)

### By Domain

| Domain | Count | Intents |
|--------|-------|---------|
| **Scheduling** | 3 | scheduling, calendar_event, reschedule |
| **Tasks** | 1 | task_management |
| **Communication** | 2 | email, reminder |
| **Information** | 4 | search, briefing, status, user_data_query |
| **System** | 7 | greeting, thanks, confirm, cancel, help, app_info_query, adjust_preferences |
| **Planning** | 1 | adjust_plan |
| **Slots** | 2 | temporal_slot_fill, time_slot_fill |
| **Fallback** | 3 | chitchat, unknown, clarification_request |

### New Intents Added

1. **app_info_query** - Questions about PulsePlan features, pricing, integrations
2. **adjust_preferences** - Change user settings, notifications, working hours
3. **user_data_query** - Ask for personal data, statistics, task/event info
4. **clarification_request** - Request clarification when something is unclear

## Dataset Statistics

### Training Data (JSONL format)

| Split | Examples | Unique Labels | Avg per Intent |
|-------|----------|---------------|----------------|
| **train.jsonl** | 395 | 23 | 17.2 |
| **dev.jsonl** | 105 | 23 | 4.6 |
| **test.jsonl** | 105 | 23 | 4.6 |
| **TOTAL** | 605 | 23 | 26.3 |

### Contrastive Pairs (train_pairs.jsonl)

```
Total pairs:     2,316
Positive:        579 (25.0%)
Negative:        1,737 (75.0%)
Ratio:           1:3.00 (optimal)
```

**Negative Distribution:**
- Hard negatives (same domain): ~33%
- Medium negatives (adjacent domains): ~33%
- Easy negatives (different domains): ~33%

### Multi-Intent Examples (multi_intent_examples.jsonl)

```
Total examples:      74
Unique combinations: 21
Avg intents/query:   1.9
```

**Top Intent Combinations:**
1. briefing + search (8 examples)
2. adjust_preferences + scheduling (5 examples)
3. scheduling + task_management (4 examples)
4. email + search (4 examples)
5. reminder + reschedule (4 examples)

## Data Quality Features

### ✅ Implemented

- [x] **Placeholder normalization**: {person}, {date}, {time}, {task}, {event}, {course}
- [x] **Hard negative mining**: Same-domain negatives for better discrimination
- [x] **Domain-based stratification**: Adjacent domains as medium negatives
- [x] **Deduplication**: No duplicate pairs or examples
- [x] **Semantic descriptions**: Rich intent descriptions optimized for embeddings
- [x] **Keyword tagging**: Each intent has semantic keywords
- [x] **Hard negative hints**: Explicit hard_negatives field for confusion prevention
- [x] **1:3 positive:negative ratio**: Balanced for stable training
- [x] **Multi-intent support**: Compound query examples for complex interactions

### ⚠️ Known Limitations

- Some intents have few examples (12-15) - can expand with data augmentation
- 113 pairs have very short sentence1 (< 5 chars) - mostly slot-fills like "3pm", "yes"
- No semantic validation with model (sentence-transformers not installed during generation)

## Training Recommendations

### Hyperparameters

```yaml
model: sentence-transformers/all-MiniLM-L6-v2
batch_size: 32
epochs: 4-6
warmup_steps: 100
learning_rate: 2e-5
loss: CosineSimilarityLoss
```

### Expected Performance

| Metric | Target |
|--------|--------|
| Training accuracy (epoch 3) | >90% |
| Dev accuracy | >85% |
| Hard negative discrimination | >0.15 margin |
| Inference latency (CPU) | <50ms |

## Validation Results

Run `python ml/intent_classifier/validate_dataset.py` to verify:

```bash
✅ Intent specs: 23 intents, 8 domains
✅ Training data: 395 train, 105 dev, 105 test
✅ Contrastive pairs: 2,316 pairs (1:3.00 ratio)
✅ Multi-intent: 74 examples
```

## Next Steps

1. **Train the model**:
   ```bash
   python ml/intent_classifier/train_contrastive.py --config ml/intent_classifier/config.yaml
   ```

2. **Test inference**:
   ```bash
   python ml/intent_classifier/inference_contrastive.py
   ```

3. **Export to ONNX**:
   ```bash
   python ml/intent_classifier/export_to_onnx_contrastive.py --quantize
   ```

4. **Deploy** to `backend/app/agents/nlu/`

## Files Generated

- [intent_specs.json](./intent_specs.json) - 23 intent definitions with metadata
- [train_pairs.jsonl](./train_pairs.jsonl) - 2,316 contrastive pairs
- [multi_intent_examples.jsonl](./multi_intent_examples.jsonl) - 74 multi-intent examples
- [validate_dataset.py](./validate_dataset.py) - Quality validation script
- [DATASET_SUMMARY.md](./DATASET_SUMMARY.md) - This file

## References

- **Contrastive Learning Paper**: [SimCSE](https://arxiv.org/abs/2104.08821)
- **Sentence-Transformers**: https://www.sbert.net/
- **MiniLM Model**: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
