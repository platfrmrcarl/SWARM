from __future__ import annotations

import subprocess

from anthropic import AsyncAnthropic

from swarm.core.errors import ProviderError
from swarm.core.types import Message


class ClaudeProvider:
    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        api_key: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.auth_mode = "api_key" if api_key else "subscription"
        self._api_key = api_key

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if self.auth_mode == "subscription":
            return await self._complete_subscription(messages)
        return await self._complete_api(messages, temperature, max_tokens)

    async def _complete_subscription(self, messages: list[Message]) -> str:
        prompt = self._format_prompt(messages)
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ProviderError(f"claude CLI error: {result.stderr}")
        return result.stdout.strip()

    async def _complete_api(
        self,
        messages: list[Message],
        temperature: float | None,
        max_tokens: int | None,
    ) -> str:
        client = AsyncAnthropic(api_key=self._api_key)
        api_msgs = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role != "system"
        ]
        system = next((m.content for m in messages if m.role == "system"), None)
        kwargs: dict = dict(
            model=self.model,
            messages=api_msgs,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
        )
        if system:
            kwargs["system"] = system
        response = await client.messages.create(**kwargs)
        return response.content[0].text

    def _format_prompt(self, messages: list[Message]) -> str:
        parts = []
        for m in messages:
            if m.role == "system":
                parts.append(f"[System]: {m.content}")
            elif m.role == "user":
                parts.append(m.content)
            elif m.role == "assistant":
                parts.append(f"[Assistant]: {m.content}")
        return "\n\n".join(parts)
