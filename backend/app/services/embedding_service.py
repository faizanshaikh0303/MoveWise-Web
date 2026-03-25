"""Cohere embedding service for RAG knowledge base."""
from typing import List, Optional
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Lazy-initialized wrapper around Cohere's embedding API (embed-english-v3.0, 1024 dims)."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not settings.COHERE_API_KEY:
                raise RuntimeError("COHERE_API_KEY is not configured")
            import cohere
            self._client = cohere.Client(settings.COHERE_API_KEY)
        return self._client

    def embed_text(self, text: str) -> Optional[List[float]]:
        """Embed a single string. Returns None if the service is unavailable."""
        try:
            client = self._get_client()
            response = client.embed(
                texts=[text],
                model="embed-english-v3.0",
                input_type="search_query",
            )
            return response.embeddings[0]
        except Exception as e:
            logger.error("EmbeddingService.embed_text failed: %s", e)
            return None

    def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Embed a batch of strings. Returns None if the service is unavailable."""
        try:
            client = self._get_client()
            response = client.embed(
                texts=texts,
                model="embed-english-v3.0",
                input_type="search_document",
            )
            return response.embeddings
        except Exception as e:
            logger.error("EmbeddingService.embed_texts failed: %s", e)
            return None


embedding_service = EmbeddingService()
