import json
from typing import List, Dict, Any, Optional, Type
import httpx
from pydantic import BaseModel
from app.ai.base import AIProvider
from app.core.config import settings
from app.core.logging import logger


class GeminiProvider(AIProvider):
    """
    Google Gemini API Provider (gemini-1.5-pro / gemini-1.5-flash).
    Direct REST integration via httpx.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Instruction: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
            
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                return candidates[0]["content"]["parts"][0]["text"]
            return ""

    async def generate_structured(self, prompt: str, schema_cls: Type[BaseModel], system_prompt: Optional[str] = None) -> BaseModel:
        json_prompt = f"{prompt}\n\nPlease output strict JSON formatted data conforming to schema."
        text = await self.generate_text(json_prompt, system_prompt=system_prompt, temperature=0.1)
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)
        return schema_cls.model_validate(data)

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Fallback to text embedding via Gemini embedding models if needed
        # or graceful fallback
        from app.ai.mock_provider import MockProvider
        return await MockProvider().generate_embeddings(texts)
