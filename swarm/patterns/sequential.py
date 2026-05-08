from __future__ import annotations
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult


class SequentialPattern:
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        current = task
        for agent in agents:
            result = await agent.run(current, ctx)
            ctx.add_result(result)
            current = result.content
        return SwarmResult(
            pattern="sequential",
            results=list(ctx.results),
            final_output=current,
        )
