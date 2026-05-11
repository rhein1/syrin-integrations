# syrin-integrations

Third-party integrations with Syrin.

Each integration lives in its own top-level directory and should include:

- a focused README
- install and environment instructions
- copy-paste examples
- any adapter code needed to connect the third-party system to Syrin

## Available integrations

### `agoragentic/`

Agoragentic as the execution and deployment plane for Syrin.

Includes:

- a 27-tool Syrin adapter surface
- starter agent example
- deployable hosted agent starter kit with Docker and smoke tests
- preview-first platform-hosted starter kit with reviewed execution and provider contracts
- unified Syrin Agent OS export kit for self-hosted, platform-hosted, or hybrid deployments
- control-plane-aligned docs that fit Syrin Nexus, Syrin CLI, and Syrin Python
- Agent Lightning-compatible export bridge and Agent OS implementation prompt
- public marketplace browse example
- known-listing direct invoke example
- seller listing lifecycle example
- HTTP serving example
- multimodal preview-first example
- memory, secrets, passport, and registration examples
- process-verification example using hooks and checkpoints
- Agent OS control-plane loop example for autonomy planning
- Syrin v0.12 native sandbox execute-loop plan
- Syrin authority-layer example for relationship intelligence, canary review, receipts, and `syrin-status.json`
- importable relationship-intelligence pack with schemas for dossiers, relationship maps, and manual packets
- autonomous lifecycle examples for skill evolution, eval loops, trap-aware execution, multimodal process scoring, harness engineering, and optional sandbox agents
- relay-hosted seller deployment example
- a practical guide explaining when Agoragentic is the right fit
- a native-readiness roadmap for future Syrin integration support
- live-mode, schema, trap-model, sandbox, and deployment guidance

Start with [agoragentic/README.md](agoragentic/README.md), then use
[agoragentic/examples/README.md](agoragentic/examples/README.md),
[agoragentic/starter_kits/README.md](agoragentic/starter_kits/README.md),
[agoragentic/starter_kits/syrin_agent_os_export/README.md](agoragentic/starter_kits/syrin_agent_os_export/README.md),
[agoragentic/WHY_AGORAGENTIC.md](agoragentic/WHY_AGORAGENTIC.md), and
[agoragentic/RECIPES.md](agoragentic/RECIPES.md) for deeper workflow guidance.
Use [agoragentic/NATIVE_ROADMAP.md](agoragentic/NATIVE_ROADMAP.md) to track
the path from third-party integration to a future Syrin-native experience.
Use [agoragentic/AGENT_TRAP_THREAT_MODEL.md](agoragentic/AGENT_TRAP_THREAT_MODEL.md)
when adding workflows that touch untrusted content, memory, spend, deployment,
or approvals.
Use [agoragentic/SYRIN_AUTHORITY_LAYER.md](agoragentic/SYRIN_AUTHORITY_LAYER.md)
when guarded discovery or outreach workflows need canonical status, approval
receipts, canary selection, and one effective dispatch gate.
Use [agoragentic/RELATIONSHIP_INTELLIGENCE_PACK.md](agoragentic/RELATIONSHIP_INTELLIGENCE_PACK.md)
when you need reusable candidate dossiers, relationship maps, demand signals,
manual outreach packets, and local JSON schemas.

## Contributing

Add each integration in its own directory so the code, docs, and examples stay isolated and easy to evolve independently.
