# tests/patterns/test_broadcast.py
import pytest
from swarm.patterns.broadcast import BroadcastPattern
from swarm.core.types import SwarmContext
from swarm.core.errors import PatternError
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_broadcast_sends_to_all_agents(ctx):
    agents = [FakeAgent(f"a{i}", response=f"r{i}") for i in range(3)]
    result = await BroadcastPattern().execute(agents, "task", ctx)
    assert result.pattern == "broadcast"
    assert len(result.results) == 3


async def test_broadcast_combines_all_outputs(ctx):
    agents = [FakeAgent("a1", response="foo"), FakeAgent("a2", response="bar")]
    result = await BroadcastPattern().execute(agents, "task", ctx)
    assert "foo" in result.final_output
    assert "bar" in result.final_output


async def test_broadcast_requires_at_least_one_agent(ctx):
    with pytest.raises(PatternError):
        await BroadcastPattern().execute([], "task", ctx)
