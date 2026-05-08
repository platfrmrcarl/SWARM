# tests/patterns/test_parallel.py
import pytest
from swarm.patterns.parallel import ParallelPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_parallel_runs_all_agents(ctx):
    agents = [FakeAgent(f"a{i}", response=f"r{i}") for i in range(3)]
    result = await ParallelPattern().execute(agents, "task", ctx)
    assert result.pattern == "parallel"
    assert len(result.results) == 3


async def test_parallel_concatenate_merge(ctx):
    agents = [FakeAgent("a1", response="foo"), FakeAgent("a2", response="bar")]
    result = await ParallelPattern(merge_strategy="concatenate").execute(
        agents, "task", ctx
    )
    assert "foo" in result.final_output
    assert "bar" in result.final_output


async def test_parallel_vote_merge_picks_majority(ctx):
    agents = [
        FakeAgent("a1", response="yes"),
        FakeAgent("a2", response="yes"),
        FakeAgent("a3", response="no"),
    ]
    result = await ParallelPattern(merge_strategy="vote").execute(agents, "task", ctx)
    assert result.final_output == "yes"


async def test_parallel_synthesize_merge(ctx):
    agents = [FakeAgent("a1", response="part1"), FakeAgent("a2", response="part2")]
    result = await ParallelPattern(merge_strategy="synthesize").execute(
        agents, "task", ctx
    )
    assert result.final_output == "1. part1\n\n2. part2"
