# Swarm Agent Architecture Patterns: A Comprehensive Library Guide

> A definitive guide to implementing multi-agent swarm architectures for different scenarios, with detailed patterns, trade-offs, and production-ready implementation strategies.

**Last Updated**: May 2026  
**Status**: Production-Ready Framework Guide

---

## Table of Contents

1. [Overview](#overview)
2. [Core Patterns](#core-patterns)
3. [Pattern Comparison Matrix](#pattern-comparison-matrix)
4. [Detailed Pattern Specifications](#detailed-pattern-specifications)
5. [Implementation Framework](#implementation-framework)
6. [Decision Framework](#decision-framework)
7. [Hybrid Architectures](#hybrid-architectures)
8. [Common Pitfalls & Solutions](#common-pitfalls--solutions)
9. [Production Deployment Patterns](#production-deployment-patterns)

---

## Overview

Multi-agent swarm systems represent a fundamental shift in how AI orchestrates complex work. Rather than building monolithic single-agent systems, modern architectures distribute work across specialized agents that coordinate through various patterns.

### Key Principles

- **Emergence**: Complex system behavior emerges from simple local agent interactions
- **Scalability**: Patterns scale horizontally by adding agents rather than increasing model complexity
- **Fault Isolation**: Failure of one agent doesn't cascade through the entire system
- **Specialization**: Each agent develops deep expertise in a narrowly-scoped domain
- **Flexibility**: Different patterns suit different task structures and constraints

### Why Pattern Selection Matters

Pattern selection is **the highest-impact architectural decision** in multi-agent systems. It conditions every subsequent implementation choice, from storage mechanisms to communication protocols to failure handling.

---

## Core Patterns

Every production multi-agent system maps to one of five core patterns (or hybrid combinations):

### 1. **Decentralized Swarm** (Autonomous Collaboration)
Agents have shared context and working memory, deciding amongst themselves when to hand off tasks, with no central controller.

### 2. **Hierarchical Swarms** (Coordinator/Worker)
A structured approach where superior agents (supervisors) manage and delegate to specialized sub-agents in a tree-like structure.

### 3. **Parallel Swarms**
Multiple agents operate simultaneously on different aspects of a task, ideal for increased speed and independent processing.

### 4. **Sequential Swarms** (Pipeline/Chain)
Agents operate in a linear sequence, where one agent's output is the next agent's input, like a data transformation pipeline.

### 5. **Adaptive Swarms**
Teams that dynamically reorganize their structure or change members based on real-time task requirements.

### 6. **Mesh / Peer-to-Peer**
Agents communicate directly with each other to share information without a strict hierarchy, often used for distributed tasks.

---

## Pattern Comparison Matrix

| Aspect | Decentralized Swarm | Hierarchical | Parallel | Sequential | Adaptive | Mesh P2P |
|--------|-------------------|--------------|----------|-----------|----------|----------|
| **Coordination** | Emergent | Top-down | Central dispatch | Linear handoff | Dynamic rules | Direct negotiation |
| **Latency** | Variable | Medium | Low (parallel) | Highest (serial) | Medium-High | Medium |
| **Scalability** | Excellent (100+) | Good (50+) | Excellent | Limited (<10) | Very Good | Poor (3-8 optimal) |
| **Fault Tolerance** | Excellent | Moderate | Good | Poor | Excellent | Good |
| **Control Visibility** | Low | High | High | Very High | Medium | Medium |
| **Token Overhead** | Medium | Higher | Medium | Low | High | Medium |
| **Debugging Difficulty** | Hard | Easy | Medium | Easy | Hard | Medium |
| **Production Maturity** | Emerging | Proven | Proven | Proven | Experimental | Established |

---

## Detailed Pattern Specifications

### Pattern 1: Decentralized Swarm (Autonomous Collaboration)

#### Definition
A collection of autonomous agents operating as peers with shared context and working memory. Agents make local decisions based on environment signals and shared state, dynamically handing off tasks without a central orchestrator.

#### Characteristics

```
┌─────────────┐
│  Blackboard │  (Shared State/Context)
│  (Shared)   │
└──────┬──────┘
       │
   ┌───┴───┬───────┬─────────┐
   │       │       │         │
  ┌▼─┐   ┌▼─┐   ┌▼─┐   ┌──▼─┐
  │A1│   │A2│   │A3│...│ An │  (Autonomous Agents)
  └──┘   └──┘   └──┘   └────┘
   
  ↔ Direct Handoffs ↔ (No Central Control)
```

**Core Features**:
- **Shared Blackboard**: Central state repository all agents observe and modify
- **Autonomous Handoffs**: Agents decide when to pass tasks based on context and expertise
- **Emergent Behavior**: System intelligence emerges from collective local decisions
- **Distributed Control**: No single point of failure or bottleneck
- **Self-Organization**: Team reorganizes dynamically based on task requirements

#### Advantages

- ✅ **No Single Point of Failure**: If one agent fails, others continue
- ✅ **Maximum Parallelism**: Many agents can act simultaneously
- ✅ **Scales Horizontally**: Add agents without redesigning coordination logic
- ✅ **Self-Healing**: System automatically adapts to agent failures
- ✅ **Emergent Problem-Solving**: Cross-domain collaboration without explicit routing

#### Disadvantages

- ❌ **Hard to Debug**: Complex emergent behavior difficult to trace
- ❌ **Unpredictable Outcomes**: Behavior can vary across runs
- ❌ **Handoff Ping-Pong**: Agents can get stuck endlessly handing off
- ❌ **State Consistency**: Shared state can cause conflicts under contention
- ❌ **Higher Token Cost**: More agent thinking and negotiation overhead

#### Best Use Cases

- **Research & Exploration**: Multi-angle problem analysis
- **Creative Brainstorming**: Diverse perspectives on ideation
- **Fault-Tolerant Systems**: Resilience is paramount
- **Distributed Systems**: Agents across different machines/regions
- **Complex Reasoning**: Problems requiring cross-domain collaboration

#### Implementation Example (TypeScript/Node.js)

```typescript
// Core types for Decentralized Swarm
interface SwarmAgent {
  id: string;
  expertise: string[];
  systemPrompt: string;
  tools?: Record<string, Function>;
}

interface SharedContext {
  taskQueue: Task[];
  completedTasks: Record<string, TaskResult>;
  agentStates: Record<string, AgentState>;
  sharedMemory: Record<string, any>;
}

interface SwarmConfig {
  agents: SwarmAgent[];
  maxHandoffs: number;
  handoffDetectionWindow: number;
  contextStore: ContextStore;
}

class DecentralizedSwarm {
  private agents: SwarmAgent[];
  private context: SharedContext;
  private handoffHistory: HandoffRecord[] = [];
  private maxHandoffs: number;
  
  constructor(config: SwarmConfig) {
    this.agents = config.agents;
    this.context = {
      taskQueue: [],
      completedTasks: {},
      agentStates: {},
      sharedMemory: {}
    };
    this.maxHandoffs = config.maxHandoffs;
  }

  async executeSwarm(initialTask: string): Promise<any> {
    this.context.taskQueue.push({
      id: generateId(),
      content: initialTask,
      createdAt: Date.now()
    });

    let activeAgent = this.selectInitialAgent(initialTask);
    let handoffCount = 0;

    while (this.context.taskQueue.length > 0 && handoffCount < this.maxHandoffs) {
      const task = this.context.taskQueue[0];

      // Get agent response
      const response = await this.getAgentResponse(activeAgent, task);

      // Check if agent wants to hand off
      if (response.handoffTo) {
        // Detect ping-pong (same agents repeatedly handing off)
        if (this.isPingPong(activeAgent.id, response.handoffTo)) {
          console.warn('Ping-pong detected, forcing task completion');
          await this.forceTaskCompletion(task, response);
          break;
        }

        activeAgent = this.agents.find(a => a.id === response.handoffTo)!;
        this.handoffHistory.push({
          from: activeAgent.id,
          to: response.handoffTo,
          reason: response.handoffReason,
          timestamp: Date.now()
        });
        handoffCount++;
      } else {
        // Agent completed the task
        this.context.completedTasks[task.id] = response;
        this.context.taskQueue.shift();
      }
    }

    return {
      results: this.context.completedTasks,
      handoffSequence: this.handoffHistory,
      finalState: this.context.sharedMemory
    };
  }

  private selectInitialAgent(task: string): SwarmAgent {
    // Use relevance scoring to select best initial agent
    return this.agents.reduce((best, agent) => {
      const score = this.scoreRelevance(agent.expertise, task);
      return score > (best._score || 0) ? { ...agent, _score: score } : best;
    });
  }

  private async getAgentResponse(agent: SwarmAgent, task: Task): Promise<any> {
    const systemPrompt = `${agent.systemPrompt}

SHARED CONTEXT:
${JSON.stringify(this.context.sharedMemory, null, 2)}

TASK QUEUE STATUS:
${this.context.taskQueue.length} tasks pending

If you can complete this task or make progress, respond with your work.
If another agent is better suited, respond with { "handoffTo": "agent_id", "handoffReason": "..." }
If you need help or clarification, respond with { "needsInput": true, "question": "..." }`;

    const response = await callClaudeAPI({
      systemPrompt,
      userMessage: task.content,
      tools: agent.tools
    });

    // Update agent state in shared context
    this.context.agentStates[agent.id] = {
      lastActive: Date.now(),
      currentTask: task.id,
      status: 'active'
    };

    return response;
  }

  private isPingPong(fromId: string, toId: string): boolean {
    const recentHandoffs = this.handoffHistory.slice(-5);
    const pingPongPattern = recentHandoffs.filter(h => 
      (h.from === fromId && h.to === toId) ||
      (h.from === toId && h.to === fromId)
    );
    return pingPongPattern.length >= 3;
  }

  private scoreRelevance(expertise: string[], task: string): number {
    // Simple TF-IDF style relevance scoring
    const taskWords = task.toLowerCase().split(/\s+/);
    return expertise.reduce((score, skill) => {
      return score + taskWords.filter(word => 
        word.includes(skill.toLowerCase())
      ).length;
    }, 0);
  }
}
```

#### Configuration Example

```typescript
const swarmConfig: SwarmConfig = {
  agents: [
    {
      id: 'researcher',
      expertise: ['research', 'data', 'analysis', 'investigation'],
      systemPrompt: `You are a researcher specialized in gathering and analyzing information.
You excel at finding patterns, reading between lines, and identifying gaps in knowledge.
Always cite your sources and note assumptions.`
    },
    {
      id: 'strategist',
      expertise: ['strategy', 'planning', 'business', 'problem-solving'],
      systemPrompt: `You are a strategic consultant.
You excel at identifying opportunities, weighing trade-offs, and developing actionable plans.
Always consider multiple perspectives and edge cases.`
    },
    {
      id: 'writer',
      expertise: ['writing', 'communication', 'clarity', 'storytelling'],
      systemPrompt: `You are an expert writer and communicator.
You excel at distilling complex ideas into clear, engaging narratives.
Always tailor tone and depth to your audience.`
    }
  ],
  maxHandoffs: 10,
  handoffDetectionWindow: 5,
  contextStore: new RedisContextStore()
};

const swarm = new DecentralizedSwarm(swarmConfig);
```

---

### Pattern 2: Hierarchical Swarms (Coordinator/Worker)

#### Definition
A tree-structured multi-level orchestration system where superior agents (directors/supervisors) create plans, delegate to specialized worker agents, evaluate results, and issue feedback loops. Top level reasons about strategy; middle levels reason about task assignment; leaf levels execute.

#### Characteristics

```
            ┌─────────────┐
            │   Director  │  (Strategic Planning)
            └──────┬──────┘
                   │
          ┌────────┼────────┐
          │        │        │
      ┌───▼──┐ ┌──▼──┐ ┌──▼──┐
      │Super1│ │Super2│ │Super3│  (Mid-Level Supervisors)
      └───┬──┘ └──┬──┘ └──┬──┘
          │       │       │
      ┌──┬┴─┐ ┌──┬┴─┐ ┌──┬┴─┐
     ┌▼──┐┌▼─┐┌▼──┐┌▼─┐┌▼──┐┌▼─┐
     │W1 ││W2││W3 ││W4││W5 ││W6│  (Worker Agents)
     └───┘└──┘└───┘└──┘└───┘└──┘
```

**Workflow**:
1. User provides task to director
2. Director creates comprehensive plan
3. Director delegates subtasks to supervisors
4. Supervisors coordinate worker agents
5. Workers execute domain-specific tasks
6. Results flow back up; director evaluates and loops if needed

#### Advantages

- ✅ **Clear Auditability**: Single control flow easy to trace
- ✅ **Horizontal Scaling**: Add workers for new categories without redesign
- ✅ **Quality Control**: Director validates outputs before propagation
- ✅ **Specialization**: Clear domain boundaries per team
- ✅ **Production-Proven**: Proven at scale (hundreds of agents)

#### Disadvantages

- ❌ **Higher Latency**: Multiple coordination levels add delay
- ❌ **Communication Overhead**: Grows with hierarchy depth
- ❌ **Rigidity**: Difficult handling novel situations outside hierarchy
- ❌ **State Management**: Each level needs visibility into worker progress
- ❌ **Token Overhead**: Director must re-transmit context through hierarchy

#### Best Use Cases

- **Customer Support Automation**: Triage and routing at scale (90%+ autonomous resolution)
- **Enterprise Workflows**: 50+ agents across business domains
- **Project Management**: Complex task decomposition and coordination
- **Quality Assurance**: Central validation before outputs advance
- **Regulated Systems**: Audit trails and compliance requirements

#### Implementation Example

```typescript
interface HierarchicalConfig {
  director: DirectorAgent;
  supervisors: SupervisorAgent[];
  workers: WorkerAgent[];
  maxLoops: number;
  feedbackStrategy: 'strict' | 'lenient' | 'adaptive';
}

class HierarchicalSwarm {
  private director: DirectorAgent;
  private supervisors: Map<string, SupervisorAgent>;
  private workers: Map<string, WorkerAgent>;
  private planningMemory: PlanHistory[] = [];
  private executionLog: ExecutionRecord[] = [];
  
  constructor(config: HierarchicalConfig) {
    this.director = config.director;
    this.supervisors = new Map(supervisors.map(s => [s.id, s]));
    this.workers = new Map(workers.map(w => [w.id, w]));
  }

  async execute(userTask: string): Promise<ExecutionResult> {
    let loopCount = 0;
    let currentPlan: Plan | null = null;

    while (loopCount < this.maxLoops) {
      // PHASE 1: Director Planning
      console.log(`[Loop ${loopCount + 1}] Director creating plan...`);
      currentPlan = await this.directorPlanning(userTask, this.planningMemory);
      this.planningMemory.push({
        loopNumber: loopCount,
        plan: currentPlan,
        timestamp: Date.now()
      });

      // PHASE 2: Supervisor Delegation
      console.log(`[Loop ${loopCount + 1}] Supervisors delegating to workers...`);
      const supervisorResults = await this.supervisorDelegation(currentPlan);

      // PHASE 3: Worker Execution
      console.log(`[Loop ${loopCount + 1}] Workers executing tasks...`);
      const workerResults = await this.workerExecution(supervisorResults);

      // PHASE 4: Director Evaluation
      console.log(`[Loop ${loopCount + 1}] Director evaluating results...`);
      const evaluation = await this.directorEvaluation(
        currentPlan,
        workerResults,
        userTask
      );

      this.executionLog.push({
        loopNumber: loopCount,
        plan: currentPlan,
        results: workerResults,
        evaluation,
        timestamp: Date.now()
      });

      // Check if we should loop
      if (evaluation.isComplete || evaluation.confidence > 0.85) {
        return {
          success: true,
          finalResults: workerResults,
          planHistory: this.planningMemory,
          executionLog: this.executionLog,
          completedInLoops: loopCount + 1
        };
      }

      // Prepare for next loop with feedback
      userTask = evaluation.refinedTask;
      loopCount++;
    }

    return {
      success: false,
      reason: `Max loops (${this.maxLoops}) exceeded`,
      executionLog: this.executionLog
    };
  }

  private async directorPlanning(
    task: string,
    history: PlanHistory[]
  ): Promise<Plan> {
    const contextFromHistory = history.length > 0
      ? `Previous attempts:\n${history
          .slice(-2)
          .map(h => `Loop ${h.loopNumber}: ${JSON.stringify(h.plan)}`)
          .join('\n')}`
      : 'First attempt - no prior context';

    const directorPrompt = `You are a strategic director coordinating a team of specialized agents.

TASK: ${task}

AVAILABLE SUPERVISORS:
${Array.from(this.supervisors.values())
  .map(s => `- ${s.id}: manages agents for ${s.domain}`)
  .join('\n')}

CONTEXT FROM PREVIOUS ATTEMPTS:
${contextFromHistory}

Create a detailed plan that:
1. Breaks the task into discrete subtasks
2. Assigns each subtask to the most appropriate supervisor
3. Specifies success criteria for each subtask
4. Identifies dependencies between subtasks
5. Estimates effort and priority for each subtask

Format as JSON with structure:
{
  "overview": "High-level approach",
  "subtasks": [
    {
      "id": "task_1",
      "description": "...",
      "supervisor": "supervisor_id",
      "successCriteria": [...],
      "priority": "high|medium|low",
      "dependsOn": ["task_0"]
    }
  ],
  "risks": ["..."],
  "fallbacks": ["..."]
}`;

    const response = await callClaudeAPI({
      systemPrompt: this.director.systemPrompt,
      userMessage: directorPrompt
    });

    return JSON.parse(response);
  }

  private async supervisorDelegation(plan: Plan): Promise<DelegationMap> {
    const delegationResults = new Map<string, WorkerAssignment[]>();

    for (const subtask of plan.subtasks) {
      const supervisor = this.supervisors.get(subtask.supervisor);
      if (!supervisor) continue;

      const workerAssignments = await supervisor.delegateSubtask(
        subtask,
        this.workers
      );

      delegationResults.set(subtask.id, workerAssignments);
    }

    return delegationResults;
  }

  private async workerExecution(
    delegationMap: DelegationMap
  ): Promise<Map<string, WorkerResult>> {
    const results = new Map<string, WorkerResult>();

    // Execute all worker assignments in parallel
    const execPromises = Array.from(delegationMap.entries()).flatMap(
      ([taskId, assignments]) =>
        assignments.map(async (assignment) => {
          const worker = this.workers.get(assignment.workerId);
          if (!worker) return;

          const result = await worker.execute({
            task: assignment.task,
            context: assignment.context,
            tools: assignment.tools
          });

          results.set(`${taskId}:${assignment.workerId}`, result);
        })
    );

    await Promise.all(execPromises);
    return results;
  }

  private async directorEvaluation(
    plan: Plan,
    results: Map<string, WorkerResult>,
    originalTask: string
  ): Promise<EvaluationResult> {
    const resultsText = Array.from(results.entries())
      .map(([key, result]) => `${key}: ${result.output}`)
      .join('\n\n');

    const evaluationPrompt = `Review the execution results against the plan.

ORIGINAL TASK: ${originalTask}

PLAN: ${JSON.stringify(plan, null, 2)}

EXECUTION RESULTS:
${resultsText}

Evaluate:
1. Which subtasks succeeded and which failed?
2. Are the success criteria met?
3. Are there conflicts or inconsistencies?
4. What's the overall confidence in the result? (0-1)
5. Should we loop again? What should be refined?

Format as JSON:
{
  "isComplete": boolean,
  "successfulSubtasks": ["..."],
  "failedSubtasks": ["..."],
  "confidence": 0.85,
  "refinedTask": "next iteration task if looping",
  "criticalIssues": ["..."],
  "nextSteps": ["..."]
}`;

    const response = await callClaudeAPI({
      systemPrompt: this.director.systemPrompt,
      userMessage: evaluationPrompt
    });

    return JSON.parse(response);
  }
}

// Example usage
const hierarchicalConfig: HierarchicalConfig = {
  director: {
    id: 'director',
    systemPrompt: 'You are an executive director overseeing a team of specialists...',
    model: 'claude-sonnet-4-5'
  },
  supervisors: [
    {
      id: 'research_supervisor',
      domain: 'research and analysis',
      managesWorkerIds: ['researcher_1', 'analyst_1']
    },
    {
      id: 'creation_supervisor',
      domain: 'content and artifact creation',
      managesWorkerIds: ['writer_1', 'designer_1']
    }
  ],
  workers: [
    { id: 'researcher_1', specialty: 'literature and data research' },
    { id: 'analyst_1', specialty: 'data analysis and interpretation' },
    { id: 'writer_1', specialty: 'content writing' },
    { id: 'designer_1', specialty: 'visual design' }
  ],
  maxLoops: 3,
  feedbackStrategy: 'adaptive'
};
```

---

### Pattern 3: Parallel Swarms

#### Definition
Multiple specialized agents operate simultaneously on different aspects of a single task, then their outputs are aggregated or merged. Ideal for throughput-intensive workloads and independent sub-problems.

#### Characteristics

```
                  Input Task
                      │
         ┌────────────┬┴────────────┐
         │            │            │
       ┌─▼─┐        ┌─▼─┐        ┌─▼─┐
       │ A1 │        │ A2 │        │ A3 │  (Parallel Execution)
       └─┬─┘        └─┬─┘        └─┬─┘
         │            │            │
      Output1      Output2      Output3
         │            │            │
         └────────────┼────────────┘
                      │
                 ┌─────▼──────┐
                 │ Aggregator  │
                 │   Agent     │
                 └─────┬──────┘
                       │
                  Final Output
```

**Pattern Benefits**:
- **Speed**: N agents working in parallel = ~N times faster
- **Fault Tolerance**: One agent failure doesn't block others
- **Diverse Perspectives**: Different agents provide different views
- **Embarrassingly Parallel**: Ideal for independent sub-tasks

#### Advantages

- ✅ **Maximum Throughput**: All agents execute simultaneously
- ✅ **Excellent Fault Isolation**: Agent failures don't cascade
- ✅ **Consensus Building**: Multiple perspectives increase reliability
- ✅ **Simple Composition**: Easy to add/remove parallel agents
- ✅ **Quality through Diversity**: Multiple approaches often yield better results

#### Disadvantages

- ❌ **Aggregation Complexity**: Merging diverse outputs is non-trivial
- ❌ **Token Multiplication**: N agents × tokens per agent = significant cost
- ❌ **Task Decomposition**: Not all problems parallelize cleanly
- ❌ **State Coordination**: Shared state must handle concurrent writes
- ❌ **Debugging Difficulty**: Multiple simultaneous executions harder to trace

#### Best Use Cases

- **Parallel Data Analysis**: Process different data dimensions simultaneously
- **Multi-Perspective Review**: Code review, fact-checking, QA from multiple angles
- **Consensus-Based Decisions**: Voting or merit-weighted aggregation
- **Redundancy & Resilience**: Critical operations with fault tolerance needs
- **Insurance/Risk Analysis**: Parallel evaluation of coverage, liability, financial stability

#### Implementation Example

```typescript
interface ParallelAgent {
  id: string;
  perspective: string;
  systemPrompt: string;
  evaluationCriteria?: string[];
}

interface AggregationStrategy {
  type: 'consensus' | 'weighted' | 'ranked' | 'merged' | 'voting';
  weights?: Record<string, number>;
  mergeFn?: (results: AgentResult[]) => any;
}

class ParallelSwarm {
  private agents: ParallelAgent[];
  private aggregationStrategy: AggregationStrategy;
  private executionLog: ExecutionLog[] = [];

  constructor(
    agents: ParallelAgent[],
    aggregationStrategy: AggregationStrategy
  ) {
    this.agents = agents;
    this.aggregationStrategy = aggregationStrategy;
  }

  async executeParallel(task: string): Promise<FinalResult> {
    console.log(`Executing ${this.agents.length} agents in parallel...`);
    const startTime = Date.now();

    // Execute all agents simultaneously
    const agentPromises = this.agents.map((agent) =>
      this.executeAgent(agent, task)
    );

    const results = await Promise.allSettled(agentPromises);
    const executionTime = Date.now() - startTime;

    // Handle results and failures
    const successResults: AgentResult[] = [];
    const failedAgents: string[] = [];

    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        successResults.push(result.value);
      } else {
        failedAgents.push(this.agents[index].id);
        console.error(
          `Agent ${this.agents[index].id} failed:`,
          result.reason
        );
      }
    });

    // Aggregate results
    const aggregatedOutput = await this.aggregate(successResults);

    const executionRecord: ExecutionLog = {
      task,
      totalAgents: this.agents.length,
      successfulAgents: successResults.length,
      failedAgents,
      executionTime,
      results: successResults,
      aggregatedOutput,
      timestamp: Date.now()
    };

    this.executionLog.push(executionRecord);

    return {
      success: failedAgents.length < Math.ceil(this.agents.length / 2),
      aggregatedOutput,
      detailedResults: successResults,
      failedAgents,
      executionTime,
      reliability: successResults.length / this.agents.length
    };
  }

  private async executeAgent(
    agent: ParallelAgent,
    task: string
  ): Promise<AgentResult> {
    const agentPrompt = `You are analyzing from the perspective: "${agent.perspective}"

TASK: ${task}

Criteria to evaluate:
${agent.evaluationCriteria?.join('\n') || 'Provide thoughtful analysis'}

Provide a detailed response from your unique perspective.
Structure your response as:
1. Key Insights (3-5 bullet points)
2. Critical Issues
3. Recommendations
4. Confidence Level (0-1)
5. Open Questions`;

    const response = await callClaudeAPI({
      systemPrompt: agent.systemPrompt,
      userMessage: agentPrompt
    });

    return {
      agentId: agent.id,
      perspective: agent.perspective,
      output: response,
      executedAt: Date.now(),
      tokenCount: estimateTokens(response)
    };
  }

  private async aggregate(results: AgentResult[]): Promise<AggregatedOutput> {
    switch (this.aggregationStrategy.type) {
      case 'consensus':
        return this.aggregateConsensus(results);
      case 'weighted':
        return this.aggregateWeighted(results);
      case 'ranked':
        return this.aggregateRanked(results);
      case 'merged':
        return this.aggregateMerged(results);
      case 'voting':
        return this.aggregateVoting(results);
      default:
        throw new Error(`Unknown aggregation strategy`);
    }
  }

  private async aggregateConsensus(
    results: AgentResult[]
  ): Promise<AggregatedOutput> {
    const consensusPrompt = `Review the following perspectives and extract consensus:

${results
  .map(
    (r) => `
PERSPECTIVE: ${r.perspective} (${r.agentId})
---
${r.output}
---`
  )
  .join('\n')}

Extract:
1. Areas of strong agreement (3+ agents)
2. Areas of disagreement and nuance
3. Synthesized conclusion
4. Confidence in consensus
5. Recommendations

Format as JSON:
{
  "consensus": { ... },
  "disagreements": [ ... ],
  "synthesized": "...",
  "confidenceLevel": 0.85,
  "recommendations": [ ... ]
}`;

    const response = await callClaudeAPI({
      systemPrompt: 'You are an expert at synthesizing diverse perspectives.',
      userMessage: consensusPrompt
    });

    return JSON.parse(response);
  }

  private async aggregateWeighted(
    results: AgentResult[]
  ): Promise<AggregatedOutput> {
    const weights = this.aggregationStrategy.weights || {};

    const weightedResults = results.map((result) => ({
      ...result,
      weight: weights[result.agentId] || 1.0
    }));

    const totalWeight = weightedResults.reduce((sum, r) => sum + r.weight, 0);

    // Use Claude to synthesize with weighted importance
    const synthesisPrompt = `Synthesize the following perspectives, with higher weight on more important sources:

${weightedResults
  .map((r) => `WEIGHT: ${r.weight} (${(r.weight / totalWeight * 100).toFixed(1)}%)
SOURCE: ${r.agentId} (${r.perspective})
---
${r.output}`)
  .join('\n\n---\n\n')}

Create a synthesis that emphasizes insights from higher-weighted sources.`;

    const response = await callClaudeAPI({
      systemPrompt:
        'You are an expert at synthesizing and prioritizing information.',
      userMessage: synthesisPrompt
    });

    return {
      type: 'weighted',
      synthesis: response,
      weights: weights,
      totalWeight
    };
  }

  private async aggregateRanked(
    results: AgentResult[]
  ): Promise<AggregatedOutput> {
    // Ask Claude to rank the perspectives
    const rankingPrompt = `Rank these perspectives by quality and relevance:

${results
  .map(
    (r) => `[${r.agentId}] ${r.perspective}:
${r.output}`
  )
  .join('\n\n---\n\n')}

Provide ranking 1-${results.length} and synthesized output prioritizing top-ranked perspectives.`;

    const response = await callClaudeAPI({
      systemPrompt: 'You are an expert at evaluating and ranking perspectives.',
      userMessage: rankingPrompt
    });

    return {
      type: 'ranked',
      ranking: response
    };
  }

  private async aggregateMerged(
    results: AgentResult[]
  ): Promise<AggregatedOutput> {
    if (this.aggregationStrategy.mergeFn) {
      return this.aggregationStrategy.mergeFn(results);
    }

    // Default merge: concatenate with attribution
    const merged = results
      .map((r) => `[${r.agentId}] ${r.output}`)
      .join('\n\n---\n\n');

    return {
      type: 'merged',
      output: merged,
      resultCount: results.length
    };
  }

  private async aggregateVoting(
    results: AgentResult[]
  ): Promise<AggregatedOutput> {
    // Extract key recommendations and vote
    const votingPrompt = `Analyze these recommendations and aggregate votes:

${results
  .map(
    (r) =>
      `AGENT: ${r.agentId} (${r.perspective})
---
${r.output}`
  )
  .join('\n\n---\n\n')}

Identify key recommendations and count agent support for each.
Format results as vote tallies and final recommendations.`;

    const response = await callClaudeAPI({
      systemPrompt: 'You are an expert at aggregating votes and consensus.',
      userMessage: votingPrompt
    });

    return {
      type: 'voting',
      results: response
    };
  }
}

// Example: Multi-perspective product review
const reviewAgents: ParallelAgent[] = [
  {
    id: 'technical_reviewer',
    perspective: 'Technical performance and architecture',
    systemPrompt:
      'You are a technical expert evaluating implementation details...'
  },
  {
    id: 'ux_reviewer',
    perspective: 'User experience and design',
    systemPrompt: 'You are a UX specialist evaluating user-facing aspects...'
  },
  {
    id: 'business_reviewer',
    perspective: 'Business viability and market fit',
    systemPrompt: 'You are a business analyst evaluating commercial aspects...'
  },
  {
    id: 'security_reviewer',
    perspective: 'Security and compliance',
    systemPrompt:
      'You are a security expert evaluating threats and mitigations...'
  }
];

const parallelSwarm = new ParallelSwarm(reviewAgents, {
  type: 'consensus',
  weights: {
    technical_reviewer: 1.2,
    security_reviewer: 1.3,
    ux_reviewer: 1.0,
    business_reviewer: 0.9
  }
});
```

---

### Pattern 4: Sequential Swarms (Pipeline/Chain)

#### Definition
Agents operate in a strict linear sequence where each agent's output becomes the next agent's input, forming a data transformation pipeline. Perfect for workflows with clear dependencies and stage-based processing.

#### Characteristics

```
Input → [Agent 1] → Transformed Data → [Agent 2] → ... → [Agent N] → Output
         (Extract)   (Raw Facts)      (Analyze)      (Synthesize)
```

**Key Properties**:
- **Strict Ordering**: Predictable sequence, no branching
- **Single Point of Failure**: Early stage failure blocks downstream
- **Quality Degradation**: Each handoff introduces small errors that compound
- **Measurable Latency**: Sum of all agent latencies
- **Clear Dependencies**: Perfect for multi-step transformations

#### Advantages

- ✅ **Simplest to Debug**: Linear control flow easy to trace
- ✅ **Lowest Token Cost**: No redundant parallel execution
- ✅ **Predictable Behavior**: Deterministic output from known input sequence
- ✅ **Clear Data Transformation**: Perfect for refinement pipelines
- ✅ **Easy to Optimize**: Profile and tune each stage independently

#### Disadvantages

- ❌ **Slowest Execution**: Sequential = N times slower than parallel
- ❌ **Single Point of Failure**: One bad agent blocks entire pipeline
- ❌ **Quality Degradation**: Each handoff adds probabilistic deviation
- ❌ **Limited Parallelism**: Can't exploit multi-stage independence
- ❌ **Error Propagation**: Errors from earlier stages compound downstream

#### Best Use Cases

- **Content Creation Pipeline**: Research → Draft → Edit → Polish
- **Data Processing**: Extraction → Cleaning → Transformation → Export
- **Code Development**: Specification → Architecture → Implementation → Testing
- **Document Review**: Initial Draft → Specialist Review → Legal Review → Final
- **Multi-stage Reasoning**: Analysis → Synthesis → Validation → Finalization

#### Implementation Example

```typescript
interface PipelineStage {
  id: string;
  name: string;
  description: string;
  systemPrompt: string;
  expectedOutputFormat?: string;
  validateOutput?: (output: string) => boolean;
}

interface PipelineResult {
  originalInput: string;
  stageResults: StageExecution[];
  finalOutput: string;
  totalExecutionTime: number;
  qualityScore: number;
}

class SequentialPipeline {
  private stages: PipelineStage[];
  private executionLog: StageExecution[] = [];
  private qualityThresholds: Record<string, number> = {};

  constructor(stages: PipelineStage[]) {
    this.stages = stages;
  }

  async execute(initialInput: string): Promise<PipelineResult> {
    console.log(`Starting pipeline with ${this.stages.length} stages...`);
    const startTime = Date.now();

    let currentInput = initialInput;
    const stageResults: StageExecution[] = [];
    let qualityDegradeAcrossPipeline = 1.0;

    for (let i = 0; i < this.stages.length; i++) {
      const stage = this.stages[i];
      console.log(
        `[Stage ${i + 1}/${this.stages.length}] Executing: ${stage.name}`
      );

      // Execute stage
      const stageStartTime = Date.now();
      const stageOutput = await this.executeStage(stage, currentInput);
      const stageExecutionTime = Date.now() - stageStartTime;

      // Validate output
      let isValid = true;
      if (stage.validateOutput) {
        isValid = stage.validateOutput(stageOutput);
        if (!isValid) {
          console.warn(`⚠️  Stage ${stage.id} output validation failed`);
        }
      }

      // Quality degradation (typical compound degradation ~1-3% per handoff)
      const stageQuality = isValid ? 0.98 : 0.92;
      qualityDegradeAcrossPipeline *= stageQuality;

      const execution: StageExecution = {
        stageId: stage.id,
        stageName: stage.name,
        stageIndex: i,
        input: currentInput,
        output: stageOutput,
        executionTime: stageExecutionTime,
        tokenCount: estimateTokens(stageOutput),
        isValid,
        quality: stageQuality,
        cumulativeQuality: qualityDegradeAcrossPipeline,
        timestamp: Date.now()
      };

      stageResults.push(execution);
      this.executionLog.push(execution);

      // Prepare for next stage
      currentInput = stageOutput;
    }

    const totalExecutionTime = Date.now() - startTime;

    // Check if pipeline degradation is severe
    if (qualityDegradeAcrossPipeline < 0.85) {
      console.warn(
        `⚠️  Pipeline quality degradation is significant: ${(qualityDegradeAcrossPipeline * 100).toFixed(1)}%`
      );
    }

    return {
      originalInput: initialInput,
      stageResults,
      finalOutput: currentInput,
      totalExecutionTime,
      qualityScore: qualityDegradeAcrossPipeline
    };
  }

  private async executeStage(
    stage: PipelineStage,
    input: string
  ): Promise<string> {
    const stagePrompt = `${stage.description}

INPUT:
${input}

${
  stage.expectedOutputFormat
    ? `OUTPUT FORMAT: ${stage.expectedOutputFormat}`
    : ''
}

Process the input according to your instructions and provide the output.`;

    const response = await callClaudeAPI({
      systemPrompt: stage.systemPrompt,
      userMessage: stagePrompt
    });

    return response;
  }

  // Get pipeline metrics
  getMetrics(): PipelineMetrics {
    if (this.executionLog.length === 0) {
      return {
        totalStages: this.stages.length,
        executedStages: 0,
        totalTokens: 0,
        totalTime: 0,
        avgQuality: 0,
        bottlenecks: []
      };
    }

    const totalTokens = this.executionLog.reduce(
      (sum, stage) => sum + stage.tokenCount,
      0
    );
    const totalTime = this.executionLog.reduce(
      (sum, stage) => sum + stage.executionTime,
      0
    );
    const avgQuality =
      this.executionLog.reduce((sum, stage) => sum + stage.quality, 0) /
      this.executionLog.length;

    // Identify bottlenecks (stages taking >20% of total time)
    const bottlenecks = this.executionLog.filter(
      (stage) => stage.executionTime > totalTime * 0.2
    );

    return {
      totalStages: this.stages.length,
      executedStages: this.executionLog.length,
      totalTokens,
      totalTime,
      avgQuality,
      bottlenecks: bottlenecks.map((b) => ({
        stage: b.stageName,
        time: b.executionTime,
        percentOfTotal: (b.executionTime / totalTime) * 100
      }))
    };
  }
}

// Example: Content creation pipeline
const contentPipeline = new SequentialPipeline([
  {
    id: 'research',
    name: 'Research & Fact Gathering',
    description:
      'Gather comprehensive research on the topic. Focus on accuracy and source credibility.',
    systemPrompt: `You are a research expert. Your job is to:
1. Identify key aspects of the topic
2. Find authoritative sources
3. Compile relevant facts and statistics
4. Note any gaps in knowledge`,
    expectedOutputFormat: 'JSON with structure: { keyPoints: [...], sources: [...], gaps: [...] }'
  },
  {
    id: 'analysis',
    name: 'Analysis & Synthesis',
    description:
      'Analyze the research and create meaningful connections. Identify patterns and implications.',
    systemPrompt: `You are a data analyst and strategist. Your job is to:
1. Analyze the provided research
2. Identify meaningful patterns
3. Connect related concepts
4. Assess implications`,
    validateOutput: (output) => output.length > 200
  },
  {
    id: 'writing',
    name: 'Content Writing',
    description:
      'Write clear, engaging content. Transform analysis into readable narrative.',
    systemPrompt: `You are a professional writer. Your job is to:
1. Create compelling, readable content
2. Structure logically with clear flow
3. Maintain accuracy from source material
4. Engage the reader`,
    expectedOutputFormat: 'Well-structured markdown with headers, sections, and clear flow'
  },
  {
    id: 'editing',
    name: 'Editing & Polish',
    description:
      'Edit for clarity, style, and correctness. Ensure professional quality.',
    systemPrompt: `You are a professional editor. Your job is to:
1. Fix grammatical errors
2. Improve clarity and flow
3. Ensure consistency
4. Enhance readability`,
    validateOutput: (output) => !output.includes('[TODO]') && !output.includes('[EDIT]')
  }
]);

// Execute pipeline
const result = await contentPipeline.execute('Write about recent AI breakthroughs in 2026');
console.log(`\nPipeline completed in ${result.totalExecutionTime}ms`);
console.log(`Quality score: ${(result.qualityScore * 100).toFixed(1)}%`);
console.log(result.finalOutput);
```

#### Quality Degradation Analysis

Research shows sequential pipelines with 8-10+ handoffs experience measurable quality degradation:

```
Quality vs Pipeline Length:

100% ├─ Start
     │
 95% ├─ ────• (After stage 1: 98% quality)
     │       ──••── (After stage 2: 96% cumulative)
 90% ├─────────••──── (After stage 3: 94% cumulative)
     │             •• (After stage 4: 92% cumulative)
 85% ├──────────────•••• (After stage 5: 90% cumulative)
     │                  ••
 80% ├─────────────────────•••
     └────────────────────────────
     1  2  3  4  5  6  7  8  9  10+
     Pipeline Stages

❌ Beyond 8-10 stages: Quality typically <85%
✅ 3-5 stages: Quality stays >90%
✅ Mitigation: Use validation gates, quality checks between stages
```

---

### Pattern 5: Adaptive Swarms

#### Definition
Teams that dynamically reorganize their structure, membership, or role assignments based on real-time task requirements, agent availability, or system state. The system automatically adjusts to changing conditions.

#### Characteristics

```
        Initial State        Task Changes        Reorganized State
        
    ┌─────────────┐      ┌─────────────┐      ┌──────────────┐
    │   Agent A   │      │ New Task    │      │   Agent A    │
    │  Role: 1    │      │ Requires    │      │ Role: Leader │
    └────┬────────┘      │ Different   │      └─────┬────────┘
    ┌────┴────────┐      │ Skills      │      ┌─────┴────────┐
    │   Agent B   │ ──→  │ & Emphasis  │ ──→  │   Agent C    │
    │  Role: 2    │      │             │      │ Role: Exec   │
    └────┬────────┘      └─────────────┘      └─────┬────────┘
    ┌────┴────────┐                           ┌─────┴────────┐
    │   Agent C   │                           │   Agent B    │
    │  Role: 3    │                           │ Role: Support│
    └─────────────┘                           └──────────────┘
    
    Agents + Roles Change Based on Conditions
```

**Dynamics**:
- Agents elected as leaders dynamically
- Roles reassigned based on task fit
- Team composition changes (add/remove agents)
- Priority reorganization
- Failover and recovery mechanisms

#### Advantages

- ✅ **Resilience**: Automatically adapt to agent failures and changing conditions
- ✅ **Efficiency**: Resources allocated dynamically based on actual needs
- ✅ **Flexibility**: Same team handles diverse task types without redesign
- ✅ **Self-Healing**: System recovers from disruptions automatically
- ✅ **Optimal Utilization**: Agents focus on work they're best suited for

#### Disadvantages

- ❌ **Complexity**: Reorganization logic is sophisticated and hard to debug
- ❌ **Unpredictability**: Behavior varies based on dynamic conditions
- ❌ **Higher Token Cost**: Continuous re-evaluation and reorganization overhead
- ❌ **State Management**: Tracking changing state is challenging
- ❌ **Delayed Stability**: May take time to settle on stable configuration

#### Best Use Cases

- **Long-Running Operations**: Tasks that may span hours/days with changing requirements
- **Fault-Tolerant Systems**: Agent failures should be automatically handled
- **Resource-Constrained Environments**: Optimize utilization based on availability
- **Complex Multi-Phase Projects**: Different phases need different team structures
- **Real-Time Monitoring**: Systems that must respond to changing conditions

#### Implementation Example

```typescript
interface AdaptiveAgent {
  id: string;
  capabilities: string[];
  currentRole?: string;
  efficiency?: Record<string, number>; // role -> efficiency score
  availability: number; // 0-1, available capacity
  failureCount: number;
}

interface RoleDefinition {
  roleId: string;
  requiredCapabilities: string[];
  priority: number;
  criticalForSuccess: boolean;
  staffingOptions: 'single' | 'pair' | 'team';
}

interface SystemConditions {
  taskPhase: string;
  availableAgents: AdaptiveAgent[];
  completionPercentage: number;
  errorRate: number;
  timeRemaining: number;
  resources: Record<string, number>;
}

class AdaptiveSwarm {
  private agents: Map<string, AdaptiveAgent> = new Map();
  private roles: Map<string, RoleDefinition> = new Map();
  private currentAssignments: RoleAssignment[] = [];
  private reorganizationHistory: ReorganizationEvent[] = [];
  private conditionMonitor: SystemConditions;

  constructor(agents: AdaptiveAgent[], roles: RoleDefinition[]) {
    agents.forEach((agent) => this.agents.set(agent.id, agent));
    roles.forEach((role) => this.roles.set(role.roleId, role));
  }

  async executeAdaptive(task: string, maxDuration: number): Promise<any> {
    const startTime = Date.now();
    let currentState = 'initialization';

    // Initial team formation
    await this.reorganizeTeam('initial_formation', {
      taskPhase: 'initialization',
      availableAgents: Array.from(this.agents.values()),
      completionPercentage: 0,
      errorRate: 0,
      timeRemaining: maxDuration,
      resources: {}
    });

    while (Date.now() - startTime < maxDuration) {
      // Continuous monitoring and adaptation
      this.conditionMonitor = await this.monitorSystemConditions();

      // Check if reorganization is needed
      const shouldReorganize = this.evaluateReorganizationNeed(
        this.conditionMonitor,
        currentState
      );

      if (shouldReorganize) {
        console.log(
          `🔄 Reorganizing team: ${shouldReorganize.reason}`
        );
        await this.reorganizeTeam(shouldReorganize.reason, this.conditionMonitor);
      }

      // Execute current assignments
      const phaseResult = await this.executeCurrentPhase(task);
      currentState = phaseResult.nextPhase;

      // Check for failures and handle
      if (phaseResult.failures.length > 0) {
        console.log(`⚠️  Detected failures: ${phaseResult.failures.join(', ')}`);
        await this.handleFailures(phaseResult.failures);
      }

      // Brief delay before next iteration
      await sleep(1000);
    }

    return {
      completed: currentState === 'completion',
      assignments: this.currentAssignments,
      reorganizationEvents: this.reorganizationHistory,
      finalState: this.conditionMonitor
    };
  }

  private async reorganizeTeam(
    reason: string,
    conditions: SystemConditions
  ): Promise<void> {
    console.log(`Reorganizing team: ${reason}`);

    // Step 1: Evaluate agent fitness for each role
    const fitness = this.calculateAgentRoleFitness(conditions);

    // Step 2: Assign agents to roles optimally
    const newAssignments = this.optimizeAssignments(
      fitness,
      Array.from(this.roles.values())
    );

    // Step 3: Update role assignments
    this.currentAssignments.forEach((assignment) => {
      const agent = this.agents.get(assignment.agentId);
      if (agent) {
        agent.currentRole = undefined;
      }
    });

    newAssignments.forEach((assignment) => {
      const agent = this.agents.get(assignment.agentId);
      if (agent) {
        agent.currentRole = assignment.roleId;
      }
    });

    this.currentAssignments = newAssignments;

    this.reorganizationHistory.push({
      timestamp: Date.now(),
      reason,
      previousAssignments: this.currentAssignments,
      newAssignments,
      conditions
    });

    // Log reorganization
    console.log(`Team reorganized:`);
    newAssignments.forEach((a) => {
      console.log(`  ${a.agentId} → ${a.roleId}`);
    });
  }

  private calculateAgentRoleFitness(
    conditions: SystemConditions
  ): Record<string, Record<string, number>> {
    const fitness: Record<string, Record<string, number>> = {};

    for (const [agentId, agent] of this.agents) {
      fitness[agentId] = {};

      for (const [roleId, role] of this.roles) {
        let score = 0;

        // Capability match (primary factor)
        const capabilityMatch = role.requiredCapabilities.filter(
          (cap) => agent.capabilities.includes(cap)
        ).length;
        score += (capabilityMatch / role.requiredCapabilities.length) * 50;

        // Efficiency in role (if history exists)
        if (agent.efficiency && agent.efficiency[roleId]) {
          score += agent.efficiency[roleId] * 30;
        }

        // Availability (can agent handle this role?)
        score += agent.availability * 20;

        // Reliability (fewer failures = higher score)
        score += Math.max(0, 1 - agent.failureCount * 0.1) * 10;

        // Phase-based adjustment
        if (conditions.completionPercentage < 30 && role.priority > 5) {
          score *= 1.2; // Early phases: prioritize critical roles
        }

        if (
          conditions.errorRate > 0.3 &&
          agent.failureCount === 0
        ) {
          score *= 1.3; // High error rate: favor reliable agents
        }

        fitness[agentId][roleId] = score;
      }
    }

    return fitness;
  }

  private optimizeAssignments(
    fitness: Record<string, Record<string, number>>,
    roles: RoleDefinition[]
  ): RoleAssignment[] {
    const assignments: RoleAssignment[] = [];
    const assignedAgents = new Set<string>();

    // Sort roles by priority (critical roles first)
    const sortedRoles = [...roles].sort((a, b) => b.priority - a.priority);

    for (const role of sortedRoles) {
      let bestAgent: string | null = null;
      let bestScore = -1;

      // Find best-fit agent not yet assigned
      for (const [agentId, scores] of Object.entries(fitness)) {
        if (!assignedAgents.has(agentId) && scores[role.roleId] > bestScore) {
          bestScore = scores[role.roleId];
          bestAgent = agentId;
        }
      }

      if (bestAgent && bestScore >= 30) {
        // Threshold for acceptable fit
        assignments.push({
          agentId: bestAgent,
          roleId: role.roleId,
          fitScore: bestScore,
          assignedAt: Date.now()
        });
        assignedAgents.add(bestAgent);

        // If role requires pair/team, find secondaries
        if (role.staffingOptions === 'pair' || role.staffingOptions === 'team') {
          const secondaryCount =
            role.staffingOptions === 'pair' ? 1 : Math.ceil(assignedAgents.size * 0.1);
          for (let i = 0; i < secondaryCount; i++) {
            const secondaryAgent = this.findSecondaryAgent(
              fitness,
              role,
              assignedAgents
            );
            if (secondaryAgent) {
              assignments.push({
                agentId: secondaryAgent,
                roleId: `${role.roleId}_secondary`,
                fitScore: fitness[secondaryAgent][role.roleId],
                assignedAt: Date.now()
              });
              assignedAgents.add(secondaryAgent);
            }
          }
        }
      }
    }

    return assignments;
  }

  private evaluateReorganizationNeed(
    conditions: SystemConditions,
    currentState: string
  ): ReorganizationTrigger | null {
    // Check for critical failures
    if (conditions.errorRate > 0.5) {
      return {
        reason: 'High error rate detected',
        severity: 'critical'
      };
    }

    // Check for phase transitions
    if (
      (currentState === 'analysis' && conditions.completionPercentage > 40) ||
      (currentState === 'execution' && conditions.completionPercentage > 70)
    ) {
      return {
        reason: `Transitioning to next phase (${conditions.completionPercentage}% complete)`,
        severity: 'medium'
      };
    }

    // Check for agent failures
    const failedAgents = Array.from(this.agents.values()).filter(
      (a) => a.failureCount > 3
    );
    if (failedAgents.length > 0) {
      return {
        reason: `Agent failures detected: ${failedAgents.map((a) => a.id).join(', ')}`,
        severity: 'high'
      };
    }

    // Check for efficiency drops
    const avgEfficiency =
      Array.from(this.agents.values()).reduce(
        (sum, a) => sum + a.availability,
        0
      ) / this.agents.size;
    if (avgEfficiency < 0.3) {
      return {
        reason: `Team efficiency degraded to ${(avgEfficiency * 100).toFixed(0)}%`,
        severity: 'medium'
      };
    }

    return null;
  }

  private async monitorSystemConditions(): Promise<SystemConditions> {
    // In real implementation, gather actual metrics
    return {
      taskPhase: 'execution',
      availableAgents: Array.from(this.agents.values()),
      completionPercentage: Math.random() * 100,
      errorRate: Math.random() * 0.5,
      timeRemaining: 60000,
      resources: {}
    };
  }

  private async executeCurrentPhase(task: string): Promise<any> {
    // Execute assignments in current phase
    return {
      nextPhase: 'execution',
      failures: [],
      progress: 0.25
    };
  }

  private async handleFailures(failedAgentIds: string[]): Promise<void> {
    for (const agentId of failedAgentIds) {
      const agent = this.agents.get(agentId);
      if (agent) {
        agent.failureCount++;
        agent.availability = Math.max(0, agent.availability - 0.2);
        console.log(
          `Agent ${agentId} availability reduced to ${(agent.availability * 100).toFixed(0)}%`
        );
      }
    }

    // Trigger reorganization if failures are significant
    if (failedAgentIds.length > this.agents.size * 0.2) {
      await this.reorganizeTeam('agent_failures', this.conditionMonitor);
    }
  }

  private findSecondaryAgent(
    fitness: Record<string, Record<string, number>>,
    role: RoleDefinition,
    assigned: Set<string>
  ): string | null {
    let bestAgent: string | null = null;
    let bestScore = -1;

    for (const [agentId, scores] of Object.entries(fitness)) {
      if (!assigned.has(agentId) && scores[role.roleId] > bestScore) {
        bestScore = scores[role.roleId];
        bestAgent = agentId;
      }
    }

    return bestScore >= 25 ? bestAgent : null;
  }
}
```

---

### Pattern 6: Mesh / Peer-to-Peer

#### Definition
Agents communicate directly with each other in peer-to-peer fashion without a hierarchy. Each agent negotiates with peers, shares information directly, and coordinates through local interactions and distributed protocols.

#### Characteristics

```
        ┌─────────┐
        │ Agent A │─────┐
        └────┬────┘     │
             │     ┌────┴────┐
             │     │          │
        ┌────▼─┐ ┌─┴─┐    ┌──┴──┐
        │Agent B├─┤Agent C├─┤Agent D│
        └────┬─┘ └─┬─┘    └──┬──┘
             │     │         │
             └─────┼────┬────┘
                   │    │
                ┌──▼──┬─▼─┐
                │Agent E   │
                └──────────┘
        
All agents communicate directly: N(N-1)/2 potential connections
With 5 agents: 10 connections
With 10 agents: 45 connections
With 50 agents: 1,225 connections ⚠️
```

**Key Features**:
- **Direct Communication**: Agents communicate without intermediary
- **Distributed Consensus**: Decisions emerge from negotiation
- **No Central Authority**: No orchestrator or authority figure
- **Dynamic Topology**: Connections form/break based on communication needs
- **Implicit Coordination**: Agents coordinate through local interactions

#### Advantages

- ✅ **No Single Point of Failure**: All agents equal, loss of one has limited impact
- ✅ **Horizontal Scalability**: Add agents, peer-discovery finds them
- ✅ **Resilient Architecture**: System continues despite agent failures
- ✅ **Natural Collaboration**: Suits truly distributed systems
- ✅ **Reduced Bottlenecks**: Direct agent-to-agent communication

#### Disadvantages

- ❌ **Combinatorial Complexity**: N agents = N(N-1)/2 potential connections
  - 5 agents = 10 connections (manageable)
  - 10 agents = 45 connections
  - 50 agents = 1,225 connections ⚠️ (difficult to debug)
- ❌ **Conflict Resolution**: No authority to break ties
- ❌ **Emergent Chaos**: Unpredictable collective behavior
- ❌ **Debugging Nightmare**: Hard to trace flow through many agent interactions
- ❌ **Higher Token Overhead**: Negotiation messages multiply

#### Best Use Cases

- **Small Specialist Teams** (3-8 agents): Tightly coupled experts
- **Truly Distributed Systems**: Agents across different locations
- **Consensus-Based Decisions**: Voting or distributed consensus
- **Resilience-First**: Fault tolerance paramount
- **Research Environments**: Exploration and experimentation

#### Practical Limits

```
Optimal Mesh Size: 3-8 agents
- Provides fault tolerance
- Maintains manageable complexity
- Direct communication works well

Beyond 8 agents: Consider hierarchy
- Decompose into sub-meshes
- Coordinate sub-meshes hierarchically
- Reduces complexity from O(n²) to O(n)
```

#### Implementation Example

```typescript
interface PeerAgent {
  id: string;
  specialty: string;
  messageQueue: Message[];
  knownPeers: Set<string>;
  consensus?: string;
}

interface Message {
  fromId: string;
  toId: string | 'broadcast';
  type: 'query' | 'response' | 'proposal' | 'vote';
  content: any;
  timestamp: number;
  ttl: number;
}

interface PeerProtocol {
  onReceiveMessage(message: Message): Promise<void>;
  onPeerJoin(peerId: string): Promise<void>;
  onPeerLeave(peerId: string): Promise<void>;
}

class MeshSwarm implements PeerProtocol {
  private peers: Map<string, PeerAgent> = new Map();
  private messageLog: Message[] = [];
  private consensusLog: ConsensusEvent[] = [];
  private maxPeers: number = 8; // Practical limit

  constructor(agents: PeerAgent[], maxPeers: number = 8) {
    agents.forEach((agent) => this.peers.set(agent.id, agent));
    this.maxPeers = maxPeers;
  }

  async executeCollaborative(task: string): Promise<any> {
    console.log(`Starting mesh collaboration with ${this.peers.size} peers`);

    if (this.peers.size > this.maxPeers) {
      console.warn(
        `⚠️  Mesh has ${this.peers.size} agents (optimal: ≤${this.maxPeers})`
      );
    }

    // Initialize mesh topology
    this.initializeMeshTopology();

    // Start collaborative problem-solving
    const result = await this.collaborativeReasoningLoop(task);

    return result;
  }

  private initializeMeshTopology(): void {
    // Each peer discovers and connects to all others
    for (const [peerId, peer] of this.peers) {
      for (const otherId of this.peers.keys()) {
        if (otherId !== peerId) {
          peer.knownPeers.add(otherId);
        }
      }
    }

    console.log(
      `Mesh topology initialized: ${this.peers.size * (this.peers.size - 1) / 2} connections`
    );
  }

  async onReceiveMessage(message: Message): Promise<void> {
    this.messageLog.push(message);

    const recipient = this.peers.get(message.toId as string);
    if (!recipient) return;

    const response = await this.processPeerMessage(recipient, message);
    if (response) {
      await this.broadcastMessage(response);
    }
  }

  async onPeerJoin(peerId: string): Promise<void> {
    console.log(`Peer ${peerId} joined the mesh`);

    // Notify existing peers of new member
    for (const [id, peer] of this.peers) {
      if (id !== peerId) {
        peer.knownPeers.add(peerId);
        await this.sendMessage({
          fromId: id,
          toId: peerId,
          type: 'proposal',
          content: { action: 'welcome', existingPeers: Array.from(peer.knownPeers) },
          timestamp: Date.now(),
          ttl: 100
        });
      }
    }
  }

  async onPeerLeave(peerId: string): Promise<void> {
    console.log(`Peer ${peerId} left the mesh`);
    this.peers.delete(peerId);

    // Remove failed peer from others' known peers
    for (const peer of this.peers.values()) {
      peer.knownPeers.delete(peerId);
    }
  }

  private async collaborativeReasoningLoop(task: string): Promise<any> {
    // Phase 1: Broadcast task to all peers
    const initialProposal = await this.createInitialProposal(task);
    await this.broadcastMessage({
      fromId: 'system',
      toId: 'broadcast',
      type: 'proposal',
      content: { task, initialApproach: initialProposal },
      timestamp: Date.now(),
      ttl: 100
    });

    // Phase 2: Peers propose solutions
    const proposals = await this.collectProposals(task);

    // Phase 3: Peer negotiation and refinement
    const refinedProposal = await this.negotiateProposal(proposals);

    // Phase 4: Consensus building
    const consensus = await this.buildConsensus(refinedProposal);

    return {
      task,
      proposals,
      refinedProposal,
      consensus,
      messageCount: this.messageLog.length,
      topologyHealthy: this.peers.size > Math.ceil(this.maxPeers / 2)
    };
  }

  private async createInitialProposal(task: string): Promise<any> {
    // First peer to respond with initial approach
    const firstPeer = this.peers.values().next().value;
    if (!firstPeer) return null;

    return await callClaudeAPI({
      systemPrompt: `You are a ${firstPeer.specialty} specialist.
Create an initial approach to this task that invites peer input and collaboration.`,
      userMessage: `Task: ${task}\n\nCreate an initial proposal for collaborative solving.`
    });
  }

  private async collectProposals(task: string): Promise<Map<string, any>> {
    const proposals = new Map<string, any>();

    const proposalPromises = Array.from(this.peers.entries()).map(
      async ([peerId, peer]) => {
        const proposal = await callClaudeAPI({
          systemPrompt: `You are a ${peer.specialty} specialist in a peer collaboration.
Propose your approach to the task, ready to negotiate with peers.`,
          userMessage: `Task: ${task}\n\nProvide your specialized perspective and proposal.`
        });
        proposals.set(peerId, proposal);
      }
    );

    await Promise.all(proposalPromises);
    return proposals;
  }

  private async negotiateProposal(proposals: Map<string, any>): Promise<any> {
    const proposalText = Array.from(proposals.entries())
      .map(([id, prop]) => `[${id}]: ${prop}`)
      .join('\n\n');

    // Use Claude to synthesize peer proposals
    const negotiationPrompt = `These are proposals from different specialists:

${proposalText}

Synthesize a refined proposal that:
1. Incorporates the best ideas from all proposals
2. Resolves conflicts between different approaches
3. Acknowledges trade-offs
4. Increases likelihood of peer consensus`;

    return await callClaudeAPI({
      systemPrompt:
        'You are a diplomatic synthesizer skilled at finding common ground.',
      userMessage: negotiationPrompt
    });
  }

  private async buildConsensus(refinedProposal: any): Promise<any> {
    // Voting/consensus mechanism
    const votes = new Map<string, boolean>();

    const votePromises = Array.from(this.peers.entries()).map(
      async ([peerId, peer]) => {
        const vote = await callClaudeAPI({
          systemPrompt: `You are a ${peer.specialty} specialist.
Vote on whether you support the refined proposal.
Consider: Does it incorporate your concerns? Is it practical?`,
          userMessage: `Refined Proposal:\n${JSON.stringify(refinedProposal)}\n\nDo you support this? Answer with JSON: { "vote": true|false, "reasoning": "..." }`
        });

        try {
          const parsed = JSON.parse(vote);
          votes.set(peerId, parsed.vote);
        } catch {
          votes.set(peerId, vote.toLowerCase().includes('yes'));
        }
      }
    );

    await Promise.all(votePromises);

    const supportCount = Array.from(votes.values()).filter((v) => v).length;
    const threshold = Math.ceil(this.peers.size / 2); // Simple majority

    const consensusEvent: ConsensusEvent = {
      timestamp: Date.now(),
      proposal: refinedProposal,
      votes,
      supportCount,
      threshold,
      achieved: supportCount >= threshold
    };

    this.consensusLog.push(consensusEvent);

    return consensusEvent;
  }

  private async sendMessage(message: Message): Promise<void> {
    // Simulate message sending with TTL
    if (message.ttl <= 0) return;

    const recipient = this.peers.get(message.toId as string);
    if (recipient) {
      recipient.messageQueue.push(message);
      await this.onReceiveMessage(message);
    }
  }

  private async broadcastMessage(message: Message): Promise<void> {
    for (const peer of this.peers.values()) {
      if (peer.id !== (message.fromId)) {
        await this.sendMessage({
          ...message,
          toId: peer.id
        });
      }
    }
  }

  private async processPeerMessage(
    peer: PeerAgent,
    message: Message
  ): Promise<Message | null> {
    // Process message and generate response if needed
    if (message.type === 'proposal') {
      return {
        fromId: peer.id,
        toId: message.fromId,
        type: 'response',
        content: { feedback: `Response from ${peer.specialty}` },
        timestamp: Date.now(),
        ttl: message.ttl - 1
      };
    }

    return null;
  }

  getMeshMetrics(): MeshMetrics {
    return {
      agentCount: this.peers.size,
      maxOptimal: this.maxPeers,
      connectionCount: (this.peers.size * (this.peers.size - 1)) / 2,
      messageCount: this.messageLog.length,
      consensusEvents: this.consensusLog.length,
      topologyType:
        this.peers.size > this.maxPeers
          ? 'overcrowded'
          : 'healthy'
    };
  }
}

// Example: Research collaboration mesh
const researchMesh = new MeshSwarm([
  {
    id: 'theorist',
    specialty: 'theoretical research',
    messageQueue: [],
    knownPeers: new Set()
  },
  {
    id: 'empiricist',
    specialty: 'empirical validation',
    messageQueue: [],
    knownPeers: new Set()
  },
  {
    id: 'practitioner',
    specialty: 'practical applications',
    messageQueue: [],
    knownPeers: new Set()
  },
  {
    id: 'critic',
    specialty: 'critical analysis',
    messageQueue: [],
    knownPeers: new Set()
  }
], 8);

const result = await researchMesh.executeCollaborative(
  'Design a novel approach to multi-agent coordination'
);
```

---

## Pattern Comparison Matrix

## Implementation Framework

### Core Components

Every swarm implementation requires:

1. **Agent Manager**: Lifecycle management, initialization, health monitoring
2. **Context Store**: Shared state (Redis, Firestore, in-memory)
3. **Message Queue**: Task distribution and handoff coordination
4. **Execution Engine**: Parallel/sequential execution controller
5. **Monitoring & Observability**: Logging, metrics, debugging

### Technology Stack Recommendations

```typescript
// Context Storage
- Redis: Fast shared state, good for small-medium swarms
- Firestore: Distributed state, scales well, good for hierarchical
- PostgreSQL: Durable state, excellent for audit trails
- In-Memory: Single-process only, great for development

// Execution
- Node.js + AsyncPara llel: Sequential/parallel coordination
- LangGraph: Graph-based workflows, excellent for state machines
- Temporal: Long-running workflows, retry logic, durability
- Bull/RabbitMQ: Message queues for distributed systems

// LLM APIs
- Anthropic Claude: Excellent for agentic reasoning
- OpenAI GPT: Competitive alternative
- Together AI: Open-source models, cost optimization
```

### Generic Swarm Library Template

```typescript
/**
 * Generic Swarm Framework
 * Supports all six patterns with pluggable components
 */

abstract class SwarmBase {
  protected agents: Map<string, Agent> = new Map();
  protected contextStore: ContextStore;
  protected executionEngine: ExecutionEngine;
  protected monitoringService: MonitoringService;

  abstract async execute(task: string): Promise<SwarmResult>;

  protected async callAgent(agent: Agent, message: string): Promise<string> {
    return await this.executionEngine.callLLM({
      systemPrompt: agent.systemPrompt,
      userMessage: message,
      model: agent.model,
      tools: agent.tools
    });
  }

  protected async updateSharedContext(key: string, value: any): Promise<void> {
    await this.contextStore.set(key, value);
  }

  protected async getSharedContext(key: string): Promise<any> {
    return await this.contextStore.get(key);
  }

  protected logEvent(event: string, details?: any): void {
    this.monitoringService.logEvent({
      timestamp: Date.now(),
      event,
      details,
      swarmPattern: this.constructor.name
    });
  }
}

// Pattern-specific implementations extend SwarmBase
class DecentralizedSwarmImpl extends SwarmBase {
  async execute(task: string): Promise<SwarmResult> {
    // Implementation...
  }
}

class HierarchicalSwarmImpl extends SwarmBase {
  async execute(task: string): Promise<SwarmResult> {
    // Implementation...
  }
}

// ... etc for other patterns
```

---

## Decision Framework

### Choosing the Right Pattern

Use this decision tree:

```
START
  │
  ├─ Is there a CLEAR HIERARCHY?
  │  │
  │  ├─ YES → HIERARCHICAL SWARM
  │  │   (Best for: Large teams, enterprise, quality control)
  │  │
  │  └─ NO ↓
  │
  ├─ Are TASKS INDEPENDENT?
  │  │
  │  ├─ YES → Can you execute in PARALLEL?
  │  │   │
  │  │   ├─ YES → PARALLEL SWARMS
  │  │   │   (Best for: Throughput, redundancy, consensus)
  │  │   │
  │  │   └─ NO → SEQUENTIAL SWARMS
  │  │       (Best for: Multi-stage transformation, pipelines)
  │  │
  │  └─ NO ↓
  │
  ├─ Are agents TIGHTLY COUPLED?
  │  │
  │  ├─ YES & (<8 agents) → MESH P2P
  │  │   (Best for: Specialist collaboration, distributed)
  │  │
  │  └─ NO ↓
  │
  ├─ Do you need DYNAMIC ADAPTATION?
  │  │
  │  ├─ YES → ADAPTIVE SWARM
  │  │   (Best for: Long-running, changing requirements)
  │  │
  │  └─ NO ↓
  │
  └─ DEFAULT → DECENTRALIZED SWARM
     (Best for: Fault tolerance, emergence, research)
```

### Selection Criteria

| Criterion | Best Pattern |
|-----------|--------------|
| **Maximum throughput** | Parallel Swarms |
| **Lowest latency** | Parallel Swarms |
| **Best fault tolerance** | Decentralized Swarm, Adaptive |
| **Easiest to debug** | Sequential, Hierarchical |
| **Scales 50+ agents** | Hierarchical |
| **Most flexible** | Adaptive Swarm |
| **Lowest token cost** | Sequential, Hierarchical |
| **Handles novel inputs** | Decentralized, Mesh |
| **Production-proven** | Hierarchical, Parallel, Sequential |
| **Experimental/Research** | Decentralized, Adaptive, Mesh |

---

## Hybrid Architectures

Most production systems combine patterns:

### Common Hybrid Examples

#### 1. Hierarchical + Pipeline
```
Director
  ├─ Team A: Sequential pipeline (Extract → Analyze → Synthesize)
  ├─ Team B: Sequential pipeline (Research → Validation)
  └─ Team C: Parallel agents (Multi-perspective review)
```

#### 2. Hierarchical + Mesh at Leaf Level
```
Director
  └─ Supervisor
      └─ Mesh Team (4 tightly-coupled specialists)
```

#### 3. Pipeline + Parallel in Middle Stage
```
[Stage 1: Researcher] 
  → [Stage 2: Parallel Analysis (5 agents) 
    → aggregate → Stage 3: Writer]
```

#### 4. Supervisor with Swarm Fallback
```
Primary: Orchestrator-Worker Pattern
Fallback: Decentralized Swarm (if orchestrator fails)
```

### Benefits of Hybrids

- ✅ **Optimize each subsystem** for its requirements
- ✅ **Reduce complexity** through decomposition
- ✅ **Balance cost and quality** within constraints
- ✅ **Production-proven** patterns in known parts
- ✅ **Experimentation room** for new patterns

### Composition Rules

1. **Hierarchical contains sub-patterns**: Director → (Hierarchical | Parallel | Sequential)
2. **Sequential can spawn parallel at stages**: Stage → Parallel agents
3. **Mesh limited to 3-8**: Larger teams require hierarchy
4. **Fallback patterns**: Primary pattern + secondary for resilience
5. **Clear boundaries**: Each pattern has inputs/outputs interface

---

## Common Pitfalls & Solutions

### Pitfall 1: Ping-Pong in Decentralized Swarms

**Problem**: Agents keep handing off back and forth, same two agents in loop

**Causes**:
- Ambiguous expertise boundaries
- No handoff completion criteria
- Agents unsure if they can complete task

**Solutions**:
```typescript
// Solution 1: Handoff detection and force completion
if (isPingPong(lastNHandoffs)) {
  forceTaskCompletion(currentTask, lastResponse);
}

// Solution 2: Clear expertise boundaries
agent.canHandle = (task) => {
  return task.requiredSkills.every(skill => 
    agent.expertise.includes(skill)
  );
};

// Solution 3: Max handoffs with fallback agent
if (handoffCount > MAX_HANDOFFS) {
  assignToGeneralist();
}
```

### Pitfall 2: State Consistency Issues

**Problem**: Agents write conflicting state simultaneously

**Causes**:
- No locking on shared state
- Race conditions in concurrent updates
- Lost updates from simultaneous writes

**Solutions**:
```typescript
// Solution 1: Lock-based synchronization
await contextStore.acquireLock(taskId);
try {
  await contextStore.update(taskId, newState);
} finally {
  await contextStore.releaseLock(taskId);
}

// Solution 2: Event-sourcing
const events = await contextStore.getEvents(taskId);
const state = applyEvents(initialState, events);

// Solution 3: Last-write-wins with versioning
state.version = currentVersion + 1;
await contextStore.put(taskId, state);
```

### Pitfall 3: Quality Degradation in Sequential Pipelines

**Problem**: Output quality drops significantly after 8+ stages

**Causes**:
- Each LLM handoff introduces ~1-3% error
- Errors compound: 0.98^8 = 78% quality after 8 stages
- Context loss in handoffs
- Divergence from original intent

**Solutions**:
```typescript
// Solution 1: Validation gates between stages
const stageOutput = await executeStage(stage, input);
if (!validateOutput(stageOutput, stage.criteria)) {
  // Retry or escalate
  return await retryStageWithFeedback(stage, input);
}

// Solution 2: Reference context throughout pipeline
const referenceContext = {
  originalInput,
  userIntent,
  keyRequirements
};

// Include in each stage prompt
`Remember the original intent: ${referenceContext.userIntent}
Ensure output aligns with: ${referenceContext.keyRequirements}`

// Solution 3: Limit pipeline to 3-5 high-confidence stages
// Use parallel swarms for broader perspectives if needed
```

### Pitfall 4: Mesh Combinatorial Explosion

**Problem**: Mesh with 20+ agents becomes impossible to debug

**Causes**:
- 20 agents = 190 potential connections
- 50 agents = 1,225 connections
- Message explosion in broadcasts
- Complex interdependencies

**Solutions**:
```typescript
// Solution 1: Enforce mesh size limit
if (agents.length > MESH_MAX) {
  throw new Error(`Mesh limited to ${MESH_MAX} agents, have ${agents.length}`);
}

// Solution 2: Decompose into sub-meshes
const subMesh1 = new Mesh(agents.slice(0, 5));
const subMesh2 = new Mesh(agents.slice(5, 10));
const coordinator = new HierarchicalOrchestrator([subMesh1, subMesh2]);

// Solution 3: Limited peer connections
agent.maxPeerConnections = 3; // Only talk to 3 peers, not all
```

### Pitfall 5: Token Cost Explosion

**Problem**: System uses 10x expected tokens

**Causes**:
- Redundant parallel execution
- Re-transmitting context through hierarchy
- Handoff overhead in swarms
- No caching of results

**Solutions**:
```typescript
// Solution 1: Result caching
const cached = await resultCache.get(hash(task));
if (cached) return cached;

// Solution 2: Context batching
// Instead of: 3 LLM calls with full context
// Use: 1 batch call with function calling

// Solution 3: Selective parallelism
// Don't parallelize everything:
// - Parallelize independent tasks ✓
// - Don't parallelize sequential dependencies ✗

// Solution 4: Prompt caching (with Claude API)
const response = await claude.messages.create({
  system: [
    { type: 'text', text: systemPrompt },
    { type: 'text', text: cachedContext, cache_control: { type: 'ephemeral' } }
  ]
});
```

### Pitfall 6: Difficult Debugging and Observability

**Problem**: Can't figure out why system behaved unexpectedly

**Causes**:
- No execution traces
- Message logs scattered across services
- State changes not tracked
- Agent reasoning opaque

**Solutions**:
```typescript
// Solution 1: Comprehensive execution logging
logExecutionTrace({
  swarmId,
  pattern,
  agentId,
  task,
  systemPrompt,
  response,
  timestamp,
  executionTime
});

// Solution 2: Structured logging
logger.info('agent_handoff', {
  from: agent1.id,
  to: agent2.id,
  reason: response.handoffReason,
  context: currentState
});

// Solution 3: Message auditing
messageLog.append({
  timestamp,
  agentId,
  messageType,
  messageContent,
  response,
  executionTime
});

// Solution 4: Visualization and replay
viewer.replay(executionTrace); // Show visual replay of swarm
viewer.inspect(agentId); // Inspect single agent's decisions
```

---

## Production Deployment Patterns

### Deployment Architecture

```
┌──────────────────────────────────────────┐
│        API Gateway / Load Balancer       │
└────────────────┬─────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
   ┌────▼────┐      ┌────▼────┐
   │ Process │      │ Process │  (Horizontal Scaling)
   │  Pool 1 │      │  Pool 2 │
   └────┬────┘      └────┬────┘
        │                 │
        └────────┬────────┘
                 │
         ┌───────▼────────┐
         │  Context Store │  (Redis/Firestore)
         │   (Shared)     │
         └────────────────┘
                 │
         ┌───────▼────────┐
         │  Message Queue │  (Redis/RabbitMQ)
         │   (Durable)    │
         └────────────────┘
                 │
         ┌───────▼────────┐
         │  LLM Provider  │  (Anthropic/OpenAI)
         │   (External)   │
         └────────────────┘
```

### Configuration for Each Pattern

#### Decentralized Swarm Deployment
```yaml
pattern: decentralized
maxHandoffs: 10
contextStore: redis  # Fast shared state
messageQueue: bullmq  # Durable handoffs
workers: 4  # Process pool
timeout: 300s
fallback: hierarchy  # If handoffs exceed max
```

#### Hierarchical Swarm Deployment
```yaml
pattern: hierarchical
maxLevels: 3
workers: 
  director: 1
  supervisors: 3-5
  leaf_agents: 20-50
contextStore: firestore  # Good for hierarchy
audit: strict  # Log all decisions
scaling: horizontal  # Add workers
```

#### Parallel Swarms Deployment
```yaml
pattern: parallel
agentCount: 5-10
concurrency: max  # Run all simultaneously
aggregation: weighted  # Supervisor aggregates
contextStore: redis
messageQueue: none  # No handoffs needed
timeout: 120s per agent
```

#### Sequential Pipeline Deployment
```yaml
pattern: sequential
stages: 5  # Keep <8 for quality
timeout: perStage
contextStore: redis
validation: perStage  # Validate between stages
fallback: retry  # Retry failed stages
```

### Monitoring & Observability

```typescript
interface SwarmMetrics {
  // Execution
  executionTime: number;
  totalAgents: number;
  activeAgents: number;
  failedAgents: number;

  // Quality
  successRate: number;
  errorRate: number;
  qualityScore: number;

  // Efficiency
  totalTokens: number;
  tokensPerAgent: number;
  costPerExecution: number;

  // Coordination
  handoffCount: number;
  handoffErrors: number;
  averageHandoffTime: number;

  // System
  messageCount: number;
  stateUpdates: number;
  uptime: number;
}

class SwarmMonitor {
  async collectMetrics(swarmId: string): Promise<SwarmMetrics> {
    return {
      executionTime: await this.getExecutionTime(swarmId),
      totalAgents: await this.getTotalAgents(swarmId),
      activeAgents: await this.getActiveAgents(swarmId),
      failedAgents: await this.getFailedAgents(swarmId),
      successRate: await this.getSuccessRate(swarmId),
      errorRate: await this.getErrorRate(swarmId),
      qualityScore: await this.getQualityScore(swarmId),
      totalTokens: await this.getTotalTokens(swarmId),
      tokensPerAgent: await this.getTokensPerAgent(swarmId),
      costPerExecution: await this.getCost(swarmId),
      handoffCount: await this.getHandoffCount(swarmId),
      handoffErrors: await this.getHandoffErrors(swarmId),
      averageHandoffTime: await this.getAvgHandoffTime(swarmId),
      messageCount: await this.getMessageCount(swarmId),
      stateUpdates: await this.getStateUpdates(swarmId),
      uptime: await this.getUptime(swarmId)
    };
  }

  async alertIfAnomalous(metrics: SwarmMetrics): Promise<void> {
    if (metrics.errorRate > 0.2) {
      await this.alert('High error rate detected', { metrics });
    }
    if (metrics.qualityScore < 0.8) {
      await this.alert('Quality degradation detected', { metrics });
    }
    if (metrics.handoffErrors > 5) {
      await this.alert('Handoff failures detected', { metrics });
    }
  }
}
```

---

## Conclusion

| Pattern | Best For | Maturity | Complexity |
|---------|----------|----------|-----------|
| **Decentralized Swarm** | Fault tolerance, emergence | Emerging | High |
| **Hierarchical** | Enterprise, large-scale | Production | Medium |
| **Parallel** | Throughput, consensus | Production | Medium |
| **Sequential** | Multi-stage workflows | Production | Low |
| **Adaptive** | Long-running, dynamic | Experimental | Very High |
| **Mesh P2P** | Distributed, specialist teams | Established | Medium-High |

**Key Takeaways**:

1. **Pattern selection is foundational** - Choose wrong and you'll pay for it
2. **Hybrids are common** - Combine patterns at subsystem level
3. **Monitor everything** - Observability is critical for swarms
4. **Start simple** - Begin with proven patterns (Hierarchical, Parallel, Sequential)
5. **Experimental carefully** - Save Decentralized, Adaptive, Mesh for R&D
6. **Scaling** - Hierarchical for 50+, Parallel for throughput, Mesh only <8
7. **Production requirements** - Add quality gates, validation, fallback patterns
8. **Token optimization** - Use caching, batching, selective parallelism

---

## References

- [OpenAI Swarm Framework](https://github.com/openai/swarm)
- [LangGraph Multi-Agent Patterns](https://python.langchain.com/docs/langgraph/)
- [Strands Agents SDK](https://strandsagents.com/docs/)
- [Microsoft AI Agent Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/)
- [AWS Multi-Agent Collaboration](https://aws.amazon.com/blogs/machine-learning/)
- [Anthropic Prompt Caching API](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)

---

**Document Version**: 1.0  
**Last Updated**: May 2026  
**Audience**: Architects, Engineers, AI/ML Teams  
**Status**: Production-Ready Reference
