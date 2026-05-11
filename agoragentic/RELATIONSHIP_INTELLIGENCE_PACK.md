# Relationship Intelligence Pack

The relationship intelligence pack is the reusable data layer underneath the
Syrin authority layer. It helps Syrin act as an ecosystem scout, lead
intelligence agent, market research agent, and manual outreach copilot without
becoming an autonomous sender.

Use it to convert raw repo, maintainer, community, issue, or discussion records
into:

- candidate dossiers
- relationship maps
- demand-signal classifications
- contact-channel recommendations
- manual outreach packets
- no-send status summaries
- bundled JSON schemas

The importable package lives in
[`relationship_intelligence/`](relationship_intelligence/). The runnable demo is
[`examples/syrin_relationship_intelligence_pack.py`](examples/syrin_relationship_intelligence_pack.py).

## Core Boundary

The pack does not send messages, open GitHub issues, mutate queues, or spend
funds. It only prepares structured intelligence for review.

Public send authority belongs to the authority layer:

- current-run canary selection
- DNC and suppression enforcement
- approval receipt
- effective dispatch state
- `syrin-status.json`

## Data Products

| Product | Purpose |
|---------|---------|
| Candidate dossier | Stable identity, relationship type, channel, facts, pain points, demand signals, operations, and suppression state |
| Relationship map | Digestable set of candidates grouped by relationship type and channel |
| Manual outreach packet | Human-reviewable packet with draft quality checks and `dispatch_enabled_effective=false` |
| Full pack | Dossiers, map, packets, top opportunities, and no-material-change status |

## Demand Signals

The pack classifies demand signals that matter to Agoragentic:

- discovery
- routing
- billing
- trust
- hosted agents
- local context governance
- x402
- MCP
- marketplace fit

These signals let Syrin hand Hermes or a Platform Growth Agent a clear answer:

```text
Here are the best opportunities, why they matter, what they likely need, and
what channel should be used next.
```

## Example

```bash
python agoragentic/examples/syrin_relationship_intelligence_pack.py \
  --run-id run_2026_05_11_relationship_intelligence
```

Or use the package directly:

```python
from agoragentic.relationship_intelligence import build_relationship_intelligence_pack

pack = build_relationship_intelligence_pack(
    (
        {
            "name": "local-agent-router",
            "repo_url": "https://github.com/example/local-agent-router",
            "maintainer": "local-router-maintainer",
            "description": "OpenAI-compatible local routing with MCP server examples.",
            "topics": ["mcp", "routing", "local agents"],
            "repo_facts": [
                "OpenAI-compatible local routing",
                "MCP server examples",
            ],
            "discussions_enabled": True,
        },
    ),
    run_id="run_2026_05_11_relationship_intelligence",
)

assert pack["send_authority"]["dispatch_enabled_effective"] is False
```

## Schemas

Bundled schemas live under `relationship_intelligence/schemas/`:

- `candidate_dossier.schema.json`
- `relationship_map.schema.json`
- `manual_outreach_packet.schema.json`
- `relationship_intelligence_pack.schema.json`

They are intentionally local and dependency-free so CI, humans, and agents can
inspect the contract without installing a validator.
