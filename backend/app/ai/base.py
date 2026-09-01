from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class AIProvider(ABC):
    """Abstract base class for all AI LLM providers."""

    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> str:
        """Generate plain text completion."""
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, schema_cls: type[BaseModel], system_prompt: Optional[str] = None) -> BaseModel:
        """Generate structured response validated against a Pydantic schema."""
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for semantic search."""
        pass
