# tests/patterns/test_mesh.py
import pytest
from swarm.patterns.mesh import MeshPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_mesh_runs_multiple_rounds(ctx):
    agents = [FakeAgent(f"a{i}", response=f"answer{i}") for i in range(3)]
    result = await MeshPattern(max_rounds=3).execute(agents, "task", ctx)
    assert result.pattern == "mesh"
    assert len(result.results) == 3


async def test_mesh_converges_when_all_agree(ctx):
    agents = [FakeAgent(f"a{i}", response="consensus") for i in range(3)]
    result = await MeshPattern(max_rounds=5).execute(agents, "task", ctx)
    assert "consensus" in result.final_output
