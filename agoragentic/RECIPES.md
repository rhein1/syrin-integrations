# Agoragentic Recipes

Use these playbooks when you want concrete ways to apply Agoragentic inside a
Syrin agent instead of only reading the raw tool reference.

## 1. Preview-first research routing

Use this when the agent needs to decide whether the market has a good provider
before it spends.

Recommended flow:

1. Call `agoragentic_match` with the task and budget cap.
2. Inspect the ranked providers and their scores.
3. Call `agoragentic_execute` only if the preview looks good.

Start from:

- [examples/marketplace_agent.py](examples/marketplace_agent.py)

Good fit:

- paper summarization
- web research
- structured extraction
- budget-sensitive buyer agents

## 2. Multimodal operator review

Use this when the input includes an image plus a supporting document and the
agent should stay preview-first by default.

Recommended flow:

1. Build a structured payload with image and document URLs.
2. Preview the provider match before running a live call.
3. Run live only when the route and budget look acceptable.

Start from:

- [examples/marketplace_multimodal_preview.py](examples/marketplace_multimodal_preview.py)

Good fit:

- visual inspections with supporting SOPs
- creative review plus text brief
- issue triage with screenshot plus documentation

## 3. Served marketplace-backed agent

Use this when you want to expose a Syrin HTTP service or playground-backed agent
that can route marketplace work on demand.

Recommended flow:

1. Build an agent with `AgoragenticTools`.
2. Keep the system prompt explicit about preview-first routing.
3. Expose it through `agent.serve()` for internal or external callers.

Start from:

- [examples/marketplace_agent_serve.py](examples/marketplace_agent_serve.py)

Good fit:

- internal tooling
- operator copilots
- agent services that need changing provider supply over time

## 4. Learning loop after execution

Use this when the agent should not just execute tasks, but also remember what
worked and save reusable lessons for later.

Recommended flow:

1. Search memory before repeating prior work.
2. Execute or invoke the chosen marketplace workflow.
3. Save one reusable note when the result yields a durable lesson.

Start from:

- [examples/marketplace_process_verification.py](examples/marketplace_process_verification.py)

Good fit:

- repeated research tasks
- recurring routing decisions
- seller or buyer agents that improve from prior outcomes

## 5. Autonomous lifecycle loop

Use this when the agent should improve its workflow through measured attempts
instead of untracked chat history.

Recommended flow:

1. Select a reusable skill or workflow by behavior, not name alone.
2. Build an Agoragentic execute payload with a small budget cap.
3. Grade the result with deterministic checks.
4. Record an attempt and reflection.
5. Save or propose a learning note only after evidence passes.

Start from:

- [examples/skill_evolution_loop.py](examples/skill_evolution_loop.py)
- [examples/autonomous_eval_loop.py](examples/autonomous_eval_loop.py)

Good fit:

- self-improving buyer agents
- repeated marketplace tasks
- PR-backed workflow improvement

## 6. Trap-aware execution

Use this before allowing untrusted content to influence memory, spend,
deployment, secret access, or human approval.

Recommended flow:

1. Classify source trust and requested action.
2. Scan for hidden or direct trap signals.
3. Build a constrained execute payload.
4. Require approval evidence for medium or high risk.

Start from:

- [examples/trap_aware_execute.py](examples/trap_aware_execute.py)
- [AGENT_TRAP_THREAT_MODEL.md](AGENT_TRAP_THREAT_MODEL.md)

Good fit:

- web, email, document, and RAG inputs
- approval screens
- memory-write workflows
- paid or mutating tool calls

## 7. Multimodal process verification

Use this when the process matters as much as the final answer.

Recommended flow:

1. Log visual and search tool events.
2. Capture evidence-bearing artifacts.
3. Score strategy, visual tool use, visual evidence, and overthinking.
4. Use the score to decide whether to keep, iterate, or rerun.

Start from:

- [examples/multimodal_process_eval.py](examples/multimodal_process_eval.py)

Good fit:

- screenshot triage
- document plus image analysis
- visual SOP review
- cost-sensitive multimodal runs

## 8. Harness engineering

Use this when an agent proposes improvements to prompts, tools, or orchestration
while benchmark plumbing and safety rails stay fixed.

Recommended flow:

1. Define editable and fixed paths.
2. Reject fixed-boundary or prohibited-action changes.
3. Compare before and after scores.
4. Keep only improvements or equal-score simplifications.

Start from:

- [examples/harness_engineering_loop.py](examples/harness_engineering_loop.py)
- [examples/openai_agents_sandbox_loop.py](examples/openai_agents_sandbox_loop.py)

Good fit:

- prompt and tool-routing optimization
- sandboxed code-assist loops
- future Agents SDK or MCP-backed harnesses

## Practical rule of thumb

Use Agoragentic when provider choice is part of the problem.

If the agent should always call one fixed backend, a direct integration may be
simpler. If the agent should inspect the market, route under a budget, and keep
the option to change providers over time, these recipes are the right place to
start.
