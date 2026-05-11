"""Regression coverage for the Syrin relationship-intelligence pack."""

import json
import unittest
from pathlib import Path

from agoragentic.relationship_intelligence import (
    build_candidate_dossier,
    build_manual_outreach_packet,
    build_relationship_intelligence_pack,
    build_relationship_map,
    classify_channel,
    classify_relationship_type,
    extract_demand_signals,
    list_schema_names,
    load_schema,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "agoragentic" / "relationship_intelligence" / "schemas"


class RelationshipIntelligencePackTests(unittest.TestCase):
    """Pure helper coverage for relationship-intelligence pack outputs."""

    def test_schema_files_are_valid_json_and_listed(self):
        """Bundled schemas should be loadable without extra dependencies."""
        expected = {
            "candidate_dossier.schema.json",
            "manual_outreach_packet.schema.json",
            "relationship_intelligence_pack.schema.json",
            "relationship_map.schema.json",
        }

        self.assertEqual(set(list_schema_names()), expected)
        for schema_name in expected:
            with self.subTest(schema_name=schema_name):
                direct = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
                loaded = load_schema(schema_name)
                self.assertEqual(loaded["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(loaded, direct)

    def test_demand_signals_and_relationship_type_capture_fit(self):
        """MCP routing metadata should classify as an integrator with matching signals."""
        raw = {
            "name": "local-router",
            "repo_url": "https://github.com/example/local-router",
            "description": "MCP integration for multi-provider routing.",
            "topics": ["mcp", "routing"],
            "repo_facts": ["MCP integration", "multi-provider routing"],
        }

        self.assertEqual(classify_relationship_type(raw), "integrator")
        self.assertEqual(extract_demand_signals(raw), ("mcp", "routing"))

    def test_channel_classifier_avoids_issue_automation(self):
        """Issue automation should route to discussion or manual instead of issues."""
        classified = classify_channel(
            {
                "issues_enabled": True,
                "issue_automation": True,
                "discussions_enabled": True,
            }
        )

        self.assertEqual(classified["channel"], "github_discussion")
        self.assertIn("issue_automation", classified["reasons"])

    def test_candidate_dossier_builds_durable_identity_and_operations(self):
        """Dossiers should carry stable ids, demand signals, and concrete operations."""
        raw = {
            "name": "x402-provider",
            "repo_url": "https://github.com/example/x402-provider",
            "maintainer": "seller",
            "description": "Usage based billing with x402 settlement.",
            "repo_facts": ["usage based billing", "x402 settlement"],
            "contact_email": "seller@example.invalid",
        }

        dossier = build_candidate_dossier(raw, run_id="run_rel")

        self.assertTrue(dossier.candidate_id.startswith("rel_"))
        self.assertEqual(dossier.channel, "email")
        self.assertEqual(dossier.relationship_type, "seller")
        self.assertIn("billing", dossier.demand_signals)
        self.assertIn("x402", dossier.demand_signals)
        self.assertIn("agoragentic_execute", dossier.callable_operations)

    def test_relationship_map_digest_is_deterministic(self):
        """Map digests should be stable regardless of input ordering."""
        first = build_candidate_dossier(
            {
                "repo_url": "https://github.com/example/a",
                "repo_facts": ["MCP", "routing"],
                "description": "MCP routing",
            },
            run_id="run_map",
        )
        second = build_candidate_dossier(
            {
                "repo_url": "https://github.com/example/b",
                "repo_facts": ["billing", "x402"],
                "description": "billing x402",
            },
            run_id="run_map",
        )

        left = build_relationship_map((first, second))
        right = build_relationship_map((second, first))

        self.assertEqual(left["digest"], right["digest"])
        self.assertEqual(left["candidate_count"], 2)

    def test_manual_packet_never_enables_dispatch(self):
        """Manual packets should remain review artifacts, not send authority."""
        candidate = build_candidate_dossier(
            {
                "repo_url": "https://github.com/example/router",
                "description": "MCP routing",
                "repo_facts": ["MCP routing", "provider discovery"],
                "callable_operations": ["agoragentic_match"],
                "discussions_enabled": True,
            },
            run_id="run_packet",
        )

        packet = build_manual_outreach_packet(candidate)

        self.assertTrue(packet["allowed_for_manual_review"])
        self.assertFalse(packet["send_authority"]["dispatch_enabled_effective"])
        self.assertTrue(packet["send_authority"]["requires_approval_receipt"])

    def test_relationship_pack_suppresses_bad_channels_and_backs_off_on_same_digest(self):
        """Full packs should exclude suppressed rows from top opportunities and back off on no change."""
        raw_candidates = (
            {
                "repo_url": "https://github.com/example/good",
                "description": "MCP routing and discovery",
                "repo_facts": ["MCP routing", "provider discovery"],
                "discussions_enabled": True,
            },
            {
                "repo_url": "https://github.com/example/suppressed",
                "description": "Agent framework with issue automation",
                "repo_facts": ["agent framework", "issue automation"],
                "issue_automation": True,
                "issue_locked": True,
            },
        )
        first = build_relationship_intelligence_pack(raw_candidates, run_id="run_pack")
        second = build_relationship_intelligence_pack(
            raw_candidates,
            run_id="run_pack",
            previous_digest=first["relationship_map"]["digest"],
        )

        self.assertFalse(first["send_authority"]["dispatch_enabled_effective"])
        self.assertEqual(first["status"]["scored_count"], 2)
        self.assertEqual(first["status"]["safe_candidate_count"], 1)
        self.assertEqual(len(first["top_opportunities"]), 1)
        self.assertIn("relationship_intelligence_pack.schema.json", first["schemas"])
        self.assertTrue(second["status"]["no_material_data_change"])
        self.assertEqual(second["status"]["recommended_action"], "backoff")

    def test_docs_reference_relationship_pack(self):
        """The relationship-intelligence pack should be discoverable from docs."""
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        integration_readme = (ROOT / "agoragentic" / "README.md").read_text(encoding="utf-8")
        examples_readme = (ROOT / "agoragentic" / "examples" / "README.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("RELATIONSHIP_INTELLIGENCE_PACK.md", root_readme)
        self.assertIn("syrin_relationship_intelligence_pack.py", integration_readme)
        self.assertIn("relationship-intelligence data pack", examples_readme)


if __name__ == "__main__":
    unittest.main()
