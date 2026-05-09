from __future__ import annotations
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult


class BlackboardPattern:
    def __init__(self, max_rounds: int = 5) -> None:
        self.max_rounds = max_rounds

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        blackboard: dict[str, str] = {}
        ctx.state["blackboard"] = blackboard
        all_results = []

        for _round in range(self.max_rounds):
            prev_blackboard = dict(blackboard)

            for agent in agents:
                board_context = task + "\n\nBlackboard:\n" + str(blackboard)
                result = await agent.run(board_context, ctx)
                ctx.add_result(result)
                all_results.append(result)
                blackboard[agent.name] = result.content

            ctx.state["blackboard"] = blackboard

            if blackboard == prev_blackboard:
                break

        final_output = "\n".join(f"[{k}]: {v}" for k, v in blackboard.items())
        return SwarmResult(
            pattern="blackboard",
            results=all_results,
            final_output=final_output,
        )
