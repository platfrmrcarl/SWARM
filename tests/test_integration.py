import pytest
from swarm import Swarm
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


async def test_full_pipeline_via_public_api():
    agents = [FakeAgent(f"a{i}", response=f"step{i}") for i in range(3)]
    result = await (
        Swarm()
        .sequential("plan", [agents[0]])
        .parallel("work", [agents[1], agents[2]])
        .run("build something")
    )
    assert result is not None
    assert result.final_output != ""


def test_swarm_run_sync_works():
    agent = FakeAgent("solo", response="sync result")
    result = Swarm().sequential("s", [agent]).run_sync("task")
    assert result.final_output == "sync result"
