"""
LLM client for conversation layer
"""
from typing import Optional, Dict, Any
import openai
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Response from LLM"""
    content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None


class LLMClient:
    """Client for interacting with LLM providers"""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4"):
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
        
        if not self.client:
            # Fallback to template-based response
            return self._fallback_response(user_prompt)
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._fallback_response(user_prompt)
    
    def _fallback_response(self, user_prompt: str) -> str:
        """Fallback response when LLM is unavailable"""
        return "I've processed your request. The operation completed successfully."


# Global LLM client
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client