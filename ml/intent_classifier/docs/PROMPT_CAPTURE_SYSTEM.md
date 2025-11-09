# Prompt Capture System

Continuous learning system for capturing and refining intent classification using real production data.

## Overview

The prompt capture system automatically logs every user prompt that goes through the NLU pipeline, along with the model's prediction and outcome. This creates a feedback loop for continuous model improvement.

```
User Prompt → NLU Service → Log Prediction → Execute Workflow → Log Outcome
                                ↓
                     Production Prompt Database
                                ↓
                      Weekly Export & Review
                                ↓
                      Retrain Model with Real Data
```

## Architecture

### Database Schema

**Table: `nlu_prompt_logs`**

```sql
CREATE TABLE nlu_prompt_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),

    -- Prediction
    prompt TEXT NOT NULL,
    predicted_intent TEXT NOT NULL,
    confidence REAL CHECK (confidence >= 0 AND confidence <= 1),
    secondary_intents JSONB DEFAULT '[]',

    -- Human corrections
    corrected_intent TEXT,
    correction_notes TEXT,

    -- Workflow outcome
    was_successful BOOLEAN,
    workflow_type TEXT,
    execution_error TEXT,

    -- Context
    conversation_id UUID,
    message_index INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Components

1. **NLU Service** (`backend/app/agents/services/nlu_service.py`)
   - Logs every prompt automatically
   - Returns `log_id` in `NLUResult` for outcome tracking

2. **NLU Repository** (`backend/app/database/nlu_repository.py`)
   - `log_prompt()` - Log initial prediction
   - `update_prompt_log_outcome()` - Log workflow success/failure
   - `add_prompt_correction()` - Add manual corrections
   - `get_low_confidence_prompts()` - Get prompts for review
   - `get_prompts_for_retraining()` - Export training data

3. **Export Script** (`ml/intent_classifier/scripts/export_production_data.py`)
   - Export production prompts for retraining
   - Export low-confidence prompts for manual review

## Usage

### 1. Automatic Logging (Already Integrated)

The NLU service automatically logs every prediction:

```python
from app.agents.services.nlu_service import create_nlu_service

nlu_service = create_nlu_service(classifier)

result = await nlu_service.process_message(
    message="schedule time to work on assignment",
    user_id=user_id,
    conversation_id=conversation_id,
    message_index=0
)

# Result contains log_id for outcome tracking
print(f"Logged as: {result.log_id}")
```

### 2. Update Workflow Outcome

After executing a workflow, update the log with the outcome:

```python
# After workflow execution
await nlu_service.update_workflow_outcome(
    log_id=result.log_id,
    was_successful=True,
    workflow_type="scheduling",
    execution_error=None  # or error message if failed
)
```

### 3. Export for Retraining

Export production prompts (corrected + high-confidence) for model retraining:

```bash
cd ml/intent_classifier

# Export all production data
python scripts/export_production_data.py --mode retraining

# Export only last 30 days
python scripts/export_production_data.py --mode retraining --days 30

# Custom output path
python scripts/export_production_data.py --mode retraining --output /path/to/output.jsonl
```

**Output format:**

```jsonl
{"text": "schedule time for math homework", "label": "scheduling", "confidence": 0.92, "source": "production", "corrected": false}
{"text": "add event to calendar", "label": "calendar_event", "confidence": 0.67, "source": "production", "corrected": true}
```

### 4. Export for Manual Review

Export low-confidence predictions for human review:

```bash
# Export prompts with confidence < 0.7
python scripts/export_production_data.py --mode review

# Custom threshold
python scripts/export_production_data.py --mode review --confidence-threshold 0.6
```

**Output format (for review):**

```json
{
  "id": "uuid",
  "prompt": "can you help me with my schedule",
  "predicted_intent": "scheduling",
  "confidence": 0.65,
  "created_at": "2025-10-25T...",
  "corrected_intent": "",  // Fill this in
  "notes": ""              // Add explanation
}
```

### 5. Add Manual Corrections

After reviewing prompts, add corrections back to database:

```python
from app.database.nlu_repository import create_nlu_repository

repo = create_nlu_repository()

await repo.add_prompt_correction(
    log_id="uuid-from-review-file",
    corrected_intent="calendar_event",
    correction_notes="User wanted to create calendar event, not schedule work time"
)
```

## Continuous Improvement Workflow

### Weekly Cycle

**Week 1: Production**
- ✅ System logs all prompts automatically
- ✅ Workflow outcomes tracked
- 📊 Data accumulates in database

**Week 2: Review**
```bash
# Export low-confidence prompts
python scripts/export_production_data.py --mode review --days 7

# Review file manually, add corrections
# Import corrections back to database (using API or script)
```

**Week 3: Retrain**
```bash
# Export training data (corrected + high-confidence)
python scripts/export_production_data.py --mode retraining --days 30

# Convert to contrastive pairs
python scripts/convert_to_pairs.py --input data/production_prompts.jsonl --output data/production_pairs.jsonl

# Retrain model
python scripts/train_contrastive.py --additional-data data/production_pairs.jsonl
```

**Week 4: Deploy**
```bash
# Export to ONNX
python scripts/export_to_onnx_contrastive.py

# Deploy new model
# Backend will auto-reload on model file change
```

## Monitoring Queries

### Get Low-Confidence Prompts

```python
low_conf = await repo.get_low_confidence_prompts(threshold=0.7, limit=100)
```

### Get Failed Workflows

```python
failed = await repo.get_failed_workflow_prompts(limit=100)
```

### Get Statistics

```sql
-- Confidence distribution
SELECT
    ROUND(confidence::numeric, 1) as conf_bucket,
    COUNT(*) as count
FROM nlu_prompt_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY conf_bucket
ORDER BY conf_bucket DESC;

-- Intent distribution
SELECT
    predicted_intent,
    COUNT(*) as count,
    AVG(confidence) as avg_conf,
    COUNT(corrected_intent) as corrections
FROM nlu_prompt_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY predicted_intent
ORDER BY count DESC;

-- Workflow success rate by intent
SELECT
    predicted_intent,
    COUNT(*) as total,
    COUNT(CASE WHEN was_successful = TRUE THEN 1 END) as successes,
    ROUND(100.0 * COUNT(CASE WHEN was_successful = TRUE THEN 1 END) / COUNT(*), 1) as success_rate
FROM nlu_prompt_logs
WHERE was_successful IS NOT NULL
GROUP BY predicted_intent
ORDER BY success_rate ASC;
```

## Benefits

✅ **Continuous Improvement** - Model gets better over time with real data
✅ **Catch Misclassifications** - Human review of low-confidence predictions
✅ **Track Performance** - Monitor workflow success rates by intent
✅ **Domain Adaptation** - Learn user-specific language patterns
✅ **Error Analysis** - Identify which intents need more training data
✅ **A/B Testing** - Compare old vs new model on production data

## Privacy & Security

- ✅ Row-level security enforced (users can only see their own logs)
- ✅ Logs tied to user_id for proper isolation
- ✅ Can be anonymized for model training (strip user_id, keep prompt+intent)
- ✅ Retention policy recommended: 90 days for raw logs, indefinite for anonymized training data

## Next Steps

1. ✅ Database migration applied
2. ✅ NLU service integrated
3. ✅ Export scripts created
4. ⏳ Create import script for manual corrections
5. ⏳ Add analytics dashboard for monitoring
6. ⏳ Set up weekly cron job for automated exports
7. ⏳ Create Slack/email alerts for high error rates

## See Also

- [DATASET_SUMMARY.md](./DATASET_SUMMARY.md) - Initial training dataset
- [CONTRASTIVE_MIGRATION_GUIDE.md](./CONTRASTIVE_MIGRATION_GUIDE.md) - Model architecture
- [Intent Specs](../../backend/app/agents/core/intent_specs.py) - Intent definitions
