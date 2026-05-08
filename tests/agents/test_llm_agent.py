import pytest
from swarm.agents.llm_agent import LLMAgent
from swarm.core.types import SwarmContext, Message
from tests.conftest import FakeProvider


@pytest.fixture
def agent():
    return LLMAgent(
        name="worker",
        provider=FakeProvider(),
        system_prompt="You are a helpful worker.",
    )


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_agent_name(agent):
    assert agent.name == "worker"


async def test_agent_returns_agent_result(agent, ctx):
    result = await agent.run("do a task", ctx)
    assert result.agent_name == "worker"
    assert result.content == "fake response"
    assert result.confidence == 1.0
    assert result.next_agent is None


async def test_agent_appends_to_context_history(agent, ctx):
    await agent.run("task", ctx)
    assert len(ctx.history) == 2
    assert ctx.history[0].role == "user"
    assert ctx.history[0].content == "task"
    assert ctx.history[1].role == "assistant"
    assert ctx.history[1].content == "fake response"


async def test_agent_with_context_window_zero(ctx):
    received: list = []

    class RecordingProvider:
        async def complete(self, messages, *, tools=None, temperature=None, max_tokens=None) -> str:
            received.extend(messages)
            return "fake response"

    agent = LLMAgent(
        name="minimal",
        provider=RecordingProvider(),
        system_prompt="You are minimal.",
        context_window=0,
    )
    ctx.history.append(Message(role="user", content="old message"))
    result = await agent.run("new task", ctx)
    assert result.content == "fake response"
    # Only system prompt + new user task should be sent — no old history
    roles = [m.role for m in received]
    assert "system" in roles
    assert not any(m.content == "old message" for m in received)
