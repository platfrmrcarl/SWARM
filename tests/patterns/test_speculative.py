import pytest
from swarm.patterns.speculative import SpeculativePattern
from swarm.core.types import SwarmContext
from swarm.core.errors import PatternError
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_speculative_requires_exactly_two_agents(ctx):
    with pytest.raises(PatternError):
        await SpeculativePattern().execute([FakeAgent("solo")], "task", ctx)


async def test_speculative_requires_exactly_two_agents_not_three(ctx):
    agents = [FakeAgent("a"), FakeAgent("b"), FakeAgent("c")]
    with pytest.raises(PatternError):
        await SpeculativePattern().execute(agents, "task", ctx)


async def test_speculative_returns_correct_pattern_name(ctx):
    agents = [FakeAgent("spec", confidence=0.9), FakeAgent("actor")]
    result = await SpeculativePattern().execute(agents, "task", ctx)
    assert result.pattern == "speculative"


async def test_speculative_short_circuits_on_high_confidence(ctx):
    speculator = FakeAgent("spec", response="fast answer", confidence=0.95)
    actor = FakeAgent("actor", response="slow answer", confidence=1.0)
    result = await SpeculativePattern(threshold=0.8).execute(
        [speculator, actor], "task", ctx
    )
    assert result.final_output == "fast answer"
    assert len(result.results) == 1


async def test_speculative_falls_through_on_low_confidence(ctx):
    speculator = FakeAgent("spec", response="uncertain", confidence=0.5)
    actor = FakeAgent("actor", response="definitive", confidence=1.0)
    result = await SpeculativePattern(threshold=0.8).execute(
        [speculator, actor], "task", ctx
    )
    assert result.final_output == "definitive"
    assert len(result.results) == 2


async def test_speculative_ctx_contains_results(ctx):
    speculator = FakeAgent("spec", confidence=0.5)
    actor = FakeAgent("actor", confidence=1.0)
    await SpeculativePattern(threshold=0.8).execute([speculator, actor], "task", ctx)
    assert len(ctx.results) == 2


async def test_speculative_exact_threshold_boundary(ctx):
    # confidence == threshold should short-circuit (>=)
    speculator = FakeAgent("spec", response="boundary", confidence=0.8)
    actor = FakeAgent("actor", response="actor_answer", confidence=1.0)
    result = await SpeculativePattern(threshold=0.8).execute(
        [speculator, actor], "task", ctx
    )
    assert result.final_output == "boundary"
    assert len(result.results) == 1
