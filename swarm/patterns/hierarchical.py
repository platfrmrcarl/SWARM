from __future__ import annotations
import asyncio
import re
from swarm.core.protocols import Agent
from swarm.core.types import AgentResult, SwarmContext, SwarmResult
from swarm.core.errors import PatternError


def _parse_subtasks(plan: str, n_workers: int) -> list[str]:
    lines = [l.strip() for l in plan.splitlines() if l.strip()]
    numbered = [re.sub(r"^\d+[\.\)]\s*", "", l) for l in lines
                if re.match(r"^\d+[\.\)]", l)]
    subtasks = numbered if numbered else lines
    if len(subtasks) < n_workers:
        subtasks = subtasks + [plan] * (n_workers - len(subtasks))
    return subtasks[:n_workers]


def _synthesize_prompt(results: list[AgentResult]) -> str:
    parts = "\n\n".join(f"Worker {i+1}: {r.content}" for i, r in enumerate(results))
    return f"Synthesize these results into a final answer:\n\n{parts}"


class HierarchicalPattern:
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if len(agents) < 2:
            raise PatternError("HierarchicalPattern requires at least 2 agents (coordinator + 1 worker)")
        coordinator, *workers = agents
        plan = await coordinator.run(task, ctx)
        ctx.add_result(plan)
        subtasks = _parse_subtasks(plan.content, len(workers))
        worker_results = list(
            await asyncio.gather(*[w.run(s, ctx) for w, s in zip(workers, subtasks)])
        )
        for r in worker_results:
            ctx.add_result(r)
        final = await coordinator.run(_synthesize_prompt(worker_results), ctx)
        ctx.add_result(final)
        return SwarmResult(
            pattern="hierarchical",
            results=[plan, *worker_results, final],
            final_output=final.content,
        )
