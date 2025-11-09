# Intent Classifier - Contrastive Learning

**Production-ready 23-intent classifier using MiniLM embeddings and similarity search.**

## 📁 Directory Structure

```
ml/intent_classifier/
├── README.md                 # This file
├── config.yaml              # Training configuration
├── __init__.py              # Package initialization
├── utils_logging.py         # Logging utilities
│
├── 📂 scripts/              # Executable scripts
│   ├── train_contrastive.py          # Main training script
│   ├── inference_contrastive.py      # Inference & testing
│   ├── export_to_onnx_contrastive.py # ONNX export with quantization
│   └── validate_dataset.py           # Dataset validation
│
├── 📂 data/                 # Training data
│   ├── intent_specs.json             # 23 intent definitions
│   ├── train_pairs.jsonl             # 2,481 contrastive pairs
│   └── multi_intent_examples.jsonl   # 74 multi-intent examples
│
└── 📂 docs/                 # Documentation
    ├── DATASET_SUMMARY.md            # Dataset statistics & overview
    ├── INTENT_BOUNDARIES.md          # Decision rules for confusing intents
    └── CONTRASTIVE_MIGRATION_GUIDE.md # Migration guide
```

## 📦 Installation

**First time setup:**

```bash
cd ml/intent_classifier

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import torch, sentence_transformers; print('✅ Ready to train!')"
```

**Requirements:**
- Python 3.8+
- PyTorch 2.0+
- sentence-transformers 2.2+
- 500MB disk space for model outputs

**📋 See [PRE_TRAINING_CHECKLIST.md](PRE_TRAINING_CHECKLIST.md) for complete setup guide.**

---

## 🚀 Quick Start

### 1. Validate Dataset

```bash
python scripts/validate_dataset.py
```

**Expected output:**
```
✅ Intent specs: 23 intents, 8 domains
✅ Training data: 440 train, 105 dev, 105 test
✅ Contrastive pairs: 2,481 pairs (1:2.98 ratio)
✅ Multi-intent: 74 examples
```

### 2. Train Model

```bash
python scripts/train_contrastive.py --config config.yaml
```

**Training time:**
- GPU (3060 Ti): ~10-15 minutes
- CPU: ~45-60 minutes

**Output:**
- Model: `outputs/contrastive_model/`
- Embeddings: `data/intent_specs_embedded.json`
- Logs: `training_contrastive.log`

### 3. Test Inference

```bash
# Single query
python scripts/inference_contrastive.py \
  --query "move my 3pm meeting to tomorrow"

# Batch test
python scripts/inference_contrastive.py
```

### 4. Export to ONNX

```bash
python scripts/export_to_onnx_contrastive.py \
  --model outputs/contrastive_model \
  --output-dir onnx \
  --quantize
```

**Output:**
- `onnx/model.onnx` (~90MB)
- `onnx/model_quantized.onnx` (~23MB)
- `onnx/inference_config.json`

## 📊 Dataset Overview

### 23 Intents Across 8 Domains

| Domain | Intents |
|--------|---------|
| **Scheduling** (3) | scheduling, calendar_event, reschedule |
| **Tasks** (1) | task_management |
| **Communication** (2) | email, reminder |
| **Information** (4) | search, briefing, status, user_data_query |
| **System** (7) | greeting, thanks, confirm, cancel, help, app_info_query, adjust_preferences |
| **Planning** (1) | adjust_plan |
| **Slots** (2) | temporal_slot_fill, time_slot_fill |
| **Fallback** (3) | chitchat, unknown, clarification_request |

### Data Statistics

```
Training Examples: 440 train, 105 dev, 105 test (650 total)
Contrastive Pairs:  2,481 pairs (624 positive, 1,857 negative)
Ratio:              1:2.98 (optimal for stability)
Multi-Intent:       74 compound query examples
```

### Key Features

✅ **Hard negative mining** - Explicit negatives for confusing intent pairs
✅ **Borderline examples** - 45 examples for tricky discriminations
✅ **Placeholder normalization** - {person}, {date}, {time}, etc.
✅ **Semantic descriptions** - Rich intent definitions optimized for embeddings
✅ **Multi-intent support** - Native handling of compound queries

## 🎯 Confusing Intent Pairs

The model has been optimized for these tricky discriminations:

1. **calendar_event vs scheduling**
   - `calendar_event`: Structured events with details
   - `scheduling`: Time-blocking without formal events

2. **reschedule vs adjust_plan**
   - `reschedule`: Move ONE item
   - `adjust_plan`: Restructure WHOLE schedule

3. **briefing vs status vs search vs user_data_query**
   - `briefing`: Summary/overview
   - `status`: Metrics/progress
   - `search`: Filtered queries
   - `user_data_query`: General data requests

See [docs/INTENT_BOUNDARIES.md](docs/INTENT_BOUNDARIES.md) for decision rules.

## 📈 Expected Performance

| Metric | Target |
|--------|--------|
| Training accuracy (epoch 3) | >90% |
| Dev accuracy | >85% |
| Hard negative margin | >0.15 |
| Inference latency (CPU) | <50ms |

## 🔧 Configuration

Edit `config.yaml` to adjust:

```yaml
model:
  base_model_name: "sentence-transformers/all-MiniLM-L6-v2"

training:
  device_preference_train: "cuda"  # or "cpu"
  batch_size_train: 32
  num_epochs: 4-6
  learning_rate: 2.0e-5

data:
  train_file: "data/intents/train.jsonl"
  dev_file: "data/intents/dev.jsonl"
  test_file: "data/intents/test.jsonl"
```

## 📚 Documentation

- **[DATASET_SUMMARY.md](docs/DATASET_SUMMARY.md)** - Complete dataset overview
- **[INTENT_BOUNDARIES.md](docs/INTENT_BOUNDARIES.md)** - Decision rules for confusing intents
- **[CONTRASTIVE_MIGRATION_GUIDE.md](docs/CONTRASTIVE_MIGRATION_GUIDE.md)** - Migration from classification approach

## 🗂️ Data Files

### intent_specs.json
23 intent definitions with:
- Natural language descriptions
- Domain classifications
- Keywords
- Hard negatives
- Example utterances

### train_pairs.jsonl
Contrastive training pairs in format:
```json
{"sentence1": "move my meeting to tomorrow", "sentence2": "Move, postpone, delay...", "label": 1}
{"sentence1": "move my meeting to tomorrow", "sentence2": "Create new task...", "label": 0}
```

### multi_intent_examples.jsonl
Compound queries with decomposition:
```json
{
  "text": "check my calendar and email professor",
  "intents": ["user_data_query", "email"],
  "decomposed": [
    {"clause": "check my calendar", "intent": "user_data_query"},
    {"clause": "email professor", "intent": "email"}
  ]
}
```

## 🔄 Training Source Data

The contrastive pairs are **automatically generated** from:
- `../../data/intents/train.jsonl` (440 examples)
- `../../data/intents/dev.jsonl` (105 examples)
- `../../data/intents/test.jsonl` (105 examples)

These files use format: `{"text": "...", "label": "..."}`

## 📝 Notes

- All scripts use the **contrastive learning** approach (CosineSimilarityLoss)
- Training data source: `../../data/intents/{train,dev,test}.jsonl`
- Old classification approach has been removed (available in git history if needed)

## 🚢 Deployment

After training and export:

1. Copy ONNX model to backend:
   ```bash
   cp -r onnx/ ../../backend/app/agents/nlu/models/
   ```

2. Update NLU service to use `inference_contrastive.py`:
   ```python
   from ml.intent_classifier.scripts.inference_contrastive import ContrastiveIntentClassifier

   classifier = ContrastiveIntentClassifier(
       model_path="models/onnx/model_quantized.onnx",
       intent_specs_path="models/intent_specs_embedded.json"
   )
   ```

## 🐛 Troubleshooting

**Issue: Low similarity scores (<0.5)**
- Check that `intent_specs_embedded.json` was generated during training
- Verify model path points to correct directory

**Issue: Confusing similar intents**
- Review [INTENT_BOUNDARIES.md](docs/INTENT_BOUNDARIES.md)
- Add more borderline examples to `../../data/intents/train.jsonl`
- Retrain with new examples

**Issue: Multi-intent not working**
- Lower threshold in `predict_multi_intent()` (default 0.6 → 0.5)
- Check that query actually contains multiple intents

## 📝 License

Part of the PulsePlan AI agent system.

## 🔗 References

- **Sentence-Transformers**: https://www.sbert.net/
- **MiniLM**: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- **Contrastive Learning**: https://arxiv.org/abs/2104.08821
