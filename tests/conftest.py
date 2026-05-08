import pytest
from swarm.core.types import AgentResult, SwarmContext


class FakeProvider:
    async def complete(self, messages, **kw) -> str:
        return "fake response"


class FakeAgent:
    def __init__(
        self,
        name: str,
        response: str = "ok",
        confidence: float = 1.0,
        next_agent: str | None = None,
    ):
        self.name = name
        self._response = response
        self._confidence = confidence
        self._next = next_agent

    async def run(self, task: str, ctx: SwarmContext) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            content=self._response,
            confidence=self._confidence,
            next_agent=self._next,
        )


@pytest.fixture
def fake_provider():
    return FakeProvider()


@pytest.fixture
def ctx():
    return SwarmContext()
