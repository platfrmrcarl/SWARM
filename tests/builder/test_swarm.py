import pytest
from swarm.builder.swarm import Swarm
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def agents():
    return [FakeAgent(f"a{i}", response=f"r{i}") for i in range(4)]


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_swarm_linear_sequential(agents, ctx):
    result = await (
        Swarm()
        .sequential("s1", [agents[0]])
        .sequential("s2", [agents[1]])
        .run("task", ctx)
    )
    assert result.final_output == "r1"


def test_swarm_run_sync(agents):
    result = Swarm().sequential("s1", [agents[0]]).run_sync("task")
    assert result.final_output == "r0"


async def test_swarm_branching(agents, ctx):
    s = Swarm()
    s.sequential("plan", [agents[0]])
    s.sequential("branch_a", [agents[1]], after="plan")
    s.sequential("branch_b", [agents[2]], after="plan")
    s.sequential("merge", [agents[3]], after=["branch_a", "branch_b"])
    result = await s.run("task", ctx)
    assert result.final_output == "r3"


async def test_swarm_to_config_roundtrip(agents, ctx):
    swarm = Swarm().sequential("s1", [agents[0]]).parallel("s2", [agents[1], agents[2]])
    config = swarm.to_config()
    assert len(config) == 2
    assert config[0]["name"] == "s1"
    assert config[1]["name"] == "s2"
    agent_registry = {a.name: a for a in agents}
    swarm2 = Swarm.from_config(config, agent_registry)
    result = await swarm2.run("task", ctx)
    assert result is not None


async def test_swarm_all_pattern_methods(agents, ctx):
    s = Swarm()
    s.sequential("seq", [agents[0]])
    s.parallel("par", [agents[1], agents[2]], after="seq")
    result = await s.run("task", ctx)
    assert result.pattern in ("parallel", "sequential")
