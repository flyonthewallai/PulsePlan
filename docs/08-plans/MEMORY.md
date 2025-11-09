🧠 PulsePlan Agent Memory Implementation Plan

Goal: Build a tiered, long-term memory system that continuously learns from user interactions, preferences, and session summaries — without slowing the real-time workflow.

⚙️ Architecture Overview
Layer	Storage	Function	TTL / Retention	Accessed By
Short-Term Memory	Redis (chat:{user_id})	Holds recent messages and tool calls	24 h or until idle summarization	LLM context, SummarizationService
Medium-Term Memory (Episodic)	chat_summary table	Stores condensed session summaries and metadata	30 days+	VectorMemoryService, analytics
Long-Term Memory (Semantic / Structured)	vector_memories table + embeddings	Persistent knowledge & user preferences	Permanent	LLM context builder, personalization layer
🧩 Phase 1: Schema & Core Models
1. Database Tables
chat_summary
CREATE TABLE chat_summary (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  summary TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

vector_memories
CREATE TABLE vector_memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  namespace TEXT NOT NULL,              -- e.g. profile_snapshot, preferences
  doc_id TEXT UNIQUE NOT NULL,          -- pref:study_time:2025-11-03
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON vector_memories (user_id, namespace);

2. Pydantic Models
class MemoryEntry(BaseModel):
    namespace: str
    doc_id: str
    content: str
    embedding: list[float]
    metadata: dict

class SessionSummary(BaseModel):
    user_id: str
    summary: str
    metadata: dict

🔁 Phase 2: Memory Creation Pipeline
A. Short-Term → Summarization

Trigger conditions

User idle for X minutes

End of action workflow

Daily cron (e.g., midnight)

async def summarize_and_persist_session(user_id: str):
    msgs = redis_client.lrange(f"chat:{user_id}", 0, -1)
    if not msgs:
        return
    summary = await llm_client.summarize_chat(msgs)
    meta = {"intent_mix": analyze_intents(msgs)}
    await chat_summary_repo.insert(user_id=user_id, summary=summary, metadata=meta)
    redis_client.delete(f"chat:{user_id}")


Background worker handles these via Celery queue summarization_tasks.

B. Structured Slot → Vector Memory

After every successful action_executor call:

async def post_nlu_hook(user_id, slots, action_id):
    normalized = normalize_slots(slots)
    for pref in normalized:
        await vector_memory.upsert_memory(
            namespace="preferences",
            doc_id=f"pref:{pref['key']}:{date.today()}",
            content=pref["statement"],
            metadata={
                "source": "nlu",
                "confidence": pref["confidence"],
                "action_id": action_id
            }
        )


This runs asynchronously so the user never feels latency.

C. Historical Backfill Worker

A one-time or scheduled script:

async def backfill_preferences():
    for user in users_repo.all():
        logs = prompt_log_repo.fetch_user_logs(user.id)
        for text in extract_preference_statements(logs):
            await vector_memory.upsert_memory(
                namespace="profile_snapshot",
                doc_id=f"backfill:{uuid4()}",
                content=text,
                metadata={"source": "backfill", "confidence": 0.8}
            )


Include sanitization (hash emails, redact sensitive data) and confirm RLS isolation.

D. Explicit Memory-Write Tool

File: backend/app/agents/tools/store_memory_tool.py

@tool("store_memory", description="Persist a durable fact about the user")
async def store_memory(content: str, category: str, confidence: float = 1.0):
    await vector_memory.upsert_memory(
        namespace="profile_snapshot",
        doc_id=f"{category}:{uuid4()}",
        content=content,
        metadata={"source": "user_command", "confidence": confidence}
    )


Used by LLM when user says “Remember that I hate Thursday evening classes.”

🧮 Phase 3: Metadata Schema Standardization

Every memory document includes:

{
  "source": "nlu_prompt_log|session_summary|user_command",
  "confidence": 0.95,
  "category": "time_preference|constraint|goal|habit",
  "entities": ["study", "morning"],
  "created_at": "2025-11-04T22:15:00Z"
}


Benefits:

Easy filtering by category or source

Auditability and explainability

Future-proof for retrieval scoring

🧠 Phase 4: Retrieval & Context Injection

Enhance VectorMemoryService.retrieve_context() to support:

def retrieve_context(user_id, namespaces=None, categories=None, limit=10):
    memories = query_vector_store(user_id, namespaces, categories)
    recent_summaries = chat_summary_repo.fetch_recent(user_id, n=3)
    return merge_and_rank(memories, recent_summaries)


Uses MMR to balance recency and relevance

Provides both semantic (embeddings) and episodic (summary) recall

Supports namespace filtering (preferences, chat_summary)

⚙️ Phase 5: Worker Infrastructure
Celery / Background Workers
Queue	Responsibility
summarization_tasks	Run summarize_and_persist_session
memory_upsert_tasks	Write slot preferences to vector store
backfill_tasks	Mine old logs for preferences

All workers import VectorMemoryService and SummarizationService with Supabase + Redis credentials.

🔒 Phase 6: Privacy & Policy

Encrypt all embeddings and redact any PII before insertion.

Row-Level Security:

CREATE POLICY user_isolation ON vector_memories
FOR ALL USING (user_id = auth.uid());


Allow user data export/delete via GDPR endpoint calling:

vector_memory.delete_user_memories(user_id)
chat_summary_repo.delete_user_summaries(user_id)

🧭 Phase 7: Testing & Validation
Test	Expected Behavior
Summarization after idle	Redis chat cleared, chat_summary row inserted
Post-NLU hook	Preference written to vector store
store_memory tool call	Manual memory persisted
Retrieval context	Returns combined semantic + episodic snippets
Backfill worker dry-run	Inserts sanitized memories only
RLS check	Cross-user read denied
📅 Deployment Order & Effort
Step	Description	Time
1	DB migrations + models	1 h
2	SummarizationService integration	2 h
3	Slot→vector hook	1 h
4	store_memory tool	30 m
5	Worker setup + queues	2 h
6	Retrieval updates	1 h
7	Privacy policies + tests	1 h
Total	≈ 8 hours end-to-end