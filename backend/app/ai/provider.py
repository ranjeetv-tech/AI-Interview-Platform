import json
import httpx
from abc import ABC, abstractmethod
from app.core.config import settings

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str) -> str: ...

class OllamaProvider(LLMProvider):
    async def complete(self, prompt: str) -> str:
        url = settings.ollama_base_url.rstrip("/") + "/api/generate"
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(url, json={"model": settings.llm_model, "prompt": prompt, "stream": False, "format": "json"})
            r.raise_for_status()
            return r.json().get("response", "")

class OpenAICompatibleProvider(LLMProvider):
    async def complete(self, prompt: str) -> str:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        url = settings.openai_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        payload = {"model": settings.llm_model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "response_format": {"type": "json_object"}}
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

def get_provider() -> LLMProvider:
    return OpenAICompatibleProvider() if settings.llm_provider.lower() in {"openai", "openai-compatible"} else OllamaProvider()

def parse_json(raw: str) -> dict:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start:end+1])
        raise
