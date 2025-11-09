# Intent Classifier Training & Deployment Guide

Complete guide for training the ONNX intent classification model and deploying it to the PulsePlan agent system.

---

## 📋 Overview

This guide covers the complete pipeline:

1. **Prepare Training Data** - Create/update intent examples
2. **Train Model** - Fine-tune MiniLM on your data
3. **Export to ONNX** - Convert for optimized inference
4. **Quantize (Optional)** - Reduce model size for CPU
5. **Deploy to Backend** - Slot into agent workflow
6. **Validate** - Test the deployed model

---

## 📂 File Structure

```
PulsePlan/
├── data/intents/                      # Training data
│   ├── train.jsonl                    # Training set (~10k examples)
│   ├── dev.jsonl                      # Validation set (~3k examples)
│   └── test.jsonl                     # Test set (~2k examples)
│
├── ml/intent_classifier/              # Training pipeline
│   ├── config.yaml                    # Training configuration
│   ├── train.py                       # Training script
│   ├── export_to_onnx.py              # ONNX export script
│   ├── quantize_onnx.py               # Model quantization
│   ├── evaluate.py                    # Evaluation script
│   └── dataset.py                     # Data loading utilities
│
└── backend/app/agents/nlu/            # Deployment location
    ├── models/
    │   ├── intent_classifier.onnx     # Deployed model
    │   └── labels.json                # Intent labels
    └── classifier_onnx.py             # Inference engine
```

---

## 🚀 Step 1: Prepare Training Data

### Data Format

Training data is in JSONL format (one JSON object per line):

```jsonl
{"text": "create a task to finish my homework", "label": "task_management"}
{"text": "schedule a meeting tomorrow at 3pm", "label": "calendar_event"}
{"text": "what's on my agenda today", "label": "briefing"}
```

### Check Existing Data

```bash
cd /Users/admin/PulsePlan

# View data statistics
wc -l data/intents/*.jsonl
# train.jsonl:    ~200 lines
# dev.jsonl:      ~60 lines
# test.jsonl:     ~40 lines

# View sample examples
head -5 data/intents/train.jsonl
```

### Add New Examples

To add more training examples:

```bash
# Edit training file
nano data/intents/train.jsonl

# Add lines in format:
# {"text": "your example query", "label": "intent_name"}
```

**Intent Labels (19 total):**
- `task_management` - Create/manage tasks
- `scheduling` - Schedule time blocks
- `calendar_event` - Create calendar events
- `reschedule` - Reschedule events
- `reminder` - Set reminders
- `email` - Email operations
- `search` - Search tasks/events
- `briefing` - Daily briefings
- `status` - Status queries
- `greeting` - Greetings
- `thanks` - Gratitude
- `confirm` - Confirmations
- `cancel` - Cancellations
- `help` - Help requests
- `adjust_plan` - Adjust plans
- `temporal_slot_fill` - Fill time slots
- `time_slot_fill` - Fill specific times
- `unknown` - Unknown intents
- `chitchat` - Casual conversation

### Best Practices for Training Data

✅ **DO:**
- Include 20+ examples per intent
- Use natural, conversational language
- Vary phrasing and structure
- Include typos and abbreviations (realistic user input)
- Balance classes (similar number of examples per intent)

❌ **DON'T:**
- Use overly formal language
- Repeat identical examples
- Include PII or sensitive data
- Mix multiple intents in one example

---

## 🧠 Step 2: Train the Model

### Prerequisites

Install required dependencies:

```bash
# Install PyTorch (GPU version for faster training)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install training dependencies
pip install transformers==4.36.0
pip install sentence-transformers==2.2.2
pip install scikit-learn==1.3.2
pip install pyyaml==6.0.1
```

### Configure Training

Edit `ml/intent_classifier/config.yaml`:

```yaml
model:
  base_model_name: "sentence-transformers/all-MiniLM-L6-v2"
  num_labels: 19  # Match number of intents

training:
  device_preference_train: "cuda"  # Use GPU if available
  batch_size_train: 32
  num_epochs: 10
  learning_rate: 2.0e-5

  # Early stopping
  early_stopping_patience: 3
  early_stopping_metric: "eval_f1"

data:
  train_file: "data/intents/train.jsonl"
  dev_file: "data/intents/dev.jsonl"
  test_file: "data/intents/test.jsonl"
```

### Run Training

```bash
cd /Users/admin/PulsePlan/ml/intent_classifier

# Train the model
python train.py

# Training will:
# 1. Load data from data/intents/
# 2. Fine-tune MiniLM model
# 3. Use early stopping based on validation F1
# 4. Save checkpoints to ml/intent_classifier/checkpoints/
# 5. Save best model to ml/intent_classifier/outputs/
```

**Expected output:**

```
Loading training data from data/intents/train.jsonl...
Loaded 200 examples
Creating datasets...
Training on cuda (NVIDIA GeForce RTX 3060 Ti)...

Epoch 1/10: 100%|██████████| 7/7 [00:02<00:00,  3.15it/s]
{'eval_loss': 0.45, 'eval_accuracy': 0.92, 'eval_f1': 0.91}

Epoch 2/10: 100%|██████████| 7/7 [00:02<00:00,  3.18it/s]
{'eval_loss': 0.32, 'eval_accuracy': 0.95, 'eval_f1': 0.94}

...

Training complete!
Best model saved to: ml/intent_classifier/outputs/checkpoint-600/
Test accuracy: 0.95
```

**Training time:**
- **GPU (3060 Ti)**: ~5-10 minutes
- **CPU**: ~30-60 minutes

### Evaluate Model

```bash
# Run evaluation on test set
python evaluate.py --checkpoint ml/intent_classifier/outputs/checkpoint-600/

# Output: classification report with per-intent metrics
```

---

## 📦 Step 3: Export to ONNX

ONNX format provides:
- **Fast inference** (~10x faster than PyTorch)
- **Small size** (~90MB vs ~500MB)
- **CPU optimized** (no GPU needed in production)

### Export Model

```bash
cd /Users/admin/PulsePlan/ml/intent_classifier

# Export to ONNX
python export_to_onnx.py \
  --checkpoint outputs/checkpoint-600/ \
  --output model.onnx \
  --opset-version 14

# This creates:
# - ml/intent_classifier/model.onnx (90MB)
# - ml/intent_classifier/labels.json (intent mappings)
```

**Expected output:**

```
Loading model from outputs/checkpoint-600/...
Exporting to ONNX format...
ONNX model saved: ml/intent_classifier/model.onnx
Labels saved: ml/intent_classifier/labels.json

Testing ONNX inference...
Query: "create a task to study"
Predicted: task_management (confidence: 0.95)
✓ ONNX export successful!
```

---

## 🗜️ Step 4: Quantize Model (Optional)

Quantization reduces model size by ~4x with minimal accuracy loss:

```bash
cd /Users/admin/PulsePlan/ml/intent_classifier

# Quantize ONNX model
python quantize_onnx.py \
  --input model.onnx \
  --output model_quantized.onnx \
  --mode dynamic

# This creates:
# - ml/intent_classifier/model_quantized.onnx (~23MB)
```

**Size comparison:**
- Original ONNX: ~90MB
- Quantized ONNX: ~23MB
- Accuracy drop: <1%

**When to quantize:**
- ✅ Use quantized model for production (faster CPU inference)
- ❌ Skip if deploying on GPU

---

## 🚀 Step 5: Deploy to Backend

### Copy Model Files

```bash
# Navigate to backend
cd /Users/admin/PulsePlan/backend/app/agents/nlu/

# Create models directory if it doesn't exist
mkdir -p models

# Copy ONNX model and labels
cp /Users/admin/PulsePlan/ml/intent_classifier/model_quantized.onnx models/intent_classifier.onnx
cp /Users/admin/PulsePlan/ml/intent_classifier/labels.json models/labels.json

# Verify files copied
ls -lh models/
# Should show:
# intent_classifier.onnx  (~23MB)
# labels.json             (~1KB)
```

### Update Configuration

Edit `backend/app/config/core/settings.py` to ensure model path is correct:

```python
class Settings(BaseSettings):
    # Intent classification model
    INTENT_MODEL_PATH: str = "backend/app/agents/nlu/models/intent_classifier.onnx"
    INTENT_LABELS_PATH: str = "backend/app/agents/nlu/models/labels.json"
    HF_TOKENIZER: str = "sentence-transformers/all-MiniLM-L6-v2"
```

### Verify Deployment

The ONNX classifier is already integrated! Check `backend/app/agents/nlu/classifier_onnx.py`:

```python
from app.agents.nlu.classifier_onnx import create_classifier
from app.config.core.settings import get_settings

settings = get_settings()
classifier = create_classifier(
    model_path=settings.INTENT_MODEL_PATH,
    labels=settings.INTENT_LABELS,
    hf_tokenizer=settings.HF_TOKENIZER
)

# Test inference
intent, confidence = classifier.predict("create a task to study")
print(f"Intent: {intent}, Confidence: {confidence:.2f}")
# Output: Intent: task_management, Confidence: 0.95
```

---

## ✅ Step 6: Validate Deployment

### Test via Python

```bash
cd /Users/admin/PulsePlan/backend

# Test the classifier
python -c "
from app.agents.nlu.classifier_onnx import create_classifier
from app.config.core.settings import get_settings

settings = get_settings()
classifier = create_classifier(
    model_path=settings.INTENT_MODEL_PATH,
    labels=settings.INTENT_LABELS,
    hf_tokenizer=settings.HF_TOKENIZER
)

# Test queries
test_queries = [
    'create a task to finish homework',
    'schedule a meeting tomorrow at 3pm',
    'what is on my agenda today',
    'search for urgent tasks',
    'draft an email to my professor'
]

for query in test_queries:
    intent, conf = classifier.predict(query)
    print(f'{query:45} → {intent:20} ({conf:.2f})')
"
```

**Expected output:**

```
create a task to finish homework              → task_management     (0.96)
schedule a meeting tomorrow at 3pm            → calendar_event      (0.94)
what is on my agenda today                    → briefing            (0.92)
search for urgent tasks                       → search              (0.91)
draft an email to my professor                → email               (0.89)
```

### Test via API

```bash
# Start backend server
cd /Users/admin/PulsePlan/backend
python main.py

# In another terminal, test agent endpoint
curl -X POST http://localhost:8000/api/v1/agents/unified \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "create a task to study for finals",
    "user_id": "test-user"
  }'

# Response should show:
# "intent": "task_management"
# "confidence": 0.95
```

---

## 🔄 Retraining Workflow

When you need to retrain (e.g., add new intents or improve accuracy):

### 1. Collect New Data

```bash
# Add examples to training file
nano data/intents/train.jsonl

# Add new examples or intents
{"text": "new example query", "label": "new_intent"}
```

### 2. Update Configuration

If adding new intents:

```yaml
# ml/intent_classifier/config.yaml
model:
  num_labels: 20  # Increment if adding new intent

labels:
  - "existing_intent_1"
  - "existing_intent_2"
  - "new_intent"  # Add new intent
```

### 3. Retrain

```bash
cd /Users/admin/PulsePlan/ml/intent_classifier

# Full retraining pipeline
python train.py                    # Train model
python export_to_onnx.py           # Export to ONNX
python quantize_onnx.py            # Quantize

# Deploy
cp model_quantized.onnx ../../backend/app/agents/nlu/models/intent_classifier.onnx
cp labels.json ../../backend/app/agents/nlu/models/labels.json

# Restart backend to load new model
```

---

## 📊 Performance Benchmarks

**Model Size:**
- PyTorch checkpoint: ~500MB
- ONNX model: ~90MB
- Quantized ONNX: ~23MB

**Inference Speed (CPU):**
- PyTorch: ~100ms per query
- ONNX: ~10ms per query
- Quantized ONNX: ~8ms per query

**Accuracy:**
- Training: ~96%
- Validation: ~95%
- Test: ~95%
- Quantized: ~94%

---

## 🐛 Troubleshooting

### Issue: "ONNX model not found"

```bash
# Check if model exists
ls backend/app/agents/nlu/models/intent_classifier.onnx

# If missing, copy from ml directory
cp ml/intent_classifier/model_quantized.onnx backend/app/agents/nlu/models/intent_classifier.onnx
```

### Issue: "Low confidence predictions"

**Solution**: Add more training examples for that intent

```bash
# Check per-intent performance
cd ml/intent_classifier
python evaluate.py --checkpoint outputs/checkpoint-600/

# Add 10-20 more examples for low-performing intents
```

### Issue: "CUDA out of memory"

**Solution**: Reduce batch size

```yaml
# ml/intent_classifier/config.yaml
training:
  batch_size_train: 16  # Reduce from 32
```

### Issue: "Model predicts 'unknown' too often"

**Solution**: Improve training data quality

1. Add more diverse examples for target intents
2. Remove ambiguous examples
3. Balance class distribution

---

## 📚 Additional Resources

- **Transformers docs**: https://huggingface.co/docs/transformers
- **ONNX Runtime**: https://onnxruntime.ai/
- **Sentence Transformers**: https://www.sbert.net/

---

## 🎯 Quick Reference

```bash
# Full training + deployment pipeline (copy-paste)
cd /Users/admin/PulsePlan/ml/intent_classifier

# 1. Train
python train.py

# 2. Export to ONNX
python export_to_onnx.py --checkpoint outputs/checkpoint-600/ --output model.onnx

# 3. Quantize
python quantize_onnx.py --input model.onnx --output model_quantized.onnx

# 4. Deploy
cp model_quantized.onnx ../../backend/app/agents/nlu/models/intent_classifier.onnx
cp labels.json ../../backend/app/agents/nlu/models/labels.json

# 5. Test
cd ../../backend
python main.py  # Restart backend with new model
```

---

## ✅ Success Checklist

- [ ] Training data has 20+ examples per intent
- [ ] Model trains successfully (F1 > 0.90)
- [ ] ONNX export completes without errors
- [ ] Model files copied to `backend/app/agents/nlu/models/`
- [ ] Backend starts without model loading errors
- [ ] Test queries return correct intents with >0.7 confidence
- [ ] Agent API endpoint works end-to-end

**Your intent classification model is now trained and deployed!** 🎉
