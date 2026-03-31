"""Ollama local model integration service"""

import logging
from typing import Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama local models"""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.client = httpx.Client(timeout=60.0)

    async def check_health(self) -> bool:
        """Check if Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    def check_health_sync(self) -> bool:
        """Synchronous version of health check"""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def summarize(self, text: str, model: Optional[str] = None) -> Optional[str]:
        """
        Summarize text using Ollama

        Args:
            text: Text to summarize
            model: Model to use (defaults to configured model)

        Returns:
            Summary string or None if failed
        """
        model = model or self.model

        prompt = f"""Please summarize the following text in 2-3 sentences for a software engineer:

Text:
{text}

Summary:"""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "").strip()
                else:
                    logger.error(f"Ollama error: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None

    def summarize_sync(self, text: str, model: Optional[str] = None) -> Optional[str]:
        """Synchronous version of summarize"""
        model = model or self.model

        prompt = f"""Please summarize the following text in 2-3 sentences for a software engineer:

Text:
{text}

Summary:"""

        try:
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=120.0,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama error: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None

    async def extract_keywords(self, text: str, model: Optional[str] = None) -> list[str]:
        """
        Extract keywords from text using Ollama

        Args:
            text: Text to extract keywords from
            model: Model to use

        Returns:
            List of keywords
        """
        model = model or self.model

        prompt = f"""Extract 3-5 key technical terms or concepts from this text. Return only a comma-separated list.

Text:
{text}

Keywords:"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    keywords_str = result.get("response", "").strip()
                    return [k.strip() for k in keywords_str.split(",")]
                else:
                    return []
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []

    def extract_keywords_sync(self, text: str, model: Optional[str] = None) -> list[str]:
        """Synchronous version of extract_keywords"""
        model = model or self.model

        prompt = f"""Extract 3-5 key technical terms or concepts from this text. Return only a comma-separated list.

Text:
{text}

Keywords:"""

        try:
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=60.0,
            )

            if response.status_code == 200:
                result = response.json()
                keywords_str = result.get("response", "").strip()
                return [k.strip() for k in keywords_str.split(",")]
            else:
                return []
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []


# Global instance
ollama_service = OllamaService()
