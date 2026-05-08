from __future__ import annotations
from swarm.core.protocols import LLMProvider
from swarm.core.types import AgentResult, Message, SwarmContext


class LLMAgent:
    def __init__(
        self,
        name: str,
        provider: LLMProvider,
        system_prompt: str = "",
        context_window: int = 20,
        **metadata,
    ) -> None:
        self.name = name
        self._provider = provider
        self._system_prompt = system_prompt
        self._context_window = context_window
        self._metadata = metadata

    async def run(self, task: str, ctx: SwarmContext) -> AgentResult:
        messages: list[Message] = []
        if self._system_prompt:
            messages.append(Message(role="system", content=self._system_prompt))
        if self._context_window > 0:
            messages.extend(ctx.history[-self._context_window :])
        messages.append(Message(role="user", content=task))
        response = await self._provider.complete(messages)
        ctx.history.append(Message(role="user", content=task))
        ctx.history.append(Message(role="assistant", content=response))
        return AgentResult(agent_name=self.name, content=response)
