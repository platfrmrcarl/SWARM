# tests/patterns/test_decentralized.py
import pytest
from swarm.patterns.decentralized import DecentralizedPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_decentralized_picks_highest_confidence(ctx):
    agents = [
        FakeAgent("a1", response="low", confidence=0.4),
        FakeAgent("a2", response="high", confidence=0.9),
        FakeAgent("a3", response="mid", confidence=0.6),
    ]
    result = await DecentralizedPattern().execute(agents, "task", ctx)
    assert result.final_output == "high"
    assert result.pattern == "decentralized"


async def test_decentralized_all_agents_run(ctx):
    agents = [FakeAgent(f"a{i}") for i in range(4)]
    result = await DecentralizedPattern().execute(agents, "task", ctx)
    assert len(result.results) == 4
