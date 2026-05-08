from __future__ import annotations

from swarm.core.errors import ProviderError
from swarm.core.types import Message


class LiteLLMProvider:
    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._kwargs = kwargs

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        try:
            import litellm
        except ImportError as e:
            raise ProviderError("litellm not installed. pip install swarm[litellm]") from e
        api_msgs = [{"role": m.role, "content": m.content} for m in messages]
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=api_msgs,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **self._kwargs,
            )
        except Exception as e:
            raise ProviderError(f"LiteLLM error: {e}") from e
        return response.choices[0].message.content
