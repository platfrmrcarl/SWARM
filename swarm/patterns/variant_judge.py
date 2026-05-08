from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult
from swarm.core.errors import PatternError


class VariantJudgePattern:
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if len(agents) < 2:
            raise PatternError("VariantJudgePattern requires at least 2 agents (variants + judge)")
        *variants, judge = agents
        variant_results = list(
            await asyncio.gather(*[v.run(task, ctx) for v in variants])
        )
        for r in variant_results:
            ctx.add_result(r)
        judge_input = "\n\n".join(
            f"Variant {i+1} ({r.agent_name}): {r.content}"
            for i, r in enumerate(variant_results)
        )
        final = await judge.run(
            f"Evaluate these variants and pick the best:\n\n{judge_input}", ctx
        )
        ctx.add_result(final)
        return SwarmResult(
            pattern="variant_judge",
            results=[*variant_results, final],
            final_output=final.content,
        )
