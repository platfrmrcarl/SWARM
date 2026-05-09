import pytest
from swarm.patterns.mixture_of_agents import MixtureOfAgentsPattern
from swarm.core.types import SwarmContext
from swarm.core.errors import PatternError
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_moa_requires_at_least_two_agents(ctx):
    with pytest.raises(PatternError):
        await MixtureOfAgentsPattern().execute([FakeAgent("solo")], "task", ctx)


async def test_moa_returns_correct_pattern_name(ctx):
    agents = [FakeAgent("p1", response="proposal1"), FakeAgent("agg", response="summary")]
    result = await MixtureOfAgentsPattern().execute(agents, "task", ctx)
    assert result.pattern == "mixture_of_agents"


async def test_moa_last_agent_is_aggregator(ctx):
    agents = [
        FakeAgent("p1", response="idea A"),
        FakeAgent("p2", response="idea B"),
        FakeAgent("agg", response="aggregated"),
    ]
    result = await MixtureOfAgentsPattern().execute(agents, "task", ctx)
    assert result.final_output == "aggregated"


async def test_moa_proposals_included_in_agg_task(ctx):
    received_tasks = []

    class CapturingAgent:
        name = "agg"

        async def run(self, task, ctx):
            received_tasks.append(task)
            from swarm.core.types import AgentResult
            return AgentResult(agent_name=self.name, content="done", confidence=1.0)

    agents = [
        FakeAgent("p1", response="proposal1"),
        CapturingAgent(),
    ]
    await MixtureOfAgentsPattern().execute(agents, "base task", ctx)
    assert "proposal1" in received_tasks[0]
    assert "[p1]:" in received_tasks[0]


async def test_moa_all_results_stored_in_ctx(ctx):
    agents = [
        FakeAgent("p1", response="r1"),
        FakeAgent("p2", response="r2"),
        FakeAgent("agg", response="final"),
    ]
    result = await MixtureOfAgentsPattern().execute(agents, "task", ctx)
    assert len(result.results) == 3
    assert len(ctx.results) == 3
