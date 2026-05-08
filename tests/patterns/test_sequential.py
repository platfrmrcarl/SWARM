import pytest
from swarm.patterns.sequential import SequentialPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_sequential_chains_output_to_input(ctx):
    received: list[str] = []

    class RecordingAgent:
        def __init__(self, name: str, response: str):
            self.name = name
            self._response = response

        async def run(self, task: str, _ctx):
            received.append(task)
            from swarm.core.types import AgentResult
            return AgentResult(agent_name=self.name, content=self._response)

    a1 = RecordingAgent("a1", "step1")
    a2 = RecordingAgent("a2", "step2")
    a3 = RecordingAgent("a3", "step3")
    pattern = SequentialPattern()
    result = await pattern.execute([a1, a2, a3], "start", ctx)
    assert result.final_output == "step3"
    assert result.pattern == "sequential"
    assert len(result.results) == 3
    assert received == ["start", "step1", "step2"]


async def test_sequential_single_agent(ctx):
    a = FakeAgent("solo", response="done")
    result = await SequentialPattern().execute([a], "go", ctx)
    assert result.final_output == "done"
    assert len(result.results) == 1


async def test_sequential_adds_results_to_ctx(ctx):
    agents = [FakeAgent(f"a{i}", response=f"r{i}") for i in range(3)]
    await SequentialPattern().execute(agents, "task", ctx)
    assert len(ctx.results) == 3
