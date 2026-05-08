# tests/patterns/test_hierarchical.py
import pytest
from swarm.patterns.hierarchical import HierarchicalPattern
from swarm.core.types import AgentResult, SwarmContext
from swarm.core.errors import PatternError


class PlanningCoordinator:
    name = "coordinator"
    call_count = 0

    async def run(self, task, ctx):
        self.call_count += 1
        if self.call_count == 1:
            return AgentResult(agent_name="coordinator", content="1. subtask1\n2. subtask2")
        return AgentResult(agent_name="coordinator", content="synthesized")


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_hierarchical_calls_coordinator_twice(ctx):
    coord = PlanningCoordinator()
    from tests.conftest import FakeAgent
    w1 = FakeAgent("w1", response="worker1 result")
    w2 = FakeAgent("w2", response="worker2 result")
    result = await HierarchicalPattern().execute([coord, w1, w2], "big task", ctx)
    assert coord.call_count == 2
    assert result.final_output == "synthesized"
    assert result.pattern == "hierarchical"


async def test_hierarchical_requires_at_least_two_agents(ctx):
    from tests.conftest import FakeAgent
    with pytest.raises(PatternError):
        await HierarchicalPattern().execute([FakeAgent("solo")], "task", ctx)
