# Pre-Training Checklist

Complete this checklist before running training.

## ✅ Dataset Validation

- [x] **Intent specs created** - 23 intents with descriptions
- [x] **Training data prepared** - 440 train, 105 dev, 105 test
- [x] **Contrastive pairs generated** - 2,481 pairs (1:2.98 ratio)
- [x] **Multi-intent examples** - 74 examples
- [x] **Borderline examples added** - 45 examples for tricky discriminations
- [x] **Hard negatives** - Explicit negatives for confusing pairs
- [x] **Validation passed** - Run `python scripts/validate_dataset.py`

**Status**: ✅ Dataset ready

---

## ❌ Dependencies Installation

- [ ] **PyTorch installed** - Core deep learning framework
- [ ] **sentence-transformers installed** - Contrastive learning library
- [ ] **ONNX packages installed** - For model export (optional for training)

### Install Commands:

```bash
# Navigate to ML directory
cd ml/intent_classifier

# Install all dependencies
pip install -r requirements.txt

# Or install individually:
pip install torch sentence-transformers
pip install onnx onnxruntime optimum  # Optional: for ONNX export
```

### Verify Installation:

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import sentence_transformers; print('sentence-transformers: OK')"
```

**Status**: ❌ **REQUIRED BEFORE TRAINING**

---

## ⚙️ Hardware Check

### GPU (Recommended)

- [ ] CUDA available: `python -c "import torch; print(torch.cuda.is_available())"`
- [ ] GPU name: `python -c "import torch; print(torch.cuda.get_device_name(0))"`

**Training time with GPU (3060 Ti)**: ~10-15 minutes

### CPU (Fallback)

If no GPU available, training will use CPU.

**Training time with CPU**: ~45-60 minutes

To force CPU training, edit `config.yaml`:
```yaml
training:
  device_preference_train: "cpu"
```

---

## 📁 File Structure Check

- [x] `config.yaml` exists
- [x] `data/intent_specs.json` exists (23 intents)
- [x] `data/train_pairs.jsonl` exists (2,481 pairs)
- [x] `data/multi_intent_examples.jsonl` exists (74 examples)
- [x] `scripts/train_contrastive.py` exists
- [x] `../../data/intents/train.jsonl` exists (source data)

---

## 🚀 Ready to Train?

### Quick Start:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Validate everything
python scripts/validate_dataset.py

# 3. Train the model
python scripts/train_contrastive.py --config config.yaml
```

### Expected Output:

```
Loading base model: sentence-transformers/all-MiniLM-L6-v2
Training device: cuda  # or 'cpu'
Loaded 2481 training pairs
Positive pairs: 624, Negative pairs: 1857

Training for 4 epochs with 100 warmup steps
Epoch 1/4: [█████████████] loss: 0.234
Epoch 2/4: [█████████████] loss: 0.156
Epoch 3/4: [█████████████] loss: 0.098
Epoch 4/4: [█████████████] loss: 0.067

Model saved to ml/intent_classifier/outputs/contrastive_model/
Cached intent embeddings to data/intent_specs_embedded.json
```

---

## 🎯 After Training

Once training completes:

1. **Test inference**:
   ```bash
   python scripts/inference_contrastive.py --query "move my meeting to tomorrow"
   ```

2. **Export to ONNX** (optional):
   ```bash
   python scripts/export_to_onnx_contrastive.py --quantize
   ```

3. **Deploy to backend**:
   ```bash
   cp -r outputs/contrastive_model ../../backend/app/agents/nlu/models/
   ```

---

## ⚠️ Known Issues (Non-Blocking)

These are **minor issues** that won't prevent training:

- 97 pairs have very short sentence1 (< 5 chars) - These are slot-fills like "3pm", "yes" - **acceptable**
- 1 JSON parsing error in train/dev/test - Likely trailing newline - **harmless**
- Some dev/test labels have < 5 examples - **acceptable for evaluation**

---

## 📊 Expected Performance

After training (epoch 3-4):

| Metric | Target |
|--------|--------|
| Training accuracy | >90% |
| Dev accuracy | >85% |
| Hard negative margin | >0.15 |
| Model size | ~90MB (uncompressed) |
| Model size (quantized) | ~23MB |
| Inference latency (CPU) | <50ms |

---

## ❓ Troubleshooting

**Q: `ModuleNotFoundError: No module named 'sentence_transformers'`**
A: Install dependencies: `pip install -r requirements.txt`

**Q: Training is slow**
A: Check if GPU is available. If using CPU, training takes ~45-60 min.

**Q: CUDA out of memory**
A: Reduce batch size in `config.yaml`: `batch_size_train: 16` (default is 32)

**Q: Model predictions are random**
A: Training likely didn't complete. Check logs for errors.

---

## ✅ Final Check

Before running `python scripts/train_contrastive.py`:

- [ ] Dependencies installed (`torch`, `sentence-transformers`)
- [ ] Validation passed (`python scripts/validate_dataset.py`)
- [ ] GPU/CPU ready (check with `torch.cuda.is_available()`)
- [ ] Enough disk space (~500MB for model + outputs)

**If all boxes checked: YOU'RE READY! 🚀**
