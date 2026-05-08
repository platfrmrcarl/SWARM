# tests/patterns/test_variant_judge.py
import pytest
from swarm.patterns.variant_judge import VariantJudgePattern
from swarm.core.types import AgentResult, SwarmContext
from swarm.core.errors import PatternError


class JudgeAgent:
    name = "judge"
    async def run(self, task, ctx):
        return AgentResult(agent_name="judge", content="variant2 wins", confidence=1.0)


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_variant_judge_last_agent_is_judge(ctx):
    from tests.conftest import FakeAgent
    v1 = FakeAgent("v1", response="option A")
    v2 = FakeAgent("v2", response="option B")
    judge = JudgeAgent()
    result = await VariantJudgePattern().execute([v1, v2, judge], "task", ctx)
    assert result.final_output == "variant2 wins"
    assert result.pattern == "variant_judge"


async def test_variant_judge_requires_at_least_two_agents(ctx):
    from tests.conftest import FakeAgent
    with pytest.raises(PatternError):
        await VariantJudgePattern().execute([FakeAgent("solo")], "task", ctx)
