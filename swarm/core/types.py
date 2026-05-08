from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    agent_name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    next_agent: str | None = None
    confidence: float = 1.0


@dataclass
class SwarmResult:
    pattern: str
    results: list[AgentResult]
    final_output: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SwarmContext:
    def __init__(self) -> None:
        self.state: dict[str, Any] = {}
        self.history: list[Message] = []
        self.results: list[AgentResult] = []

    def add_result(self, result: AgentResult) -> None:
        self.results.append(result)
