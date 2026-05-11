"""Build a no-send Syrin relationship-intelligence pack.

This example converts raw ecosystem observations into candidate dossiers,
relationship maps, demand signals, and manual outreach packets. It does not
send messages, open issues, mutate state, or spend funds.

Run:
    python agoragentic/examples/syrin_relationship_intelligence_pack.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from agoragentic.relationship_intelligence import build_relationship_intelligence_pack  # noqa: E402


def sample_raw_candidates() -> tuple[dict[str, object], ...]:
    """Return deterministic ecosystem observations for the CLI demo."""
    return (
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
            "pain_points": [
                "needs provider discovery",
                "needs trust evidence before routing",
            ],
            "discussions_enabled": True,
        },
        {
            "name": "pay-per-call-tools",
            "repo_url": "https://github.com/example/pay-per-call-tools",
            "maintainer": "seller-maintainer",
            "description": "Hosted API tools with usage based billing and x402 settlement.",
            "topics": ["x402", "billing", "api"],
            "repo_facts": [
                "usage based billing",
                "x402 settlement",
            ],
            "contact_email": "maintainer@example.invalid",
        },
        {
            "name": "locked-issue-framework",
            "repo_url": "https://github.com/example/locked-issue-framework",
            "maintainer": "busy-maintainer",
            "description": "Agent framework with issue automation.",
            "repo_facts": [
                "agent framework",
                "issue automation",
            ],
            "issue_automation": True,
            "issues_enabled": True,
            "issue_locked": True,
        },
    )


def main() -> None:
    """Print a relationship-intelligence pack as JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="run_2026_05_11_relationship_intelligence")
    parser.add_argument("--previous-digest", default=None)
    args = parser.parse_args()

    pack = build_relationship_intelligence_pack(
        sample_raw_candidates(),
        run_id=args.run_id,
        previous_digest=args.previous_digest,
    )
    print(json.dumps(pack, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
