"""
Intent Classification Service
Handles LLM-based intent classification and confidence scoring
"""
from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI


class IntentClassificationService:
    """Service for classifying user intents using LLM"""
    
    def __init__(self):
        self.llm = None
    
    def _get_llm(self):
        """Lazy initialization of LLM"""
        if self.llm is None:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        return self.llm
    
    def classify_intent(self, query: str) -> Dict[str, Any]:
        """LLM-based intent classification with confidence and reasoning"""
        prompt = f"""
        You are an Intent Classifier for PulsePlan, an AI-powered academic planner. Your job is to classify user requests into workflow categories.
        
        IMPORTANT: You only need to identify the correct workflow type. Each workflow has its own intelligent supervisor that will handle context validation, parameter extraction, and clarification. Focus solely on routing accuracy.
        
        Classify the following user request into one of these intents:
        
        Intent categories:
        - calendar: scheduling meetings, events, appointments, checking availability
        - task: creating, managing, or updating complex tasks with dependencies, scheduling, or detailed project work  
        - todo: creating, managing, or updating simple todos, quick reminders, basic to-do items, shopping lists
        - briefing: requesting summaries, reports, daily briefings, status updates
        - scheduling: creating schedules, time management, organizing weekly/daily plans, optimizing time
        - email: sending emails, composing messages, email management, reading emails, checking inbox, email operations
        - canvas: Canvas LMS related operations including syncing assignments, getting course data, upcoming assignments
        - search: web search requests for external information, research queries, "search for", "look up", "find information about"
        - chat: greetings, questions about user's information/profile, seeking help, general conversation, app questions
        - unknown: anything that doesn't clearly fit the above categories
        
        Classification rules:
        - If the user is asking about a specific email or sending an email, classify as "email"
        - If the user asks about their calendar, classify as "calendar"
        - If the user asks about Canvas sync, classify as "canvas" (ONLY SYNC AVAILABLE THROUGH THIS TOOL)
        - If the user asks about their own information, preferences, or context that the system knows about → classify as "chat"
        - If the user asks for external information not in the system → classify as "search"
        - If the user asks "what can you do?" or similar → classify as "chat"
        - If the user asks about PulsePlan, the app, or the developers → classify as "chat"
        - If the user asks about their schedule, tasks, or personal info → classify as "chat"
        
        Examples:
        - "hi", "hello", "hey" = chat (high confidence)
        - "what can you help me with?" = chat
        - "what are my preferences?" = chat (system has this info)
        - "tell me about myself" = chat (system has user profile)
        - "who made this app?" = chat (system has this info)
        - "what are your capabilities?" = chat (system has this info)
        - "schedule a meeting tomorrow" = calendar
        - "add task to finish project" = task
        - "make my schedule for this week" = scheduling
        - "email John about the meeting" = email
        - "send an email to mom" = email
        - "check my inbox" = email
        - "read my emails" = email
        - "compose an email to my teacher" = email
        - "sync my Canvas assignments" = canvas
        - "get my Canvas courses" = canvas
        - "show me upcoming Canvas assignments" = canvas
        - "sync Canvas data" = canvas
        - "show me today's summary" = briefing
        - "search for study tips" = search (external info)
        - "look up the weather in Seattle" = search (external info)
        - "find information about machine learning" = search (external info)
        
        User request: "{query}"
        
        Response format:
        {{
            "intent": "category_name",
            "confidence": 0.85,
            "reasoning": "Very brief explanation of why this intent was chosen",
            "ambiguous": false,
            "alternative_intents": ["other_possible_intent"]
        }}
        """
        
        try:
            print(f"[LLM PROMPT] Sending to LLM:")
            print(f"    Model: gpt-4o-mini")
            print(f"    Temperature: 0")
            print(f"    Query: '{query}'")
            print(f"    Prompt length: {len(prompt)} characters")
            
            resp = self._get_llm().invoke(prompt)
            
            # Try to parse JSON response - ensure we handle the response properly
            response_content = resp.content if hasattr(resp, 'content') else str(resp)
            print(f"[LLM RAW RESPONSE] {response_content}")
            
            try:
                result = json.loads(response_content.strip())
                print(f"[LLM PARSED] Successfully parsed JSON response")
            except json.JSONDecodeError:
                print(f"[LLM PARSE ERROR] Failed to parse JSON response")
                # Fallback: extract just the intent if JSON parsing fails
                content = response_content.strip().lower()
                valid_intents = ["calendar", "task", "todo", "briefing", "scheduling", "email", "canvas", "search", "chat", "unknown"]
                
                for intent in valid_intents:
                    if intent in content:
                        print(f"[LLM FALLBACK] Found intent '{intent}' in response text")
                        return {
                            "intent": intent,
                            "confidence": 0.5,
                            "reasoning": "Fallback parsing - JSON response failed",
                            "ambiguous": True,
                            "alternative_intents": [],
                            "raw_response": response_content
                        }
                
                return {
                    "intent": "unknown",
                    "confidence": 0.1,
                    "reasoning": "Could not parse LLM response",
                    "ambiguous": True,
                    "alternative_intents": [],
                    "raw_response": response_content
                }
            
            # Validate and normalize the parsed result
            intent = result.get("intent", "unknown").lower()
            valid_intents = ["calendar", "task", "todo", "briefing", "scheduling", "email", "canvas", "search", "chat", "unknown"]
            
            if intent not in valid_intents:
                intent = "unknown"
                result["confidence"] = 0.1
                result["reasoning"] = f"Invalid intent '{result.get('intent')}' returned by LLM"
                result["ambiguous"] = True
            
            # Ensure all required fields exist
            classification = {
                "intent": intent,
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", "No reasoning provided"),
                "ambiguous": result.get("ambiguous", False),
                "alternative_intents": result.get("alternative_intents", []),
                "raw_response": response_content
            }
            
            # Auto-detect ambiguity based on confidence
            if classification["confidence"] < 0.5:
                classification["ambiguous"] = True
            
            return classification
                
        except Exception as e:
            # Fallback to unknown if LLM fails
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "reasoning": f"LLM classification failed: {str(e)}",
                "ambiguous": True,
                "alternative_intents": [],
                "error": str(e)
            }
    
    def determine_confidence_threshold(self, classification: Dict[str, Any]) -> str:
        """Determine routing based on confidence thresholds"""
        confidence = classification.get("confidence", 0.0)
        
        if confidence < 0.4 or classification.get("ambiguous", False):
            return "ambiguous"
        elif confidence >= 0.7:
            return "high_confidence"
        else:
            return "medium_confidence"