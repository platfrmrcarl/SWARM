# SWARM Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python swarm agent library implementing 10 coordination patterns with hybrid composition, 3 LLM providers, a fluent builder API, and a CLI.

**Architecture:** Protocol-first layered package (core → providers → agents → patterns → builder → CLI). TDD throughout — no real LLM calls in any test; FakeProvider + FakeAgent as structural fakes. DAG engine enables arbitrary pattern composition.

**Tech Stack:** Python 3.11+, Typer, anthropic SDK, httpx, PyYAML, pytest-asyncio

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Package config, deps, pytest settings |
| `swarm/__init__.py` | Public API re-exports |
| `swarm/py.typed` | PEP 561 marker |
| `swarm/core/types.py` | Message, AgentResult, SwarmResult, SwarmContext |
| `swarm/core/protocols.py` | LLMProvider, Agent, Pattern, Tool protocols |
| `swarm/core/errors.py` | SwarmError, ProviderError, PatternError |
| `swarm/providers/claude.py` | ClaudeProvider (subscription + api_key) |
| `swarm/providers/ollama.py` | OllamaProvider (httpx to localhost:11434) |
| `swarm/providers/litellm.py` | LiteLLMProvider (wraps litellm.acompletion) |
| `swarm/agents/llm_agent.py` | LLMAgent — wraps provider, builds message history |
| `swarm/patterns/sequential.py` | Agent1 → Agent2 → … pipeline |
| `swarm/patterns/parallel.py` | Fan-out + merge (concatenate/vote/synthesize) |
| `swarm/patterns/hierarchical.py` | Coordinator decomposes → workers → coordinator synthesizes |
| `swarm/patterns/decentralized.py` | All agents vote, winner by max confidence |
| `swarm/patterns/adaptive.py` | Route by confidence + next_agent until threshold |
| `swarm/patterns/mesh.py` | Rounds of all-agent comms until converged |
| `swarm/patterns/variant_judge.py` | N variants run in parallel, judge picks best |
| `swarm/patterns/reflection.py` | Generator + critic loop until critic satisfied |
| `swarm/patterns/broadcast.py` | Broadcaster emits event, listeners respond |
| `swarm/patterns/auction.py` | All agents bid (confidence), winner executes |
| `swarm/builder/dag.py` | DAGNode, DAG (topological sort + execute) |
| `swarm/builder/swarm.py` | Swarm fluent builder + from_config |
| `swarm/builder/config.py` | build_provider, build_agents helpers |
| `swarm/cli/main.py` | Typer CLI: run, init, validate, export |
| `tests/conftest.py` | FakeProvider, FakeAgent, shared fixtures |
| `tests/core/test_types.py` | SwarmContext, Message, AgentResult, SwarmResult |
| `tests/core/test_protocols.py` | Protocol structural checks |
| `tests/providers/test_claude.py` | ClaudeProvider (mocked subprocess + AsyncAnthropic) |
| `tests/providers/test_ollama.py` | OllamaProvider (mocked httpx) |
| `tests/agents/test_llm_agent.py` | LLMAgent with FakeProvider |
| `tests/patterns/test_sequential.py` | SequentialPattern |
| `tests/patterns/test_parallel.py` | ParallelPattern (all merge strategies) |
| `tests/patterns/test_hierarchical.py` | HierarchicalPattern |
| `tests/patterns/test_decentralized.py` | DecentralizedPattern |
| `tests/patterns/test_adaptive.py` | AdaptivePattern (routing, threshold, max_hops) |
| `tests/patterns/test_mesh.py` | MeshPattern (convergence) |
| `tests/patterns/test_variant_judge.py` | VariantJudgePattern |
| `tests/patterns/test_reflection.py` | ReflectionPattern |
| `tests/patterns/test_broadcast.py` | BroadcastPattern |
| `tests/patterns/test_auction.py` | AuctionPattern |
| `tests/builder/test_dag.py` | DAG topological sort, wiring, branching |
| `tests/builder/test_swarm.py` | Swarm builder API + from_config |
| `tests/cli/test_cli.py` | CLI commands (typer test runner) |

---

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `swarm/__init__.py`
- Create: `swarm/py.typed`
- Create: `swarm/core/__init__.py`, `swarm/providers/__init__.py`, `swarm/agents/__init__.py`, `swarm/patterns/__init__.py`, `swarm/builder/__init__.py`, `swarm/cli/__init__.py`
- Create: `tests/__init__.py`, `tests/core/__init__.py`, `tests/providers/__init__.py`, `tests/agents/__init__.py`, `tests/patterns/__init__.py`, `tests/builder/__init__.py`, `tests/cli/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "swarm"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "anthropic>=0.40",
    "httpx>=0.27",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
litellm = ["litellm>=1.40"]
dev = ["pytest>=8", "pytest-asyncio>=0.23", "ruff", "mypy", "hatchling"]

[project.scripts]
swarm = "swarm.cli.main:app"

[tool.pytest.ini_options]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
```

- [ ] **Step 2: Create package skeleton**

```bash
mkdir -p swarm/{core,providers,agents,patterns,builder,cli}
mkdir -p tests/{core,providers,agents,patterns,builder,cli}
touch swarm/py.typed
touch swarm/__init__.py swarm/core/__init__.py swarm/providers/__init__.py
touch swarm/agents/__init__.py swarm/patterns/__init__.py
touch swarm/builder/__init__.py swarm/cli/__init__.py
touch tests/__init__.py tests/core/__init__.py tests/providers/__init__.py
touch tests/agents/__init__.py tests/patterns/__init__.py
touch tests/builder/__init__.py tests/cli/__init__.py
pip install -e ".[dev]"
```

- [ ] **Step 3: Create tests/conftest.py**

```python
import pytest
from swarm.core.types import AgentResult, SwarmContext


class FakeProvider:
    async def complete(self, messages, **kw) -> str:
        return "fake response"


class FakeAgent:
    def __init__(
        self,
        name: str,
        response: str = "ok",
        confidence: float = 1.0,
        next_agent: str | None = None,
    ):
        self.name = name
        self._response = response
        self._confidence = confidence
        self._next = next_agent

    async def run(self, task: str, ctx: SwarmContext) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            content=self._response,
            confidence=self._confidence,
            next_agent=self._next,
        )


@pytest.fixture
def fake_provider():
    return FakeProvider()


@pytest.fixture
def ctx():
    return SwarmContext()
```

- [ ] **Step 4: Run tests (should collect 0, no errors)**

```bash
pytest --collect-only
```

Expected: `no tests ran` with exit code 5 (no tests collected) or 0.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml swarm/ tests/
git commit -m "feat: scaffold swarm package structure"
```

---

### Task 2: Core Types

**Files:**
- Create: `swarm/core/types.py`
- Create: `tests/core/test_types.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/core/test_types.py
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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/core/test_types.py -v
```

Expected: `ImportError` or `ModuleNotFoundError`.

- [ ] **Step 3: Implement swarm/core/types.py**

```python
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
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/core/test_types.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add swarm/core/types.py tests/core/test_types.py
git commit -m "feat: add core types (Message, AgentResult, SwarmResult, SwarmContext)"
```

---

### Task 3: Core Protocols + Errors

**Files:**
- Create: `swarm/core/protocols.py`
- Create: `swarm/core/errors.py`
- Create: `tests/core/test_protocols.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/core/test_protocols.py
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
```

Add `import pytest` at top of the test file.

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/core/test_protocols.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/core/protocols.py**

```python
from __future__ import annotations
from typing import Any, Protocol, runtime_checkable
from swarm.core.types import AgentResult, Message, SwarmContext, SwarmResult


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str: ...


@runtime_checkable
class Agent(Protocol):
    name: str

    async def run(self, task: str, ctx: SwarmContext) -> AgentResult: ...


@runtime_checkable
class Pattern(Protocol):
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult: ...


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str

    async def __call__(self, **kwargs: Any) -> Any: ...
```

- [ ] **Step 4: Implement swarm/core/errors.py**

```python
class SwarmError(Exception):
    pass


class ProviderError(SwarmError):
    pass


class PatternError(SwarmError):
    pass
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
pytest tests/core/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add swarm/core/protocols.py swarm/core/errors.py tests/core/test_protocols.py
git commit -m "feat: add core protocols and error types"
```

---

### Task 4: ClaudeProvider

**Files:**
- Create: `swarm/providers/claude.py`
- Create: `tests/providers/test_claude.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/providers/test_claude.py
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swarm.core.types import Message
from swarm.providers.claude import ClaudeProvider


def test_subscription_mode_is_default():
    p = ClaudeProvider(model="claude-sonnet-4-6")
    assert p.auth_mode == "subscription"


def test_api_key_mode_sets_auth():
    p = ClaudeProvider(model="claude-sonnet-4-6", api_key="sk-ant-test")
    assert p.auth_mode == "api_key"


@pytest.mark.asyncio
async def test_subscription_calls_subprocess():
    p = ClaudeProvider(model="claude-sonnet-4-6")
    messages = [Message(role="user", content="hello")]
    mock_result = MagicMock()
    mock_result.stdout = "world"
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = await p.complete(messages)
    assert result == "world"
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "claude"
    assert "-p" in args


@pytest.mark.asyncio
async def test_api_key_calls_anthropic():
    p = ClaudeProvider(model="claude-sonnet-4-6", api_key="sk-ant-test")
    messages = [Message(role="user", content="hello")]
    mock_client = AsyncMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="world")]
    )
    with patch("swarm.providers.claude.AsyncAnthropic", return_value=mock_client):
        result = await p.complete(messages)
    assert result == "world"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/providers/test_claude.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/providers/claude.py**

```python
from __future__ import annotations
import subprocess
from swarm.core.types import Message
from swarm.core.errors import ProviderError


class ClaudeProvider:
    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        api_key: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.auth_mode = "api_key" if api_key else "subscription"
        self._api_key = api_key

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if self.auth_mode == "subscription":
            return await self._complete_subscription(messages)
        return await self._complete_api(messages, temperature, max_tokens)

    async def _complete_subscription(self, messages: list[Message]) -> str:
        prompt = self._format_prompt(messages)
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ProviderError(f"claude CLI error: {result.stderr}")
        return result.stdout.strip()

    async def _complete_api(
        self,
        messages: list[Message],
        temperature: float | None,
        max_tokens: int | None,
    ) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self._api_key)
        api_msgs = [{"role": m.role, "content": m.content} for m in messages
                    if m.role != "system"]
        system = next((m.content for m in messages if m.role == "system"), None)
        kwargs: dict = dict(
            model=self.model,
            messages=api_msgs,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
        )
        if system:
            kwargs["system"] = system
        response = await client.messages.create(**kwargs)
        return response.content[0].text

    def _format_prompt(self, messages: list[Message]) -> str:
        parts = []
        for m in messages:
            if m.role == "system":
                parts.append(f"[System]: {m.content}")
            elif m.role == "user":
                parts.append(m.content)
            elif m.role == "assistant":
                parts.append(f"[Assistant]: {m.content}")
        return "\n\n".join(parts)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/providers/test_claude.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add swarm/providers/claude.py tests/providers/test_claude.py
git commit -m "feat: add ClaudeProvider (subscription + api_key modes)"
```

---

### Task 5: OllamaProvider + LiteLLMProvider

**Files:**
- Create: `swarm/providers/ollama.py`
- Create: `swarm/providers/litellm.py`
- Create: `tests/providers/test_ollama.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/providers/test_ollama.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from swarm.core.types import Message
from swarm.providers.ollama import OllamaProvider


def test_ollama_default_url():
    p = OllamaProvider(model="gemma3")
    assert p.base_url == "http://localhost:11434"


@pytest.mark.asyncio
async def test_ollama_posts_to_api():
    p = OllamaProvider(model="gemma3")
    messages = [Message(role="user", content="hello")]
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "world"}}
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await p.complete(messages)
    assert result == "world"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/providers/test_ollama.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/providers/ollama.py**

```python
from __future__ import annotations
import httpx
from swarm.core.types import Message
from swarm.core.errors import ProviderError


class OllamaProvider:
    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            },
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat", json=payload, timeout=120.0
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise ProviderError(f"Ollama error: {e}") from e
        return response.json()["message"]["content"]
```

- [ ] **Step 4: Implement swarm/providers/litellm.py**

```python
from __future__ import annotations
from swarm.core.types import Message
from swarm.core.errors import ProviderError


class LiteLLMProvider:
    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._kwargs = kwargs

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        try:
            import litellm
        except ImportError as e:
            raise ProviderError("litellm not installed. pip install swarm[litellm]") from e
        api_msgs = [{"role": m.role, "content": m.content} for m in messages]
        response = await litellm.acompletion(
            model=self.model,
            messages=api_msgs,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **self._kwargs,
        )
        return response.choices[0].message.content
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
pytest tests/providers/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add swarm/providers/ollama.py swarm/providers/litellm.py tests/providers/test_ollama.py
git commit -m "feat: add OllamaProvider and LiteLLMProvider"
```

---

### Task 6: LLMAgent

**Files:**
- Create: `swarm/agents/llm_agent.py`
- Create: `tests/agents/test_llm_agent.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/agents/test_llm_agent.py
import pytest
from swarm.agents.llm_agent import LLMAgent
from swarm.core.types import SwarmContext
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
    assert len(ctx.history) >= 1


async def test_agent_with_context_window_zero(ctx):
    agent = LLMAgent(
        name="minimal",
        provider=FakeProvider(),
        system_prompt="You are minimal.",
        context_window=0,
    )
    ctx.history.append(
        __import__("swarm.core.types", fromlist=["Message"]).Message(
            role="user", content="old message"
        )
    )
    result = await agent.run("new task", ctx)
    assert result.content == "fake response"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/agents/test_llm_agent.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/agents/llm_agent.py**

```python
from __future__ import annotations
from swarm.core.protocols import LLMProvider
from swarm.core.types import AgentResult, Message, SwarmContext


class LLMAgent:
    def __init__(
        self,
        name: str,
        provider: LLMProvider,
        system_prompt: str = "",
        context_window: int = 20,
        **metadata,
    ) -> None:
        self.name = name
        self._provider = provider
        self._system_prompt = system_prompt
        self._context_window = context_window
        self._metadata = metadata

    async def run(self, task: str, ctx: SwarmContext) -> AgentResult:
        messages: list[Message] = []
        if self._system_prompt:
            messages.append(Message(role="system", content=self._system_prompt))
        if self._context_window > 0:
            messages.extend(ctx.history[-self._context_window :])
        messages.append(Message(role="user", content=task))
        response = await self._provider.complete(messages)
        ctx.history.append(Message(role="user", content=task))
        ctx.history.append(Message(role="assistant", content=response))
        return AgentResult(agent_name=self.name, content=response)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/agents/test_llm_agent.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add swarm/agents/llm_agent.py tests/agents/test_llm_agent.py
git commit -m "feat: add LLMAgent"
```

---

### Task 7: SequentialPattern

**Files:**
- Create: `swarm/patterns/sequential.py`
- Create: `tests/patterns/test_sequential.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/patterns/test_sequential.py
import pytest
from swarm.patterns.sequential import SequentialPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_sequential_chains_output_to_input(ctx):
    a1 = FakeAgent("a1", response="step1")
    a2 = FakeAgent("a2", response="step2")
    a3 = FakeAgent("a3", response="step3")
    pattern = SequentialPattern()
    result = await pattern.execute([a1, a2, a3], "start", ctx)
    assert result.final_output == "step3"
    assert result.pattern == "sequential"
    assert len(result.results) == 3


async def test_sequential_single_agent(ctx):
    a = FakeAgent("solo", response="done")
    result = await SequentialPattern().execute([a], "go", ctx)
    assert result.final_output == "done"
    assert len(result.results) == 1


async def test_sequential_adds_results_to_ctx(ctx):
    agents = [FakeAgent(f"a{i}", response=f"r{i}") for i in range(3)]
    await SequentialPattern().execute(agents, "task", ctx)
    assert len(ctx.results) == 3
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/patterns/test_sequential.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/patterns/sequential.py**

```python
from __future__ import annotations
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult


class SequentialPattern:
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        current = task
        for agent in agents:
            result = await agent.run(current, ctx)
            ctx.add_result(result)
            current = result.content
        return SwarmResult(
            pattern="sequential",
            results=list(ctx.results),
            final_output=current,
        )
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/patterns/test_sequential.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add swarm/patterns/sequential.py tests/patterns/test_sequential.py
git commit -m "feat: add SequentialPattern"
```

---

### Task 8: ParallelPattern

**Files:**
- Create: `swarm/patterns/parallel.py`
- Create: `tests/patterns/test_parallel.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/patterns/test_parallel.py
import pytest
from swarm.patterns.parallel import ParallelPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_parallel_runs_all_agents(ctx):
    agents = [FakeAgent(f"a{i}", response=f"r{i}") for i in range(3)]
    result = await ParallelPattern().execute(agents, "task", ctx)
    assert result.pattern == "parallel"
    assert len(result.results) == 3


async def test_parallel_concatenate_merge(ctx):
    agents = [FakeAgent("a1", response="foo"), FakeAgent("a2", response="bar")]
    result = await ParallelPattern(merge_strategy="concatenate").execute(
        agents, "task", ctx
    )
    assert "foo" in result.final_output
    assert "bar" in result.final_output


async def test_parallel_vote_merge_picks_majority(ctx):
    agents = [
        FakeAgent("a1", response="yes"),
        FakeAgent("a2", response="yes"),
        FakeAgent("a3", response="no"),
    ]
    result = await ParallelPattern(merge_strategy="vote").execute(agents, "task", ctx)
    assert result.final_output == "yes"


async def test_parallel_synthesize_merge(ctx):
    agents = [FakeAgent("a1", response="part1"), FakeAgent("a2", response="part2")]
    result = await ParallelPattern(merge_strategy="synthesize").execute(
        agents, "task", ctx
    )
    assert "1." in result.final_output or "part1" in result.final_output
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/patterns/test_parallel.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/patterns/parallel.py**

```python
from __future__ import annotations
import asyncio
from collections import Counter
from swarm.core.protocols import Agent
from swarm.core.types import AgentResult, SwarmContext, SwarmResult


def _merge(results: list[AgentResult], strategy: str) -> str:
    if strategy == "vote":
        counts = Counter(r.content for r in results)
        return counts.most_common(1)[0][0]
    if strategy == "synthesize":
        return "\n\n".join(f"{i+1}. {r.content}" for i, r in enumerate(results))
    return "\n\n".join(r.content for r in results)


class ParallelPattern:
    def __init__(self, merge_strategy: str = "concatenate") -> None:
        self.merge_strategy = merge_strategy

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        results = list(await asyncio.gather(*[a.run(task, ctx) for a in agents]))
        for r in results:
            ctx.add_result(r)
        merged = _merge(results, self.merge_strategy)
        return SwarmResult(pattern="parallel", results=results, final_output=merged)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/patterns/test_parallel.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add swarm/patterns/parallel.py tests/patterns/test_parallel.py
git commit -m "feat: add ParallelPattern with concatenate/vote/synthesize merge"
```

---

### Task 9: HierarchicalPattern

**Files:**
- Create: `swarm/patterns/hierarchical.py`
- Create: `tests/patterns/test_hierarchical.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/patterns/test_hierarchical.py
import pytest
from swarm.patterns.hierarchical import HierarchicalPattern
from swarm.core.types import AgentResult, SwarmContext
from swarm.core.errors import PatternError


class PlanningCoordinator:
    name = "coordinator"
    call_count = 0

    async def run(self, task, ctx):
        self.call_count += 1
        if self.call_count == 1:
            return AgentResult(agent_name="coordinator", content="1. subtask1\n2. subtask2")
        return AgentResult(agent_name="coordinator", content="synthesized")


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_hierarchical_calls_coordinator_twice(ctx):
    coord = PlanningCoordinator()
    from tests.conftest import FakeAgent
    w1 = FakeAgent("w1", response="worker1 result")
    w2 = FakeAgent("w2", response="worker2 result")
    result = await HierarchicalPattern().execute([coord, w1, w2], "big task", ctx)
    assert coord.call_count == 2
    assert result.final_output == "synthesized"
    assert result.pattern == "hierarchical"


async def test_hierarchical_requires_at_least_two_agents(ctx):
    from tests.conftest import FakeAgent
    with pytest.raises(PatternError):
        await HierarchicalPattern().execute([FakeAgent("solo")], "task", ctx)
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/patterns/test_hierarchical.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/patterns/hierarchical.py**

```python
from __future__ import annotations
import asyncio
import re
from swarm.core.protocols import Agent
from swarm.core.types import AgentResult, SwarmContext, SwarmResult
from swarm.core.errors import PatternError


def _parse_subtasks(plan: str, n_workers: int) -> list[str]:
    lines = [l.strip() for l in plan.splitlines() if l.strip()]
    numbered = [re.sub(r"^\d+[\.\)]\s*", "", l) for l in lines
                if re.match(r"^\d+[\.\)]", l)]
    subtasks = numbered if numbered else lines
    if len(subtasks) < n_workers:
        subtasks = subtasks + [plan] * (n_workers - len(subtasks))
    return subtasks[:n_workers]


def _synthesize_prompt(results: list[AgentResult]) -> str:
    parts = "\n\n".join(f"Worker {i+1}: {r.content}" for i, r in enumerate(results))
    return f"Synthesize these results into a final answer:\n\n{parts}"


class HierarchicalPattern:
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if len(agents) < 2:
            raise PatternError("HierarchicalPattern requires at least 2 agents (coordinator + 1 worker)")
        coordinator, *workers = agents
        plan = await coordinator.run(task, ctx)
        ctx.add_result(plan)
        subtasks = _parse_subtasks(plan.content, len(workers))
        worker_results = list(
            await asyncio.gather(*[w.run(s, ctx) for w, s in zip(workers, subtasks)])
        )
        for r in worker_results:
            ctx.add_result(r)
        final = await coordinator.run(_synthesize_prompt(worker_results), ctx)
        ctx.add_result(final)
        return SwarmResult(
            pattern="hierarchical",
            results=[plan, *worker_results, final],
            final_output=final.content,
        )
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/patterns/test_hierarchical.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add swarm/patterns/hierarchical.py tests/patterns/test_hierarchical.py
git commit -m "feat: add HierarchicalPattern"
```

---

### Task 10: DecentralizedPattern + AdaptivePattern

**Files:**
- Create: `swarm/patterns/decentralized.py`
- Create: `swarm/patterns/adaptive.py`
- Create: `tests/patterns/test_decentralized.py`
- Create: `tests/patterns/test_adaptive.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/patterns/test_decentralized.py
import pytest
from swarm.patterns.decentralized import DecentralizedPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_decentralized_picks_highest_confidence(ctx):
    agents = [
        FakeAgent("a1", response="low", confidence=0.4),
        FakeAgent("a2", response="high", confidence=0.9),
        FakeAgent("a3", response="mid", confidence=0.6),
    ]
    result = await DecentralizedPattern().execute(agents, "task", ctx)
    assert result.final_output == "high"
    assert result.pattern == "decentralized"


async def test_decentralized_all_agents_run(ctx):
    agents = [FakeAgent(f"a{i}") for i in range(4)]
    result = await DecentralizedPattern().execute(agents, "task", ctx)
    assert len(result.results) == 4
```

```python
# tests/patterns/test_adaptive.py
import pytest
from swarm.patterns.adaptive import AdaptivePattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_adaptive_stops_when_confident(ctx):
    a1 = FakeAgent("a1", response="done", confidence=0.95)
    a2 = FakeAgent("a2", response="never reached")
    result = await AdaptivePattern(threshold=0.8).execute([a1, a2], "task", ctx)
    assert result.final_output == "done"


async def test_adaptive_routes_to_next_agent(ctx):
    a1 = FakeAgent("a1", response="partial", confidence=0.3, next_agent="a2")
    a2 = FakeAgent("a2", response="final", confidence=0.95)
    result = await AdaptivePattern(threshold=0.8).execute([a1, a2], "task", ctx)
    assert result.final_output == "final"


async def test_adaptive_stops_at_max_hops(ctx):
    agents = [FakeAgent(f"a{i}", response=f"r{i}", confidence=0.1, next_agent=f"a{i+1}")
              for i in range(10)]
    result = await AdaptivePattern(threshold=0.8, max_hops=3).execute(agents, "task", ctx)
    assert result.pattern == "adaptive"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/patterns/test_decentralized.py tests/patterns/test_adaptive.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/patterns/decentralized.py**

```python
from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult


class DecentralizedPattern:
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        results = list(await asyncio.gather(*[a.run(task, ctx) for a in agents]))
        for r in results:
            ctx.add_result(r)
        winner = max(results, key=lambda r: r.confidence)
        return SwarmResult(
            pattern="decentralized", results=results, final_output=winner.content
        )
```

- [ ] **Step 4: Implement swarm/patterns/adaptive.py**

```python
from __future__ import annotations
from swarm.core.protocols import Agent
from swarm.core.types import AgentResult, SwarmContext, SwarmResult


class AdaptivePattern:
    def __init__(self, threshold: float = 0.8, max_hops: int = 5) -> None:
        self.threshold = threshold
        self.max_hops = max_hops

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        agent_map = {a.name: a for a in agents}
        current = agents[0]
        result: AgentResult | None = None
        for _ in range(self.max_hops):
            result = await current.run(task, ctx)
            ctx.add_result(result)
            if result.confidence >= self.threshold:
                break
            if not result.next_agent or result.next_agent not in agent_map:
                break
            current = agent_map[result.next_agent]
        return SwarmResult(
            pattern="adaptive",
            results=list(ctx.results),
            final_output=result.content if result else "",
        )
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
pytest tests/patterns/test_decentralized.py tests/patterns/test_adaptive.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add swarm/patterns/decentralized.py swarm/patterns/adaptive.py \
        tests/patterns/test_decentralized.py tests/patterns/test_adaptive.py
git commit -m "feat: add DecentralizedPattern and AdaptivePattern"
```

---

### Task 11: MeshPattern + VariantJudgePattern

**Files:**
- Create: `swarm/patterns/mesh.py`
- Create: `swarm/patterns/variant_judge.py`
- Create: `tests/patterns/test_mesh.py`
- Create: `tests/patterns/test_variant_judge.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/patterns/test_mesh.py
import pytest
from swarm.patterns.mesh import MeshPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_mesh_runs_multiple_rounds(ctx):
    agents = [FakeAgent(f"a{i}", response="stable") for i in range(3)]
    result = await MeshPattern(max_rounds=3).execute(agents, "task", ctx)
    assert result.pattern == "mesh"
    assert result.final_output != ""


async def test_mesh_converges_when_all_agree(ctx):
    agents = [FakeAgent(f"a{i}", response="consensus") for i in range(3)]
    result = await MeshPattern(max_rounds=5).execute(agents, "task", ctx)
    assert "consensus" in result.final_output
```

```python
# tests/patterns/test_variant_judge.py
import pytest
from swarm.patterns.variant_judge import VariantJudgePattern
from swarm.core.types import AgentResult, SwarmContext
from swarm.core.errors import PatternError


class JudgeAgent:
    name = "judge"
    async def run(self, task, ctx):
        return AgentResult(agent_name="judge", content="variant2 wins", confidence=1.0)


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_variant_judge_last_agent_is_judge(ctx):
    from tests.conftest import FakeAgent
    v1 = FakeAgent("v1", response="option A")
    v2 = FakeAgent("v2", response="option B")
    judge = JudgeAgent()
    result = await VariantJudgePattern().execute([v1, v2, judge], "task", ctx)
    assert result.final_output == "variant2 wins"
    assert result.pattern == "variant_judge"


async def test_variant_judge_requires_at_least_two_agents(ctx):
    from tests.conftest import FakeAgent
    with pytest.raises(PatternError):
        await VariantJudgePattern().execute([FakeAgent("solo")], "task", ctx)
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/patterns/test_mesh.py tests/patterns/test_variant_judge.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/patterns/mesh.py**

```python
from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import AgentResult, SwarmContext, SwarmResult


def _converged(results: list[AgentResult]) -> bool:
    contents = [r.content for r in results]
    return len(set(contents)) == 1


class MeshPattern:
    def __init__(self, max_rounds: int = 5) -> None:
        self.max_rounds = max_rounds

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        results: list[AgentResult] = []
        for _ in range(self.max_rounds):
            results = list(await asyncio.gather(*[a.run(task, ctx) for a in agents]))
            ctx.state["mesh_round"] = results
            if _converged(results):
                break
        for r in results:
            ctx.add_result(r)
        final = "\n\n".join(r.content for r in results)
        return SwarmResult(pattern="mesh", results=results, final_output=final)
```

- [ ] **Step 4: Implement swarm/patterns/variant_judge.py**

```python
from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult
from swarm.core.errors import PatternError


class VariantJudgePattern:
    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        if len(agents) < 2:
            raise PatternError("VariantJudgePattern requires at least 2 agents (variants + judge)")
        *variants, judge = agents
        variant_results = list(
            await asyncio.gather(*[v.run(task, ctx) for v in variants])
        )
        for r in variant_results:
            ctx.add_result(r)
        judge_input = "\n\n".join(
            f"Variant {i+1} ({r.agent_name}): {r.content}"
            for i, r in enumerate(variant_results)
        )
        final = await judge.run(
            f"Evaluate these variants and pick the best:\n\n{judge_input}", ctx
        )
        ctx.add_result(final)
        return SwarmResult(
            pattern="variant_judge",
            results=[*variant_results, final],
            final_output=final.content,
        )
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
pytest tests/patterns/test_mesh.py tests/patterns/test_variant_judge.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add swarm/patterns/mesh.py swarm/patterns/variant_judge.py \
        tests/patterns/test_mesh.py tests/patterns/test_variant_judge.py
git commit -m "feat: add MeshPattern and VariantJudgePattern"
```

---

### Task 12: ReflectionPattern + BroadcastPattern + AuctionPattern

**Files:**
- Create: `swarm/patterns/reflection.py`
- Create: `swarm/patterns/broadcast.py`
- Create: `swarm/patterns/auction.py`
- Create: `tests/patterns/test_reflection.py`
- Create: `tests/patterns/test_broadcast.py`
- Create: `tests/patterns/test_auction.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/patterns/test_reflection.py
import pytest
from swarm.patterns.reflection import ReflectionPattern
from swarm.core.types import AgentResult, SwarmContext


class CriticAgent:
    name = "critic"
    call_count = 0

    async def run(self, task, ctx):
        self.call_count += 1
        satisfied = self.call_count >= 2
        return AgentResult(
            agent_name="critic",
            content="looks good" if satisfied else "needs revision",
            confidence=0.9 if satisfied else 0.3,
        )


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_reflection_loops_until_satisfied(ctx):
    from tests.conftest import FakeAgent
    generator = FakeAgent("gen", response="draft")
    critic = CriticAgent()
    result = await ReflectionPattern(threshold=0.8, max_iterations=5).execute(
        [generator, critic], "write something", ctx
    )
    assert result.pattern == "reflection"
    assert critic.call_count >= 2


async def test_reflection_single_agent_self_critique(ctx):
    from tests.conftest import FakeAgent
    agent = FakeAgent("solo", response="done", confidence=0.9)
    result = await ReflectionPattern(threshold=0.8).execute([agent], "task", ctx)
    assert result.pattern == "reflection"
```

```python
# tests/patterns/test_broadcast.py
import pytest
from swarm.patterns.broadcast import BroadcastPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_broadcast_first_agent_is_broadcaster(ctx):
    broadcaster = FakeAgent("broadcaster", response="event happened")
    listener1 = FakeAgent("l1", response="heard it")
    listener2 = FakeAgent("l2", response="got it")
    result = await BroadcastPattern().execute(
        [broadcaster, listener1, listener2], "notify", ctx
    )
    assert "event happened" in result.final_output
    assert result.pattern == "broadcast"
    assert ctx.state.get("broadcast_event") == "event happened"


async def test_broadcast_stores_event_in_ctx(ctx):
    broadcaster = FakeAgent("b", response="ping")
    listener = FakeAgent("l", response="pong")
    await BroadcastPattern().execute([broadcaster, listener], "task", ctx)
    assert ctx.state["broadcast_event"] == "ping"
```

```python
# tests/patterns/test_auction.py
import pytest
from swarm.patterns.auction import AuctionPattern
from swarm.core.types import SwarmContext
from tests.conftest import FakeAgent


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_auction_winner_is_highest_confidence(ctx):
    agents = [
        FakeAgent("a1", response="low bid result", confidence=0.3),
        FakeAgent("a2", response="high bid result", confidence=0.95),
        FakeAgent("a3", response="mid bid result", confidence=0.6),
    ]
    result = await AuctionPattern().execute(agents, "task", ctx)
    assert result.final_output == "high bid result"
    assert result.pattern == "auction"


async def test_auction_all_agents_bid(ctx):
    agents = [FakeAgent(f"a{i}", confidence=float(i) / 10) for i in range(4)]
    result = await AuctionPattern().execute(agents, "task", ctx)
    assert len(result.results) == len(agents) + 1
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/patterns/test_reflection.py tests/patterns/test_broadcast.py tests/patterns/test_auction.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/patterns/reflection.py**

```python
from __future__ import annotations
from swarm.core.protocols import Agent
from swarm.core.types import SwarmContext, SwarmResult


class ReflectionPattern:
    def __init__(self, threshold: float = 0.8, max_iterations: int = 5) -> None:
        self.threshold = threshold
        self.max_iterations = max_iterations

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        generator = agents[0]
        critic = agents[0] if len(agents) == 1 else agents[1]
        output = await generator.run(task, ctx)
        ctx.add_result(output)
        for _ in range(self.max_iterations):
            critique = await critic.run(output.content, ctx)
            ctx.add_result(critique)
            if critique.confidence >= self.threshold:
                output = critique
                break
            output = await generator.run(
                f"Original task: {task}\nCritique: {critique.content}\nRevise:", ctx
            )
            ctx.add_result(output)
        return SwarmResult(
            pattern="reflection",
            results=list(ctx.results),
            final_output=output.content,
        )
```

- [ ] **Step 4: Implement swarm/patterns/broadcast.py**

```python
from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import AgentResult, SwarmContext, SwarmResult


class BroadcastPattern:
    def __init__(self, merge_strategy: str = "concatenate") -> None:
        self.merge_strategy = merge_strategy

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        broadcaster, *listeners = agents
        event = await broadcaster.run(task, ctx)
        ctx.state["broadcast_event"] = event.content
        ctx.add_result(event)
        responses = list(
            await asyncio.gather(*[l.run(event.content, ctx) for l in listeners])
        )
        for r in responses:
            ctx.add_result(r)
        all_results = [event, *responses]
        merged = "\n\n".join(r.content for r in all_results)
        return SwarmResult(
            pattern="broadcast", results=all_results, final_output=merged
        )
```

- [ ] **Step 5: Implement swarm/patterns/auction.py**

```python
from __future__ import annotations
import asyncio
from swarm.core.protocols import Agent
from swarm.core.types import AgentResult, SwarmContext, SwarmResult


class AuctionPattern:
    def __init__(self, bid_prefix: str = "Bid on this task:") -> None:
        self.bid_prefix = bid_prefix

    async def execute(
        self, agents: list[Agent], task: str, ctx: SwarmContext
    ) -> SwarmResult:
        bids: list[AgentResult] = list(
            await asyncio.gather(
                *[a.run(f"{self.bid_prefix} {task}", ctx) for a in agents]
            )
        )
        for b in bids:
            ctx.add_result(b)
        winner_bid = max(bids, key=lambda r: r.confidence)
        winning_agent = next(a for a in agents if a.name == winner_bid.agent_name)
        result = await winning_agent.run(task, ctx)
        ctx.add_result(result)
        return SwarmResult(
            pattern="auction",
            results=[*bids, result],
            final_output=result.content,
        )
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
pytest tests/patterns/ -v
```

Expected: all pattern tests pass.

- [ ] **Step 7: Commit**

```bash
git add swarm/patterns/reflection.py swarm/patterns/broadcast.py swarm/patterns/auction.py \
        tests/patterns/test_reflection.py tests/patterns/test_broadcast.py tests/patterns/test_auction.py
git commit -m "feat: add ReflectionPattern, BroadcastPattern, AuctionPattern"
```

---

### Task 13: DAG Engine

**Files:**
- Create: `swarm/builder/dag.py`
- Create: `tests/builder/test_dag.py`

- [ ] **Step 1: Write failing tests**

```python
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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/builder/test_dag.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/builder/dag.py**

```python
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
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/builder/test_dag.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add swarm/builder/dag.py tests/builder/test_dag.py
git commit -m "feat: add DAG engine with topological sort and predecessor wiring"
```

---

### Task 14: Config Helpers + Swarm Builder

**Files:**
- Create: `swarm/builder/config.py`
- Create: `swarm/builder/swarm.py`
- Create: `tests/builder/test_swarm.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/builder/test_swarm.py
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


async def test_swarm_run_sync(agents):
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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/builder/test_swarm.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/builder/config.py**

```python
from __future__ import annotations
from swarm.core.protocols import Pattern


def pattern_from_name(name: str, entry: dict) -> Pattern:
    name = name.lower()
    if name == "sequential":
        from swarm.patterns.sequential import SequentialPattern
        return SequentialPattern()
    if name == "parallel":
        from swarm.patterns.parallel import ParallelPattern
        return ParallelPattern(merge_strategy=entry.get("merge", "concatenate"))
    if name == "hierarchical":
        from swarm.patterns.hierarchical import HierarchicalPattern
        return HierarchicalPattern()
    if name == "decentralized":
        from swarm.patterns.decentralized import DecentralizedPattern
        return DecentralizedPattern()
    if name == "adaptive":
        from swarm.patterns.adaptive import AdaptivePattern
        return AdaptivePattern(
            threshold=entry.get("threshold", 0.8),
            max_hops=entry.get("max_hops", 5),
        )
    if name == "mesh":
        from swarm.patterns.mesh import MeshPattern
        return MeshPattern(max_rounds=entry.get("max_rounds", 5))
    if name in ("variant_judge", "variantjudge"):
        from swarm.patterns.variant_judge import VariantJudgePattern
        return VariantJudgePattern()
    if name == "reflection":
        from swarm.patterns.reflection import ReflectionPattern
        return ReflectionPattern(
            threshold=entry.get("threshold", 0.8),
            max_iterations=entry.get("max_iterations", 5),
        )
    if name == "broadcast":
        from swarm.patterns.broadcast import BroadcastPattern
        return BroadcastPattern()
    if name == "auction":
        from swarm.patterns.auction import AuctionPattern
        return AuctionPattern()
    raise ValueError(f"Unknown pattern: {name!r}")


def build_provider(provider_cfg: dict, api_key: str | None = None):
    ptype = provider_cfg.get("type", "claude")
    model = provider_cfg.get("model", "claude-sonnet-4-6")
    if ptype == "claude":
        from swarm.providers.claude import ClaudeProvider
        auth_mode = provider_cfg.get("auth_mode", "subscription")
        key = api_key if auth_mode == "api_key" else None
        return ClaudeProvider(model=model, api_key=key)
    if ptype == "ollama":
        from swarm.providers.ollama import OllamaProvider
        return OllamaProvider(model=model, base_url=provider_cfg.get("base_url", "http://localhost:11434"))
    if ptype == "litellm":
        from swarm.providers.litellm import LiteLLMProvider
        return LiteLLMProvider(model=model)
    raise ValueError(f"Unknown provider type: {ptype!r}")
```

- [ ] **Step 4: Implement swarm/builder/swarm.py**

```python
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

    def reflection(self, name: str, agents: list[Agent], *, threshold: float = 0.8, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, ReflectionPattern(threshold=threshold), agents, after)

    def broadcast(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, BroadcastPattern(), agents, after)

    def auction(self, name: str, agents: list[Agent], *, after: str | list[str] | None = None) -> "Swarm":
        return self._add_node(name, AuctionPattern(), agents, after)

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
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
pytest tests/builder/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add swarm/builder/config.py swarm/builder/swarm.py tests/builder/test_swarm.py
git commit -m "feat: add Swarm builder, config helpers, and DAG integration"
```

---

### Task 15: CLI

**Files:**
- Create: `swarm/cli/main.py`
- Create: `tests/cli/test_cli.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/cli/test_cli.py
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from swarm.cli.main import app

runner = CliRunner()


def test_init_creates_config_file(tmp_path):
    result = runner.invoke(app, ["init", "--output", str(tmp_path / "swarm.yaml")])
    assert result.exit_code == 0
    assert (tmp_path / "swarm.yaml").exists()


def test_validate_valid_config(tmp_path):
    config = tmp_path / "swarm.yaml"
    config.write_text(
        "provider:\n  type: claude\nagents:\n  worker:\n    system_prompt: You are a worker.\nswarm:\n  - name: s1\n    pattern: sequential\n    agents: [worker]\n"
    )
    result = runner.invoke(app, ["validate", "--config", str(config)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_invalid_config(tmp_path):
    config = tmp_path / "bad.yaml"
    config.write_text("not: yaml: config")
    result = runner.invoke(app, ["validate", "--config", str(config)])
    assert result.exit_code != 0 or "error" in result.output.lower() or "invalid" in result.output.lower()


def test_run_command_invokes_swarm(tmp_path):
    config = tmp_path / "swarm.yaml"
    config.write_text(
        "provider:\n  type: claude\nagents:\n  worker:\n    system_prompt: You are a worker.\nswarm:\n  - name: s1\n    pattern: sequential\n    agents: [worker]\n"
    )
    mock_result = MagicMock()
    mock_result.final_output = "test output"
    with patch("swarm.cli.main.run_swarm", return_value=mock_result):
        result = runner.invoke(
            app, ["run", "--config", str(config), "do a task"]
        )
    assert result.exit_code == 0
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/cli/test_cli.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement swarm/cli/main.py**

```python
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

import typer
import yaml

app = typer.Typer(help="SWARM — multi-agent coordination library")


def run_swarm(config_path: Path, task: str, api_key: str | None = None):
    from swarm.builder.swarm import Swarm
    from swarm.builder.config import build_provider
    from swarm.agents.llm_agent import LLMAgent

    cfg = yaml.safe_load(config_path.read_text())
    provider = build_provider(cfg.get("provider", {}), api_key=api_key)
    agents = {
        name: LLMAgent(name=name, provider=provider, **spec)
        for name, spec in cfg.get("agents", {}).items()
    }
    swarm = Swarm.from_config(cfg["swarm"], agents)
    return asyncio.run(swarm.run(task))


@app.command()
def run(
    task: str = typer.Argument(..., help="Task to execute"),
    config: Path = typer.Option(..., help="Path to swarm.yaml"),
    api_key: str | None = typer.Option(None, envvar="ANTHROPIC_API_KEY"),
    output: str = typer.Option("text", help="Output format: text | json | markdown"),
):
    """Run a swarm from a config file."""
    if not config.exists():
        typer.echo(f"Error: config file not found: {config}", err=True)
        raise typer.Exit(1)
    result = run_swarm(config, task, api_key=api_key)
    if output == "json":
        import json
        typer.echo(json.dumps({"output": result.final_output, "pattern": result.pattern}))
    elif output == "markdown":
        typer.echo(f"# Result\n\n{result.final_output}")
    else:
        typer.echo(result.final_output)


@app.command()
def init(
    output: Path = typer.Option(Path("swarm.yaml"), help="Output path for config file"),
):
    """Scaffold a swarm config file."""
    template = """\
provider:
  type: claude          # claude | ollama | litellm
  model: claude-sonnet-4-6
  auth_mode: subscription  # subscription (default) | api_key

agents:
  coordinator:
    system_prompt: "You are a coordinator. Break tasks into subtasks."
  worker:
    system_prompt: "You are a thorough researcher and writer."

swarm:
  - name: main
    pattern: sequential
    agents: [coordinator, worker]
"""
    output.write_text(template)
    typer.echo(f"Created {output}")


@app.command()
def validate(
    config: Path = typer.Option(..., help="Path to swarm.yaml"),
):
    """Validate a swarm config file without running it."""
    if not config.exists():
        typer.echo(f"Error: config file not found: {config}", err=True)
        raise typer.Exit(1)
    try:
        cfg = yaml.safe_load(config.read_text())
        if not isinstance(cfg, dict):
            typer.echo("Invalid: config must be a YAML mapping", err=True)
            raise typer.Exit(1)
        if "swarm" not in cfg:
            typer.echo("Invalid: missing 'swarm' key", err=True)
            raise typer.Exit(1)
        if "agents" not in cfg:
            typer.echo("Invalid: missing 'agents' key", err=True)
            raise typer.Exit(1)
        typer.echo(f"Config is valid: {len(cfg['swarm'])} swarm node(s), {len(cfg['agents'])} agent(s)")
    except yaml.YAMLError as e:
        typer.echo(f"Invalid YAML: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def export(
    output: Path = typer.Option(Path("swarm-export.yaml"), help="Output path"),
):
    """Export a swarm config skeleton (use from Python after building programmatically)."""
    typer.echo("Use Swarm().to_config() in Python and write to YAML.")


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/cli/test_cli.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add swarm/cli/main.py tests/cli/test_cli.py
git commit -m "feat: add Typer CLI (run, init, validate, export)"
```

---

### Task 16: Public API + Full Test Suite

**Files:**
- Modify: `swarm/__init__.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
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


async def test_swarm_run_sync_works():
    agent = FakeAgent("solo", response="sync result")
    result = Swarm().sequential("s", [agent]).run_sync("task")
    assert result.final_output == "sync result"
```

- [ ] **Step 2: Run integration test — verify it fails**

```bash
pytest tests/test_integration.py -v
```

Expected: `ImportError` (Swarm not yet exported from `swarm/__init__.py`).

- [ ] **Step 3: Populate swarm/__init__.py**

```python
from swarm.builder.swarm import Swarm
from swarm.agents.llm_agent import LLMAgent
from swarm.providers.claude import ClaudeProvider
from swarm.providers.ollama import OllamaProvider
from swarm.providers.litellm import LiteLLMProvider
from swarm.core.types import AgentResult, Message, SwarmContext, SwarmResult
from swarm.core.protocols import Agent, LLMProvider, Pattern, Tool
from swarm.core.errors import PatternError, ProviderError, SwarmError

__all__ = [
    "Swarm",
    "LLMAgent",
    "ClaudeProvider",
    "OllamaProvider",
    "LiteLLMProvider",
    "AgentResult",
    "Message",
    "SwarmContext",
    "SwarmResult",
    "Agent",
    "LLMProvider",
    "Pattern",
    "Tool",
    "SwarmError",
    "ProviderError",
    "PatternError",
]
```

- [ ] **Step 4: Run full test suite**

```bash
pytest -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add swarm/__init__.py tests/test_integration.py
git commit -m "feat: wire public API and add integration tests"
```

---

### Task 17: Pattern Packages Init Files

**Files:**
- Modify: `swarm/patterns/__init__.py`

- [ ] **Step 1: Populate patterns __init__**

```python
# swarm/patterns/__init__.py
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

__all__ = [
    "SequentialPattern",
    "ParallelPattern",
    "HierarchicalPattern",
    "DecentralizedPattern",
    "AdaptivePattern",
    "MeshPattern",
    "VariantJudgePattern",
    "ReflectionPattern",
    "BroadcastPattern",
    "AuctionPattern",
]
```

- [ ] **Step 2: Run full suite**

```bash
pytest -v
```

Expected: all pass, no regressions.

- [ ] **Step 3: Commit**

```bash
git add swarm/patterns/__init__.py
git commit -m "chore: export all pattern classes from swarm.patterns"
```

---

## Self-Review

**Spec coverage:**
- [x] All 10 patterns implemented: Sequential, Parallel, Hierarchical, Decentralized, Adaptive, Mesh, Variant+Judge, Reflection, Broadcast, Auction
- [x] 3 providers: Claude (subscription + api_key), Ollama, LiteLLM
- [x] LLMAgent with context_window, system_prompt
- [x] DAG engine with topological sort and predecessor wiring
- [x] Fluent builder API with all 10 pattern methods
- [x] Swarm.from_config / to_config roundtrip
- [x] CLI: run, init, validate, export
- [x] Protocol-first with @runtime_checkable
- [x] TDD throughout — FakeProvider, FakeAgent in conftest
- [x] Layer rule: core → providers → agents → patterns → builder → CLI
- [x] SwarmContext entirely in core/types.py
- [x] pytest-asyncio asyncio_mode = "auto" in pyproject.toml

**Type consistency check:**
- `AgentResult` fields used in all patterns: `agent_name`, `content`, `confidence`, `next_agent` — consistent throughout
- `SwarmResult` constructor: `pattern=`, `results=`, `final_output=` — consistent throughout
- `ctx.add_result()` called after every agent.run() — consistent
- `DAG.from_config` calls `pattern_from_name` from `swarm.builder.config` — consistent with implementation

**No placeholders found.**
