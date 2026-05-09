import pytest
from swarm.patterns.tree_of_thoughts import TreeOfThoughtsPattern
from swarm.core.types import SwarmContext, AgentResult
from swarm.core.errors import PatternError
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_tot_requires_at_least_two_agents(ctx):
    with pytest.raises(PatternError):
        await TreeOfThoughtsPattern().execute([FakeAgent("solo")], "task", ctx)


async def test_tot_returns_correct_pattern_name(ctx):
    reasoner = FakeAgent("r1", response="thought")
    validator = FakeAgent("val", response="ok", confidence=0.9)
    result = await TreeOfThoughtsPattern(max_depth=1, branching_factor=1).execute(
        [reasoner, validator], "task", ctx
    )
    assert result.pattern == "tree_of_thoughts"


async def test_tot_last_agent_is_validator(ctx):
    reasoner = FakeAgent("r1", response="my thought")
    validator = FakeAgent("val", response="score", confidence=0.95)
    result = await TreeOfThoughtsPattern(max_depth=1, branching_factor=1).execute(
        [reasoner, validator], "task", ctx
    )
    # With confidence >= 0.9 and branching_factor=1 -> early stop after depth 1
    assert result.final_output == "my thought"


async def test_tot_early_stop_on_high_confidence(ctx):
    reasoner = FakeAgent("r1", response="best thought")
    validator = FakeAgent("val", response="great", confidence=0.95)
    result = await TreeOfThoughtsPattern(max_depth=5, branching_factor=1).execute(
        [reasoner, validator], "task", ctx
    )
    # Should stop after depth 1 due to high confidence
    # depth 1: 1 reasoner result + 1 validator result = 2 total
    assert len(result.results) == 2


async def test_tot_keeps_top_branching_factor_thoughts(ctx):
    # Two reasoners, validator scores them — we keep top branching_factor=1
    r1 = FakeAgent("r1", response="thought_a")
    r2 = FakeAgent("r2", response="thought_b")

    call_count = [0]

    class ScoringValidator:
        name = "val"

        async def run(self, task, ctx):
            call_count[0] += 1
            # Alternate confidence: first call high, second low
            conf = 0.9 if call_count[0] % 2 == 1 else 0.5
            return AgentResult(agent_name=self.name, content="score", confidence=conf)

    result = await TreeOfThoughtsPattern(max_depth=1, branching_factor=1).execute(
        [r1, r2, ScoringValidator()], "task", ctx
    )
    # The highest scoring thought (thought_a) should win
    assert result.final_output == "thought_a"


async def test_tot_final_output_nonempty(ctx):
    reasoner = FakeAgent("r1", response="answer")
    validator = FakeAgent("val", response="ok", confidence=0.5)
    result = await TreeOfThoughtsPattern(max_depth=1, branching_factor=2).execute(
        [reasoner, validator], "task", ctx
    )
    assert result.final_output != ""
