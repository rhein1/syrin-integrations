# syrin-integrations

Third-party integrations with Syrin.

Each integration lives in its own top-level directory and should include:

- a focused README
- a `syrin-integration.json` manifest
- install and environment instructions
- copy-paste examples
- any adapter code needed to connect the third-party system to Syrin

## Integration manifest

Each integration can expose a machine-readable manifest at:

```text
<integration>/syrin-integration.json
```

The draft contract is documented in [INTEGRATION_SPEC.md](INTEGRATION_SPEC.md).

This is the smallest useful step toward a future install flow such as:

```bash
syrin integrate agoragentic
```

## Available integrations

### `agoragentic/`

Agoragentic as an execute-first capability router for Syrin.

Includes:

- a 16-tool Syrin adapter surface
- a machine-readable integration manifest
- starter agent example
- HTTP serving example
- process-verification example using hooks and checkpoints

See [agoragentic/README.md](agoragentic/README.md).

## Contributing

Add each integration in its own directory so the code, docs, examples, and manifest stay isolated and easy to evolve independently.
