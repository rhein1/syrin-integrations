# Syrin Integration Manifest Draft

This repository is moving toward a small machine-readable contract for third-party integrations.

The goal is to make future workflows like `syrin integrate <slug>` possible without hard-coding
per-integration logic into the Syrin CLI.

This is intentionally narrow. It does not try to describe every packaging edge case. It only
captures enough metadata for discovery, installation hints, environment setup, and example entry
points.

## Manifest location

Each integration directory should include:

- `README.md`
- `syrin-integration.json`
- adapter code
- runnable examples

The manifest path is:

```text
<integration>/syrin-integration.json
```

## Required fields

| Field | Type | Purpose |
|-------|------|---------|
| `schema_version` | string | Manifest schema version |
| `slug` | string | Stable integration id used by tooling |
| `name` | string | Human-readable integration name |
| `summary` | string | Short description for listing and install UX |
| `homepage` | string | Primary project or product URL |
| `install` | object | Install commands and runtime prerequisites |
| `env` | array | Environment variables needed by the integration |
| `entrypoints` | object | Canonical adapter, README, and example paths |

## Recommended fields

| Field | Type | Purpose |
|-------|------|---------|
| `repository` | string | Upstream source repository |
| `owners` | array | Maintainers or owners for the integration directory |
| `tags` | array | Search and categorization hints |
| `tooling` | object | Tool count, prefixes, or framework-facing metadata |
| `notes` | array | Honest caveats such as paid actions or mock fallbacks |

## Suggested shape

```json
{
  "schema_version": "0.1.0",
  "slug": "example",
  "name": "Example",
  "summary": "Short summary",
  "homepage": "https://example.com",
  "repository": "https://github.com/example/example",
  "owners": ["maintainer"],
  "tags": ["python", "tools"],
  "install": {
    "language": "python",
    "package_manager": "pip",
    "python": ">=3.10",
    "commands": ["pip install syrin requests python-dotenv"]
  },
  "env": [
    {
      "name": "EXAMPLE_API_KEY",
      "required": true,
      "secret": true,
      "description": "API key used by the adapter"
    }
  ],
  "entrypoints": {
    "readme": "example/README.md",
    "adapter": "example/example_syrin.py",
    "examples": [
      {
        "id": "starter",
        "path": "example/examples/starter.py",
        "description": "Starter example"
      }
    ]
  }
}
```

## What a future CLI can do with this

A future `syrin integrate <slug>` flow could:

1. find the directory by `slug`
2. show the summary and install commands
3. print or materialize required environment variables
4. point users at the canonical examples
5. copy template files only when the manifest explicitly opts into that behavior

## Non-goals

- full dependency lockfiles
- framework-specific hidden behavior
- deployment orchestration
- secret distribution

The first win is reliable discovery and installation metadata, not a full plugin system.
