"""
Dialog Intent Service - Enhanced intent classification with structured acts

Extends the existing intent service to return structured dialog acts
compatible with the universal dialog system.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from app.core.llm import get_llm_client
from .quick_reply_handler import get_quick_reply_handler

logger = logging.getLogger(__name__)


class DialogIntentService:
    """Enhanced intent service that returns structured dialog acts"""

    def __init__(self):
        self.llm = get_llm_client()
        self.quick_reply_handler = get_quick_reply_handler()

    async def classify_with_acts(
        self,
        user_query: str,
        conversation_context: Dict[str, Any],
        hot_state: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Classify intent and return structured dialog acts.

        Returns:
            {
                "acts": [
                    {
                        "type": "INVOKE|ASK|CANCEL|SWITCH",
                        "action": "delete_task",
                        "confidence": 0.86,
                        "params": {...},
                        "refs": {...}
                    }
                ],
                "meta": {
                    "cancel_signal": bool,
                    "switch_signal": bool,
                    "followup_freeform": str
                }
            }
        """

        try:
            # Check for quick reply patterns first
            quick_reply = self.quick_reply_handler.detect_quick_reply(user_query, hot_state)
            if quick_reply:
                return self._convert_quick_reply_to_acts(quick_reply)

            # Check for greetings and route to chat workflow with generate_response action
            if self._is_greeting(user_query):
                return {
                    "acts": [{
                        "type": "INVOKE",
                        "action": "generate_response",
                        "confidence": 0.95,
                        "params": {"message": user_query},
                        "refs": {}
                    }],
                    "meta": {
                        "cancel_signal": False,
                        "switch_signal": False,
                        "followup_freeform": "",
                        "greeting_detected": True
                    }
                }

            # Get conversation summary and recent turns
            summary = conversation_context.get("summary", "")
            history = conversation_context.get("history", [])[-8:]

            # Build context for LLM
            context_str = self._build_context_string(summary, history, hot_state)

            # Create LLM prompt for structured act generation
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(user_query, context_str)

            # Get LLM response
            response = await self.llm.generate_response(system_prompt, user_prompt)

            # Parse and validate the JSON response
            try:
                acts_data = json.loads(response)
                return self._validate_and_normalize_acts(acts_data)

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM acts response: {response}")
                return self._fallback_to_simple_intent(user_query, conversation_context)

        except Exception as e:
            logger.error(f"Dialog intent classification error: {e}")
            return self._fallback_to_simple_intent(user_query, conversation_context)

    def _convert_quick_reply_to_acts(self, quick_reply: Dict[str, Any]) -> Dict[str, Any]:
        """Convert quick reply detection result to dialog acts format"""

        quick_type = quick_reply["type"]
        quick_data = quick_reply["data"]

        if quick_type == "cancel":
            return {
                "acts": [{"type": "CANCEL", "target": "current"}],
                "meta": {"cancel_signal": True, "switch_signal": False, "followup_freeform": ""}
            }

        elif quick_type == "choice":
            return {
                "acts": [{
                    "type": "INVOKE",
                    "action": "select_choice",
                    "params": {"choice": quick_data},
                    "confidence": 0.95
                }],
                "meta": {"cancel_signal": False, "switch_signal": False, "followup_freeform": ""}
            }

        elif quick_type in ["confirm", "deny"]:
            return {
                "acts": [{
                    "type": "INVOKE",
                    "action": "respond_to_confirmation",
                    "params": {"confirmed": quick_data["confirmed"]},
                    "confidence": 0.9
                }],
                "meta": {"cancel_signal": False, "switch_signal": False, "followup_freeform": ""}
            }

        # Fallback
        return {
            "acts": [],
            "meta": {"cancel_signal": False, "switch_signal": False, "followup_freeform": ""}
        }

    def _is_greeting(self, user_query: str) -> bool:
        """Check if user query is a greeting"""
        from .greeting_service import get_greeting_service
        greeting_service = get_greeting_service()
        return greeting_service.is_greeting(user_query)


    def _build_context_string(
        self,
        summary: str,
        history: List[Dict[str, Any]],
        hot_state: Dict[str, Any] = None
    ) -> str:
        """Build context string for LLM prompt"""

        context_parts = []

        if summary:
            context_parts.append(f"CONVERSATION SUMMARY:\n{summary}")

        if history:
            context_parts.append("RECENT CONVERSATION:")
            for i, msg in enumerate(history):
                role = msg.get('role', 'user')
                content = msg.get('content', msg.get('message', ''))
                context_parts.append(f"{i+1}. {role}: {content}")

        if hot_state and hot_state.get("frame_stack"):
            context_parts.append("ACTIVE DIALOG FRAMES:")
            for frame in hot_state["frame_stack"]:
                workflow = frame.get("workflow", "unknown")
                action = frame.get("pending_action", "unknown")
                status = frame.get("status", "unknown")
                context_parts.append(f"- {workflow}: {action} (status: {status})")

                if frame.get("candidates"):
                    context_parts.append(f"  Candidates: {len(frame['candidates'])} options available")

        return "\n\n".join(context_parts) if context_parts else ""

    def _create_system_prompt(self) -> str:
        """Create system prompt for structured act generation"""

        return """You are a dialog controller for PulsePlan. Analyze user queries and return structured JSON with dialog acts.

The system supports these workflows: tasks, calendar, search, chat.

Dialog acts:
- INVOKE(action, params, refs): Execute an action (or propose it)
- ASK(question, choices): Ask user for clarification
- CANCEL(target): Cancel current or specific frame
- SWITCH(action, params): Context shift to new action

Common actions by workflow:
Tasks: create_task, delete_task, complete_task, schedule_task, list_tasks
Calendar: reschedule_day, block_time, list_events
Search: web_search, find_information
Chat: generate_response, casual_conversation

For entity references, use the "refs" field:
- task_query: {by_id, by_name, filters}
- date_query: {date, start_date, end_date}
- search_query: {query}

Examples:
"delete my lab assignment" →
{"acts":[{"type":"INVOKE","action":"delete_task","confidence":0.9,"refs":{"task_query":{"by_name":"lab assignment"}}}]}

"I found 3 tasks. Which one?" →
{"acts":[{"type":"ASK","question":"Which task?","choices":[...]}]}

"actually nevermind" →
{"acts":[{"type":"CANCEL","target":"current"}]}

Return only valid JSON. No extra text."""

    def _create_user_prompt(self, user_query: str, context: str) -> str:
        """Create user prompt with query and context"""

        prompt_parts = []

        if context:
            prompt_parts.append(f"CONTEXT:\n{context}")

        prompt_parts.append(f"USER QUERY: '{user_query}'")
        prompt_parts.append("Return JSON with dialog acts:")

        return "\n\n".join(prompt_parts)

    def _validate_and_normalize_acts(self, acts_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize the acts response from LLM"""

        # Ensure required structure
        if "acts" not in acts_data:
            acts_data["acts"] = []

        if "meta" not in acts_data:
            acts_data["meta"] = {
                "cancel_signal": False,
                "switch_signal": False,
                "followup_freeform": ""
            }

        # Validate each act
        normalized_acts = []
        for act in acts_data["acts"]:
            if not isinstance(act, dict) or "type" not in act:
                continue

            act_type = act["type"].upper()
            if act_type not in ["INVOKE", "ASK", "CANCEL", "SWITCH"]:
                continue

            # Normalize act structure
            normalized_act = {
                "type": act_type,
                "confidence": act.get("confidence", 1.0)
            }

            # Add type-specific fields
            if act_type == "INVOKE":
                normalized_act["action"] = act.get("action", "unknown")
                normalized_act["params"] = act.get("params", {})
                normalized_act["refs"] = act.get("refs", {})

            elif act_type == "ASK":
                normalized_act["question"] = act.get("question", "Need more information")
                normalized_act["choices"] = act.get("choices", [])

            elif act_type == "CANCEL":
                normalized_act["target"] = act.get("target", "current")

            elif act_type == "SWITCH":
                normalized_act["action"] = act.get("action", "unknown")
                normalized_act["params"] = act.get("params", {})

            normalized_acts.append(normalized_act)

        acts_data["acts"] = normalized_acts

        # Update meta signals based on acts
        for act in normalized_acts:
            if act["type"] == "CANCEL":
                acts_data["meta"]["cancel_signal"] = True
            elif act["type"] == "SWITCH":
                acts_data["meta"]["switch_signal"] = True

        return acts_data

    def _fallback_to_simple_intent(
        self,
        user_query: str,
        conversation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback to simple intent classification if LLM fails"""

        query_lower = user_query.lower().strip()

        # Enhanced pattern-based classification
        if any(word in query_lower for word in ['delete', 'remove', 'cancel']) and 'task' in query_lower:
            action = "delete_task"
            workflow = "tasks"
        elif any(word in query_lower for word in ['complete', 'done', 'finish']) and 'task' in query_lower:
            action = "complete_task"
            workflow = "tasks"
        elif any(word in query_lower for word in ['create', 'add', 'make', 'new']) and 'task' in query_lower:
            action = "create_task"
            workflow = "tasks"
        elif any(word in query_lower for word in ['list', 'show', 'view']) and any(word in query_lower for word in ['task', 'assignment']):
            action = "list_tasks"
            workflow = "tasks"
        elif any(word in query_lower for word in ['search', 'find', 'look']) and not 'task' in query_lower:
            action = "web_search"
            workflow = "search"
        elif any(word in query_lower for word in ['schedule', 'calendar', 'reschedule']):
            action = "reschedule_day"
            workflow = "calendar"
        else:
            action = "generate_response"
            workflow = "chat"

        # Extract potential entity references with better parsing
        refs = {}
        params = {}

        if workflow == "tasks":
            if action == "create_task":
                # Try to extract task title from natural language
                title = self._extract_task_title_from_query(user_query)
                if title:
                    params["title"] = title
                    refs["task_query"] = {"by_name": title}
                else:
                    refs["task_query"] = {"by_name": user_query}
            elif action == "delete_task":
                # Extract task name from deletion query
                task_name = self._extract_task_name_from_deletion_query(user_query)
                if task_name:
                    refs["task_query"] = {"by_name": task_name}
                else:
                    refs["task_query"] = {"by_name": user_query}
            elif action == "complete_task":
                # Extract task name from completion query
                task_name = self._extract_task_name_from_completion_query(user_query)
                if task_name:
                    refs["task_query"] = {"by_name": task_name}
                else:
                    refs["task_query"] = {"by_name": user_query}
            else:
                refs["task_query"] = {"by_name": user_query}
        elif workflow == "search":
            search_query = self._extract_search_query(user_query)
            refs["search_query"] = {"query": search_query}
            params["query"] = search_query

        # Add message for chat workflows
        if workflow == "chat":
            params["message"] = user_query

        return {
            "acts": [{
                "type": "INVOKE",
                "action": action,
                "confidence": 0.6,
                "params": params,
                "refs": refs
            }],
            "meta": {
                "cancel_signal": False,
                "switch_signal": False,
                "followup_freeform": "Generated by fallback classification"
            }
        }

    def _extract_task_title_from_query(self, query: str) -> Optional[str]:
        """Extract task title from natural language query"""
        import re

        query_lower = query.lower().strip()

        # Common patterns for task creation
        patterns = [
            r"create\s+(?:a\s+)?task\s+(?:called\s+)?['\"]([^'\"]+)['\"]",
            r"create\s+(?:a\s+)?task\s+(?:called\s+)?(.+?)(?:\s+for\s+|\s+due\s+|$)",
            r"add\s+(?:a\s+)?task\s+(?:called\s+)?['\"]([^'\"]+)['\"]",
            r"add\s+(?:a\s+)?task\s+(?:called\s+)?(.+?)(?:\s+for\s+|\s+due\s+|$)",
            r"make\s+(?:a\s+)?task\s+(?:called\s+)?['\"]([^'\"]+)['\"]",
            r"make\s+(?:a\s+)?task\s+(?:called\s+)?(.+?)(?:\s+for\s+|\s+due\s+|$)",
            r"new\s+task\s+['\"]([^'\"]+)['\"]",
            r"new\s+task\s+(.+?)(?:\s+for\s+|\s+due\s+|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                title = match.group(1).strip()
                # Clean up common words
                title = re.sub(r'^\s*called\s+', '', title)
                title = re.sub(r'^\s*to\s+', '', title)
                if len(title) > 2:  # Ensure it's not too short
                    return title

        return None

    def _extract_search_query(self, query: str) -> str:
        """Extract search query from natural language"""
        import re

        query_lower = query.lower().strip()

        # Common patterns for search
        patterns = [
            r"search\s+for\s+(.+)",
            r"find\s+(?:me\s+)?(.+)",
            r"look\s+(?:up\s+)?(.+)",
            r"can\s+you\s+(?:search\s+for\s+|find\s+)?(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                search_term = match.group(1).strip()
                if len(search_term) > 2:
                    return search_term

        # Fallback: return the original query
        return query

    def _extract_task_name_from_deletion_query(self, query: str) -> Optional[str]:
        """Extract task name from deletion query"""
        import re

        query_lower = query.lower().strip()

        # Common patterns for task deletion - improved to handle quoted task names
        patterns = [
            # Handle "delete the task 'add todo'" pattern
            r"delete\s+(?:the\s+)?task\s+['\"]([^'\"]+)['\"]",
            r"delete\s+(?:my\s+)?task\s+['\"]([^'\"]+)['\"]",
            r"delete\s+(?:the\s+)?task\s+(.+?)(?:\s*$|\s+please|\s+now)",
            r"delete\s+(?:my\s+)?task\s+(.+?)(?:\s*$|\s+please|\s+now)",
            r"remove\s+(?:the\s+)?task\s+['\"]([^'\"]+)['\"]",
            r"remove\s+(?:my\s+)?task\s+['\"]([^'\"]+)['\"]",
            r"remove\s+(?:the\s+)?task\s+(.+?)(?:\s*$|\s+please|\s+now)",
            r"remove\s+(?:my\s+)?task\s+(.+?)(?:\s*$|\s+please|\s+now)",
            r"delete\s+['\"]([^'\"]+)['\"]",
            r"remove\s+['\"]([^'\"]+)['\"]",
            r"delete\s+(.+?)(?:\s*$|\s+please|\s+now)",
            r"remove\s+(.+?)(?:\s*$|\s+please|\s+now)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                task_name = match.group(1).strip()
                # Clean up common words
                task_name = re.sub(r'^\s*my\s+', '', task_name)
                task_name = re.sub(r'^\s*the\s+', '', task_name)
                task_name = re.sub(r'^\s*task\s+', '', task_name)
                if len(task_name) > 1:  # Ensure it's not too short
                    return task_name

        return None

    def _extract_task_name_from_completion_query(self, query: str) -> Optional[str]:
        """Extract task name from completion query"""
        import re

        query_lower = query.lower().strip()

        # Common patterns for task completion
        patterns = [
            r"complete\s+(?:my\s+)?task\s+['\"]([^'\"]+)['\"]",
            r"complete\s+(?:my\s+)?task\s+(.+?)(?:\s*$|\s+please|\s+now)",
            r"mark\s+(?:my\s+)?task\s+['\"]([^'\"]+)['\"]\s+(?:as\s+)?(?:complete|done)",
            r"mark\s+(?:my\s+)?task\s+(.+?)\s+(?:as\s+)?(?:complete|done)",
            r"finish\s+(?:my\s+)?task\s+['\"]([^'\"]+)['\"]",
            r"finish\s+(?:my\s+)?task\s+(.+?)(?:\s*$|\s+please|\s+now)",
            r"(?:i\s+)?(?:finished|completed|done\s+with)\s+['\"]([^'\"]+)['\"]",
            r"(?:i\s+)?(?:finished|completed|done\s+with)\s+(.+?)(?:\s*$|\s+please|\s+now)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                task_name = match.group(1).strip()
                # Clean up common words
                task_name = re.sub(r'^\s*my\s+', '', task_name)
                task_name = re.sub(r'^\s*task\s+', '', task_name)
                if len(task_name) > 1:  # Ensure it's not too short
                    return task_name

        return None


# Global instance
_dialog_intent_service = DialogIntentService()


def get_dialog_intent_service() -> DialogIntentService:
    """Get the global dialog intent service instance"""
    return _dialog_intent_service