from __future__ import annotations
from dataclasses import dataclass, field
from swarm.core.protocols import Agent, Pattern
from swarm.core.types import SwarmContext, SwarmResult


@dataclass
class DAGNode:
    name: str
    pattern: Pattern
    agents: list[Agent]
    deps: list[str] = field(default_factory=list)


class DAG:
    def __init__(self) -> None:
        self._nodes: dict[str, DAGNode] = {}

    def add_node(
        self,
        name: str,
        pattern: Pattern,
        agents: list[Agent],
        deps: list[str],
    ) -> None:
        self._nodes[name] = DAGNode(name=name, pattern=pattern, agents=agents, deps=deps)

    def _topological_sort(self) -> list[str]:
        visited: set[str] = set()
        order: list[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            for dep in self._nodes[name].deps:
                visit(dep)
            order.append(name)

        for name in self._nodes:
            visit(name)
        return order

    async def execute(self, task: str, ctx: SwarmContext) -> SwarmResult:
        order = self._topological_sort()
        last_result: SwarmResult | None = None
        for node_name in order:
            node = self._nodes[node_name]
            if node.deps:
                predecessor_outputs = [
                    ctx.state[f"{dep}.output"] for dep in node.deps
                    if f"{dep}.output" in ctx.state
                ]
                node_task = "\n\n".join(predecessor_outputs)
            else:
                node_task = ctx.state.get(f"{node_name}.input", task)
            ctx.state[f"{node_name}.input"] = node_task
            result = await node.pattern.execute(node.agents, node_task, ctx)
            ctx.state[f"{node_name}.output"] = result.final_output
            last_result = result
        return last_result  # type: ignore[return-value]

    def to_config(self) -> list[dict]:
        order = self._topological_sort()
        config = []
        for name in order:
            node = self._nodes[name]
            entry: dict = {
                "name": name,
                "pattern": type(node.pattern).__name__.replace("Pattern", "").lower(),
                "agents": [a.name for a in node.agents],
            }
            if node.deps:
                entry["after"] = node.deps if len(node.deps) > 1 else node.deps[0]
            config.append(entry)
        return config

    @classmethod
    def from_config(cls, config: list[dict], agents: dict[str, Agent]) -> "DAG":
        from swarm.builder.config import pattern_from_name
        dag = cls()
        for entry in config:
            after = entry.get("after")
            deps: list[str] = []
            if isinstance(after, list):
                deps = after
            elif isinstance(after, str):
                deps = [after]
            node_agents = [agents[n] for n in entry["agents"]]
            pattern = pattern_from_name(entry["pattern"], entry)
            dag.add_node(entry["name"], pattern, node_agents, deps)
        return dag
