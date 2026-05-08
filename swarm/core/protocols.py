from __future__ import annotations
from typing import Any, Protocol, runtime_checkable
from swarm.core.types import AgentResult, Message, SwarmContext, SwarmResult


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str: ...


@runtime_checkable
class Agent(Protocol):
    name: str

    async def run(self, task: str, ctx: SwarmContext) -> AgentResult: ...


@runtime_checkable
class Pattern(Protocol):
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult: ...


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str

    async def __call__(self, **kwargs: Any) -> Any: ...
