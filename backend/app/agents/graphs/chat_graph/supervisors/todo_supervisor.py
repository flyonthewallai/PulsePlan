"""
Todo Workflow Supervisor Agent
Handles todo operations with LLM proposal + Policy enforcement + Multi-turn conversations
"""
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime, timedelta

from .base import (
    BaseWorkflowSupervisor, 
    WorkflowPolicyValidator, 
    LLMProposal, 
    SupervisionResult
)


class TodoPolicyValidator(WorkflowPolicyValidator):
    """Deterministic policy validation for todo operations"""
    
    OPERATION_REQUIREMENTS = {
        "create": ["title"],
        "update": ["todo_id"],
        "delete": ["todo_id"], 
        "get": ["todo_id"],
        "list": [],  # No required fields for listing
        "bulk_toggle": ["todo_ids"],
        "convert_to_task": ["todo_id"]
    }
    
    ALLOWED_VALUES = {
        "priority": ["low", "medium", "high"],
        "status": ["pending", "in_progress", "completed", "cancelled"],
        "operation_type": list(OPERATION_REQUIREMENTS.keys())
    }
    
    def get_required_fields(self, operation_type: str) -> List[str]:
        """Return required fields for todo operations"""
        return self.OPERATION_REQUIREMENTS.get(operation_type, [])
    
    def get_allowed_values(self, field_name: str) -> List[Any]:
        """Return allowed values for todo fields"""
        return self.ALLOWED_VALUES.get(field_name, [])
    
    def validate_permissions(self, operation_type: str, context: Dict[str, Any]) -> List[str]:
        """Check user permissions for todo operations"""
        errors = []
        
        # Basic authentication check
        if not context.get("user_id"):
            errors.append("User authentication required")
        
        # Todo operations are generally allowed for authenticated users
        # Add specific permission checks here if needed
        
        return errors


class TodoSupervisorAgent(BaseWorkflowSupervisor):
    """Supervisor agent for todo workflow with multi-turn conversation support"""
    
    def __init__(self):
        policy_validator = TodoPolicyValidator()
        super().__init__("todo", policy_validator)
    
    async def _build_llm_prompt(
        self, 
        query: str, 
        context: Dict[str, Any], 
        conversation_context: str
    ) -> str:
        """Build todo-specific LLM prompt"""
        
        current_date = datetime.utcnow().isoformat()[:10]  # YYYY-MM-DD format
        
        # Extract comprehensive context if available
        user_profile = context.get("user_context", "")
        memory_context = context.get("memory_context", "")
        system_context = context.get("system_context", "")
        
        # Build the prompt in parts to avoid f-string issues
        tomorrow_date = datetime.strftime(datetime.utcnow() + timedelta(days=1), '%Y-%m-%d')
        
        context_part = system_context if system_context else f"USER CONTEXT: {json.dumps(context, indent=2)}"
        conversation_part = f"CONVERSATION HISTORY:\n{conversation_context}" if conversation_context else ""
        memory_part = f"RELEVANT MEMORIES:\n{memory_context}" if memory_context else ""
        
        # Use string formatting to avoid f-string issues with complex JSON
        prompt_template = """
You are a Todo Workflow Supervisor. Analyze the user's request and propose the appropriate todo operation.

CURRENT DATE: {current_date}

USER REQUEST: "{query}"

COMPREHENSIVE CONTEXT:
{context_part}

{conversation_part}

{memory_part}

AVAILABLE OPERATIONS:
- create: Create new todo (requires: title, optional: description, priority, due_date, tags)
- update: Update existing todo (requires: todo_id, optional: any updateable fields)
- delete: Delete todo (requires: todo_id)  
- get: Get specific todo (requires: todo_id)
- list: List todos (optional: filters like completed, priority, tags)
- bulk_toggle: Toggle completion status for multiple todos (requires: todo_ids, optional: completed)
- convert_to_task: Convert todo to full task (requires: todo_id)

PARAMETER EXTRACTION GUIDELINES:
1. TITLE: Extract the main action/item from natural language
   - "buy groceries" → title: "buy groceries"
   - "call mom tomorrow" → title: "call mom"
   - "add homework" → title: "homework"

2. PRIORITY: Infer from language intensity
   - "urgent", "asap", "important" → "high"
   - "when I can", "eventually", "maybe" → "low"  
   - default → "medium"

3. DUE_DATE: Parse relative and absolute dates
   - "tomorrow" → {current_date + 1 day}
   - "next week" → {current_date + 7 days}
   - "Friday" → {next Friday date}
   - "January 15" → "2024-01-15" (if reasonable year)

4. TAGS: Infer from context
   - "work meeting" → tags: ["work"]
   - "grocery shopping" → tags: ["shopping", "personal"]
   - "homework assignment" → tags: ["school", "homework"]

5. DESCRIPTION: Extract additional context
   - "call mom about dinner plans" → title: "call mom", description: "about dinner plans"

RESPONSE FORMAT (JSON):
{{
    "operation_type": "create|update|delete|get|list|bulk_toggle|convert_to_task",
    "parameters": {{
        "title": "extracted title",
        "description": "optional description",
        "priority": "low|medium|high",
        "due_date": "YYYY-MM-DD or null",
        "tags": ["tag1", "tag2"],
        "todo_id": "required for update/delete/get operations",
        "todo_ids": ["id1", "id2"], 
        "completed": true/false,
        "filters": {{"completed": true, "priority": "high"}}
    }},
    "confidence": 0.85,
    "reasoning": "Brief explanation of your analysis",
    "missing_context": ["field1", "field2"],
    "clarification_suggestion": "What specific todo would you like me to add?"
}}

EXAMPLES:

Input: "add todo"
Output: {{
    "operation_type": "create",
    "parameters": {{}},
    "confidence": 0.2,
    "reasoning": "User wants to create todo but didn't specify what",
    "missing_context": ["title"],
    "clarification_suggestion": "What would you like to add to your todo list?"
}}

Input: "add buy milk to my todos"
Output: {{
    "operation_type": "create", 
    "parameters": {{"title": "buy milk", "tags": ["shopping"]}},
    "confidence": 0.95,
    "reasoning": "Clear todo creation request with specific item",
    "missing_context": [],
    "clarification_suggestion": null
}}

Input: "remind me to call mom tomorrow"
Output: {{
    "operation_type": "create",
    "parameters": {{
        "title": "call mom",
        "due_date": "{tomorrow_date}",
        "tags": ["personal"]
    }},
    "confidence": 0.9,
    "reasoning": "Todo creation with relative due date",
    "missing_context": [],
    "clarification_suggestion": null
}}

Input: "show me my high priority todos"
Output: {{
    "operation_type": "list",
    "parameters": {{"filters": {{"priority": "high"}}}},
    "confidence": 0.9,
    "reasoning": "List todos with priority filter",
    "missing_context": [],
    "clarification_suggestion": null
}}

Analyze the user's request and respond with the JSON structure.
"""
        
        prompt = prompt_template.format(
            current_date=current_date,
            query=query,
            context_part=context_part,
            conversation_part=conversation_part,
            memory_part=memory_part,
            tomorrow_date=tomorrow_date
        )
        return prompt
    
    async def _parse_llm_response(self, response_content: str) -> LLMProposal:
        """Parse LLM response into LLMProposal"""
        try:
            # Clean response and parse JSON
            cleaned_response = response_content.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:-3].strip()
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:-3].strip()
            
            data = json.loads(cleaned_response)
            
            return LLMProposal(
                operation_type=data.get("operation_type", "unknown"),
                parameters=data.get("parameters", {}),
                confidence=float(data.get("confidence", 0.0)),
                reasoning=data.get("reasoning", "No reasoning provided"),
                missing_context=data.get("missing_context", []),
                clarification_suggestion=data.get("clarification_suggestion")
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback parsing
            return LLMProposal(
                operation_type="unknown",
                parameters={},
                confidence=0.0,
                reasoning=f"Failed to parse LLM response: {e}",
                missing_context=["operation_type"],
                clarification_suggestion="I had trouble understanding your request. Could you please rephrase it?"
            )
    
    async def handle_multi_turn_conversation(
        self, 
        initial_query: str,
        user_id: str,
        max_turns: int = 5
    ) -> SupervisionResult:
        """Handle complete multi-turn conversation until ready to execute"""
        
        conversation_id = str(uuid.uuid4())
        context = {"user_id": user_id}
        current_query = initial_query
        turn_count = 0
        
        while turn_count < max_turns:
            # Get supervision result
            result = await self.supervise(current_query, context, conversation_id)
            
            # Update conversation history
            self.update_conversation(
                conversation_id, 
                current_query, 
                result.clarification_message or "Processing..."
            )
            
            # If ready to execute or hit max turns, return result
            if result.ready_to_execute or turn_count >= max_turns - 1:
                return result
            
            # In a real implementation, this would wait for user input
            # For now, we'll simulate or return the clarification request
            if result.clarification_message:
                # This would be handled by the orchestrator in practice
                result.conversation_id = conversation_id
                return result
            
            turn_count += 1
        
        # Max turns reached without resolution
        return SupervisionResult(
            operation_type="unknown",
            parameters={},
            ready_to_execute=False,
            clarification_message="I couldn't gather enough information after several attempts. Please provide a more detailed request.",
            missing_context=["complete_request"],
            confidence=0.0,
            conversation_id=conversation_id
        )
    
    def get_operation_examples(self) -> Dict[str, List[str]]:
        """Get example queries for each operation type"""
        return {
            "create": [
                "add buy milk to my todos",
                "remind me to call mom tomorrow", 
                "create urgent todo for project deadline",
                "add homework assignment for Friday"
            ],
            "update": [
                "mark my grocery todo as done",
                "change priority of homework to high",
                "update due date for call mom todo"
            ],
            "delete": [
                "delete the milk todo",
                "remove my homework todo"
            ],
            "list": [
                "show my todos",
                "list high priority todos",
                "show completed todos from today",
                "what are my pending todos?"
            ],
            "bulk_toggle": [
                "mark all shopping todos as done",
                "complete all high priority todos"
            ]
        }