# SWARM

![SWARM Logo](logo.png)

A Python library for composing multi-agent AI pipelines using declarative coordination patterns. Chain agents sequentially, run them in parallel, let them debate, vote, or self-correct — then wire stages together into a DAG with a fluent builder API.

---

## Install

```bash
pip install swarm
```

Requires Python 3.11+. LiteLLM support is optional:

```bash
pip install "swarm[litellm]"
```

---

## Setup

### Providers

SWARM ships three providers out of the box.

**Claude (Anthropic)**

```python
from swarm import ClaudeProvider

# Uses ANTHROPIC_API_KEY env var, or pass explicitly
provider = ClaudeProvider(model="claude-sonnet-4-6", api_key="sk-...")
```

**Ollama (local)**

```python
from swarm import OllamaProvider

provider = OllamaProvider(model="llama3", base_url="http://localhost:11434")
```

**LiteLLM (any model)**

```python
from swarm import LiteLLMProvider

provider = LiteLLMProvider(model="gpt-4o", api_key="...")
```

### Agents

Wrap a provider in `LLMAgent` to get a named agent with an optional system prompt:

```python
from swarm import LLMAgent

coordinator = LLMAgent(
    name="coordinator",
    provider=provider,
    system_prompt="You are a coordinator. Break tasks into numbered subtasks.",
)
worker = LLMAgent(name="worker", provider=provider)
```

---

## Quickstart

```python
import asyncio
from swarm import Swarm, LLMAgent, ClaudeProvider

provider = ClaudeProvider(model="claude-sonnet-4-6")
researcher = LLMAgent("researcher", provider, system_prompt="Research thoroughly.")
writer    = LLMAgent("writer",     provider, system_prompt="Write clearly.")

result = (
    Swarm()
    .sequential("research", [researcher])
    .sequential("write",    [writer])
    .run_sync("Write a report on quantum computing")
)

print(result.final_output)
```

Use `run_sync` for scripts, `await run(task)` inside async code.

---

## Patterns

Every method on `Swarm` adds a named stage that runs a particular pattern. Stages chain automatically (each depends on the previous) unless you specify `after=`.

### Sequential

Agents run one after another. Each agent receives the previous agent's output as its input.

```
[agent1] → [agent2] → [agent3]
```

```python
Swarm().sequential("pipeline", [agent1, agent2, agent3])
```

**Use when:** tasks have a natural order — research → draft → edit → review.

---

### Parallel

All agents run concurrently on the same input. Outputs are merged.

```
         ┌─[agent1]─┐
input ───┼─[agent2]─┼──► merged output
         └─[agent3]─┘
```

```python
Swarm().parallel("analyse", [agent1, agent2, agent3])

# Merge strategies: "concatenate" (default), "vote", "synthesize"
Swarm().parallel("vote", [agent1, agent2, agent3], merge="vote")
```

| Strategy | Behaviour |
|---|---|
| `concatenate` | Join all outputs with blank lines |
| `vote` | Return the most common output |
| `synthesize` | Number and join outputs (`1. …\n\n2. …`) |

**Use when:** you need multiple perspectives on the same input, or want to speed up independent subtasks.

---

### Hierarchical

First agent is the coordinator. It creates a plan; workers execute subtasks in parallel; coordinator synthesizes the result.

```
coordinator ──► plan
                 ├─[worker1: subtask1]─┐
                 └─[worker2: subtask2]─┘
                        ↓
              coordinator ──► final synthesis
```

```python
Swarm().hierarchical("team", [coordinator, worker1, worker2])
```

Requires at least 2 agents (coordinator + 1 worker). The coordinator's first response is parsed for numbered subtasks; workers receive one subtask each.

**Use when:** a task is too large for one agent but benefits from central planning and synthesis — research reports, code reviews, document generation.

---

### Decentralized

All agents run in parallel and compete. The agent that returns the highest `confidence` score wins.

```
         ┌─[agent1 conf=0.6]─┐
input ───┼─[agent2 conf=0.9]─┼──► winner (agent2)
         └─[agent3 conf=0.7]─┘
```

```python
Swarm().decentralized("compete", [agent1, agent2, agent3])
```

**Use when:** you want the most confident answer without manual arbitration — fact retrieval, classification, diagnosis.

---

### Adaptive

Agents run sequentially, but each agent can hand off to a named next agent based on confidence. Stops when confidence meets the threshold or max hops is reached.

```
[agent1] ──(low conf, next="agent2")──► [agent2] ──(high conf)──► done
```

```python
Swarm().adaptive("route", [specialist_a, specialist_b, fallback], threshold=0.8)
```

Agents signal hand-off by returning an `AgentResult` with `next_agent` set to another agent's name.

**Use when:** different agents specialise in different domains and you want automatic routing — support triage, multi-domain Q&A.

---

### Reflection

A generator-critic loop. The generator drafts, the critic reviews, the generator revises. Repeats for `max_iterations` rounds.

```
generator ──► draft ──► critic ──► feedback ──► generator ──► ...
```

```python
Swarm().reflection("refine", [generator, critic], max_iterations=3)
```

Requires exactly 2 agents: generator (index 0) and critic (index 1).

**Use when:** output quality matters more than speed — essays, code, plans that need iterative improvement.

---

### Mesh

All agents run in parallel, repeat up to `max_rounds` times, and stop early if all outputs converge (become identical). Final output joins all agent responses.

```
round 1: [a1][a2][a3] ──► not converged
round 2: [a1][a2][a3] ──► converged ──► done
```

```python
Swarm().mesh("consensus", [agent1, agent2, agent3], max_rounds=5)
```

**Use when:** you want agents to iteratively reach consensus — group decision making, distributed estimation.

---

### Variant Judge

Variant agents run in parallel; a judge selects the best response.

```
         ┌─[variant1]─┐
input ───┼─[variant2]─┼──► judge ──► winner
         └─[variant3]─┘
```

```python
Swarm().variant_judge("judge", [variant1, variant2, judge])
```

Last agent in the list is always the judge. Requires at least 2 agents.

**Use when:** you want creative diversity plus explicit quality arbitration — generating and evaluating ad copy, code approaches, hypotheses.

---

### Broadcast

Same as parallel but without merging strategies — all outputs are concatenated. Semantically emphasises "fan-out to all agents, collect all replies."

```python
Swarm().broadcast("notify", [agent1, agent2, agent3])
```

**Use when:** the task is a notification or query that all agents should respond to independently.

---

### Auction

All agents run in parallel and bid via `confidence`. Highest confidence wins — identical to Decentralized but named to emphasise the bidding metaphor.

```python
Swarm().auction("bid", [bidder1, bidder2, bidder3])
```

**Use when:** agents represent different services or specialists and you want the most capable to claim the task.

---

## Combining Patterns

Every stage method returns the `Swarm` instance, so you can chain them. By default each stage depends on the previous one. Use `after=` to wire arbitrary DAGs.

### Linear pipeline

```python
result = (
    Swarm()
    .sequential("research",  [researcher])
    .reflection("draft",     [writer, editor], max_iterations=2)
    .parallel("translate",   [fr_agent, de_agent, es_agent])
    .run_sync("Write a press release about our new product")
)
```

```
[research] ──► [draft/refine] ──► [translate: fr | de | es]
```

---

### Branch and merge

```python
s = Swarm()
s.sequential("plan",    [planner])
s.parallel("research",  [web_agent, db_agent],   after="plan")
s.parallel("draft",     [writer1, writer2],       after="plan")
s.hierarchical("merge", [editor, reviewer1, reviewer2], after=["research", "draft"])

result = await s.run("Produce a market analysis report")
```

```
              ┌──[research: web | db]──┐
[plan] ───────┤                        ├──► [merge: editor + reviewers]
              └──[draft: w1 | w2]──────┘
```

---

### Triage + specialised handling

```python
result = (
    Swarm()
    .adaptive("triage",   [classifier, specialist_a, specialist_b], threshold=0.85)
    .reflection("polish", [generator, critic], max_iterations=2)
    .run_sync("Diagnose this network issue: …")
)
```

```
[triage: route to best specialist] ──► [polish: generate + critique]
```

---

### Full pipeline example

```python
from swarm import Swarm, LLMAgent, ClaudeProvider

provider = ClaudeProvider(model="claude-sonnet-4-6")

def agent(name, prompt=""):
    return LLMAgent(name, provider, system_prompt=prompt)

result = (
    Swarm()
    .hierarchical("plan",    [agent("coord", "Decompose into subtasks."),
                               agent("sub1"), agent("sub2")])
    .parallel("review",      [agent("critic_a"), agent("critic_b")], merge="synthesize")
    .reflection("finalise",  [agent("writer"), agent("editor")], max_iterations=2)
    .run_sync("Design a REST API for a task management app")
)

print(result.final_output)
print(f"Pattern: {result.pattern}")
print(f"Steps:   {len(result.results)}")
```

---

## Config file + CLI

Scaffold a config:

```bash
swarm init                    # writes swarm.yaml
swarm init --output my.yaml   # custom path
```

`swarm.yaml`:

```yaml
provider:
  type: claude
  model: claude-sonnet-4-6

agents:
  coordinator:
    system_prompt: "You are a coordinator. Break tasks into numbered subtasks."
  worker:
    system_prompt: "You are a thorough researcher and writer."

swarm:
  - name: main
    pattern: sequential
    agents: [coordinator, worker]
```

Run:

```bash
swarm run "Write a summary of quantum computing" --config swarm.yaml
swarm run "…" --config swarm.yaml --output json
swarm run "…" --config swarm.yaml --output markdown
```

Validate without running:

```bash
swarm validate --config swarm.yaml
```

---

## API Reference

### `Swarm` builder

| Method | Signature | Description |
|---|---|---|
| `sequential` | `(name, agents, *, after=None)` | Chain agents in order |
| `parallel` | `(name, agents, *, after=None, merge="concatenate")` | Run agents concurrently |
| `hierarchical` | `(name, agents, *, after=None)` | Coordinator + workers |
| `decentralized` | `(name, agents, *, after=None)` | All run, highest confidence wins |
| `adaptive` | `(name, agents, *, threshold=0.8, after=None)` | Route by confidence |
| `mesh` | `(name, agents, *, after=None, max_rounds=5)` | Iterate until convergence |
| `variant_judge` | `(name, agents, *, after=None)` | Variants + judge selects best |
| `reflection` | `(name, agents, *, max_iterations=3, after=None)` | Generator-critic loop |
| `broadcast` | `(name, agents, *, after=None)` | Fan-out, collect all |
| `auction` | `(name, agents, *, after=None)` | All bid, highest confidence wins |
| `run` | `(task, ctx=None) -> SwarmResult` | Execute (async) |
| `run_sync` | `(task) -> SwarmResult` | Execute (sync) |
| `to_config` | `() -> list[dict]` | Serialise to config |
| `from_config` | `(config, agents) -> Swarm` | Deserialise from config |

### `SwarmResult`

```python
result.final_output   # str   — the final answer
result.pattern        # str   — pattern name of the last stage
result.results        # list[AgentResult] — all intermediate results
```

### `AgentResult`

```python
result.agent_name   # str
result.content      # str
result.confidence   # float (default 1.0)
result.next_agent   # str | None  (used by AdaptivePattern)
```

---

## Development

```bash
pip install -e ".[dev]"
pytest          # 64 tests
```
