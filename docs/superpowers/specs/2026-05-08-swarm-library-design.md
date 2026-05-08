# SWARM Library — Design Spec

**Date:** 2026-05-08  
**Status:** Approved

## Overview

A Python library implementing ten swarm agent design patterns, with a hybrid composition mode that lets any number of patterns be combined to tackle complex tasks. Agents are LLMs backed by Claude (default: subscription/auth-token mode), Claude API key, Ollama (open-source models), or LiteLLM.

## Decisions Summary

| Decision | Choice |
|---|---|
| Interface | Python SDK + CLI (Typer) |
| Agent definition | Config-driven (`LLMAgent`) + class-based (`BaseAgent`) |
| Hybrid composition | Builder (fluent) → DAG engine → auto-serialized config |
| State/context | Shared store (`SwarmContext.state`) + typed messages (`AgentResult`) |
| Async | Async-first; `run_sync()` convenience wrapper |
| Architecture | Protocol-first (`typing.Protocol` at every boundary) |
| Package layout | Layered subpackages |
| Auth default | Claude subscription (auth token, no API key) |
| Testing | TDD — no real LLM calls in any test |

---

## Package Structure

```
swarm/
├── __init__.py              # public API re-exports
├── py.typed                 # PEP 561 marker

├── core/                    # Layer 0: protocols + data types
│   ├── protocols.py         # LLMProvider, Agent, Pattern, Tool
│   ├── types.py             # Message, AgentResult, SwarmResult, SwarmContext
│   └── errors.py            # SwarmError, ProviderError, PatternError

├── providers/               # Layer 1: LLM backends
│   ├── base.py
│   ├── claude.py            # auth token (default) or API key
│   ├── ollama.py            # Gemma4, Qwen-2.5b, etc.
│   └── litellm.py           # any litellm-supported model

├── agents/                  # Layer 2: agent implementations
│   ├── base.py              # BaseAgent (subclass for custom logic)
│   ├── llm_agent.py         # LLMAgent — config-driven
│   └── context.py           # SwarmContext implementation

├── patterns/                # Layer 3: pattern implementations
│   ├── base.py
│   ├── sequential.py
│   ├── parallel.py
│   ├── hierarchical.py
│   ├── decentralized.py
│   ├── adaptive.py
│   ├── mesh.py
│   ├── variant_judge.py
│   ├── reflection.py
│   ├── broadcast.py
│   └── auction.py

├── builder/                 # Layer 4: swarm composition
│   ├── swarm.py             # Swarm builder class
│   ├── dag.py               # DAG engine
│   └── config.py            # serialize/deserialize to/from dict/YAML

└── cli/                     # Layer 5: CLI
    └── main.py              # Typer app
```

**Layer rule:** each layer imports only from layers to its right. `core` has zero external dependencies.

---

## Core Protocols & Types

### Protocols (`swarm/core/protocols.py`)

```python
from typing import Protocol, runtime_checkable, Any

@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self, messages: list[Message], *,
        tools: list[Tool] | None = None,
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
        self, agents: list[Agent], task: str, ctx: SwarmContext,
    ) -> SwarmResult: ...

@runtime_checkable
class Tool(Protocol):
    name: str
    description: str
    async def __call__(self, **kwargs: Any) -> Any: ...
```

### Data types (`swarm/core/types.py`)

```python
@dataclass
class Message:
    role: str          # "user" | "assistant" | "system" | "tool"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentResult:
    agent_name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    next_agent: str | None = None    # routing hint for adaptive pattern
    confidence: float = 1.0          # used by adaptive + decentralized

@dataclass
class SwarmResult:
    pattern: str
    results: list[AgentResult]
    final_output: str
    metadata: dict[str, Any] = field(default_factory=dict)

class SwarmContext:
    state: dict[str, Any]       # shared key-value store (read/write by any agent)
    history: list[Message]      # full conversation history
    results: list[AgentResult]  # accumulated agent results

    def add_result(self, result: AgentResult) -> None: ...
```

---

## Provider & Auth Layer

### ClaudeProvider (`swarm/providers/claude.py`)

Two auth modes:

- **`subscription`** (default): Claude CLI subprocess. No API key. Requires `claude` CLI installed and logged in. Same pattern as the AIDE project.
- **`api_key`**: Anthropic SDK (`AsyncAnthropic`). Reads `ANTHROPIC_API_KEY` env var or explicit `api_key=` parameter.

Auto-detection: if `ANTHROPIC_API_KEY` env var is set or `api_key=` is passed → `api_key` mode; otherwise → `subscription` mode.

```python
ClaudeProvider()                              # subscription mode (default)
ClaudeProvider(auth_mode="api_key")          # reads ANTHROPIC_API_KEY env var
ClaudeProvider(api_key="sk-ant-...")         # explicit key → api_key mode
```

### OllamaProvider (`swarm/providers/ollama.py`)

HTTP calls to local Ollama server (`http://localhost:11434` by default). Supports any Ollama model: `gemma3`, `qwen2.5:3b`, etc.

### LiteLLMProvider (`swarm/providers/litellm.py`)

Wraps `litellm.acompletion()`. Accepts any litellm model string (`gpt-4o`, `gemini/gemini-2.0-flash`, etc.).

---

## Agent Layer

### LLMAgent (`swarm/agents/llm_agent.py`)

Config-driven. Implements `Agent` protocol without subclassing.

```python
LLMAgent(
    name="researcher",
    provider=ClaudeProvider(),
    system_prompt="You are a thorough researcher.",
    tools=[search_tool],
    temperature=0.7,
)
```

`run()` builds messages from `system_prompt` + last 10 turns of `ctx.history` + current task, calls `provider.complete()`, returns `AgentResult`.

### BaseAgent (`swarm/agents/base.py`)

Subclass for custom agent logic. Provides `name` and `provider`; requires `run()` override.

### agent_from_config()

Factory function: `dict → LLMAgent`. Used by `Swarm.from_config()` and CLI.

---

## Pattern Implementations

All patterns implement the `Pattern` protocol: `async execute(agents, task, ctx) → SwarmResult`.

### Sequential
Chains agents: output of each becomes input of next. Strict ordering.

### Parallel
`asyncio.gather()` fan-out across all agents. Configurable merge strategy: `"concatenate"` | `"vote"` | `"synthesize"`.

### Hierarchical
First agent = coordinator: decomposes task into subtasks. Remaining agents = workers: run subtasks in parallel. Coordinator synthesizes results.

### Decentralized
All agents run independently on same task. Results combined via weighted consensus (weight = `AgentResult.confidence`).

### Adaptive
Dynamic routing: run agent → check `confidence >= threshold` → if low, follow `next_agent` hint to route to specialist. Configurable `confidence_threshold` (default 0.8) and `max_hops` (default 5).

### Mesh P2P
Agents communicate via shared `ctx.state["mesh_round"]`. Multiple rounds until results converge or `max_rounds` reached.

### Variant + Judge
All agents except the last run as "variant" workers in parallel — each produces a distinct solution/approach to the same task. The final agent is the judge: it receives all variant outputs formatted as a numbered list and returns the best solution (or a synthesized combination). The judge acts as an LLM evaluator, not a consensus mechanism; it reasons explicitly about trade-offs before picking or blending variants.

```python
*variants, judge = agents
results = await asyncio.gather(*[v.run(task, ctx) for v in variants])
for r in results:
    ctx.add_result(r)
judge_input = format_variants(results)   # "Variant 1: ...\nVariant 2: ..."
final = await judge.run(judge_input, ctx)
return SwarmResult(pattern="variant_judge", results=[*results, final], final_output=final.content)
```

Configurable `judge_prompt_template` (default instructs the judge to evaluate and select/synthesize). At least 2 agents required (1+ variants + 1 judge).

### Reflection
A generator agent produces output; a critic agent evaluates it. If the critic's `confidence < threshold`, the generator revises using the critique. Repeats until the critic is satisfied or `max_iterations` (default 3) is reached.

- **1-agent form**: single agent plays both roles — generates, then critiques its own output, then regenerates.
- **2-agent form**: `agents[0]` = generator, `agents[1]` = critic.

```python
generator, critic = (agents[0], agents[0]) if len(agents) == 1 else (agents[0], agents[1])
output = await generator.run(task, ctx)
for _ in range(max_iterations):
    critique = await critic.run(output.content, ctx)
    ctx.add_result(critique)
    if critique.confidence >= threshold:
        break
    output = await generator.run(
        f"Original task: {task}\nCritique: {critique.content}\nRevise:", ctx
    )
    ctx.add_result(output)
return SwarmResult(pattern="reflection", results=ctx.results, final_output=output.content)
```

Configurable `confidence_threshold` (default 0.8) and `max_iterations` (default 3).

### Broadcast
First agent = broadcaster: runs on the task and produces an event/message. All remaining agents = listeners: receive the broadcast output in parallel and each responds independently. Results are aggregated (concatenate by default).

Distinct from Parallel in that there is an explicit triggering step — the broadcaster shapes WHAT the listeners receive, rather than all agents seeing the raw task.

```python
broadcaster, *listeners = agents
event = await broadcaster.run(task, ctx)
ctx.state["broadcast_event"] = event.content
ctx.add_result(event)
responses = await asyncio.gather(*[l.run(event.content, ctx) for l in listeners])
for r in responses:
    ctx.add_result(r)
merged = merge_results([event, *responses], strategy=merge_strategy)
return SwarmResult(pattern="broadcast", results=[event, *responses], final_output=merged)
```

Configurable `merge_strategy`: `"concatenate"` | `"synthesize"` (default `"concatenate"`).

### Auction
All agents evaluate the task in parallel (bid round), each returning a `confidence` score representing their self-assessed capability. The agent with the highest confidence wins and executes the task fully (execution round).

Agents should be prompted with a `bid_prefix` (default `"[BID]"`) to signal bid mode — system prompts should instruct agents to respond with a confidence score and rationale rather than attempting the full task.

```python
bids = await asyncio.gather(*[a.run(f"{bid_prefix} {task}", ctx) for a in agents])
winner_bid = max(bids, key=lambda r: r.confidence)
winning_agent = next(a for a in agents if a.name == winner_bid.agent_name)
result = await winning_agent.run(task, ctx)
return SwarmResult(pattern="auction", results=[*bids, result], final_output=result.content)
```

Configurable `bid_prefix` (default `"[BID]"`). At least 2 agents required.

---

## Agent Roles

Roles are not separate pattern classes — they are behavioral contracts expressed through `LLMAgent(system_prompt=...)`. The pattern determines structure; the role determines behavior. Any agent can play any role in any pattern.

| Role | Responsibility | Typical pattern context |
|---|---|---|
| **Planner** | Breaks high-level goals into ordered steps | Hierarchical (coordinator), Sequential (first agent) |
| **Orchestrator** | Coordinates agent interactions based on a plan | Hierarchical (coordinator), Adaptive (router) |
| **Executor/Worker** | Executes a specific subtask; may use tools | All patterns (worker agents) |
| **Observer/Monitor** | Watches state/events; reports findings without acting | Mesh (monitoring agents), Broadcast (listener) |
| **Judge/Critic** | Validates output quality; provides structured feedback | Variant+Judge (judge), Reflection (critic) |
| **Enforcer** | Guards protocol compliance; blocks or flags violations | Sequential (last agent), any pattern as a post-step |

Roles are composable — the same `LLMAgent` instance can act as a Planner in one DAG node and a Judge in another.

---

## Advanced Mechanisms

### Shared Memory / Blackboard
`SwarmContext.state` IS the blackboard. Any agent can read or write any key during `run()`. Patterns use namespaced keys by convention (e.g., `"mesh_round"`, `"broadcast_event"`, `"{node}.output"`).

### Context-Minimization
`LLMAgent.run()` passes the last 10 turns of `ctx.history` by default. For tasks where agents should only receive task-specific context (not shared history), set `context_window=0` on the `LLMAgent` — it will only receive its `system_prompt` + the immediate task string, preventing context bleed between agents.

```python
LLMAgent(name="executor", provider=..., system_prompt="...", context_window=0)
```

### Pattern Aliases (Mapping to Common Terminology)

| Common name | Library pattern |
|---|---|
| Pipeline | Sequential |
| Orchestrator-Worker / Delegative | Hierarchical |
| Autonomous Handoffs / Specialization with Handoffs | Adaptive |
| Debate / Competitive | Variant+Judge |
| Fan-Out/Fan-In | Parallel |
| Blackboard | SwarmContext.state (mechanism, not a pattern) |

---

## Swarm Builder & DAG Engine

### Swarm (`swarm/builder/swarm.py`)

Fluent builder. Each method adds a DAG node. `after=` param controls dependencies (defaults to previous node).

```python
# Linear (implicit chaining)
result = await (Swarm()
    .hierarchical("plan", [coordinator, *workers])
    .parallel("research", [r1, r2, r3])
    .sequential("write", [writer, editor])
    .adaptive("review", [reviewer, specialist])
    .variant_judge("select", [draft_a, draft_b, judge])
    .reflection("refine", [generator, critic])
    .broadcast("notify", [broadcaster, listener_a, listener_b])
    .auction("assign", [specialist_a, specialist_b, specialist_c])
    .run("task"))

# Branching (explicit after=)
s = Swarm()
s.hierarchical("plan",     [coordinator, *workers])
s.parallel("research",     [r1, r2, r3], after="plan")
s.parallel("data",         [d1, d2],      after="plan")
s.sequential("synthesize", [synth],       after=["research", "data"])
result = await s.run("task")

# Sync convenience
result = s.run_sync("task")

# Serialize to config
config = s.to_config()

# Load from config
s = Swarm.from_config(config, agents=agent_registry)
```

### DAG (`swarm/builder/dag.py`)

- Nodes: `{name, pattern, agents, dependencies}`
- `execute()`: topological sort → execute nodes in order
- Before executing each node, the DAG collects all predecessor outputs from `ctx.state["{dep}.output"]`, joins them (newline-separated), and writes the result to `ctx.state["{name}.input"]`. Nodes with no dependencies use the original task string.
- After executing each node, the DAG writes `result.final_output` to `ctx.state["{name}.output"]`
- Nodes with multiple `after=` dependencies receive all predecessors' outputs merged in declaration order

### Config (`swarm/builder/config.py`)

Serialize/deserialize `Swarm` ↔ `dict` ↔ YAML. Used by CLI and `Swarm.from_config()`.

---

## CLI

Built with Typer. Entry point: `swarm` command.

```bash
# Run from config file
swarm run --config swarm.yaml "task"

# Inline single pattern
swarm run --pattern hierarchical --agents coordinator,worker1 "task"

# Provider overrides
swarm run --config swarm.yaml --api-key sk-ant-... "task"
swarm run --config swarm.yaml --provider ollama --model gemma3 "task"

# Output format
swarm run --config swarm.yaml --output json "task"

# Scaffold
swarm init > swarm.yaml

# Validate
swarm validate --config swarm.yaml

# Export SDK swarm to YAML
swarm export --config generated.yaml  # from programmatic Swarm
```

### swarm.yaml format

```yaml
provider:
  type: claude           # claude | ollama | litellm
  model: claude-sonnet-4-6
  auth_mode: subscription   # subscription (default) | api_key

agents:
  coordinator:
    system_prompt: "Break tasks into subtasks."
  researcher:
    system_prompt: "Research thoroughly."
  writer:
    system_prompt: "Write clear reports."

swarm:
  - name: plan
    pattern: hierarchical
    agents: [coordinator, researcher]
  - name: research
    pattern: parallel
    agents: [researcher, researcher]
    after: plan
    merge: synthesize
  - name: write
    pattern: sequential
    agents: [writer]
    after: research
```

---

## TDD Approach

### Test structure

```
tests/
├── core/        test_protocols.py, test_types.py
├── providers/   test_claude.py, test_ollama.py, test_litellm.py
├── agents/      test_llm_agent.py, test_base_agent.py
├── patterns/    test_sequential.py, test_parallel.py, test_hierarchical.py
│                test_decentralized.py, test_adaptive.py, test_mesh.py
│                test_variant_judge.py, test_reflection.py
│                test_broadcast.py, test_auction.py
├── builder/     test_swarm.py, test_dag.py, test_config.py
└── cli/         test_main.py
```

### Rules

1. **No real LLM calls** in any test. Protocol boundaries make fakes trivial.
2. **Write test first**, minimum code to pass.
3. **TDD order**: core → providers → agents → patterns → builder → CLI

### Key test fixtures

```python
class FakeProvider:
    async def complete(self, messages, **kw) -> str:
        return "fake response"

class FakeAgent:
    def __init__(self, name, response="ok", confidence=1.0, next_agent=None):
        self.name = name
        self._response, self._confidence, self._next = response, confidence, next_agent

    async def run(self, task, ctx):
        return AgentResult(agent_name=self.name, content=self._response,
                           confidence=self._confidence, next_agent=self._next)
```

Both satisfy their protocols structurally — no mock framework needed.

### Provider auth testing

- Subscription mode: mock subprocess call, assert correct CLI args
- API key mode: mock `AsyncAnthropic`, assert correct messages
- `_resolve_auth_mode()`: parametric tests across env var / kwarg combinations

---

## Public API (`swarm/__init__.py`)

```python
from swarm import (
    Swarm,            # builder
    Agent,            # protocol (for type hints)
    BaseAgent,        # subclass for custom agents
    LLMAgent,         # config-driven agent
    ClaudeProvider,   # auth token or API key
    OllamaProvider,   # open-source LLMs
    LiteLLMProvider,  # any litellm model
    AgentResult,      # typed inter-agent message
    SwarmResult,      # aggregate pattern output
    SwarmContext,     # shared state store
)
```

---

## Dependencies

```toml
[project]
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "anthropic>=0.40",   # for API key mode
    "httpx>=0.27",       # for Ollama provider
    "pyyaml>=6.0",
]

[project.optional-dependencies]
litellm = ["litellm>=1.40"]
dev = ["pytest>=8", "pytest-asyncio>=0.23", "ruff", "mypy"]

[project.scripts]
swarm = "swarm.cli.main:app"
```

`litellm` is optional — only installed if needed. Ollama uses plain HTTP (`httpx`), no extra dep.
