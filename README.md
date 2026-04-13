# syrin-integrations

Third-party integrations with Syrin.

Each integration lives in its own top-level directory and should include:

- a focused README
- install and environment instructions
- copy-paste examples
- any adapter code needed to connect the third-party system to Syrin

## Available integrations

### `agoragentic/`

Agoragentic as an execute-first capability router for Syrin.

Includes:

- a 27-tool Syrin adapter surface
- starter agent example
- public marketplace browse example
- known-listing direct invoke example
- seller listing lifecycle example
- HTTP serving example
- multimodal preview-first example
- memory, secrets, passport, and registration examples
- process-verification example using hooks and checkpoints
- relay-hosted seller deployment example
- a practical guide explaining when Agoragentic is the right fit

Start with [agoragentic/README.md](agoragentic/README.md), then use
[agoragentic/examples/README.md](agoragentic/examples/README.md),
[agoragentic/WHY_AGORAGENTIC.md](agoragentic/WHY_AGORAGENTIC.md), and
[agoragentic/RECIPES.md](agoragentic/RECIPES.md) for deeper workflow guidance.

## Contributing

Add each integration in its own directory so the code, docs, and examples stay isolated and easy to evolve independently.
