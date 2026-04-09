"""Process-verify an Agoragentic workflow with checkpoints and trace inspection.

Demonstrates:
  - loading a machine-readable eval pack
  - checkpointing around a marketplace-assisted workflow
  - inspecting `response.trace` for process-level verification
  - writing trace/checkpoint/result artifacts for local inspection

Requires:
  - `OPENAI_API_KEY` to let the agent decide which tools to call
  - `AGORAGENTIC_API_KEY` if you want live marketplace responses instead of error payloads

Run:
    python agoragentic/examples/marketplace_process_verification.py
    python agoragentic/examples/marketplace_process_verification.py agoragentic/evals/paper_summary_preview_only.json
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agoragentic.agoragentic_syrin import AgoragenticTools
from agoragentic.eval_runner import load_eval_spec, run_eval_spec
from syrin import Agent, Budget, CheckpointConfig, CheckpointTrigger, Model
from syrin.enums import ExceedPolicy


def _build_model() -> Model:
    """Create a tool-calling model when configured, otherwise a fast mock model."""
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key:
        return Model.OpenAI("gpt-4o-mini", api_key=openai_key)
    return Model.mock(latency_min=0, latency_max=0)


def _build_agent(checkpoint_path: str) -> Agent:
    """Create a checkpointed agent that reuses the Agoragentic tool surface."""
    return Agent(
        model=_build_model(),
        budget=Budget(max_cost=1.00, exceed_policy=ExceedPolicy.STOP),
        checkpoint=CheckpointConfig(
            storage="sqlite",
            path=checkpoint_path,
            trigger=CheckpointTrigger.TOOL,
            max_checkpoints=10,
        ),
        system_prompt=(
            "You are a marketplace-native research agent. Use agoragentic_match before "
            "agoragentic_execute when fit is unclear. Search marketplace memory before "
            "repeating prior work. Do not execute paid actions unless the user explicitly "
            "asks for them."
        ),
        tools=AgoragenticTools(api_key=os.getenv("AGORAGENTIC_API_KEY", "")),
    )


def main() -> None:
    """Run a small process-verification pass against the Agoragentic tool workflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "eval_spec",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1] / "evals" / "paper_summary_preview_only.json"),
        help="Path to an eval-pack JSON file.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="",
        help="Optional directory for trace/checkpoint/result artifacts.",
    )
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    eval_spec = load_eval_spec(args.eval_spec)

    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_path = Path(tmpdir) / "agoragentic_process.sqlite"
        agent = _build_agent(str(checkpoint_path))

        print("Configured tools:", [tool_spec.name for tool_spec in agent.tools])
        print(f"Checkpoint store: {checkpoint_path}")
        print(f"Eval spec: {args.eval_spec}")

        if not os.getenv("OPENAI_API_KEY", "").strip():
            print("OPENAI_API_KEY not set; configure it to verify tool-calling behavior via agent.run().")
            return

        artifacts_dir = args.artifacts_dir or str(
            Path.cwd() / "eval_artifacts" / eval_spec.name
        )
        result = run_eval_spec(agent, eval_spec, artifacts_dir=artifacts_dir)

        print("\n=== Verification summary ===")
        print("Eval:", result.spec_name)
        print("Observed tools:", result.observed_tools)
        print("Missing tools:", result.missing_tools or "none")
        print("Forbidden tools used:", result.forbidden_tools_used or "none")
        print("Unexpected tools:", result.unexpected_tools or "none")
        print("Failures:", result.failures or "none")
        print("Artifacts:", result.artifacts_dir)
        print("Checkpoints:", result.checkpoints)

        print("\n=== Trace summary ===")
        print(f"Trace steps: {len(result.trace_summary)}")
        for step in result.trace_summary:
            print(
                f"  Step {step['index']}: {step['step_type']}, "
                f"latency={step['latency_ms']:.1f}ms, cost=${step['cost_usd']:.6f}"
            )

        print("\n=== Agent output ===")
        print(result.output_text[:1200])
        if result.total_cost_usd is not None:
            print(f"\nTotal cost: ${result.total_cost_usd:.6f}")


if __name__ == "__main__":
    main()
