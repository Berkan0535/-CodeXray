import json
from typing import List, Dict, Any, Optional, Type
import httpx
from pydantic import BaseModel
from app.ai.base import AIProvider
from app.core.config import settings
from app.core.logging import logger


class OpenAIProvider(AIProvider):
    """
    OpenAI API Provider (GPT-4o, etc.).
    Uses raw httpx calls so no extra heavy SDK package lock is required.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.base_url = "https://api.openai.com/v1"

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def generate_structured(self, prompt: str, schema_cls: Type[BaseModel], system_prompt: Optional[str] = None) -> BaseModel:
        # Prompting for JSON output and validating with Pydantic
        json_prompt = f"{prompt}\n\nPlease respond strictly with a valid JSON object matching the requested schema."
        text = await self.generate_text(json_prompt, system_prompt=system_prompt, temperature=0.1)
        
        # Clean markdown codeblocks ```json ... ```
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)
        return schema_cls.model_validate(data)

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "text-embedding-3-small",
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url}/embeddings", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
