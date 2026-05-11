# Syrin Relationship Intelligence Pack

This package turns raw ecosystem observations into reusable relationship
intelligence for Syrin and Agoragentic.

It is not a sender. It is the structured layer before any authority gate:

- classify projects as buyers, sellers, integrators, competitors, ecosystem
  partners, or unknown
- extract demand signals for routing, billing, trust, hosted agents, local
  context governance, x402, MCP, and marketplace fit
- build durable candidate dossiers
- build a relationship map with a stable digest
- produce manual outreach packets that remain no-send by default
- expose bundled JSON schemas for downstream validation

## Files

| File | Purpose |
|------|---------|
| `pack.py` | Importable builders for dossiers, maps, packets, and full pack snapshots |
| `schemas/candidate_dossier.schema.json` | Candidate dossier contract |
| `schemas/relationship_map.schema.json` | Relationship map contract |
| `schemas/manual_outreach_packet.schema.json` | Manual review packet contract |
| `schemas/relationship_intelligence_pack.schema.json` | Full pack contract |

## Example

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
    run_id="run_2026_05_11_blackbox_guarded",
)

assert pack["send_authority"]["dispatch_enabled_effective"] is False
```

## Safety Boundary

The pack only prepares evidence. Public sends still require the Syrin authority
layer:

- current-run canary selection
- suppression and DNC enforcement
- approval receipt
- effective dispatch state
- `syrin-status.json`

Use `agoragentic/examples/syrin_authority_layer.py` for that authority layer.
