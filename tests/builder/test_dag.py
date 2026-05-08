# tests/builder/test_dag.py
import pytest
from swarm.builder.dag import DAG, DAGNode
from swarm.core.types import SwarmContext
from swarm.patterns.sequential import SequentialPattern
from swarm.patterns.parallel import ParallelPattern
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_dag_single_node(ctx):
    dag = DAG()
    agent = FakeAgent("a", response="result")
    dag.add_node("step1", SequentialPattern(), [agent], deps=[])
    result = await dag.execute("task", ctx)
    assert result.final_output == "result"


async def test_dag_linear_chain_passes_output(ctx):
    dag = DAG()
    a1 = FakeAgent("a1", response="from_a1")
    a2 = FakeAgent("a2", response="from_a2")
    dag.add_node("s1", SequentialPattern(), [a1], deps=[])
    dag.add_node("s2", SequentialPattern(), [a2], deps=["s1"])
    result = await dag.execute("initial", ctx)
    assert result.final_output == "from_a2"
    assert ctx.state["s1.output"] == "from_a1"
    assert ctx.state["s2.output"] == "from_a2"


async def test_dag_branching_merges_predecessors(ctx):
    dag = DAG()
    a_plan = FakeAgent("plan", response="plan_out")
    a_r1 = FakeAgent("r1", response="research1")
    a_r2 = FakeAgent("r2", response="research2")
    a_synth = FakeAgent("synth", response="final")
    dag.add_node("plan", SequentialPattern(), [a_plan], deps=[])
    dag.add_node("r1", SequentialPattern(), [a_r1], deps=["plan"])
    dag.add_node("r2", SequentialPattern(), [a_r2], deps=["plan"])
    dag.add_node("synth", SequentialPattern(), [a_synth], deps=["r1", "r2"])
    result = await dag.execute("task", ctx)
    assert result.final_output == "final"
    synth_input = ctx.state["synth.input"]
    assert "research1" in synth_input
    assert "research2" in synth_input


async def test_dag_topological_sort_respects_deps(ctx):
    dag = DAG()
    execution_order = []

    class TrackingAgent:
        def __init__(self, name):
            self.name = name
        async def run(self, task, ctx):
            from swarm.core.types import AgentResult
            execution_order.append(self.name)
            return AgentResult(agent_name=self.name, content=f"{self.name}_done")

    dag.add_node("c", SequentialPattern(), [TrackingAgent("c")], deps=["a", "b"])
    dag.add_node("a", SequentialPattern(), [TrackingAgent("a")], deps=[])
    dag.add_node("b", SequentialPattern(), [TrackingAgent("b")], deps=[])
    await dag.execute("task", ctx)
    assert execution_order.index("a") < execution_order.index("c")
    assert execution_order.index("b") < execution_order.index("c")
