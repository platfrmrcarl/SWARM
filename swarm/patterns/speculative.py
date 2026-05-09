from __future__ import annotations
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult
from swarm.core.errors import PatternError


class SpeculativePattern:
    def __init__(self, threshold: float = 0.8) -> None:
        self.threshold = threshold

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if len(agents) != 2:
            raise PatternError(
                "SpeculativePattern requires exactly 2 agents (speculator + actor)"
            )
        speculator, actor = agents

        spec_result = await speculator.run(task, ctx)
        ctx.add_result(spec_result)

        if spec_result.confidence >= self.threshold:
            return SwarmResult(
                pattern="speculative",
                results=[spec_result],
                final_output=spec_result.content,
            )

        actor_result = await actor.run(task, ctx)
        ctx.add_result(actor_result)
        return SwarmResult(
            pattern="speculative",
            results=[spec_result, actor_result],
            final_output=actor_result.content,
        )
