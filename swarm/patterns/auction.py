from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult
from swarm.core.errors import PatternError


class AuctionPattern:
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if not agents:
            raise PatternError("AuctionPattern requires at least 1 agent")
        results = list(await asyncio.gather(*[a.run(task, ctx) for a in agents]))
        for r in results:
            ctx.add_result(r)
        winner = max(results, key=lambda r: r.confidence)
        return SwarmResult(
            pattern="auction",
            results=results,
            final_output=winner.content,
        )
