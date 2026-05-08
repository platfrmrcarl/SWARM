from __future__ import annotations

import httpx

from swarm.core.errors import ProviderError
from swarm.core.types import Message


class OllamaProvider:
    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            },
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat", json=payload, timeout=120.0
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise ProviderError(f"Ollama error: {e}") from e
            except Exception as e:
                raise ProviderError(f"Ollama error: {e}") from e
        return response.json()["message"]["content"]
