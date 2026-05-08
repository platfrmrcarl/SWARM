import pytest
from swarm.patterns.sequential import SequentialPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_sequential_chains_output_to_input(ctx):
    a1 = FakeAgent("a1", response="step1")
    a2 = FakeAgent("a2", response="step2")
    a3 = FakeAgent("a3", response="step3")
    pattern = SequentialPattern()
    result = await pattern.execute([a1, a2, a3], "start", ctx)
    assert result.final_output == "step3"
    assert result.pattern == "sequential"
    assert len(result.results) == 3


async def test_sequential_single_agent(ctx):
    a = FakeAgent("solo", response="done")
    result = await SequentialPattern().execute([a], "go", ctx)
    assert result.final_output == "done"
    assert len(result.results) == 1


async def test_sequential_adds_results_to_ctx(ctx):
    agents = [FakeAgent(f"a{i}", response=f"r{i}") for i in range(3)]
    await SequentialPattern().execute(agents, "task", ctx)
    assert len(ctx.results) == 3
