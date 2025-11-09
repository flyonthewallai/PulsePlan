# Admin NLU Dashboard Guide

Complete guide for using the admin NLU monitoring dashboard for model performance tracking and continuous improvement.

## Overview

The admin dashboard provides real-time monitoring and management tools for the NLU intent classification system. It's designed for **ML operations**, separate from PostHog product analytics.

**Access:** `https://app.pulseplan.com/admin/nlu`

**Auth:** Only accessible to admin users (configured in `backend/app/api/v1/endpoints/admin_nlu.py`)

## Features

### 1. Overview Tab 📊

**Real-time metrics refreshed every 30 seconds:**

#### Key Metrics Cards
- **Total Prompts (7d)** - Weekly prompt volume with today's count
- **Avg Confidence** - Model confidence trend (today vs. 7-day average)
- **Low Confidence** - Count of prompts <70% needing review
- **Failed Workflows** - Execution errors requiring investigation

#### Visualizations
- **Intent Distribution** - Top 10 most common intents (progress bars)
- **Confidence Distribution** - Bucketed by confidence ranges
- **Workflow Success Rates** - Table showing success rates per intent

**Use Cases:**
- Daily health check of NLU system
- Identify intents with low success rates
- Track model confidence trends
- Spot anomalies in prompt distribution

### 2. Low Confidence Tab 🔍

**Manual review and correction workflow:**

#### Features
- Table of all prompts with confidence < 70%
- Inline correction interface
- Add correction notes for training context

#### Workflow
1. Review prompt and predicted intent
2. Click "Correct" button
3. Enter correct intent label
4. Add notes explaining why (optional)
5. Save correction

**Corrections are:**
- ✅ Stored in database with notes
- ✅ Included in training data exports
- ✅ Prioritized for model retraining

**Best Practices:**
- Review 10-20 prompts weekly
- Focus on patterns (similar prompts misclassified)
- Add detailed notes for ambiguous cases
- Use intent labels from `intent_specs.json`

### 3. Failed Workflows Tab ❌

**Error investigation and debugging:**

#### Features
- All prompts that led to workflow failures
- Error messages for debugging
- Workflow type for context

#### Common Failure Reasons
1. **Intent Misclassification** - Wrong workflow triggered
2. **Missing Slots** - Required data not extracted
3. **Integration Errors** - Canvas, Calendar, etc. failures
4. **Data Issues** - Invalid task IDs, dates, etc.

**Investigation Steps:**
1. Check error message
2. Verify predicted intent is correct
3. If wrong: Add correction in Low Confidence tab
4. If right: Bug in workflow execution (fix code)

### 4. Corrections Tab 📝

**View all manual corrections:**

Currently shows placeholder. Will display:
- All corrected prompts
- Before/after intent labels
- Correction notes
- Timestamp and admin who corrected

### 5. Exports Tab 📥

**One-click data exports for retraining:**

#### Export Training Data
- **What:** Corrected prompts + high-confidence (>85%) predictions
- **Format:** JSON array with `text`, `label`, `confidence`, `source`, `corrected` fields
- **Use:** Model retraining with production data
- **Timeframe:** Last 30 days

**Example output:**
```json
[
  {
    "text": "schedule time to work on assignment",
    "label": "scheduling",
    "confidence": 0.92,
    "source": "production",
    "corrected": false
  },
  {
    "text": "add event to my calendar",
    "label": "calendar_event",
    "confidence": 0.68,
    "source": "production",
    "corrected": true
  }
]
```

#### Export Review Queue
- **What:** Low-confidence prompts needing manual review
- **Format:** JSON with prompt, predicted intent, confidence
- **Use:** Offline review and bulk corrections
- **Threshold:** Confidence < 70%

## Weekly Workflow

### Monday: Health Check
1. Open Overview tab
2. Check avg confidence (should be >75%)
3. Review failed workflows count
4. Identify any anomalies

### Wednesday: Manual Review
1. Open Low Confidence tab
2. Review 10-20 prompts
3. Add corrections for misclassifications
4. Note patterns in correction notes

### Friday: Export & Plan
1. Open Exports tab
2. Export Training Data (last 7 days)
3. Review correction count
4. Plan retraining if >50 corrections

### Monthly: Retrain & Deploy
1. Export Training Data (last 30 days)
2. Convert to contrastive pairs
3. Retrain model with production data
4. A/B test new vs old model
5. Deploy if better performance

## API Endpoints

All endpoints require admin authentication.

### GET /v1/admin/nlu/stats
```typescript
{
  total_prompts: number;
  total_prompts_today: number;
  total_prompts_week: number;
  avg_confidence: number;
  avg_confidence_today: number;
  low_confidence_count: number;
  failed_workflows: number;
  correction_count: number;
  intent_distribution: Array<{intent: string, count: number}>;
  confidence_distribution: Array<{bucket: string, count: number}>;
  workflow_success_rate: Record<string, {total: number, success: number, rate: number}>;
}
```

### GET /v1/admin/nlu/low-confidence
**Query params:** `threshold` (default 0.7), `limit` (default 100)

### GET /v1/admin/nlu/failed-workflows
**Query params:** `limit` (default 100)

### POST /v1/admin/nlu/correct-intent
```typescript
{
  log_id: string;
  corrected_intent: string;
  correction_notes?: string;
}
```

### POST /v1/admin/nlu/export-training-data
```typescript
{
  days: number; // Default 30
  mode: "retraining" | "review";
}
```

## Admin Access Configuration

**Current:** Hardcoded email whitelist in `backend/app/api/v1/endpoints/admin_nlu.py`

```python
admin_emails = [
    "conner@pulseplan.com",
    "admin@pulseplan.com",
]
```

**TODO:** Replace with proper role-based access control
- Add `role` field to users table
- Check `user.role === 'admin'` instead of email
- Allow multi-admin support

## Monitoring Alerts (Future)

**Recommended alerts to set up:**

1. **Low Confidence Spike** - Alert if >20% of prompts <70% confidence
2. **Failed Workflows Spike** - Alert if >10% workflows failing
3. **Confidence Drop** - Alert if avg confidence drops >10% week-over-week
4. **Zero Prompts** - Alert if no prompts received in 24h (system down)

**Implementation options:**
- PostHog for metrics tracking
- Sentry for error tracking
- Custom webhook to Slack/email

## Troubleshooting

### Dashboard won't load
- Check admin email is whitelisted
- Verify backend API is running
- Check browser console for errors
- Verify `/v1/admin/nlu/stats` endpoint responds

### No data showing
- Confirm prompts are being logged (check database)
- Verify NLU service integration is active
- Check user_id is being passed to `process_message()`

### Export fails
- Check file download permissions
- Verify API response is valid JSON
- Check browser console for errors

### Corrections not saving
- Verify log_id is valid UUID
- Check corrected_intent is valid intent label
- Confirm admin has write permissions

## Best Practices

✅ **DO:**
- Review low-confidence prompts weekly
- Add detailed correction notes
- Export training data monthly
- Monitor confidence trends
- Investigate failed workflows

❌ **DON'T:**
- Ignore low-confidence prompts
- Correct without understanding why
- Export without reviewing quality
- Deploy retraining without A/B testing
- Change intent labels from spec

## Next Steps

After using the dashboard for a few weeks:

1. **Automate exports** - Cron job for weekly exports
2. **Add alerts** - Slack notifications for anomalies
3. **Expand corrections tab** - Full view of all corrections
4. **Add A/B testing UI** - Deploy and compare models
5. **Intent analytics** - Deep dive per-intent performance

## See Also

- [PROMPT_CAPTURE_SYSTEM.md](./PROMPT_CAPTURE_SYSTEM.md) - Full system architecture
- [PROMPT_CAPTURE_IMPLEMENTATION.md](../PROMPT_CAPTURE_IMPLEMENTATION.md) - Implementation details
- [Intent Specs](../../backend/app/agents/core/intent_specs.py) - Intent definitions
