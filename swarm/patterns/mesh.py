from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import AgentResult, SwarmContext, SwarmResult


def _converged(results: list[AgentResult]) -> bool:
    contents = [r.content for r in results]
    return len(set(contents)) == 1


class MeshPattern:
    def __init__(self, max_rounds: int = 5) -> None:
        self.max_rounds = max_rounds

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        results: list[AgentResult] = []
        for _ in range(self.max_rounds):
            results = list(await asyncio.gather(*[a.run(task, ctx) for a in agents]))
            ctx.state["mesh_round"] = results
            if _converged(results):
                break
        for r in results:
            ctx.add_result(r)
        final = "\n\n".join(r.content for r in results)
        return SwarmResult(pattern="mesh", results=results, final_output=final)
