"""
Response Generation Service
Handles immediate response generation and task preview creation
"""
from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI


class ResponseGenerationService:
    """Service for generating immediate responses and task previews"""
    
    def __init__(self):
        self.llm_fast = None
        self.llm_chat = None
    
    def _get_llm_fast(self):
        """Lazy initialization of fast LLM"""
        if self.llm_fast is None:
            from langchain_openai import ChatOpenAI
            self.llm_fast = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        return self.llm_fast
    
    def _get_llm_chat(self):
        """Lazy initialization of chat LLM"""
        if self.llm_chat is None:
            from langchain_openai import ChatOpenAI
            self.llm_chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
        return self.llm_chat
    
    def generate_immediate_response(self, query: str, intent: str, classification: dict) -> dict:
        """Generate immediate conversational response with task preview for non-chat intents"""
        query_lower = query.lower().strip()
        
        if intent == "chat":
            # All chat queries use LLM for natural, varied responses (no robotic fast paths)
            return {
                "response": "Let me respond to that...",
                "conversation_type": "processing",
                "immediate": True,
                "needs_llm": True,
                "natural_response": True  # Generate natural, varied response
            }
        
        elif intent in ["calendar", "task", "todo", "briefing", "scheduling", "email", "search"]:
            # Generate task response for actionable intents
            task_response = self.generate_task_response(query, intent)
            
            # Create task preview based on intent
            task_preview = self._create_task_preview(intent, task_response["task_name"])
            
            return {
                "response": task_response["acknowledgment"],
                "conversation_type": "task_initiated",
                "immediate": True,
                "actual_title": task_response["actual_title"],
                "task_preview": task_preview
            }
        
        else:
            # For ambiguous/unknown, provide clarification immediately
            return {
                "response": f"I want to make sure I understand correctly. You said: '{query}' - could you clarify what you'd like me to help with?",
                "conversation_type": "clarification",
                "immediate": True,
                "needs_clarification": True,
                "suggestions": [
                    {"type": "calendar", "example": "Schedule a meeting with John tomorrow"},
                    {"type": "task", "example": "Create a project plan with dependencies"}, 
                    {"type": "todo", "example": "Add buy milk to my todo list"},
                    {"type": "briefing", "example": "Show me my daily agenda"},
                    {"type": "chat", "example": "What can you help me with?"}
                ]
            }
    
    def generate_task_response(self, query: str, intent: str) -> dict:
        """Generate both task name and acknowledgment response in a single LLM call"""
        intent_context = {
            "calendar": "scheduling/calendar task",
            "task": "complex task creation", 
            "todo": "simple todo creation",
            "briefing": "briefing generation",
            "scheduling": "schedule creation",
            "email": "email task",
            "search": "web search"
        }
        
        task_context = intent_context.get(intent, "task")
        
        prompt = f"""
        Generate both a concise task name and a natural acknowledgment response for this user request.
        
        User request: "{query}"
        Task type: {task_context}
        
        CRITICAL: You MUST return a JSON object with exactly these fields:
        - "task_name": concise 4-word max summary for UI display (e.g., "Add Todo Item")
        - "actual_title": REQUIRED - the actual item title to save in database
        - "acknowledgment": natural, enthusiastic response (1 sentence, under 15 words)
        
        IMPORTANT: The "actual_title" field is MANDATORY and must contain the meaningful action/item (what the user actually wants to do):
        - "add milk to my todos" → actual_title: "Buy milk"
        - "add buy groceries to my todo list" → actual_title: "Buy groceries"  
        - "create a task to write report" → actual_title: "Write report"
        - "remind me to call mom" → actual_title: "Call mom"
        - "add walk the dog to my todos" → actual_title: "Walk the dog"
        - "create todo for dentist appointment" → actual_title: "Dentist appointment"

        Examples:
        {{
            "task_name": "Add Todo Item",
            "actual_title": "Buy milk",
            "acknowledgment": "Perfect, I'll add milk to your todos!"
        }}
        {{
            "task_name": "Create Task", 
            "actual_title": "Write project report",
            "acknowledgment": "Got it! I'll create that task for you."
        }}
        {{
            "task_name": "Add Reminder",
            "actual_title": "Call mom",
            "acknowledgment": "I'll set up that reminder to call mom!"
        }}
        {{
            "task_name": "Web Search",
            "actual_title": "study methods",
            "acknowledgment": "Perfect, let me search for study methods!"
        }}
        
        Make the acknowledgment sound enthusiastic and helpful. Don't repeat the exact query - rephrase it naturally.
        Return only valid JSON.
        """
        
        try:
            response = self._get_llm_fast().invoke(prompt)
            response_content = response.content.strip()
            
            print(f"🤖 [LLM RESPONSE] Raw response for query '{query}': {response_content}")
            
            result = json.loads(response_content)
            
            # Validate and set defaults
            if not isinstance(result, dict):
                raise ValueError("Response is not a valid JSON object")
            
            actual_title = result.get("actual_title", "").strip()
            if not actual_title:
                print(f"⚠️  [LLM RESPONSE] Empty actual_title, using fallback for query: '{query}'")
                actual_title = query
            
            # Ensure task name is 4 words or less
            task_name = result.get("task_name", "").strip()
            if not task_name:
                task_name = "Process Request"
            words = task_name.split()
            if len(words) > 4:
                task_name = ' '.join(words[:4])
            
            task_response = {
                "task_name": task_name,
                "actual_title": actual_title,
                "acknowledgment": result.get("acknowledgment", "I'll help you with that!").strip()
            }
            
            print(f"✅ [LLM RESPONSE] Parsed response - task_name: '{task_response['task_name']}', actual_title: '{task_response['actual_title']}', acknowledgment: '{task_response['acknowledgment']}'")
            
            return task_response
            
        except Exception as e:
            print(f"❌ [TASK RESPONSE] Failed to parse LLM response: {e}")
            print(f"❌ [TASK RESPONSE] Raw response was: {response_content if 'response_content' in locals() else 'No response'}")
            
            # Fallback responses if LLM fails
            fallback_names = {
                "calendar": "Schedule Event",
                "task": "Create Task", 
                "briefing": "Generate Briefing",
                "scheduling": "Create Schedule",
                "email": "Send Email",
                "search": "Web Search"
            }
            fallback_responses = {
                "calendar": "Got it! I'll help with that scheduling request.",
                "task": "Perfect! I'll create that task for you.",
                "briefing": "I'll prepare that briefing for you!",
                "scheduling": "Let me create that schedule for you.",
                "email": "I'll help you with that email task.",
                "search": "Perfect, let me search for that information!"
            }
            
            return {
                "task_name": fallback_names.get(intent, "Task"),
                "actual_title": query,  # Fallback to original query
                "acknowledgment": fallback_responses.get(intent, "I'll help you with that!")
            }
    
    def _create_task_preview(self, intent: str, task_name: str) -> dict:
        """Create task preview with estimated tools based on intent"""
        previews = {
            "calendar": {
                "task_name": task_name,
                "task_type": "calendar",
                "status": "starting",
                "estimated_tools": [
                    {"id": "cal_1", "name": "calendar_analyzer", "description": "Parse scheduling request", "status": "pending"},
                    {"id": "cal_2", "name": "availability_checker", "description": "Check calendar availability", "status": "pending"},
                    {"id": "cal_3", "name": "event_creator", "description": "Create calendar event", "status": "pending"}
                ]
            },
            "task": {
                "task_name": task_name,
                "task_type": "database_task",
                "status": "starting",
                "estimated_tools": [
                    {"id": "task_1", "name": "task_parser", "description": "Parse task details", "status": "pending"},
                    {"id": "task_2", "name": "dependency_analyzer", "description": "Check task dependencies", "status": "pending"},
                    {"id": "task_3", "name": "scheduling_optimizer", "description": "Optimize task scheduling", "status": "pending"},
                    {"id": "task_4", "name": "task_creator", "description": "Create task in system", "status": "pending"}
                ]
            },
            "todo": {
                "task_name": task_name,
                "task_type": "database_todo",
                "status": "starting",
                "estimated_tools": [
                    {"id": "todo_1", "name": "todo_parser", "description": "Parse todo details", "status": "pending"},
                    {"id": "todo_2", "name": "priority_analyzer", "description": "Determine todo priority", "status": "pending"},
                    {"id": "todo_3", "name": "todo_creator", "description": "Create todo in system", "status": "pending"}
                ]
            },
            "briefing": {
                "task_name": task_name,
                "task_type": "briefing",
                "status": "starting",
                "estimated_tools": [
                    {"id": "brief_1", "name": "data_aggregator", "description": "Collect calendar and task data", "status": "pending"},
                    {"id": "brief_2", "name": "content_synthesizer", "description": "Generate briefing content", "status": "pending"},
                    {"id": "brief_3", "name": "formatter", "description": "Format final briefing", "status": "pending"}
                ]
            },
            "scheduling": {
                "task_name": task_name,
                "task_type": "scheduling",
                "status": "starting",
                "estimated_tools": [
                    {"id": "sched_1", "name": "task_analyzer", "description": "Analyze tasks and priorities", "status": "pending"},
                    {"id": "sched_2", "name": "time_optimizer", "description": "Find optimal time slots", "status": "pending"},
                    {"id": "sched_3", "name": "schedule_builder", "description": "Build final schedule", "status": "pending"}
                ]
            },
            "email": {
                "task_name": task_name,
                "task_type": "email",
                "status": "starting",
                "estimated_tools": [
                    {"id": "email_1", "name": "email_parser", "description": "Parse email request", "status": "pending"},
                    {"id": "email_2", "name": "content_generator", "description": "Generate email content", "status": "pending"},
                    {"id": "email_3", "name": "email_sender", "description": "Send or prepare email", "status": "pending"}
                ]
            },
            "search": {
                "task_name": task_name,
                "task_type": "search",
                "status": "starting",
                "estimated_tools": [
                    {"id": "search_1", "name": "query_analyzer", "description": "Analyze and optimize search query", "status": "pending"},
                    {"id": "search_2", "name": "web_search", "description": "Search the web for information", "status": "pending"},
                    {"id": "search_3", "name": "result_synthesizer", "description": "Synthesize and format results", "status": "pending"}
                ]
            }
        }
        
        return previews.get(intent, {
            "task_name": task_name,
            "task_type": "generic",
            "status": "starting",
            "estimated_tools": []
        })
    
    def generate_llm_chat_response(self, query: str, user_context: dict) -> dict:
        """Generate intelligent chat response using LLM"""
        prompt = f"""
        The user is asking: "{query}"

        You are Pulse. The user knows you well and you remember them.
        
        If this is a greeting, respond naturally and warmly like you know them.
        For questions, provide helpful responses about your capabilities.

        If this is a question about your capabilities (e.g. what can you do?), respond with a detailed list of your capabilities.
        
        Your capabilities:
        - Calendar: Schedule meetings, check availability, manage events
        - Tasks: Create reminders, set deadlines, manage priorities  
        - Briefing: Daily summaries, status reports, progress updates
        - Email: Read emails, compose and send emails (with user approval), manage inbox
        - Intelligent scheduling: Optimize time blocks and priorities

        PulsePlan Info:
        - PulsePlan allows users to create optimized schedules for their tasks and activities. 
        - PulsePlan was developed by Fly on the Wall LLC, founded by Conner Groth, Isaias Perez, and Jake Pechart. Learn more about us at https://flyonthewalldev.com
        
        Guidelines:
        - For greetings: Be warm and familiar (don't introduce yourself)
        - For questions: Be informative and helpful
        - For capabilities: List out all capabilities and be clear about what you can do.
        - Keep responses concise but engaging
        - Respond like you remember them and your past interactions
        - Never introduce yourself - they know who you are
        
        Respond in JSON format:
        {{
            "response": "Natural, conversational response",
            "conversation_type": "greeting|help|explanation|general_chat|feature_question", 
            "reasoning": "Very brief (1 sentence max) explanation of why you responded this way",
            "helpful_actions": [
                {{
                    "action": "calendar|task|briefing|chat",
                    "description": "What they could do next",
                    "example_query": "Example of how to phrase this request"
                }}
            ],
            "follow_up_questions": ["Short, helpful questions"]
        }}
        
        Be natural and familiar.
        """
        
        try:
            resp = self._get_llm_chat().invoke(prompt)
            
            # Parse LLM response - ensure we handle the response properly
            response_content = resp.content if hasattr(resp, 'content') else str(resp)
            try:
                llm_response = json.loads(response_content.strip())
                llm_response["raw_response"] = response_content
                return llm_response
            except json.JSONDecodeError:
                # Fallback response
                return {
                    "response": f"I'd be happy to help! Regarding '{query}', I can assist you with scheduling, task management, daily briefings, and general productivity questions. What specifically would you like to know more about?",
                    "conversation_type": "general_chat",
                    "reasoning": "JSON parsing failed, using fallback response",
                    "helpful_actions": [
                        {"action": "chat", "description": "Ask me specific questions about PulsePlan features", "example_query": "How do I schedule a meeting?"}
                    ],
                    "follow_up_questions": ["What specific feature would you like to know more about?"],
                    "raw_response": response_content,
                    "fallback_reason": "JSON parsing failed"
                }
                
        except Exception as e:
            # Error fallback
            return {
                "response": f"I'm here to help with '{query}'. I can assist with scheduling, task management, briefings, and productivity questions. What would you like to know?",
                "conversation_type": "general_chat", 
                "reasoning": f"LLM chat generation failed: {str(e)}",
                "helpful_actions": [
                    {"action": "chat", "description": "Ask me about PulsePlan features", "example_query": "What can you help me with?"}
                ],
                "follow_up_questions": ["What specific aspect would you like help with?"],
                "error": str(e)
            }
    
    def generate_llm_clarification(self, query: str, clarification_type: str, context: dict = None) -> dict:
        """Generate intelligent clarification using LLM"""
        if clarification_type == "ambiguous":
            possible_intents = context.get("possible_intents", [])
            reasoning = context.get("reasoning", "")
            
            prompt = f"""
            The user said: "{query}"
            
            I detected this could be related to multiple intents: {possible_intents}
            My reasoning: {reasoning}
            
            Generate a helpful clarifying question and specific actionable options to help the user clarify what they want to do.
            
            Available workflows:
            - calendar: Schedule meetings, events, check availability
            - task: Create tasks, set reminders, manage deadlines  
            - briefing: Get summaries, daily reports, status updates
            - chat: Ask questions, get help, general conversation
            
            Respond in JSON format:
            {{
                "message": "Friendly clarifying question that acknowledges the ambiguity",
                "explanation": "Brief explanation of why this is ambiguous",
                "options": [
                    {{
                        "action": "calendar",
                        "description": "Specific description of what this would do for their request",
                        "example": "Example of how this would work"
                    }},
                    {{
                        "action": "task", 
                        "description": "Specific description of what this would do for their request",
                        "example": "Example of how this would work"
                    }}
                ],
                "clarifying_questions": ["Specific question to help disambiguate"]
            }}
            """
        else:  # unknown
            prompt = f"""
            The user said: "{query}"
            
            I couldn't determine what they want to do. Generate a helpful response that:
            1. Acknowledges their request
            2. Explains what I can help with
            3. Provides specific options based on what they said
            
            Available workflows:
            - calendar: Schedule meetings, events, check availability
            - task: Create tasks, set reminders, manage deadlines
            - briefing: Get summaries, daily reports, status updates  
            - chat: Ask questions, get help, general conversation
            
            Respond in JSON format:
            {{
                "message": "Helpful message acknowledging their request",
                "explanation": "What I can help with generally",
                "options": [
                    {{
                        "action": "calendar",
                        "description": "How this might relate to their request",
                        "example": "Specific example"
                    }},
                    {{
                        "action": "task",
                        "description": "How this might relate to their request", 
                        "example": "Specific example"
                    }},
                    {{
                        "action": "briefing",
                        "description": "How this might relate to their request",
                        "example": "Specific example"
                    }},
                    {{
                        "action": "chat",
                        "description": "How this might relate to their request",
                        "example": "Specific example"
                    }}
                ],
                "suggestions": ["Specific ways they could rephrase their request"]
            }}
            """
        
        try:
            resp = self._get_llm_chat().invoke(prompt)
            
            # Parse LLM response - ensure we handle the response properly
            response_content = resp.content if hasattr(resp, 'content') else str(resp)
            try:
                llm_response = json.loads(response_content.strip())
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return self._fallback_clarification(query, clarification_type, context)
            
            # Structure the response
            clarification_response = {
                "workflow_type": "clarification",
                "clarification_type": clarification_type,
                "original_query": query,
                "message": llm_response.get("message", "I need clarification on what you'd like me to do."),
                "explanation": llm_response.get("explanation", ""),
                "options": llm_response.get("options", []),
                "llm_reasoning": llm_response.get("explanation", ""),
                "raw_llm_response": response_content
            }
            
            # Add type-specific fields
            if clarification_type == "ambiguous":
                clarification_response["possible_intents"] = context.get("possible_intents", []) if context else []
                clarification_response["clarifying_questions"] = llm_response.get("clarifying_questions", [])
            else:
                clarification_response["suggestions"] = llm_response.get("suggestions", [])
            
            return clarification_response
            
        except Exception as e:
            # Fallback to simple clarification if LLM fails
            return self._fallback_clarification(query, clarification_type, context, str(e))
    
    def _fallback_clarification(self, query: str, clarification_type: str, context: dict = None, error: str = None) -> dict:
        """Fallback clarification when LLM fails"""
        if clarification_type == "ambiguous":
            return {
                "workflow_type": "clarification",
                "clarification_type": "ambiguous",
                "original_query": query,
                "message": f"I see a few ways to help with '{query}'. What would you like me to do?",
                "explanation": "This request could be handled in multiple ways.",
                "options": [
                    {"action": "calendar", "description": "Schedule this as a meeting or event", "example": "Add to your calendar"},
                    {"action": "task", "description": "Create this as a task or reminder", "example": "Add to your task list"},
                ],
                "possible_intents": context.get("possible_intents", []) if context else [],
                "clarifying_questions": ["Would you like to schedule this or create a task?"],
                "fallback_reason": f"LLM clarification failed: {error}" if error else "Using fallback clarification"
            }
        else:
            return {
                "workflow_type": "clarification",
                "clarification_type": "unknown", 
                "original_query": query,
                "message": f"I'm not sure what you'd like me to help with regarding: '{query}'",
                "explanation": "I can help you with scheduling, tasks, briefings, or general questions.",
                "options": [
                    {"action": "calendar", "description": "Schedule meetings or events", "example": "Schedule a meeting"},
                    {"action": "task", "description": "Create and manage tasks", "example": "Create a reminder"},
                    {"action": "briefing", "description": "Get daily summaries", "example": "Show my daily briefing"},
                    {"action": "chat", "description": "Ask questions or get help", "example": "How does this work?"}
                ],
                "suggestions": ["Try being more specific about what you want to do"],
                "fallback_reason": f"LLM clarification failed: {error}" if error else "Using fallback clarification"
            }