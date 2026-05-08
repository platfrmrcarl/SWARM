import pytest
from swarm.core.protocols import Agent, LLMProvider, Pattern, Tool
from swarm.core.types import AgentResult, SwarmContext, SwarmResult, Message
from swarm.core.errors import SwarmError, ProviderError, PatternError


class MinimalProvider:
    async def complete(self, messages: list, **kw) -> str:
        return "x"


class MinimalAgent:
    name = "a"

    async def run(self, task: str, ctx: SwarmContext) -> AgentResult:
        return AgentResult(agent_name="a", content="x")


class MinimalPattern:
    async def execute(self, agents, task, ctx) -> SwarmResult:
        return SwarmResult(pattern="p", results=[], final_output="x")


def test_provider_structural_check():
    assert isinstance(MinimalProvider(), LLMProvider)


def test_agent_structural_check():
    assert isinstance(MinimalAgent(), Agent)


def test_pattern_structural_check():
    assert isinstance(MinimalPattern(), Pattern)


def test_error_hierarchy():
    assert issubclass(ProviderError, SwarmError)
    assert issubclass(PatternError, SwarmError)


def test_swarm_error_is_exception():
    with pytest.raises(SwarmError):
        raise SwarmError("boom")
