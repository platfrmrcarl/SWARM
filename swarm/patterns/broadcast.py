from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult
from swarm.core.errors import PatternError


class BroadcastPattern:
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if not agents:
            raise PatternError("BroadcastPattern requires at least 1 agent")
        results = list(await asyncio.gather(*[a.run(task, ctx) for a in agents]))
        for r in results:
            ctx.add_result(r)
        combined = "\n\n".join(r.content for r in results)
        return SwarmResult(pattern="broadcast", results=results, final_output=combined)
