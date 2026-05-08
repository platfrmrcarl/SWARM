from swarm.core.types import AgentResult, Message, SwarmContext, SwarmResult


def test_message_defaults():
    m = Message(role="user", content="hello")
    assert m.role == "user"
    assert m.content == "hello"
    assert m.metadata == {}


def test_agent_result_defaults():
    r = AgentResult(agent_name="a1", content="done")
    assert r.confidence == 1.0
    assert r.next_agent is None
    assert r.metadata == {}


def test_swarm_result_defaults():
    r = AgentResult(agent_name="a", content="x")
    sr = SwarmResult(pattern="sequential", results=[r], final_output="x")
    assert sr.metadata == {}


def test_swarm_context_add_result():
    ctx = SwarmContext()
    assert ctx.state == {}
    assert ctx.history == []
    assert ctx.results == []
    r = AgentResult(agent_name="a", content="y")
    ctx.add_result(r)
    assert len(ctx.results) == 1
    assert ctx.results[0] is r


def test_swarm_context_state_isolation():
    ctx1 = SwarmContext()
    ctx2 = SwarmContext()
    ctx1.state["x"] = 1
    assert "x" not in ctx2.state
