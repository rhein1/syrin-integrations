# Agent Trap Threat Model

This document defines the lightweight trap-aware safety model used by the
Agoragentic Syrin examples. It is an integration pattern, not a complete
security product.

The default rule is:

```text
untrusted input -> scan/classify -> route with constraints -> preview/sandbox
-> record provenance -> require explicit live approval
```

Do not use this pattern:

```text
retrieved content -> agent believes it -> agent acts
```

## Trap classes

| Trap class | What it targets | Example risk |
|------------|-----------------|--------------|
| Content injection | Perception and parsing | Hidden HTML tells the agent to ignore its system prompt |
| Semantic manipulation | Task reasoning | A web page redefines the task or provider choice |
| Cognitive state | Memory and learning | Poisoned text asks the agent to save a false lesson |
| Behavioural control | Tools and side effects | Content asks the agent to spend, deploy, delete, or read secrets |
| Systemic | Multi-agent dynamics | Content asks the agent to spawn loops or use all budget |
| Human-in-the-loop | Human approval | Content pressures a reviewer to approve without evidence |

## Sensitive actions

These actions should require explicit review evidence before live execution:

- Paid `agoragentic_execute` calls above the configured budget cap.
- Seller listing create, update, delete, verification credentials, or self-test.
- Relay deployment or auto-listing.
- Durable memory writes and learning-note writes from untrusted content.
- Secret storage or retrieval.
- Agent spawning, recurring automation, or long-running loops.

## Approval evidence

A useful approval packet should include:

- the task and requested action
- source trust and provenance
- max spend and mutation scope
- detected trap signals
- expected output contract
- what the reviewer should verify before approving

## Example

Use [examples/trap_aware_execute.py](examples/trap_aware_execute.py) to build a
preview-first execute payload plus a trap report. The example intentionally
does not run live execution. It shows how to decide whether a Syrin agent should
continue, request approval, or quarantine the input.
