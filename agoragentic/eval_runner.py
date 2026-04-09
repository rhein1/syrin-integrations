"""Small process-aware eval runner for Syrin integrations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from syrin import Agent


@dataclass
class TraceExpectation:
    """Expected trace or tool-usage behavior for an eval run."""

    step_type: str | None = None
    tool_name: str | None = None
    min_count: int = 0
    max_count: int | None = None


@dataclass
class CheckpointAssertion:
    """Expected checkpoint labeling behavior for an eval run."""

    label_contains: str | None = None
    min_count: int = 0


@dataclass
class EvalSpec:
    """Minimal machine-readable eval contract for a Syrin workflow."""

    name: str
    prompt: str
    expected_tools: list[str] = field(default_factory=list)
    forbidden_tools: list[str] = field(default_factory=list)
    trace_expectations: list[TraceExpectation] = field(default_factory=list)
    checkpoint_assertions: list[CheckpointAssertion] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvalSpec":
        """Build an eval spec from a JSON-compatible dictionary."""
        return cls(
            name=data["name"],
            prompt=data["prompt"],
            expected_tools=list(data.get("expected_tools", [])),
            forbidden_tools=list(data.get("forbidden_tools", [])),
            trace_expectations=[
                TraceExpectation(**item) for item in data.get("trace_expectations", [])
            ],
            checkpoint_assertions=[
                CheckpointAssertion(**item) for item in data.get("checkpoint_assertions", [])
            ],
        )


@dataclass
class EvalResult:
    """Inspectable result bundle for a process-aware eval run."""

    success: bool
    spec_name: str
    output_text: str
    observed_tools: list[str]
    missing_tools: list[str]
    forbidden_tools_used: list[str]
    unexpected_tools: list[str]
    trace_summary: list[dict[str, Any]]
    checkpoints: list[dict[str, Any]]
    failures: list[str]
    artifacts_dir: str | None = None
    total_cost_usd: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable result payload."""
        return asdict(self)


def load_eval_spec(path: str | Path) -> EvalSpec:
    """Load an eval spec from disk."""
    spec_path = Path(path)
    return EvalSpec.from_dict(json.loads(spec_path.read_text(encoding="utf-8")))


def run_eval_spec(
    agent: Agent,
    eval_spec: EvalSpec,
    *,
    artifacts_dir: str | Path | None = None,
) -> EvalResult:
    """Run one eval spec against an already-configured Syrin agent."""
    tool_events: list[str] = []
    agent.events.on_tool(lambda ctx: tool_events.append(ctx.get("tool_name", "")))

    checkpoints = [
        {
            "id": agent.save_checkpoint(f"before_{eval_spec.name}"),
            "label": f"before_{eval_spec.name}",
        }
    ]
    response = agent.run(eval_spec.prompt)
    checkpoints.append(
        {
            "id": agent.save_checkpoint(f"after_{eval_spec.name}"),
            "label": f"after_{eval_spec.name}",
        }
    )

    observed_tools = [tool_name for tool_name in tool_events if tool_name]
    trace_summary = [
        _normalize_trace_step(index=index, step=step)
        for index, step in enumerate(getattr(response, "trace", []) or [], start=1)
    ]

    missing_tools = [
        tool_name for tool_name in eval_spec.expected_tools if tool_name not in observed_tools
    ]
    forbidden_tools_used = [
        tool_name for tool_name in observed_tools if tool_name in eval_spec.forbidden_tools
    ]
    unexpected_tools = [
        tool_name
        for tool_name in observed_tools
        if tool_name not in eval_spec.expected_tools and tool_name not in eval_spec.forbidden_tools
    ]

    failures: list[str] = []
    if missing_tools:
        failures.append(f"Missing expected tools: {', '.join(missing_tools)}")
    if forbidden_tools_used:
        failures.append(f"Forbidden tools used: {', '.join(forbidden_tools_used)}")

    failures.extend(_evaluate_trace_expectations(eval_spec, observed_tools, trace_summary))
    failures.extend(_evaluate_checkpoint_assertions(eval_spec, checkpoints))

    result = EvalResult(
        success=not failures,
        spec_name=eval_spec.name,
        output_text=str(getattr(response, "content", "")),
        observed_tools=observed_tools,
        missing_tools=missing_tools,
        forbidden_tools_used=forbidden_tools_used,
        unexpected_tools=unexpected_tools,
        trace_summary=trace_summary,
        checkpoints=_normalize_checkpoint_inventory(agent, checkpoints),
        failures=failures,
        total_cost_usd=getattr(response, "cost", None),
    )

    if artifacts_dir is not None:
        artifact_root = Path(artifacts_dir)
        artifact_root.mkdir(parents=True, exist_ok=True)
        (artifact_root / "trace.json").write_text(
            json.dumps(trace_summary, indent=2),
            encoding="utf-8",
        )
        (artifact_root / "checkpoints.json").write_text(
            json.dumps(result.checkpoints, indent=2),
            encoding="utf-8",
        )
        (artifact_root / "result.json").write_text(
            json.dumps(result.to_dict(), indent=2),
            encoding="utf-8",
        )
        result.artifacts_dir = str(artifact_root)

    return result


def _normalize_trace_step(index: int, step: Any) -> dict[str, Any]:
    """Flatten a Syrin trace step into a JSON-friendly dictionary."""
    return {
        "index": index,
        "step_type": getattr(step, "step_type", "unknown"),
        "tool_name": getattr(step, "tool_name", None),
        "latency_ms": getattr(step, "latency_ms", 0.0),
        "cost_usd": getattr(step, "cost_usd", 0.0),
    }


def _normalize_checkpoint_inventory(
    agent: Agent,
    checkpoints: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge explicit checkpoint labels with the agent inventory when available."""
    try:
        inventory = agent.list_checkpoints()
    except Exception:
        inventory = []

    normalized_inventory = [{"raw": _json_safe(item)} for item in inventory]
    return checkpoints + normalized_inventory


def _evaluate_trace_expectations(
    eval_spec: EvalSpec,
    observed_tools: list[str],
    trace_summary: list[dict[str, Any]],
) -> list[str]:
    """Evaluate tool and step-count expectations against the observed trace."""
    failures: list[str] = []
    for expectation in eval_spec.trace_expectations:
        if expectation.tool_name:
            count = observed_tools.count(expectation.tool_name)
            label = f"tool {expectation.tool_name}"
        else:
            count = sum(
                1
                for step in trace_summary
                if expectation.step_type is None or step["step_type"] == expectation.step_type
            )
            label = f"step_type {expectation.step_type or '*'}"

        if count < expectation.min_count:
            failures.append(f"{label} observed {count} times, expected at least {expectation.min_count}")
        if expectation.max_count is not None and count > expectation.max_count:
            failures.append(f"{label} observed {count} times, expected at most {expectation.max_count}")
    return failures


def _evaluate_checkpoint_assertions(
    eval_spec: EvalSpec,
    checkpoints: list[dict[str, Any]],
) -> list[str]:
    """Evaluate checkpoint label assertions against saved checkpoints."""
    failures: list[str] = []
    labels = [item.get("label", "") for item in checkpoints]
    for assertion in eval_spec.checkpoint_assertions:
        count = sum(
            1 for label in labels if assertion.label_contains is None or assertion.label_contains in label
        )
        if count < assertion.min_count:
            failures.append(
                f"checkpoint label containing {assertion.label_contains!r} observed {count} times, "
                f"expected at least {assertion.min_count}"
            )
    return failures


def _json_safe(value: Any) -> Any:
    """Convert nested values into a JSON-serializable shape."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)
