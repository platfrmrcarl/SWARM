# tests/patterns/test_adaptive.py
import pytest
from swarm.patterns.adaptive import AdaptivePattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_adaptive_stops_when_confident(ctx):
    a1 = FakeAgent("a1", response="done", confidence=0.95)
    a2 = FakeAgent("a2", response="never reached")
    result = await AdaptivePattern(threshold=0.8).execute([a1, a2], "task", ctx)
    assert result.final_output == "done"


async def test_adaptive_routes_to_next_agent(ctx):
    a1 = FakeAgent("a1", response="partial", confidence=0.3, next_agent="a2")
    a2 = FakeAgent("a2", response="final", confidence=0.95)
    result = await AdaptivePattern(threshold=0.8).execute([a1, a2], "task", ctx)
    assert result.final_output == "final"


async def test_adaptive_stops_at_max_hops(ctx):
    agents = [FakeAgent(f"a{i}", response=f"r{i}", confidence=0.1, next_agent=f"a{i+1}")
              for i in range(10)]
    result = await AdaptivePattern(threshold=0.8, max_hops=3).execute(agents, "task", ctx)
    assert result.pattern == "adaptive"
