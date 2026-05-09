import pytest
from swarm.patterns.blackboard import BlackboardPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_blackboard_returns_correct_pattern_name(ctx):
    agents = [FakeAgent("a1", response="r1")]
    result = await BlackboardPattern(max_rounds=1).execute(agents, "task", ctx)
    assert result.pattern == "blackboard"


async def test_blackboard_single_agent_single_round(ctx):
    agents = [FakeAgent("a1", response="contribution")]
    result = await BlackboardPattern(max_rounds=1).execute(agents, "task", ctx)
    assert "contribution" in result.final_output
    assert "[a1]:" in result.final_output


async def test_blackboard_state_stored_in_ctx(ctx):
    agents = [FakeAgent("a1", response="data")]
    await BlackboardPattern(max_rounds=1).execute(agents, "task", ctx)
    assert "blackboard" in ctx.state
    assert ctx.state["blackboard"]["a1"] == "data"


async def test_blackboard_multiple_agents(ctx):
    agents = [FakeAgent("a1", response="r1"), FakeAgent("a2", response="r2")]
    result = await BlackboardPattern(max_rounds=1).execute(agents, "task", ctx)
    assert "[a1]:" in result.final_output
    assert "[a2]:" in result.final_output
    assert len(result.results) == 2


async def test_blackboard_runs_multiple_rounds(ctx):
    call_count = [0]

    class CountingAgent:
        name = "counter"

        async def run(self, task, ctx):
            call_count[0] += 1
            from swarm.core.types import AgentResult
            # Change response each call to prevent stability termination
            return AgentResult(
                agent_name=self.name,
                content=f"result_{call_count[0]}",
                confidence=1.0,
            )

    await BlackboardPattern(max_rounds=3).execute([CountingAgent()], "task", ctx)
    assert call_count[0] == 3


async def test_blackboard_stops_on_stability(ctx):
    # Agent always returns same response -> blackboard stabilizes after round 1 when
    # round 2 produces same blackboard as round 1 (prev == current)
    call_count = [0]

    class StableAgent:
        name = "stable"

        async def run(self, task, ctx):
            call_count[0] += 1
            from swarm.core.types import AgentResult
            return AgentResult(agent_name=self.name, content="same", confidence=1.0)

    await BlackboardPattern(max_rounds=10).execute([StableAgent()], "task", ctx)
    # Round 1: blackboard={} -> {"stable": "same"}, prev was {} -> no early stop
    # Round 2: prev={"stable": "same"}, after={"stable": "same"} -> stop
    assert call_count[0] == 2


async def test_blackboard_all_results_in_ctx(ctx):
    agents = [FakeAgent("a1", response="r1"), FakeAgent("a2", response="r2")]
    result = await BlackboardPattern(max_rounds=2).execute(agents, "task", ctx)
    assert len(ctx.results) == len(result.results)
