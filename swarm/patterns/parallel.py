from __future__ import annotations
import asyncio
from collections import Counter
from swarm.core.protocols import Agent
from swarm.core.types import AgentResult, SwarmContext, SwarmResult


def _merge(results: list[AgentResult], strategy: str) -> str:
    if strategy == "vote":
        if not results:
            return ""
        counts = Counter(r.content for r in results)
        return counts.most_common(1)[0][0]
    if strategy == "synthesize":
        return "\n\n".join(f"{i+1}. {r.content}" for i, r in enumerate(results))
    if strategy == "concatenate":
        return "\n\n".join(r.content for r in results)
    raise ValueError(f"Unknown merge strategy: {strategy!r}")


class ParallelPattern:
    def __init__(self, merge_strategy: str = "concatenate") -> None:
        self.merge_strategy = merge_strategy

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        results = list(await asyncio.gather(*[a.run(task, ctx) for a in agents]))
        for r in results:
            ctx.add_result(r)
        merged = _merge(results, self.merge_strategy)
        return SwarmResult(pattern="parallel", results=results, final_output=merged)
