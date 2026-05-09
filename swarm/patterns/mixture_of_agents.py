from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult
from swarm.core.errors import PatternError


class MixtureOfAgentsPattern:
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if len(agents) < 2:
            raise PatternError(
                "MixtureOfAgentsPattern requires at least 2 agents (proposers + aggregator)"
            )
        proposers = agents[:-1]
        aggregator = agents[-1]

        proposals = list(await asyncio.gather(*[a.run(task, ctx) for a in proposers]))
        for r in proposals:
            ctx.add_result(r)

        agg_task = (
            task
            + "\n\nProposals:\n"
            + "\n".join(f"[{r.agent_name}]: {r.content}" for r in proposals)
        )
        agg_result = await aggregator.run(agg_task, ctx)
        ctx.add_result(agg_result)

        all_results = proposals + [agg_result]
        return SwarmResult(
            pattern="mixture_of_agents",
            results=all_results,
            final_output=agg_result.content,
        )
