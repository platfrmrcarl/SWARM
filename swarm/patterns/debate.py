from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult
from swarm.core.errors import PatternError


class DebatePattern:
    def __init__(self, max_rounds: int = 3) -> None:
        self.max_rounds = max_rounds

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if len(agents) < 2:
            raise PatternError("DebatePattern requires at least 2 agents")

        responses: dict[str, str] = {}
        all_results = []
        last_round_results = []

        for round_idx in range(self.max_rounds):
            if round_idx == 0:
                round_results = list(
                    await asyncio.gather(*[a.run(task, ctx) for a in agents])
                )
            else:
                async def run_agent(agent: Agent) -> "AgentResult":  # type: ignore[name-defined]
                    others = "\n".join(
                        f"[{name}]: {resp}"
                        for name, resp in responses.items()
                        if name != agent.name
                    )
                    debate_task = (
                        task
                        + "\n\nOther agents said:\n"
                        + others
                        + "\n\nYour response:"
                    )
                    return await agent.run(debate_task, ctx)

                round_results = list(
                    await asyncio.gather(*[run_agent(a) for a in agents])
                )

            for r in round_results:
                ctx.add_result(r)
                all_results.append(r)
                responses[r.agent_name] = r.content

            last_round_results = round_results

            if len(set(responses.values())) == 1:
                break

        final_output = "\n".join(
            f"[{r.agent_name}]: {r.content}" for r in last_round_results
        )
        return SwarmResult(
            pattern="debate",
            results=all_results,
            final_output=final_output,
        )
