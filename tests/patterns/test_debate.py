import pytest
from swarm.patterns.debate import DebatePattern
from swarm.core.types import SwarmContext
from swarm.core.errors import PatternError
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_debate_requires_at_least_two_agents(ctx):
    with pytest.raises(PatternError):
        await DebatePattern().execute([FakeAgent("solo")], "task", ctx)


async def test_debate_returns_correct_pattern_name(ctx):
    agents = [FakeAgent("a1"), FakeAgent("a2")]
    result = await DebatePattern(max_rounds=1).execute(agents, "task", ctx)
    assert result.pattern == "debate"


async def test_debate_single_round(ctx):
    agents = [FakeAgent("a1", response="yes"), FakeAgent("a2", response="no")]
    result = await DebatePattern(max_rounds=1).execute(agents, "task", ctx)
    assert len(result.results) == 2


async def test_debate_runs_multiple_rounds(ctx):
    agents = [FakeAgent("a1", response="yes"), FakeAgent("a2", response="no")]
    result = await DebatePattern(max_rounds=3).execute(agents, "task", ctx)
    # 3 rounds * 2 agents = 6 results (no consensus since responses differ)
    assert len(result.results) == 6


async def test_debate_short_circuits_on_consensus(ctx):
    # Both agents always respond the same — consensus after round 0
    agents = [FakeAgent("a1", response="agree"), FakeAgent("a2", response="agree")]
    result = await DebatePattern(max_rounds=5).execute(agents, "task", ctx)
    # Only 1 round needed (2 results)
    assert len(result.results) == 2


async def test_debate_final_output_contains_agent_names(ctx):
    agents = [FakeAgent("alice", response="yes"), FakeAgent("bob", response="no")]
    result = await DebatePattern(max_rounds=1).execute(agents, "task", ctx)
    assert "[alice]:" in result.final_output
    assert "[bob]:" in result.final_output
