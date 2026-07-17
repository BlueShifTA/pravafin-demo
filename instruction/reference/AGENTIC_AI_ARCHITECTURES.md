# Agentic AI Architectures — Reference Guide

**Version:** 1.0 | **Updated:** 2026-03-22 | **Source research:** 10-iteration autoresearch loop
**Audience:** Engineers, architects, and technical leads building or evaluating agentic AI systems
**Scope:** Framework-agnostic. Applies to AI startups, robotics/embedded AI, infra SaaS, fintech.

---

## 1. Executive Summary

If you read nothing else, read this.

- **Most pipelines do not need a framework.** A linear 3–7 step pipeline with known flow is a Python state machine. Raw Python wins on simplicity, debuggability, and maintainability until you hit genuine complexity (10+ nodes, dynamic routing, durable execution requirements).

- **Multi-agent systems amplify errors, not capability.** Unstructured multi-agent networks amplify errors 17.2x vs single-agent baselines (Google DeepMind, Dec 2025). The correct decision driver is task decomposability and genuine parallelism need — not the desire to use agents.

- **Framework overhead is not the bottleneck.** LangGraph adds ~14ms and ~2.03k tokens per invocation. Against a typical 2–5 second LLM call, this is noise. Architecture decisions — number of LLM calls, parallel vs sequential routing — matter 100x more than framework choice for latency.

- **The abandonment pattern is real.** Teams routinely start with LangChain or LangGraph and strip them out in production, reverting to raw FastAPI + the LLM provider client. Validate framework fit before committing to it.

- **Regulated industries require deterministic pipelines.** Clinical, financial, and legal use cases have auditability and traceability requirements. An autonomous agent that decides its own routing steps is likely non-compliant without chain-of-thought logging, immutable audit trails, and regulatory pre-approval.

---

## 2. Framework Comparison Table

Research compiled 2026-03-22. Benchmark: 100 queries, 100 runs each, identical GPT-4.1-mini, embeddings, and tools unless otherwise noted.

| Framework | Best For | Worst For | Framework Latency Overhead | Token Usage / Query | Production Readiness | When to Use |
|-----------|----------|-----------|---------------------------|--------------------|--------------------|-------------|
| **Raw Python** | Known fixed pipelines, regulated domains, small teams | Dynamic agent behavior, workflows needing durable execution | ~0ms | None | Depends on team discipline | Any pipeline where you can enumerate the steps upfront |
| **LangGraph** | Complex stateful workflows, conditional multi-branch routing, production systems | Simple linear tasks, solo/small teams, regulated contexts without observability budget | ~14ms | ~2.03k/query | High (v1.0, Oct 2025) | >7 nodes, conditional routing, multi-engineer teams, observability required |
| **LangChain** (without LangGraph) | Thin tool/chain wrapper, rapid prototyping | Production at scale, complex state | ~10ms | ~2.40k/query | Medium | When you need quick LLM chaining without graph complexity |
| **CrewAI** | Role-based prototyping, demos, Fortune 500 pilots | Complex branching, high-throughput production | ~3x LangGraph latency (~42ms) | ~3x LangGraph | Medium | Role-driven workflows where manager/agent hierarchy maps naturally to the domain |
| **AutoGen** | Research workflows, conversational multi-agent | Production at scale (merging into Microsoft Agent Framework, GA Q1 2026), strict latency budgets | Moderate | Slightly more efficient than LangGraph on simple tasks | Medium (in transition) | Microsoft/Azure ecosystems; research and conversational tasks |
| **DSPy** | Prompt optimization and program compilation, improving model outputs without restructuring pipelines | Multi-agent coordination, workflow orchestration | ~3.5ms | ~2.03k (lowest overhead) | Medium | Layer on top of any pipeline when prompt quality is the bottleneck, not architecture |
| **Temporal** | Long-running durable workflows (hours/days), human-in-the-loop with guaranteed execution, financial/ops workflows | Rapid prototyping, simple pipelines | N/A (workflow engine, not LLM framework) | N/A | Very high | Any workflow that cannot tolerate data loss on crash, needs pause/resume, or runs longer than a single HTTP request |
| **Microsoft Agent Framework** | Azure/M365 enterprise stack, AutoGen-native teams | Non-Microsoft cloud, early-stage startups | Moderate | — | GA Q1 2026 | Enterprise teams already in Microsoft ecosystem |

**Key distinctions:**
- DSPy is a prompt optimizer, not an orchestrator. It works alongside other frameworks.
- Temporal is a workflow engine, not an AI framework. It solves durable execution. LangGraph and Temporal are complementary, not competing.
- Conflating these layers produces bad architecture decisions.

Sources: [DataCamp — CrewAI vs LangGraph vs AutoGen](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen), [DEV Community benchmarks 2026](https://dev.to/saivishwak/benchmarking-ai-agent-frameworks-in-2026-autoagents-rust-vs-langchain-langgraph-llamaindex-338f), [Latenode — LangGraph vs AutoGen vs CrewAI](https://latenode.com/blog/platform-comparisons-alternatives/automation-platform-comparisons/langgraph-vs-autogen-vs-crewai-complete-ai-agent-framework-comparison-architecture-analysis-2025), [Galileo — AutoGen vs CrewAI vs LangGraph](https://galileo.ai/blog/autogen-vs-crewai-vs-langgraph-vs-openai-agents-framework)

---

## 3. Architecture Decision Tree

Walk this tree before picking a framework. Most teams should stop early.

```
Is your pipeline deterministic — fixed steps, known flow?
  YES
  └─ Is it <= 7 steps?
       YES → Raw Python state machine. Stop here.
       NO  → Raw Python orchestrator class. Consider LangGraph ONLY if you also
             need observability tooling and multi-engineer maintainability.
  NO (dynamic routing, agent decides its own steps)
  └─ Is this a regulated domain (clinical, financial, legal)?
       YES → Do NOT use autonomous agents without:
             - Chain-of-thought logging at every decision point
             - Immutable audit trails
             - Human-in-the-loop at all patient/client-facing decisions
             - Regulatory pre-approval of the LLM decision surface
             Use deterministic pipeline + explicit state machine instead.
       NO
       └─ Does the workflow need to survive crashes / pause for human input
          / run for hours or days?
            YES → Temporal (durable execution engine)
                  Optionally: LangGraph nodes inside Temporal activities
                  for the AI-specific orchestration layer.
            NO
            └─ Do you genuinely need multiple agents (parallel independent
               sub-tasks, hard security boundaries, separate teams)?
                 YES
                 └─ Is the agent network structured (supervisor → workers)?
                      YES → LangGraph multi-agent OR supervised CrewAI
                            Ensure: schema validation at every agent boundary,
                            max 3 retries per agent per run, context-window-aware
                            handoff summarization.
                      NO (peer network / unstructured) → DO NOT PROCEED.
                            Unstructured multi-agent nets amplify errors 17.2x.
                            Restructure or use a single agent with tools.
                 NO (single-agent is sufficient)
                 └─ Does your team need shared observability / multi-engineer
                    collaboration / complex conditional routing (>7 nodes)?
                      YES → LangGraph
                      NO  → Raw Python orchestrator with structured logging.
                            Add DSPy if prompt quality is the bottleneck.
```

### Additional branching: LLM framework vs workflow engine

```
Does the task run longer than a single HTTP request?
  YES → Temporal for durable execution. LangGraph can run inside Temporal activities.
  NO  → LLM framework is sufficient (Raw Python / LangGraph).

Is your bottleneck prompt quality, not architecture?
  YES → DSPy as a module layer on top of whatever orchestrator you have.
  NO  → Framework / architecture question above.

Are you optimizing for prototype speed over production correctness?
  YES → CrewAI or OpenAI Agents SDK. Accept the throw-away risk.
  NO  → Skip CrewAI. Use LangGraph or raw Python.
```

---

## 4. The "Build vs Framework" Decision

### When raw Python wins

Use raw Python when ALL of the following are true:

- The pipeline steps are known at design time (enumerable)
- The team is 1–3 engineers with strong Python skills
- Timeline is short (prototype, MVP, or constrained sprint)
- Regulatory compliance requires deterministic, auditable behavior
- The workflow fits in a single HTTP request lifecycle
- You can instrument with structured logging (JSON logs with step names, inputs, outputs, timestamps)

**Concrete signal:** If you can write the orchestrator as a class with named methods (`intake()`, `match()`, `recommend()`, `summarize()`), you do not need a framework. The Python IS the state machine.

### When LangGraph wins

Use LangGraph when ALL of the following are true:

- Workflow has more than 7 nodes with genuine conditional routing (not just `if/else`)
- Multiple engineers maintain the codebase and need a shared mental model
- Production reliability requires durable checkpointing (process crash recovery)
- LangSmith observability is a stated requirement (team will actually use it)
- Development timeline allows 1–2 weeks for framework onboarding
- The workflow is not in a regulated domain that prohibits non-deterministic routing

**LangGraph 1.0 (released October 2025) stabilized the API.** Breaking changes were frequent before 1.0. Tutorials from before this date may not work.

### When Temporal wins

Use Temporal when:

- Workflows run for hours, days, or weeks (e.g., research pipelines, approval workflows, async customer onboarding)
- Human-in-the-loop is required with guaranteed resume after days of wait
- Exactly-once execution semantics are required (financial transactions, compliance actions)
- You cannot tolerate data loss on process crash (Temporal provides durable state, not Redis cache)
- The team is comfortable with Go or Java (or Python SDK, which is mature but secondary)

**Two-layer architecture pattern:** Use Temporal for durable execution and LangGraph inside Temporal activities for AI-specific orchestration. Grid Dynamics moved a deep research agent from LangGraph-only to this pattern because LangGraph's Redis state management was creating lifecycle management and debugging complexity in production.

Source: [Temporal — Prototype to Production (Grid Dynamics case study)](https://temporal.io/blog/prototype-to-prod-ready-agentic-ai-grid-dynamics), [Anup.io — Temporal + LangGraph Two-Layer Architecture](https://www.anup.io/temporal-langgraph-a-two-layer-architecture-for-multi-agent-coordination/)

### The "framework abandonment" pattern

A widely corroborated practitioner observation:

> "Almost everyone starts with LangChain or similar frameworks, and almost everyone eventually strips them out. LangChain is great for demos. Production is just FastAPI and the OpenAI client."

This is not anecdote. It is a documented pattern across engineering blogs and post-mortems. The causes:

1. Five layers of abstraction (framework → chain → runnable → LCEL → tool internals) make debugging non-trivial
2. LangChain's API changed frequently before LangGraph 1.0; pinned dependencies rot
3. Framework overhead becomes visible in cost analysis at scale
4. Teams discover their actual pipeline is simpler than the framework assumes

**Mitigation:** Prototype raw first. Reach for a framework only after the raw prototype reveals a specific pain point the framework directly addresses.

### Cost-benefit analysis template

Use this template when advising a client or evaluating a framework migration:

| Cost dimension | Raw Python | LangGraph | Temporal |
|---------------|-----------|-----------|---------|
| Initial build (engineering days) | Low (1–2 weeks for complex pipeline) | Medium (+1–2 weeks onboarding) | High (+3–4 weeks) |
| Ongoing maintenance (% of build) | Low (~5–10%/yr for stable pipeline) | Medium (~15–20%/yr: drift, re-runs, updates) | Low–Medium (~10–15%/yr) |
| Observability | Custom (build your own) | LangSmith (paid at scale) | Temporal UI (included) |
| Debugging | Direct Python debugger | Through 5 abstraction layers | Workflow-level replay |
| Framework risk | None | LangChain Inc. venture-backed | Temporal.io well-funded |
| Token overhead | None | ~2.03k/invocation | None |
| Latency overhead | ~0ms | ~14ms | N/A |

**Enterprise build cost range:** $50,000–$200,000 for production-grade agentic systems including customization, data pipelines, and change management. Mid-sized LangGraph projects have been reported at $87,000 over 14 weeks with 68% resolution accuracy. Annual maintenance is approximately 15–20% of initial build cost.

Sources: [Galileo — Hidden Costs of Agentic AI](https://galileo.ai/blog/hidden-cost-of-agentic-ai), [CodespaceTechLabs — LangGraph costs 2025](https://www.codespacetechlabs.com/post/langgraph-and-development-costs-in-2025), [Ampcome — LangChain vs Custom Workflows](https://www.ampcome.com/post/langchain-vs-custom-workflows-ai-agents-2025)

---

## 5. Multi-Agent Patterns

### The compound reliability problem

Every sequential agent step multiplies failure probability:

```
Single agent, 10 sequential steps at 99% per-step reliability:
  0.99^10 = 90.4% end-to-end reliability

Multi-agent chain (3 agents, 10 steps each):
  0.99^30 = 74.0% end-to-end reliability

At 95% per step (realistic for complex tasks):
  0.95^10 = 59.9% — likely unacceptable for production
  0.95^30 = 21.5% — almost certainly unacceptable
```

Source: [Redis — Single-agent vs multi-agent](https://redis.io/blog/single-agent-vs-multi-agent-systems/)

### Google DeepMind finding (December 2025)

180 configurations, 5 agent architectures, 3 LLM families:

- **Unstructured multi-agent networks amplify errors 17.2x** vs single-agent baselines
- **Well-structured multi-agent** (supervisor → specialists): Anthropic's Claude Opus 4 + Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by **90.2%** on research evaluations

The critical variable is structure, not agent count. An unstructured peer network is almost always worse than a well-prompted single agent.

Source: [Galileo — Why Multi-Agent LLM Systems Fail](https://galileo.ai/blog/multi-agent-llm-systems-fail)

### Pattern 1: Single agent + tools

**Architecture:** One agent with access to multiple tools (web search, database query, code execution, file read/write). The agent decides which tools to call and in what order.

**When to use:**
- Task is self-contained and sequential
- Context fits comfortably in one model's context window
- Problem is solvable with prompting + tool calls
- Team is small or at prototype stage
- Speed of debugging matters more than parallelism

**When this is sufficient for >80% of production cases.** Most "we need multi-agent" instincts are solved by giving one agent better tools.

### Pattern 2: Structured multi-agent (supervisor → workers)

**Architecture:** A supervisor agent decomposes tasks and delegates to specialist worker agents. Workers report results back to supervisor. Supervisor synthesizes final output.

**When to use:**
- Tasks genuinely decompose into parallel independent sub-tasks (e.g., research 5 topics simultaneously)
- Different domains require independently scalable specialists
- Hard security/compliance boundaries mandate separation (e.g., PII-handling agent isolated from logging agent)
- Organizational separation is required (different teams own different agents)

**Requirements for this to work:**
- Strict schema validation at every agent boundary (JSON schema, never free-form)
- Context-window-aware handoff summarization (do not pass raw long outputs between agents)
- Max 3 retries per agent per run with dead-letter queue for failures
- Supervisor must be able to handle partial worker failures gracefully

### Pattern 3: Unstructured multi-agent (peer network)

**Architecture:** Multiple agents communicate as peers, each routing tasks to others dynamically.

**When to use:** Almost never in production.

**Why it fails:**
- 17.2x error amplification (Google DeepMind)
- Debugging is intractable — no single point of control
- Error cascading: one agent's bad output becomes another's input
- Audit trails are nearly impossible to reconstruct
- Context accumulates across multiple agents with no pruning logic

**The only legitimate use case** is research/exploration where correctness is not required and the goal is generating diverse candidate outputs for human review.

### Anti-patterns to avoid

| Anti-pattern | Why it fails | Correct approach |
|-------------|-------------|-----------------|
| "More agents = more capability" | Compound reliability loss (0.95^n). 17.2x error amplification in unstructured nets. | Single agent + tools unless genuine parallelism required |
| Agent decides its own routing steps in regulated domain | Non-compliant. Undocumented routing decisions fail audit. | Deterministic orchestrator with logged conditional logic |
| Passing raw LLM output between agents | Format mismatch breaks downstream agents silently | JSON schema validation at every agent boundary |
| Using a framework because the demo was impressive | Framework abandonment pattern. Adds cost without benefit. | Prototype raw first; adopt framework for specific gap |
| Multi-agent for "separation of concerns" | Separation of concerns is a code organization pattern, not an agent pattern | One agent with modular tool implementations |
| Infinite retry without circuit breaker | Budget exhaustion, runaway costs | Max 3 retries, exponential backoff, dead-letter queue |
| Storing critical workflow state in Redis cache | Cache eviction wipes state; workflow becomes non-resumable | Temporal for durable state; never rely on cache for critical path |

Sources: [arXiv 2503.13657 — Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/html/2503.13657v1), [Towards Data Science — The Multi-Agent Trap](https://towardsdatascience.com/the-multi-agent-trap/), [Microsoft Learn — Single vs Multiple Agents](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ai-agents/single-agent-multiple-agents)

---

## 6. Production Checklist for Agentic Systems

### Observability

What to trace at minimum:

```
Per agent invocation:
  - agent_id / workflow_run_id (correlation ID for full trace)
  - step_name
  - inputs (sanitized — remove PII before logging)
  - outputs (sanitized)
  - timestamp_start, timestamp_end, duration_ms
  - llm_model + version
  - token_count_input, token_count_output
  - tool_calls (name, args, result, duration_ms each)
  - confidence scores (if available)
  - error (if applicable, with type and non-verbose message)

Per workflow run:
  - total_token_cost
  - total_duration_ms
  - step_count
  - success / failure
  - human_review_triggered (boolean)
```

Do not log PII, credentials, patient data, or financial account numbers in plain text. Log a hash or reference ID instead.

Use structured JSON logs (not freeform text) so logs are machine-queryable. This is the minimum viable audit trail without a framework like LangSmith.

### Testing strategies

Agentic systems are non-deterministic. Traditional unit tests are necessary but not sufficient.

**Evaluation pyramid (bottom to top, cheapest to most expensive):**

```
[Deterministic unit tests]   — Test all non-LLM components. Fast, cheap. Required.
         |
[Schema validation tests]    — Assert output matches expected JSON schema. Catches format regressions.
         |
[Tool-call validation]       — Did agent call the correct tool with correct args?
         |
[Trajectory evaluation]      — Did agent take the correct sequence of steps?
         |
[LLM-as-judge]               — Use a judge LLM to score semantic correctness. Automated.
         |
[Human review]               — Gold standard. Expensive. Use for calibration and edge cases.
```

**Techniques:**
- **Synthetic benchmarks:** Generate structured datasets with ground-truth expected steps. Use in CI for regression detection.
- **Tool tapes:** Record tool responses in production, replay them deterministically in tests. Equivalent to HTTP fixtures. Eliminates LLM non-determinism from integration tests.
- **Real task replay:** Replay anonymized production failures. Gold standard for regression prevention.

**Automation gate (block deployment if):**

```python
success_rate_delta > -0.05     # more than 5% success rate drop
cost_per_task_delta > 0.30     # more than 30% cost increase
tool_error_rate > 0.02         # more than 2% tool call errors
```

Sources: [VirtusLab — Testing Agentic Systems](https://virtuslab.com/blog/ai/testing-evaluating-agentic-systems), [arXiv 2512.12791 — Beyond Task Completion](https://arxiv.org/abs/2512.12791), [Turing College — Evaluating AI Agents 2025](https://www.turingcollege.com/blog/evaluating-ai-agents-practical-guide)

### Error handling

```
Per tool call:
  - Timeout: explicit timeout budget per tool (e.g., 10s for web search, 30s for LLM call)
  - Retry: max 3 attempts, exponential backoff (1s, 2s, 4s)
  - Fallback: define a fallback path for each critical tool
  - Dead-letter queue: log failed calls for human review

Per agent:
  - Circuit breaker: if error rate > threshold, fail fast and return partial result
  - Context-window guard: check token count before handoffs; summarize if approaching limit
  - Schema validation: validate every LLM output before acting on it
  - Never pass raw LLM output directly to a tool or external system

Per workflow:
  - Max budget: total token or cost budget per run (hard stop)
  - Timeout: max wall-clock time for entire workflow
  - Partial result: define behavior when workflow fails mid-run
    (return partial result? rollback? queue for retry?)
```

### Cost management

```
Token budgets:
  - Set hard limits per workflow run (e.g., 100k tokens max)
  - Alert at 80% of budget
  - Log cost per workflow run in structured logs (correlate with business outcomes)

Caching:
  - Cache deterministic sub-steps (e.g., RAG retrieval for identical queries)
  - Use semantic cache (embedding similarity) for near-duplicate queries
  - Never cache outputs that depend on time, user identity, or real-time data

Model selection:
  - Use smaller/cheaper models for routing and classification steps
  - Reserve larger models for synthesis, generation, and judgment steps
  - Benchmark cost vs quality for each step independently
```

### Security

See also: `reference/SECURITY_PATTERNS.md` for implementation-level patterns.

```
Prompt injection:
  - Sanitize all user inputs before inserting into prompts
  - Use system prompt / user prompt separation; never concatenate untrusted input into system prompt
  - Validate that tool call arguments came from the agent, not from injected user content
  - OWASP LLM Top 10: 73% of production deployments have prompt injection vulnerability

Tool abuse:
  - Principle of least privilege: agents have access only to tools they need for their specific task
  - Sandboxed tool execution: code execution tools run in isolated containers
  - Tool call allowlist: define which tools each agent may call; reject others

Output validation:
  - Never execute agent output as code without sandboxed review
  - Validate all outputs against expected schema before acting
  - For actions with side effects (write to DB, send email, make API call): require explicit confirmation or human-in-the-loop for novel/high-risk actions

Data handling:
  - Log references/hashes, not raw PII
  - Patient/customer data processed in-memory only; never written to unencrypted logs
  - Audit log writes are append-only and immutable
```

Sources: [Galileo — Hidden Costs of Agentic AI](https://galileo.ai/blog/hidden-cost-of-agentic-ai), [ZenML — Agent Deployment Gap](https://www.zenml.io/blog/the-agent-deployment-gap-why-your-llm-loop-isnt-production-ready-and-what-to-do-about-it), [Medium — Engineering Challenges in Agentic AI](https://medium.com/@sahin.samia/engineering-challenges-and-failure-modes-in-agentic-ai-systems-a-practical-guide-f9c43aa0ae3f)

---

## 7. Regulatory Considerations

### When agentic AI becomes a regulated artifact

| Use case | Regulatory regime | Trigger condition |
|----------|------------------|------------------|
| Clinical decision support | FDA SaMD, EU MDR, EU AI Act | System influences a clinical decision (diagnosis, treatment, dosing) |
| Financial advice / trading | MiFID II, SEC, FINRA | System makes or influences financial recommendations |
| Legal document generation | Jurisdiction-specific bar regulations | System generates legal advice or documents |
| HR/hiring decisions | EU AI Act (high risk), EEOC | System screens or ranks candidates |
| Critical infrastructure | EU AI Act (high risk), sector-specific | System controls physical infrastructure |

**EU AI Act classification for agentic AI (2025–2026):**
- Autonomous agents in high-risk domains (listed above) are classified as **high-risk AI systems**
- Requirements: conformity assessment, technical documentation, logging, human oversight mechanism, accuracy/robustness standards
- "Unacceptable risk" category prohibits AI systems that operate with no meaningful human control over consequential decisions

### Deterministic pipelines vs autonomous agents in regulated domains

| Dimension | Deterministic pipeline | Autonomous agent |
|-----------|----------------------|-----------------|
| Auditability | Straightforward — outputs are predictable from inputs | Complex — requires reasoning chain logging at every decision |
| Regulatory fit | Well-established (SaMD, FDA CDS guidance) | Emerging; UNDCS classification proposed |
| Explainability | Inherent | Must be engineered explicitly |
| Compliance drift | Low risk | Requires continuous monitoring |
| Human oversight | Can be designed in at fixed points | Must be designed in — agent may bypass if not constrained |

**Practical rule:** In any regulated domain, use a deterministic orchestrator where the code defines which steps run and in what order. The LLM provides reasoning within each step, but does not determine the workflow path. This is auditable.

### Audit trail requirements

Minimum audit trail for regulated agentic systems:

```
Immutable, append-only log containing:
  - Session/workflow ID
  - Timestamp (UTC, millisecond precision)
  - Step name
  - Model version + prompt version (commit hash or semantic version)
  - Input hash (not raw input if PII)
  - Output hash + output text (for clinical: full output, not hash)
  - Human review triggered (boolean + reviewer ID if applicable)
  - Decision point with rationale (for any branch in the workflow)

Retention:
  - Clinical: 10 years (EU) / 7 years (US) minimum
  - Financial: 5–7 years (MiFID II, SEC)
  - General enterprise: per data retention policy
```

### Human-in-the-loop requirements

For high-risk regulated domains, human oversight is not optional. Design it in from the start:

- **Pre-action review:** Human approves before irreversible actions (prescribing medication, executing trade, sending legal document)
- **Exception handling:** Any output flagged as low-confidence, high-stakes, or outside training distribution routes to human review
- **Override always available:** The system must allow a human to override any agent decision at any point
- **Audit of overrides:** Human overrides are logged with reason; used to improve the system

Sources: [Nature npj Digital Medicine — Regulation of Clinical AI](https://www.nature.com/articles/s41746-026-02420-z), [AISERA — Agentic AI Compliance](https://aisera.com/blog/agentic-ai-compliance/), [CHAPSVision — Auditability of Clinical AI](https://www.chapsvision.com/blog/transparency-control-ai-responses-clinical-process/)

---

## 8. Consulting Framework

### Assessing an agentic architecture in 2–4 days

**Day 1: Discovery (half day + async review)**

Questions to ask:
- What task is the agent performing? What are the inputs and outputs?
- How many sequential LLM calls are in a typical workflow run?
- Is the routing dynamic (agent decides) or fixed (code decides)?
- What is the current production failure rate and failure mode?
- What observability exists today?
- What is the regulatory classification of the domain?

Artifacts to review:
- Architecture diagram (if exists)
- Framework dependencies (`pyproject.toml`, `requirements.txt`, `package.json`)
- Sample workflow trace or log
- Error/exception logs from last 30 days
- Token cost reports (if available)

**Day 2: Complexity and reliability audit**

Evaluate:
- Count LLM call nodes in the workflow graph
- Identify all agent handoff points and validate schema enforcement
- Check retry logic, timeout budgets, and circuit breakers
- Trace one full workflow run end-to-end with instrumentation
- Identify all tools an agent can call; assess least-privilege compliance

**Days 3–4: Architecture recommendation**

Produce:
- Complexity classification (over-engineered / appropriate / under-engineered)
- Framework fit assessment (is the chosen framework justified?)
- Reliability risk assessment (failure modes, error amplification risk)
- Observability gap assessment
- Regulatory compliance gap (if applicable)
- Prioritized remediation plan (quick wins vs structural changes)

### Common anti-patterns found in client systems

In order of frequency:

1. **Over-engineered multi-agent for a linear pipeline** — client used CrewAI or LangGraph for a workflow that is effectively a sequential 4-step pipeline. Full rewrite to raw Python halved the latency and eliminated the debugging burden.

2. **No schema validation at agent boundaries** — agents pass free-form text between each other. First format mismatch breaks the chain silently. Fix: JSON schema validation at every handoff.

3. **Infinite retry loops without budget** — agent A fails, calls agent B, which calls agent A. No max retry, no dead-letter queue. Result: runaway costs and no output. Fix: max 3 retries per agent, dead-letter queue, alert on budget threshold.

4. **Framework version drift** — LangChain pinned at 0.1.x (pre-1.0), tutorials written against 0.3.x fail. Dependency rot is hidden until a developer tries to add a feature. Fix: explicit version pins + automated dependency update PRs with test gate.

5. **PII in agent logs** — client logs full LLM inputs/outputs containing patient or customer data. GDPR/HIPAA non-compliant. Fix: log reference IDs + hashes, not raw data.

6. **Missing human-in-the-loop in regulated domain** — autonomous agent making clinical or financial recommendations with no override mechanism. Regulatory non-compliance. Fix: interrupt point before irreversible action, configurable confidence threshold for routing to human review.

7. **LangSmith not used despite LangGraph dependency** — team adopted LangGraph for observability but never set up LangSmith. They have the overhead without the benefit. Fix: either set up LangSmith or migrate to raw Python with structured logging.

### Recommended engagement structure

**Tier 1 — Agentic Architecture Review** (2–4 days, diagnostic)
- Deliverable: written assessment with complexity/cost/compliance trade-off analysis, prioritized remediation list
- Suitable for: clients evaluating whether to build agentic systems, or who have built and are experiencing production issues
- Output: architecture recommendation report

**Tier 2 — Agentic Architecture Design** (1–3 weeks, prescriptive)
- Deliverable: detailed technical design, decision tree for framework selection, production checklist, reference implementation pattern
- Suitable for: clients starting a new agentic system and wanting to avoid common pitfalls
- Output: design document + working prototype

**Tier 3 — Agentic System Optimization** (4–12 weeks, implementation)
- Deliverable: measurable improvements to reliability, latency, cost, or regulatory compliance of existing production system
- Suitable for: clients with production agentic systems that have reliability, cost, or compliance issues
- Output: before/after metrics, implementation, runbook

### Pricing guidance (internal reference — not client-facing)

| Engagement | Duration | CHF Range | Rationale |
|-----------|----------|-----------|-----------|
| Architecture Review | 2–4 days | 5,000–15,000 | Diagnostic, time-boxed, high-leverage |
| Architecture Design | 1–3 weeks | 15,000–35,000 | Prescriptive, requires deep domain understanding |
| System Optimization | 4–12 weeks | 40,000–120,000 | Implementation, measurable outcomes, on-site or close collaboration |

Position these as systems-level engagements, not "AI consulting." The value proposition is: performance and architectural correctness for AI infrastructure, informed by production evidence — not framework evangelism.

---

## 9. Sources

All citations from the original research (10-iteration autoresearch loop, completed 2026-03-22):

- [DataCamp — CrewAI vs LangGraph vs AutoGen](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
- [Latenode — LangGraph vs AutoGen vs CrewAI Architecture Analysis](https://latenode.com/blog/platform-comparisons-alternatives/automation-platform-comparisons/langgraph-vs-autogen-vs-crewai-complete-ai-agent-framework-comparison-architecture-analysis-2025)
- [Galileo — AutoGen vs CrewAI vs LangGraph vs OpenAI](https://galileo.ai/blog/autogen-vs-crewai-vs-langgraph-vs-openai-agents-framework)
- [Langwatch — Best AI Agent Frameworks 2025](https://langwatch.ai/blog/best-ai-agent-frameworks-in-2025-comparing-langgraph-dspy-crewai-agno-and-more)
- [Keywords AI — DSPy vs LangGraph](https://www.keywordsai.co/market-map/compare/dspy-vs-langgraph)
- [AryaXAI — Comparing Modern AI Agent Frameworks](https://www.aryaxai.com/article/comparing-modern-ai-agent-frameworks-autogen-langchain-openai-agents-crewai-and-dspy)
- [Temporal — Prototype to Production (Grid Dynamics case study)](https://temporal.io/blog/prototype-to-prod-ready-agentic-ai-grid-dynamics)
- [Temporal Community — Agentic AI vs Temporal Workflows](https://community.temporal.io/t/agentic-ai-lang-graph-vs-temporal-workflows/18371)
- [Anup.io — Temporal + LangGraph Two-Layer Architecture](https://www.anup.io/temporal-langgraph-a-two-layer-architecture-for-multi-agent-coordination/)
- [Aerospike — LangGraph in Production: Latency, Replay, Scale](https://aerospike.com/blog/langgraph-production-latency-replay-scale)
- [DEV Community — Benchmarking AI Agent Frameworks 2026](https://dev.to/saivishwak/benchmarking-ai-agent-frameworks-in-2026-autoagents-rust-vs-langchain-langgraph-llamaindex-338f)
- [Galileo — Why Multi-Agent LLM Systems Fail](https://galileo.ai/blog/multi-agent-llm-systems-fail)
- [arXiv 2503.13657 — Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/html/2503.13657v1)
- [Towards Data Science — The Multi-Agent Trap](https://towardsdatascience.com/the-multi-agent-trap/)
- [Microsoft Learn — Single vs Multiple Agents](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ai-agents/single-agent-multiple-agents)
- [Redis — Single-agent vs Multi-agent](https://redis.io/blog/single-agent-vs-multi-agent-systems/)
- [ZenML — Agent Deployment Gap](https://www.zenml.io/blog/the-agent-deployment-gap-why-your-llm-loop-isnt-production-ready-and-what-to-do-about-it)
- [Galileo — Hidden Costs of Agentic AI](https://galileo.ai/blog/hidden-cost-of-agentic-ai)
- [arXiv 2512.12791 — Beyond Task Completion](https://arxiv.org/abs/2512.12791)
- [VirtusLab — Testing Agentic Systems](https://virtuslab.com/blog/ai/testing-evaluating-agentic-systems)
- [Turing College — Evaluating AI Agents 2025](https://www.turingcollege.com/blog/evaluating-ai-agents-practical-guide)
- [Nature npj Digital Medicine — Regulation of Clinical AI (UNDCS)](https://www.nature.com/articles/s41746-026-02420-z)
- [CHAPSVision — Auditability and Transparency of Clinical AI](https://www.chapsvision.com/blog/transparency-control-ai-responses-clinical-process/)
- [AISERA — Agentic AI Compliance](https://aisera.com/blog/agentic-ai-compliance/)
- [Medium — Docker-FastAPI RAG with LangGraph Ollama FAISS](https://medium.com/@ion.stefanache0/docker-fastapi-rag-with-langgraph-faiss-and-mysql-9ca64d00abc8)
- [LangChain Docs — Ollama Integration](https://docs.langchain.com/oss/python/integrations/providers/ollama)
- [Medium — LangGraph 1.0 Released October 2025](https://medium.com/@romerorico.hugo/langgraph-1-0-released-no-breaking-changes-all-the-hard-won-lessons-8939d500ca7c)
- [Plain English — The LangChain Dilemma](https://plainenglish.io/blog/the-langchain-dilemma-an-ai-engineer-s-perspective-on-production-readiness)
- [Ampcome — LangChain vs Custom Workflows](https://www.ampcome.com/post/langchain-vs-custom-workflows-ai-agents-2025)
- [CodespaceTechLabs — LangGraph Development Costs 2025](https://www.codespacetechlabs.com/post/langgraph-and-development-costs-in-2025)
- [AWS Prescriptive Guidance — Comparing Agentic AI Frameworks](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-frameworks/comparing-agentic-ai-frameworks.html)
- [Langflow — Complete Guide to AI Agent Framework 2025](https://www.langflow.org/blog/the-complete-guide-to-choosing-an-ai-agent-framework-in-2025)
- [Maxim AI — Top 5 Frameworks 2025](https://www.getmaxim.ai/articles/top-5-ai-agent-frameworks-in-2025-a-practical-guide-for-ai-builders/)
- [First AI Movers — Agentic AI 2025 Executive Guide](https://www.firstaimovers.com/p/agentic-ai-frameworks-2025-executive-guide-langgraph-autogen-crewai)
- [LangChain Blog — How to Think About Agent Frameworks](https://blog.langchain.com/how-to-think-about-agent-frameworks/)
- [NStarX — Build vs Buy Enterprise AI 2025](https://nstarxinc.com/blog/the-strategic-framework-for-enterprise-ai-navigating-the-build-vs-buy-dilemma-in-2025/)
- [Retool — Build vs Buy AI Agents](https://retool.com/blog/build-vs-buy-ai-agents)
- [Langfuse — Open-Source AI Agent Comparison](https://langfuse.com/blog/2025-03-19-ai-agent-comparison)
- [Medium — Agent Orchestration: When to Use LangGraph](https://medium.com/@akankshasinha247/agent-orchestration-when-to-use-langchain-langgraph-autogen-or-build-an-agentic-rag-system-cc298f785ea4)
