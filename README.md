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

### Mixture of Agents (MoA)

All agents except the last run in parallel as *proposers*. The last agent is the *aggregator* — it receives all proposals and synthesises a single answer.

```
         ┌─[proposer1]─┐
input ───┼─[proposer2]─┼──► aggregator ──► final
         └─[proposer3]─┘
```

```python
Swarm().mixture_of_agents("moa", [proposer1, proposer2, proposer3, aggregator])
```

Requires at least 2 agents (1 proposer + aggregator).

**Use when:** you want diverse perspectives collapsed into one high-quality answer — research synthesis, consensus summarisation, ensemble reasoning.

---

### Debate (MAD)

Agents debate in rounds. Round 0: each agent responds independently. Subsequent rounds: each agent receives the other agents' prior responses and revises. Exits early if all agents converge on the same answer.

```
round 0: [a1][a2][a3]  (independent)
round 1: [a1 sees a2,a3][a2 sees a1,a3][a3 sees a1,a2]
...  ──► converged / max_rounds reached
```

```python
Swarm().debate("argue", [agent1, agent2, agent3], max_rounds=3)
```

Requires at least 2 agents.

**Use when:** adversarial challenge improves answer quality — fact-checking, strategy evaluation, red-teaming.

---

### Tree of Thoughts (ToT)

Expands a tree of reasoning branches depth-first. At each depth, *reasoner* agents expand each current thought; the last agent acts as a *validator* and scores branches by confidence. Low-scoring branches are pruned; only the top `branching_factor` branches survive to the next depth. Exits early if a single branch reaches confidence ≥ 0.9.

```
depth 0:  [thought]
depth 1:  [branch_a][branch_b]  ──► validator prunes to top 2
depth 2:  [a1][a2][b1][b2]      ──► validator picks winner
```

```python
Swarm().tree_of_thoughts("tot", [reasoner1, reasoner2, validator],
                          max_depth=3, branching_factor=2)
```

Requires at least 2 agents (≥1 reasoner + validator).

**Use when:** tasks benefit from exploring multiple reasoning paths with pruning — math problems, planning, multi-step logic.

---

### Speculative

Exactly 2 agents: a fast *speculator* and a slower, higher-quality *actor*. The speculator runs first. If its confidence meets the threshold, the result is returned immediately (actor skipped). Otherwise the actor runs and its result is final.

```
[speculator] ──► conf >= threshold? ──► done (fast path)
                        │
                        └──► [actor] ──► done (quality path)
```

```python
Swarm().speculative("fast", [speculator, actor], threshold=0.8)
```

Requires exactly 2 agents.

**Use when:** most inputs are easy (speculator handles them cheaply) but hard inputs need a stronger model — latency-sensitive pipelines with occasional difficult queries.

---

### Blackboard

Agents write to a shared `blackboard` dict each round. Each agent sees the full blackboard contents as context. Rounds repeat until the blackboard stabilises (no changes) or `max_rounds` is reached.

```
round 1: agent1 writes, agent2 writes, agent3 writes
round 2: all re-read board, update if needed
...  ──► stable / max_rounds reached
```

```python
Swarm().blackboard("collab", [agent1, agent2, agent3], max_rounds=5)
```

**Use when:** agents need to collaboratively build shared state — co-authoring, iterative refinement, distributed knowledge assembly.

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

### Using new patterns together

```python
from swarm import Swarm, LLMAgent, ClaudeProvider

provider = ClaudeProvider(model="claude-sonnet-4-6")

def agent(name, prompt=""):
    return LLMAgent(name, provider, system_prompt=prompt)

# Fast speculative triage → multi-perspective proposals → debate to challenge → blackboard refinement
result = (
    Swarm()
    # Quick classifier; if confident, skip the deep analyst
    .speculative("triage",
        [agent("quick_clf", "Classify the query domain in one word."),
         agent("deep_clf",  "Classify the query domain with full reasoning.")],
        threshold=0.85)
    # Multiple experts propose answers in parallel, aggregator synthesises
    .mixture_of_agents("propose",
        [agent("expert_a", "Answer from a security perspective."),
         agent("expert_b", "Answer from a performance perspective."),
         agent("expert_c", "Answer from an architecture perspective."),
         agent("synthesiser", "Combine the proposals into one coherent answer.")])
    # Agents challenge each other to surface weaknesses
    .debate("challenge",
        [agent("devil",    "Find flaws and counter-arguments."),
         agent("defender", "Defend the proposal and rebut critiques.")],
        max_rounds=2)
    # Final collaborative refinement via shared blackboard
    .blackboard("refine",
        [agent("editor",  "Improve clarity and structure."),
         agent("checker", "Verify correctness and add missing detail.")],
        max_rounds=3)
    .run_sync("How should we design authentication for a high-traffic SaaS API?")
)

print(result.final_output)
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
| `mixture_of_agents` | `(name, agents, *, after=None)` | Proposers + aggregator synthesises |
| `debate` | `(name, agents, *, max_rounds=3, after=None)` | Multi-round adversarial debate |
| `tree_of_thoughts` | `(name, agents, *, max_depth=3, branching_factor=2, after=None)` | Branch-and-prune reasoning tree |
| `speculative` | `(name, agents, *, threshold=0.8, after=None)` | Fast speculator, fallback to actor |
| `blackboard` | `(name, agents, *, max_rounds=5, after=None)` | Shared state, iterate to stability |
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
pytest          # 95 tests
```
