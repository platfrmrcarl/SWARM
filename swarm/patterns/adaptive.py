from __future__ import annotations
from swarm.core.protocols import Agent
from swarm.core.types import AgentResult, SwarmContext, SwarmResult


class AdaptivePattern:
    def __init__(self, threshold: float = 0.8, max_hops: int = 5) -> None:
        self.threshold = threshold
        self.max_hops = max_hops

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        agent_map = {a.name: a for a in agents}
        current = agents[0]
        result: AgentResult | None = None
        for _ in range(self.max_hops):
            result = await current.run(task, ctx)
            ctx.add_result(result)
            if result.confidence >= self.threshold:
                break
            if not result.next_agent or result.next_agent not in agent_map:
                break
            current = agent_map[result.next_agent]
        return SwarmResult(
            pattern="adaptive",
            results=list(ctx.results),
            final_output=result.content if result else "",
        )
