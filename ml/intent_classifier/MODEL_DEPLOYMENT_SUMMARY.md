# Intent Classifier - Model Deployment Summary

## ✅ Completed: Iteration 1 Model Deployed

**Date**: October 26, 2025
**Model Version**: v1.0 (Contrastive Learning - 22 intents)
**Status**: DEPLOYED TO BACKEND

---

## Model Performance

### Test Set Results
- **Overall Accuracy**: 88.0% (88/100)
- **Average Confidence**: 0.922
- **Confidence Std Dev**: 0.096

### Perfect Performers (100% accuracy)
- adjust_plan, app_info_query, calendar_event, cancel, email, greeting
- reschedule, scheduling, search, temporal_slot_fill, thanks, time_slot_fill, user_data_query

### Issues Identified (will fix in next iteration)
1. **clarification_request**: 33.3% accuracy - Too similar to `unknown`
2. **status**: 60% accuracy - Still overlaps with `user_data_query`
3. **unknown**: 60% accuracy - Confused with `help` and `clarification_request`
4. **chitchat**: 75% accuracy - "Weekend plans?" predicted as `scheduling`

---

## Training Data

### Current Dataset (22 intents)
- **Training examples**: 404
- **Dev examples**: 100
- **Test examples**: 100
- **Training pairs**: 23,944 (5,986 positive, 17,958 negative, 1:3 ratio)

### Changes from Initial Training
- ❌ **Removed** `briefing` intent (was causing confusion)
- ⚙️ **Refined** `status` intent (removed vague examples like "Give me an update")
- Still has issues - needs further refinement

---

## Deployment Details

### Model Location
```
backend/app/agents/nlu/contrastive_classifier/
├── model/                          # Sentence-transformers model (87.6 MB)
├── intent_specs_embedded.json      # 22 intents with pre-computed embeddings
├── config.json                      # Inference configuration
└── README.md                        # Usage instructions
```

### Integration Points
1. **Backend Entry**: `backend/main.py`
   - Initializes `ContrastiveIntentClassifier` on startup
   - Stores in `app.state.nlu_classifier`
   - Fallback to ONNX classifier if contrastive fails

2. **Classifier**: `backend/app/agents/nlu/classifier_contrastive.py`
   - Uses sentence-transformers for encoding
   - Cosine similarity with pre-computed intent embeddings
   - Confidence threshold: 0.5

3. **NLU Service**: `backend/app/agents/services/nlu_service.py`
   - Receives classifier from app state
   - Rules → Classifier → Extractors pipeline

### Dependencies Added
- `sentence-transformers>=5.1.0`
- `numpy<2.0.0`

---

## Next Steps (Iteration 2)

### Intent Refinements
1. **Remove `status` intent entirely**
   - Move metrics-focused queries to `user_data_query`
   - Examples like "how many tasks completed?" → `user_data_query`

2. **Merge `clarification_request` into `unknown`**
   - Too similar conceptually
   - Simplifies intent space

3. **Fix `chitchat` examples**
   - Remove: "Weekend plans?" (too ambiguous)
   - Add: "What are my weekend plans?" → `user_data_query`
   - Keep only clear small talk: "How's the weather?", "Did you watch the game?"

### Retraining Plan
```bash
# 1. Update intent specs
# 2. Remove status examples from train/dev/test
# 3. Merge clarification_request examples into unknown
# 4. Fix chitchat examples
# 5. Regenerate training pairs
# 6. Retrain model
# 7. Run batch inference to validate
# 8. Deploy v1.1
```

### Testing TODO
- [ ] Start backend server and verify classifier loads
- [ ] Test NLU service with sample queries
- [ ] Verify prompt logging is working
- [ ] Test full orchestrator workflow
- [ ] Monitor production logs for low-confidence predictions

---

## Technical Notes

### Why Contrastive Learning over Classification?
- **Better semantic understanding**: Learns intent relationships
- **Lower data requirements**: 400 examples vs 1000s needed for classification
- **Flexible**: Easy to add new intents without full retrain
- **Fast inference**: Pre-computed embeddings + cosine similarity

### Model Architecture
- **Base**: sentence-transformers/all-MiniLM-L6-v2
- **Training**: Contrastive pairs with CosineSimilarityLoss
- **Positive pairs**: Example↔description, example↔keyword, example↔example
- **Negative pairs**: Hard negatives from same domain (70%) + random (30%)
- **Ratio**: 1:3 positive:negative

### Performance Characteristics
- **Model size**: 87.6 MB
- **Inference speed**: ~10-20ms on CPU
- **No GPU required**: Runs efficiently on CPU
- **Memory**: ~200MB loaded

---

## Production Monitoring

### Prompt Logging (Already Set Up)
- **Database**: `nlu_prompt_logs` table
- **Admin Dashboard**: `/admin/nlu` (React page with 5 tabs)
- **Endpoints**:
  - GET `/admin/nlu/stats` - Overview metrics
  - GET `/admin/nlu/low-confidence` - Low confidence predictions
  - GET `/admin/nlu/failed-workflows` - Failed workflow executions
  - POST `/admin/nlu/correct-intent` - Manual corrections
  - POST `/admin/nlu/export-training-data` - Export for retraining

### Continuous Improvement Loop
1. **Capture**: All prompts logged automatically
2. **Monitor**: Admin dashboard shows low-confidence and failures
3. **Correct**: Manual corrections via dashboard
4. **Export**: Export corrected data for retraining
5. **Retrain**: Incorporate production data
6. **Deploy**: Updated model with better accuracy

---

## Files Modified

### Backend
- `backend/main.py` - Classifier initialization
- `backend/app/agents/nlu/classifier_contrastive.py` - NEW
- `backend/app/agents/nlu/__init__.py` - Added contrastive exports
- `backend/requirements.txt` - Added sentence-transformers

### ML
- `ml/intent_classifier/scripts/export_model_simple.py` - NEW
- `ml/intent_classifier/production_model/` - NEW (deployed to backend)
- `ml/intent_classifier/data/intent_specs.json` - Refined status
- `data/intents/train.jsonl` - Removed vague examples
- `ml/intent_classifier/data/train_pairs.jsonl` - Regenerated
- `ml/intent_classifier/scripts/batch_inference.py` - NEW
- `ml/intent_classifier/scripts/generate_training_pairs.py` - NEW

---

## Quick Start Guide

### Start Backend with New Model
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Test NLU Service
```bash
# Via Python
from app.agents.services.nlu_service import NLUService

nlu = NLUService(app.state.nlu_classifier)
result = await nlu.process_message("what's on my calendar today?")
print(f"Intent: {result.intent} (confidence: {result.confidence})")
```

### Monitor via Admin Dashboard
```
http://localhost:8000/admin/nlu
```

---

## Success Criteria for V1.1

- [ ] Overall accuracy >92% (currently 88%)
- [ ] All intents >80% accuracy (currently 3 intents <80%)
- [ ] No intent overlaps in confusion matrix
- [ ] Average confidence >0.93 (currently 0.922)
- [ ] Production validation with 100+ real queries

---

**Model Status**: ✅ READY FOR TESTING
**Next Action**: Test orchestrator workflows and collect production feedback
