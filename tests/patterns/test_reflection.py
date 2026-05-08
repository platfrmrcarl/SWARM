# tests/patterns/test_reflection.py
import pytest
from swarm.patterns.reflection import ReflectionPattern
from swarm.core.types import SwarmContext
from swarm.core.errors import PatternError
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_reflection_requires_two_agents(ctx):
    with pytest.raises(PatternError):
        await ReflectionPattern().execute([FakeAgent("solo")], "task", ctx)


async def test_reflection_runs_generator_and_critic(ctx):
    generator = FakeAgent("gen", response="draft")
    critic = FakeAgent("critic", response="feedback")
    result = await ReflectionPattern(max_iterations=2).execute(
        [generator, critic], "task", ctx
    )
    assert result.pattern == "reflection"
    assert result.final_output == "draft"


async def test_reflection_iterates_max_times(ctx):
    generator = FakeAgent("gen", response="draft")
    critic = FakeAgent("critic", response="feedback")
    result = await ReflectionPattern(max_iterations=3).execute(
        [generator, critic], "task", ctx
    )
    # 1 initial draft + (max_iterations-1) * (critic + generator) results stored
    assert len(ctx.results) == 1 + (3 - 1) * 2
