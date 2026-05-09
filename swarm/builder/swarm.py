from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent, Pattern
from swarm.core.types import SwarmContext, SwarmResult
from swarm.builder.dag import DAG
from swarm.builder.config import pattern_from_name
from swarm.patterns.sequential import SequentialPattern
from swarm.patterns.parallel import ParallelPattern
from swarm.patterns.hierarchical import HierarchicalPattern
from swarm.patterns.decentralized import DecentralizedPattern
from swarm.patterns.adaptive import AdaptivePattern
from swarm.patterns.mesh import MeshPattern
from swarm.patterns.variant_judge import VariantJudgePattern
from swarm.patterns.reflection import ReflectionPattern
from swarm.patterns.broadcast import BroadcastPattern
from swarm.patterns.auction import AuctionPattern
from swarm.patterns.mixture_of_agents import MixtureOfAgentsPattern
from swarm.patterns.debate import DebatePattern
from swarm.patterns.tree_of_thoughts import TreeOfThoughtsPattern
from swarm.patterns.speculative import SpeculativePattern
from swarm.patterns.blackboard import BlackboardPattern


class Swarm:
    def __init__(self) -> None:
        self._dag = DAG()
        self._last_node: str | None = None

    def _add_node(
        self,
        name: str,
        pattern: Pattern,
        agents: list[Agent],
        after: str | list[str] | None,
    ) -> "Swarm":
        if after is None:
            deps = [self._last_node] if self._last_node else []
        elif isinstance(after, str):
            deps = [after]
        else:
            deps = after
        self._dag.add_node(name, pattern, agents, deps)
        self._last_node = name
        return self

    def sequential(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, SequentialPattern(), agents, after)

    def parallel(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None, merge: str = "concatenate") -> "Swarm":
        return self._add_node(name, ParallelPattern(merge_strategy=merge), agents, after)

    def hierarchical(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, HierarchicalPattern(), agents, after)

    def decentralized(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, DecentralizedPattern(), agents, after)

    def adaptive(self, name: str, agents: list[Agent], *, threshold: float = 0.8, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, AdaptivePattern(threshold=threshold), agents, after)

    def mesh(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, MeshPattern(), agents, after)

    def variant_judge(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, VariantJudgePattern(), agents, after)

    def reflection(self, name: str, agents: list[Agent], *, max_iterations: int = 3, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, ReflectionPattern(max_iterations=max_iterations), agents, after)

    def broadcast(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, BroadcastPattern(), agents, after)

    def auction(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, AuctionPattern(), agents, after)

    def mixture_of_agents(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, MixtureOfAgentsPattern(), agents, after)

    def debate(self, name: str, agents: list[Agent], *, max_rounds: int = 3, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, DebatePattern(max_rounds=max_rounds), agents, after)

    def tree_of_thoughts(self, name: str, agents: list[Agent], *, max_depth: int = 3, branching_factor: int = 2, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, TreeOfThoughtsPattern(max_depth=max_depth, branching_factor=branching_factor), agents, after)

    def speculative(self, name: str, agents: list[Agent], *, threshold: float = 0.8, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, SpeculativePattern(threshold=threshold), agents, after)

    def blackboard(self, name: str, agents: list[Agent], *, max_rounds: int = 5, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, BlackboardPattern(max_rounds=max_rounds), agents, after)

    async def run(self, task: str, ctx: SwarmContext | None = None) -> SwarmResult:
        return await self._dag.execute(task, ctx or SwarmContext())

    def run_sync(self, task: str) -> SwarmResult:
        return asyncio.run(self.run(task))

    def to_config(self) -> list[dict]:
        return self._dag.to_config()

    @classmethod
    def from_config(cls, config: list[dict], agents: dict[str, Agent]) -> "Swarm":
        swarm = cls()
        swarm._dag = DAG.from_config(config, agents)
        if config:
            swarm._last_node = config[-1]["name"]
        return swarm
