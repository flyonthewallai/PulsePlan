"""
Embedding service for semantic memory.
Provides text-to-vector embeddings using OpenAI's API.
"""

import asyncio
import logging
from typing import List, Optional
import openai
from openai import AsyncOpenAI

from app.config.settings import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-small"  # 1536 dimensions, faster and cheaper
        self.max_tokens = 8191  # Max tokens for the embedding model
        
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text string.
        Returns a 1536-dimensional vector.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * 1536  # Return zero vector for empty text
            
        try:
            # Truncate text if too long
            if len(text.split()) > self.max_tokens:
                words = text.split()
                text = " ".join(words[:self.max_tokens])
                logger.warning(f"Truncated text to {self.max_tokens} tokens")
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            if len(embedding) != 1536:
                logger.error(f"Unexpected embedding dimension: {len(embedding)}")
                return [0.0] * 1536
                
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector on failure to avoid blocking the system
            return [0.0] * 1536
    
    async def embed_batch(self, texts: List[str], max_concurrent: int = 5) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in parallel.
        Uses semaphore to limit concurrent requests.
        """
        if not texts:
            return []
            
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def embed_with_semaphore(text: str) -> List[float]:
            async with semaphore:
                return await self.embed(text)
        
        try:
            embeddings = await asyncio.gather(*[
                embed_with_semaphore(text) for text in texts
            ])
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            # Return zero vectors for all texts on failure
            return [[0.0] * 1536 for _ in texts]
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate that an embedding has the correct format"""
        if not isinstance(embedding, list):
            return False
        if len(embedding) != 1536:
            return False
        if not all(isinstance(x, (int, float)) for x in embedding):
            return False
        return True
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
            
        try:
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {e}")
            return 0.0

# Global embedding service instance
embedding_service = EmbeddingService()

async def embed(text: str) -> List[float]:
    """Global function for generating embeddings"""
    return await embedding_service.embed(text)

async def embed_batch(texts: List[str]) -> List[List[float]]:
    """Global function for batch embedding generation"""
    return await embedding_service.embed_batch(texts)

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors (standalone function)"""
    return embedding_service.cosine_similarity(vec1, vec2)

def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance"""
    return embedding_service