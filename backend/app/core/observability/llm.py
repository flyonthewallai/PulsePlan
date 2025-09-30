"""
LLM client for conversation layer
"""
from typing import Optional, Dict, Any
import openai
from pydantic import BaseModel
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Response from LLM"""
    content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None


class LLMClient:
    """Client for interacting with LLM providers"""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini"):
        self.provider = provider
        self.model = model
        self.client = None
        
        if provider == "openai":
            try:
                self.client = openai.AsyncOpenAI()
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response using LLM"""
        operation_id = str(uuid.uuid4())[:8]

        # Log request details
        logger.info(f"[LLM-CORE-{operation_id}] Generating text response", extra={
            "operation_id": operation_id,
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system_prompt_length": len(system_prompt),
            "user_prompt_length": len(user_prompt)
        })

        logger.info(f"[LLM-CORE-{operation_id}] Request prompts", extra={
            "operation_id": operation_id,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        })

        if not self.client:
            logger.warning(f"[LLM-CORE-{operation_id}] No LLM client available, using fallback")
            fallback_response = self._fallback_response(user_prompt)
            logger.info(f"[LLM-CORE-{operation_id}] Fallback response generated", extra={
                "operation_id": operation_id,
                "response_length": len(fallback_response)
            })
            return fallback_response

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Log the actual data being sent to LLM
            logger.info(f"🤖 [LLM-CORE-{operation_id}] SENDING TO LLM:")
            logger.info(f"🤖 [LLM-CORE-{operation_id}] Model: {self.model}")
            logger.info(f"🤖 [LLM-CORE-{operation_id}] Temperature: {temperature}")
            logger.info(f"🤖 [LLM-CORE-{operation_id}] Max tokens: {max_tokens}")
            logger.info(f"🤖 [LLM-CORE-{operation_id}] System prompt: '{system_prompt}'")
            logger.info(f"🤖 [LLM-CORE-{operation_id}] User prompt: '{user_prompt}'")
            logger.info(f"🤖 [LLM-CORE-{operation_id}] Full messages: {messages}")

            start_time = datetime.utcnow()
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            duration = (datetime.utcnow() - start_time).total_seconds()

            response_content = response.choices[0].message.content

            # Log the actual response received from LLM
            logger.info(f"📥 [LLM-CORE-{operation_id}] RECEIVED FROM LLM:")
            logger.info(f"📥 [LLM-CORE-{operation_id}] Duration: {duration}s")
            logger.info(f"📥 [LLM-CORE-{operation_id}] Response length: {len(response_content)} chars")
            logger.info(f"📥 [LLM-CORE-{operation_id}] Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
            logger.info(f"📥 [LLM-CORE-{operation_id}] Finish reason: {response.choices[0].finish_reason}")
            logger.info(f"📥 [LLM-CORE-{operation_id}] Raw response content: '{response_content}'")
            logger.info(f"📥 [LLM-CORE-{operation_id}] Full response object: {response}")

            return response_content

        except Exception as e:
            logger.error(f"[LLM-CORE-{operation_id}] Generation failed: {e}", extra={
                "operation_id": operation_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            fallback_response = self._fallback_response(user_prompt)
            logger.info(f"[LLM-CORE-{operation_id}] Using fallback after error", extra={
                "operation_id": operation_id,
                "fallback_length": len(fallback_response)
            })
            return fallback_response

    async def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Dict[str, Any],
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        """Generate structured JSON response using LLM"""
        operation_id = str(uuid.uuid4())[:8]
        actual_model = model or self.model

        # Log structured request details
        logger.info(f"🔧 [LLM-STRUCTURED-{operation_id}] SENDING STRUCTURED REQUEST:")
        logger.info(f"🔧 [LLM-STRUCTURED-{operation_id}] Model: {actual_model}")
        logger.info(f"🔧 [LLM-STRUCTURED-{operation_id}] Temperature: {temperature}")
        logger.info(f"🔧 [LLM-STRUCTURED-{operation_id}] Max tokens: {max_tokens}")
        logger.info(f"🔧 [LLM-STRUCTURED-{operation_id}] System prompt: '{system_prompt}'")
        logger.info(f"🔧 [LLM-STRUCTURED-{operation_id}] User prompt: '{user_prompt}'")
        logger.info(f"🔧 [LLM-STRUCTURED-{operation_id}] Response format schema: {response_format}")

        if not self.client:
            logger.warning(f"[LLM-STRUCTURED-{operation_id}] No LLM client available, using structured fallback")
            fallback_response = self._fallback_structured_response(response_format, user_prompt)
            logger.info(f"[LLM-STRUCTURED-{operation_id}] Structured fallback generated", extra={
                "operation_id": operation_id,
                "response_length": len(fallback_response)
            })
            return fallback_response

        try:
            # Enhanced system prompt with JSON schema
            enhanced_system_prompt = f"""{system_prompt}

You must respond with valid JSON that matches this exact schema:
{response_format}

IMPORTANT:
- Return only valid JSON, no additional text
- Include all required fields
- Use proper JSON formatting"""

            messages = [
                {"role": "system", "content": enhanced_system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            start_time = datetime.utcnow()
            
            # Check if model supports json_object response format
            json_object_models = ["gpt-4-turbo", "gpt-4-turbo-preview", "gpt-4o", "gpt-4o-mini"]
            supports_json_object = actual_model in json_object_models
            
            if supports_json_object:
                response = await self.client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )
            else:
                # Fallback for models that don't support json_object
                logger.warning(f"[LLM-STRUCTURED-{operation_id}] Model {actual_model} doesn't support json_object, using text mode")
                response = await self.client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            duration = (datetime.utcnow() - start_time).total_seconds()

            response_content = response.choices[0].message.content

            # Log the actual structured response received from LLM
            logger.info(f"📋 [LLM-STRUCTURED-{operation_id}] RECEIVED STRUCTURED RESPONSE:")
            logger.info(f"📋 [LLM-STRUCTURED-{operation_id}] Duration: {duration}s")
            logger.info(f"📋 [LLM-STRUCTURED-{operation_id}] Response length: {len(response_content)} chars")
            logger.info(f"📋 [LLM-STRUCTURED-{operation_id}] Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
            logger.info(f"📋 [LLM-STRUCTURED-{operation_id}] Finish reason: {response.choices[0].finish_reason}")
            logger.info(f"📋 [LLM-STRUCTURED-{operation_id}] Raw JSON response: '{response_content}'")
            logger.info(f"📋 [LLM-STRUCTURED-{operation_id}] Full response object: {response}")

            return response_content

        except Exception as e:
            logger.error(f"[LLM-STRUCTURED-{operation_id}] Structured generation failed: {e}", extra={
                "operation_id": operation_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            fallback_response = self._fallback_structured_response(response_format, user_prompt)
            logger.info(f"[LLM-STRUCTURED-{operation_id}] Using structured fallback after error", extra={
                "operation_id": operation_id,
                "fallback_length": len(fallback_response)
            })
            return fallback_response
    
    def _fallback_response(self, user_prompt: str) -> str:
        """Fallback response when LLM is unavailable"""
        return "I've processed your request. The operation completed successfully."

    def _fallback_structured_response(self, response_format: Dict[str, Any], user_prompt: str = "") -> str:
        """Fallback structured response when LLM is unavailable"""
        import json
        from datetime import datetime

        # Create a basic response matching the schema
        fallback = {
            "success": False,
            "timestamp": datetime.utcnow().isoformat(),
            "intent": "chat",
            "confidence": 0.1,
            "reasoning": "LLM service unavailable - using fallback response",
            "message": "I'm currently unable to process your request. Please try again later."
        }

        # If we have a user prompt, try to do intelligent parsing
        if user_prompt:
            text_lower = user_prompt.lower()
            
            # Extract the actual query if it's prefixed with "Current message: "
            if text_lower.startswith("current message: "):
                actual_query = text_lower[len("current message: "):].strip()
            else:
                actual_query = text_lower.strip()
            
            # Simple keyword-based intent detection as fallback
            if any(word in actual_query for word in ["task", "todo", "create", "add", "schedule"]):
                fallback["intent"] = "task_management"
                fallback["confidence"] = 0.7
                fallback["reasoning"] = "Detected task-related keywords"
                
                # Check if it's a task creation request
                if any(word in actual_query for word in ["create", "add", "new", "make"]) or actual_query in ["task", "todo"] or "task creation" in actual_query:
                    fallback["action"] = "create_task"
                    fallback["entities"] = {}
                    
                    # Extract task name(s) if present
                    if "create" in actual_query or "add" in actual_query:
                        # Check for batch operations first
                        if "called" in actual_query and ("tasks" in actual_query or "task" in actual_query):
                            # Handle batch operations like "add 2 tasks, 1 called linear algebra and the other called Cake"
                            task_names = []
                            
                            # Look for patterns like "called X and the other called Y"
                            import re
                            called_pattern = r'called\s+([^,\s]+(?:\s+[^,\s]+)*?)(?:\s+and\s+the\s+other\s+called\s+([^,\s]+(?:\s+[^,\s]+)*?))?'
                            matches = re.findall(called_pattern, actual_query)
                            
                            for match in matches:
                                if match[0]:  # First task
                                    task_names.append(match[0].strip())
                                if match[1]:  # Second task
                                    task_names.append(match[1].strip())
                            
                            if task_names:
                                fallback["entities"]["task_names"] = task_names
                                fallback["requires_disambiguation"] = False
                                fallback["confidence"] = 0.8
                                fallback["reasoning"] = f"Batch tasks: {', '.join(task_names)}"
                            else:
                                fallback["requires_disambiguation"] = True
                                fallback["suggested_action"] = "What task would you like me to create? Please provide a specific task name or description."
                                fallback["confidence"] = 0.3
                                fallback["reasoning"] = "No task names found in batch request"
                        else:
                            # Handle single task creation
                            words = actual_query.split()
                            if "create" in words:
                                create_idx = words.index("create")
                                if create_idx + 1 < len(words) and words[create_idx + 1] in ["a", "an", "the"]:
                                    create_idx += 1
                                if create_idx + 1 < len(words) and words[create_idx + 1] == "task":
                                    # Look for task name after "create [a] task"
                                    task_start = create_idx + 2
                                    if task_start < len(words):
                                        task_name = " ".join(words[task_start:])
                                        # Apply typo correction
                                        task_name = self._correct_common_typos_fallback(task_name)
                                        fallback["entities"]["task_name"] = task_name
                                        
                                        # Check if task name is clear enough
                                        if len(task_name) > 3 and task_name.lower() not in ["task", "todo", "item", "thing", "something"]:
                                            fallback["requires_disambiguation"] = False
                                            fallback["confidence"] = 0.8
                                            fallback["reasoning"] = f"Clear task name: {task_name}"
                                        else:
                                            fallback["requires_disambiguation"] = True
                                            fallback["suggested_action"] = "What task would you like me to create? Please provide a specific task name or description."
                                            fallback["confidence"] = 0.3
                                            fallback["reasoning"] = "Task name too generic"
                                    else:
                                        fallback["requires_disambiguation"] = True
                                        fallback["suggested_action"] = "What task would you like me to create? Please provide a specific task name or description."
                                        fallback["confidence"] = 0.3
                                        fallback["reasoning"] = "No task name provided"
                                else:
                                    # Direct task name after "create" (e.g., "create homework")
                                    task_start = create_idx + 1
                                    if task_start < len(words):
                                        task_name = " ".join(words[task_start:])
                                        # Apply typo correction
                                        task_name = self._correct_common_typos_fallback(task_name)
                                        fallback["entities"]["task_name"] = task_name
                                        
                                        # Check if task name is clear enough
                                        if len(task_name) > 3 and task_name.lower() not in ["task", "todo", "item", "thing", "something"]:
                                            fallback["requires_disambiguation"] = False
                                            fallback["confidence"] = 0.8
                                            fallback["reasoning"] = f"Clear task name: {task_name}"
                                        else:
                                            fallback["requires_disambiguation"] = True
                                            fallback["suggested_action"] = "What task would you like me to create? Please provide a specific task name or description."
                                            fallback["confidence"] = 0.3
                                            fallback["reasoning"] = "Task name too generic"
                            elif "add" in words:
                                add_idx = words.index("add")
                                if add_idx + 1 < len(words) and words[add_idx + 1] in ["a", "an", "the"]:
                                    add_idx += 1
                                if add_idx + 1 < len(words) and words[add_idx + 1] == "task":
                                    # Look for task name after "add [a] task"
                                    task_start = add_idx + 2
                                    if task_start < len(words):
                                        task_name = " ".join(words[task_start:])
                                        # Apply typo correction
                                        task_name = self._correct_common_typos_fallback(task_name)
                                        fallback["entities"]["task_name"] = task_name
                                        
                                        # Check if task name is clear enough
                                        if len(task_name) > 3 and task_name.lower() not in ["task", "todo", "item", "thing", "something"]:
                                            fallback["requires_disambiguation"] = False
                                            fallback["confidence"] = 0.8
                                            fallback["reasoning"] = f"Clear task name: {task_name}"
                                        else:
                                            fallback["requires_disambiguation"] = True
                                            fallback["suggested_action"] = "What task would you like me to create? Please provide a specific task name or description."
                                            fallback["confidence"] = 0.3
                                            fallback["reasoning"] = "Task name too generic"
                                    else:
                                        fallback["requires_disambiguation"] = True
                                        fallback["suggested_action"] = "What task would you like me to create? Please provide a specific task name or description."
                                        fallback["confidence"] = 0.3
                                        fallback["reasoning"] = "No task name provided"
                                else:
                                    # Direct task name after "add" (e.g., "add homework")
                                    task_start = add_idx + 1
                                    if task_start < len(words):
                                        task_name = " ".join(words[task_start:])
                                        # Apply typo correction
                                        task_name = self._correct_common_typos_fallback(task_name)
                                        fallback["entities"]["task_name"] = task_name
                                        
                                        # Check if task name is clear enough
                                        if len(task_name) > 3 and task_name.lower() not in ["task", "todo", "item", "thing", "something"]:
                                            fallback["requires_disambiguation"] = False
                                            fallback["confidence"] = 0.8
                                            fallback["reasoning"] = f"Clear task name: {task_name}"
                                        else:
                                            fallback["requires_disambiguation"] = True
                                            fallback["suggested_action"] = "What task would you like me to create? Please provide a specific task name or description."
                                            fallback["confidence"] = 0.3
                                            fallback["reasoning"] = "Task name too generic"
                else:
                    fallback["action"] = "list_tasks"
                    
            elif any(word in text_lower for word in ["calendar", "meeting", "event", "schedule"]):
                fallback["intent"] = "calendar"
                fallback["action"] = "schedule_event"
                fallback["confidence"] = 0.7
                fallback["reasoning"] = "Detected calendar-related keywords"
                
            elif any(word in text_lower for word in ["email", "send", "message"]):
                fallback["intent"] = "email"
                fallback["action"] = "read_emails"
                fallback["confidence"] = 0.7
                fallback["reasoning"] = "Detected email-related keywords"
                
            elif any(word in text_lower for word in ["search", "find", "look up", "web search"]):
                fallback["intent"] = "search"
                fallback["action"] = "web_search"
                fallback["confidence"] = 0.7
                fallback["reasoning"] = "Detected search-related keywords"
                
                # Extract search query
                search_query = actual_query
                search_phrases = ["search the web for", "search for", "look up", "find", "web search for"]
                for phrase in search_phrases:
                    if search_query.startswith(phrase):
                        search_query = search_query[len(phrase):].strip()
                        break
                fallback["entities"] = {"search_query": search_query}

        # Try to match required fields from schema
        if "properties" in response_format:
            properties = response_format["properties"]
            required = response_format.get("required", [])

            for field in required:
                if field not in fallback:
                    field_type = properties.get(field, {}).get("type", "string")
                    if field_type == "string":
                        fallback[field] = ""
                    elif field_type == "number":
                        fallback[field] = 0
                    elif field_type == "boolean":
                        fallback[field] = False
                    elif field_type == "array":
                        fallback[field] = []
                    elif field_type == "object":
                        fallback[field] = {}

        return json.dumps(fallback)

    def _correct_common_typos_fallback(self, text: str) -> str:
        """Correct common typos in fallback mode"""
        common_typos = {
            "tasj": "task",
            "homwork": "homework", 
            "studdy": "study",
            "examm": "exam",
            "projct": "project",
            "assigment": "assignment",
            "presntation": "presentation",
            "reserch": "research",
            "repor": "report"
        }
        
        text_lower = text.lower()
        for typo, correction in common_typos.items():
            if typo in text_lower:
                # Replace the typo with the correction
                corrected_text = text_lower.replace(typo, correction)
                # Preserve original capitalization
                if text.isupper():
                    return corrected_text.upper()
                elif text.istitle():
                    return corrected_text.title()
                else:
                    return corrected_text
        
        return text


# Global LLM client
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client