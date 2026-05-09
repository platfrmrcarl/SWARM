from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult
from swarm.core.errors import PatternError


class TreeOfThoughtsPattern:
    def __init__(self, max_depth: int = 3, branching_factor: int = 2) -> None:
        self.max_depth = max_depth
        self.branching_factor = branching_factor

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if len(agents) < 2:
            raise PatternError(
                "TreeOfThoughtsPattern requires at least 2 agents (reasoners + validator)"
            )

        reasoners = agents[:-1]
        validator = agents[-1]

        thoughts = [task]
        all_results = []

        for _depth in range(self.max_depth):
            expansions = []
            for thought in thoughts:
                expansion_results = list(
                    await asyncio.gather(*[a.run(thought, ctx) for a in reasoners])
                )
                for r in expansion_results:
                    ctx.add_result(r)
                    all_results.append(r)
                    expansions.append(r)

            scored = []
            for exp in expansions:
                val_result = await validator.run(
                    f"Score this reasoning path: {exp.content}", ctx
                )
                ctx.add_result(val_result)
                all_results.append(val_result)
                scored.append((exp.content, val_result.confidence))

            scored.sort(key=lambda x: x[1], reverse=True)
            kept = scored[: self.branching_factor]
            thoughts = [content for content, _ in kept]

            if len(kept) == 1 and kept[0][1] >= 0.9:
                break

        final_output = thoughts[0] if thoughts else ""
        return SwarmResult(
            pattern="tree_of_thoughts",
            results=all_results,
            final_output=final_output,
        )
