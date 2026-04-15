"""Regression coverage for the Agent OS loop example helpers."""

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATH = ROOT / "agoragentic" / "examples" / "marketplace_agent_os_loop.py"


def _load_example_module():
    """Import the example module directly from its file path."""
    spec = importlib.util.spec_from_file_location("marketplace_agent_os_loop", EXAMPLE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


example = _load_example_module()


class AgentOSLoopExampleTests(unittest.TestCase):
    """Pure helper coverage for Conway-inspired Agent OS loop logic."""

    def test_classifies_sandbox_only_when_unfunded_and_not_graduated(self):
        """Unfunded agents still building Tumbler proof should stay sandbox-first."""
        tier = example.classify_survival_tier(
            account={"ledger": {"balance": 0}},
            tumbler={"lifecycle_stage": "building_sandbox_proof"},
            approvals={},
        )

        self.assertEqual(tier, "sandbox_only")

    def test_classifies_low_compute_from_small_balance(self):
        """Small production balances should force preview-only behavior."""
        tier = example.classify_survival_tier(
            account={"ledger": {"balance": "1.25"}},
            tumbler={"lifecycle_stage": "ready_for_production"},
            approvals={"pending": 0},
        )

        self.assertEqual(tier, "low_compute")

    def test_recommends_supervised_when_procurement_blocks(self):
        """Procurement approval pressure should override autonomous preview mode."""
        mode = example.recommend_operating_mode(
            survival_tier="normal",
            procurement={"status": "approval_required"},
            tasks={},
        )

        self.assertEqual(mode, "supervised")

    def test_execute_payload_uses_router_constraints(self):
        """The example should map its workflow budget to constraints.max_cost."""
        payload = example.build_execute_payload("Summarize this", 0.25)

        self.assertEqual(payload["task"], "Summarize this")
        self.assertEqual(payload["constraints"]["max_cost"], 0.25)
        self.assertEqual(payload["input"]["task"], "Summarize this")

    def test_prompt_preserves_preview_first_contract(self):
        """The prompt should keep spend and mutation gates explicit."""
        snapshot = example.ControlPlaneSnapshot(
            account={"ledger": {"balance": 3.0}},
            jobs={},
            procurement={},
            approvals={},
            learning={},
            reconciliation={},
            identity={},
            tumbler={},
            tasks={},
            survival_tier="normal",
            recommended_mode="autonomous_preview",
        )

        prompt = example.build_agent_os_prompt(
            snapshot=snapshot,
            task="Find revenue-positive work.",
            max_cost=0.25,
            live_enabled=False,
        )

        self.assertIn("Prefer agoragentic_match before any paid action.", prompt)
        self.assertIn("Mode: preview-only", prompt)
        self.assertIn("Max spend for this turn: $0.25", prompt)


if __name__ == "__main__":
    unittest.main()
