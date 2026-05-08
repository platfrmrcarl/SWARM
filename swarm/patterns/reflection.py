from __future__ import annotations
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult
from swarm.core.errors import PatternError


class ReflectionPattern:
    def __init__(self, max_iterations: int = 3) -> None:
        self.max_iterations = max_iterations

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if len(agents) < 2:
            raise PatternError("ReflectionPattern requires at least 2 agents (generator + critic)")
        generator, critic = agents[0], agents[1]
        draft = await generator.run(task, ctx)
        ctx.add_result(draft)
        for _ in range(self.max_iterations - 1):
            feedback = await critic.run(draft.content, ctx)
            ctx.add_result(feedback)
            draft = await generator.run(feedback.content, ctx)
            ctx.add_result(draft)
        return SwarmResult(
            pattern="reflection",
            results=list(ctx.results),
            final_output=draft.content,
        )
