"""
Intent Classifier Node
Handles intent classification and immediate response generation
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any

from ..base import WorkflowState, WorkflowError
from ..services.intent_service import IntentClassificationService
from ..services.response_service import ResponseGenerationService


class IntentClassifierNode:
    """Node responsible for intent classification and immediate response generation"""
    
    def __init__(self):
        self.intent_service = IntentClassificationService()
        self.response_service = ResponseGenerationService()
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Analyze user query to determine workflow type with confidence thresholding"""
        start_time = time.time()
        
        state["current_node"] = "intent_classifier"
        state["visited_nodes"].append("intent_classifier")
        
        user_query = state["input_data"].get("query", "").strip()
        user_id = state.get("user_id", "unknown")
        trace_id = state.get("trace_id", "unknown")
        
        self.logger.info(
            f"🎯 Intent classification started for query: '{user_query}'",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "query": user_query,
                "query_length": len(user_query),
                "event": "intent_classification_start"
            }
        )
        print(f"🎯 [CLASSIFICATION START] User: {user_id} | Query: '{user_query}' | Length: {len(user_query)}")
        
        if not user_query:
            self.logger.error(
                "Empty user query provided",
                extra={"user_id": user_id, "trace_id": trace_id, "event": "empty_query_error"}
            )
            raise WorkflowError("Empty user query", {"state": state})
        
        # Classify intent using service
        llm_start = time.time()
        self.logger.info(
            f"🤖 Starting LLM classification for: '{user_query}'",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "query": user_query,
                "event": "llm_classification_start"
            }
        )
        print(f"🤖 [LLM START] Calling LLM for classification of: '{user_query}'")
        
        classification = self.intent_service.classify_intent(user_query)
        classification_time = time.time() - start_time
        llm_time = time.time() - llm_start
        
        self.logger.info(
            f"🤖 LLM classification completed: {classification['intent']} (confidence: {classification['confidence']})",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "intent": classification["intent"],
                "confidence": classification["confidence"],
                "reasoning": classification["reasoning"],
                "classification_time": classification_time,
                "llm_time": llm_time,
                "event": "llm_classification_complete"
            }
        )
        print(f"🤖 [LLM RESULT] Intent: {classification['intent']} | Confidence: {classification['confidence']:.2f} | Reasoning: {classification['reasoning']} | LLM Time: {llm_time:.3f}s")
        
        intent = classification["intent"]
        confidence = classification["confidence"]
        
        # Confidence thresholding for ambiguous cases
        original_intent = intent
        if confidence < 0.4 or classification.get("ambiguous", False):
            # Low confidence - route to clarification
            intent = "ambiguous"
            state["input_data"]["needs_clarification"] = True
            state["input_data"]["clarification_context"] = {
                "possible_intents": [original_intent] + classification.get("alternative_intents", []),
                "reasoning": classification["reasoning"],
                "original_intent": classification["intent"]
            }
            print(f"❓ [LOW CONFIDENCE] Original intent: {original_intent} -> Routing to clarification (confidence: {confidence:.2f})")
        elif 0.4 <= confidence < 0.7:
            # Medium confidence - flag as uncertain but proceed
            state["input_data"]["uncertain_classification"] = True
            print(f"⚠️  [MEDIUM CONFIDENCE] Intent: {intent} (confidence: {confidence:.2f}) - proceeding with uncertainty flag")
        
        # Store comprehensive classification results
        state["input_data"]["classified_intent"] = intent
        state["input_data"]["confidence"] = confidence
        state["input_data"]["classification_details"] = classification
        
        # Generate immediate conversational response and task preview
        immediate_start = time.time()
        self.logger.info(
            f"💬 Generating immediate response for intent: {intent}",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "intent": intent,
                "confidence": confidence,
                "event": "immediate_response_start"
            }
        )
        print(f"💬 [RESPONSE START] Generating immediate response for intent: {intent}")
        
        immediate_response = self.response_service.generate_immediate_response(user_query, intent, classification)
        immediate_time = time.time() - immediate_start
        
        # Store immediate response in state so routers can access actual_title
        state["input_data"]["immediate_response"] = immediate_response
        
        response_preview = immediate_response.get("response", "")[:100] + ("..." if len(immediate_response.get("response", "")) > 100 else "")
        
        self.logger.info(
            f"💬 Immediate response generated: '{response_preview}'",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "response_type": immediate_response.get("conversation_type"),
                "has_task_preview": bool(immediate_response.get("task_preview")),
                "immediate_response_time": immediate_time,
                "event": "immediate_response_complete"
            }
        )
        print(f"💬 [RESPONSE READY] Type: {immediate_response.get('conversation_type')} | Has task preview: {bool(immediate_response.get('task_preview'))} | Time: {immediate_time:.3f}s")
        print(f"💬 [RESPONSE TEXT] '{response_preview}'")
        
        state["input_data"]["immediate_response"] = immediate_response
        
        # Enhanced metrics with full observability
        state["metrics"]["intent_classification"] = {
            "intent": intent,
            "confidence": confidence,
            "query_length": len(user_query),
            "reasoning": classification["reasoning"],
            "ambiguous": classification.get("ambiguous", False),
            "alternative_intents": classification.get("alternative_intents", []),
            "needs_clarification": state["input_data"].get("needs_clarification", False),
            "classification_timestamp": datetime.utcnow().isoformat()
        }
        
        # Log detailed classification for audit and training with performance metrics
        total_time = time.time() - start_time
        self.logger.info(
            f"✅ Intent classification completed: {intent} (confidence: {confidence:.2f})",
            extra={
                "user_id": user_id,
                "trace_id": trace_id,
                "query": user_query,
                "classification": classification,
                "final_intent": intent,
                "confidence": confidence,
                "total_time": total_time,
                "classification_time": classification_time,
                "immediate_response_time": immediate_time,
                "llm_used": True,
                "needs_clarification": state["input_data"].get("needs_clarification", False),
                "has_task_preview": bool(immediate_response.get("task_preview")),
                "response_type": immediate_response.get("conversation_type"),
                "event": "intent_classification_complete"
            }
        )
        
        # Comprehensive routing decision summary
        routing_decision = {
            "query": user_query,
            "final_intent": intent,
            "original_intent": original_intent if 'original_intent' in locals() else intent,
            "confidence": confidence,
            "llm_used": True,
            "needs_clarification": state["input_data"].get("needs_clarification", False),
            "has_task_preview": bool(immediate_response.get("task_preview")),
            "response_type": immediate_response.get("conversation_type"),
            "total_time": total_time
        }
        
        print("="*80)
        print(f"🎯 [CLASSIFICATION SUMMARY]")
        print(f"   Query: '{user_query}'")
        print(f"   Final Intent: {intent} (confidence: {confidence:.2f})")
        if 'original_intent' in locals() and original_intent != intent:
            print(f"   Original Intent: {original_intent} (modified due to low confidence)")
        print(f"   Reasoning: {classification['reasoning']}")
        print(f"   LLM Used: True")
        print(f"   Needs Clarification: {state['input_data'].get('needs_clarification', False)}")
        print(f"   Response Type: {immediate_response.get('conversation_type')}")
        print(f"   Has Task Preview: {bool(immediate_response.get('task_preview'))}")
        print(f"   Total Time: {total_time:.3f}s")
        print(f"   Next Route: {intent}_router" if intent not in ['ambiguous', 'unknown'] else f"   Next Route: clarification_generator")
        print("="*80)
        
        return state