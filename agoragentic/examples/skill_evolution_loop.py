"""Preview-first skill evolution loop for Syrin agents using Agoragentic.

This example clean-room adapts the Read -> Execute -> Reflect -> Write pattern
from self-improving agent systems into the Agoragentic/Syrin integration.

Safe default:
    The script selects a candidate workflow, builds the Agoragentic execute
    payload, and creates a reflection plus learning-note payload. It does not
    call paid routes, write memory, or edit code unless live mode is explicitly
    enabled in a caller-owned wrapper.

Run:
    python agoragentic/examples/skill_evolution_loop.py
    python agoragentic/examples/skill_evolution_loop.py "Summarize this paper and save a lesson"
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any


DEFAULT_TASK = (
    "Find a provider for technical paper summarization, preview the execution "
    "path, and propose one reusable workflow improvement."
)


@dataclass(frozen=True)
class SkillCandidate:
    """Reusable workflow unit that a Syrin agent may route through Agoragentic."""

    name: str
    intent: str
    source: str
    behavior_tags: tuple[str, ...]
    last_outcome: str = "unknown"


@dataclass(frozen=True)
class SkillEvolutionPlan:
    """Preview of one skill evolution turn."""

    task: str
    selected_skill: SkillCandidate
    execute_payload: dict[str, Any]
    reflection: dict[str, Any]
    learning_note_payload: dict[str, Any]
    recommendation: str
    live_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable plan for CLI output and tests."""
        return {
            "task": self.task,
            "selected_skill": {
                "name": self.selected_skill.name,
                "intent": self.selected_skill.intent,
                "source": self.selected_skill.source,
                "behavior_tags": list(self.selected_skill.behavior_tags),
                "last_outcome": self.selected_skill.last_outcome,
            },
            "execute_payload": self.execute_payload,
            "reflection": self.reflection,
            "learning_note_payload": self.learning_note_payload,
            "recommendation": self.recommendation,
            "live_enabled": self.live_enabled,
        }


SAMPLE_SKILLS = (
    SkillCandidate(
        name="preview-first-research-routing",
        intent="route_capability",
        source="agoragentic/examples/marketplace_agent.py",
        behavior_tags=("research", "summarization", "routing", "budget"),
        last_outcome="passed",
    ),
    SkillCandidate(
        name="process-verified-marketplace-run",
        intent="process_verification",
        source="agoragentic/examples/marketplace_process_verification.py",
        behavior_tags=("trace", "checkpoint", "tool-use", "verification"),
        last_outcome="passed",
    ),
    SkillCandidate(
        name="agent-os-control-loop",
        intent="agent_os_loop",
        source="agoragentic/examples/marketplace_agent_os_loop.py",
        behavior_tags=("agent-os", "heartbeat", "survival-tier", "approval"),
        last_outcome="passed",
    ),
)


def normalize_terms(text: str) -> set[str]:
    """Normalize a string into rough matching terms without external deps."""
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in text)
    return {term for term in cleaned.split() if term}


def score_skill_candidate(candidate: SkillCandidate, task: str) -> float:
    """Score a skill by behavioral tags plus prior outcome."""
    terms = normalize_terms(task)
    tag_terms = {term for tag in candidate.behavior_tags for term in normalize_terms(tag)}
    overlap = len(terms & tag_terms)
    prior_bonus = 0.25 if candidate.last_outcome in {"passed", "successful"} else 0.0
    return overlap + prior_bonus


def select_skill(candidates: tuple[SkillCandidate, ...], task: str) -> SkillCandidate:
    """Select the best behavioral match for the task."""
    if not candidates:
        raise ValueError("at least one candidate skill is required")
    return max(candidates, key=lambda candidate: score_skill_candidate(candidate, task))


def build_execute_payload(task: str, skill: SkillCandidate, max_cost: float) -> dict[str, Any]:
    """Build the execute-first Agoragentic payload without spending."""
    return {
        "task": task,
        "input": {
            "task": task,
            "workflow": {
                "name": skill.name,
                "intent": skill.intent,
                "source": skill.source,
                "behavior_tags": list(skill.behavior_tags),
            },
            "mode": "preview",
        },
        "constraints": {
            "max_cost": max(0.01, float(max_cost)),
            "prefer_execute": True,
        },
    }


def classify_feedback(result: dict[str, Any]) -> str:
    """Classify execution feedback into a small outcome vocabulary."""
    if result.get("error") or result.get("status") in {"failed", "error"}:
        return "failed"
    if result.get("missing_steps") or result.get("requires_revision"):
        return "partial"
    if result.get("output") or result.get("status") in {"completed", "success", "passed"}:
        return "passed"
    return "unknown"


def build_reflection(
    task: str,
    skill: SkillCandidate,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a reflection payload that can become memory only after evidence."""
    observed = result or {
        "status": "previewed",
        "output": None,
        "evidence": "No live execution was run.",
    }
    outcome = classify_feedback(observed)
    if outcome == "passed":
        next_action = "preserve_skill_and_capture_lesson"
    elif outcome == "partial":
        next_action = "tighten_schema_or_required_steps"
    elif outcome == "failed":
        next_action = "quarantine_failure_and_require_human_review"
    else:
        next_action = "run_small_sandbox_eval_before_write"

    return {
        "task": task,
        "skill": skill.name,
        "outcome": outcome,
        "evidence": observed.get("evidence") or observed.get("output") or observed.get("message"),
        "next_action": next_action,
        "write_allowed": outcome == "passed",
    }


def build_learning_note_payload(reflection: dict[str, Any]) -> dict[str, Any]:
    """Shape a learning-note write payload without performing the write."""
    return {
        "title": f"Skill loop lesson: {reflection['skill']}",
        "lesson": (
            f"Task outcome was {reflection['outcome']}. "
            f"Recommended next action: {reflection['next_action']}."
        ),
        "tags": ["syrin", "agoragentic", "skill-evolution", reflection["outcome"]],
        "metadata": {
            "task": reflection["task"],
            "skill": reflection["skill"],
            "write_allowed": reflection["write_allowed"],
        },
    }


def build_skill_evolution_plan(
    task: str,
    candidates: tuple[SkillCandidate, ...] = SAMPLE_SKILLS,
    max_cost: float = 0.25,
    result: dict[str, Any] | None = None,
    live_enabled: bool = False,
) -> SkillEvolutionPlan:
    """Build a complete preview-first skill evolution plan."""
    selected = select_skill(candidates, task)
    reflection = build_reflection(task, selected, result=result)
    recommendation = (
        "Do not write memory or mutate code until a sandbox or live result passes."
        if not reflection["write_allowed"]
        else "Save the learning note, then consider a focused workflow-schema PR."
    )
    return SkillEvolutionPlan(
        task=task,
        selected_skill=selected,
        execute_payload=build_execute_payload(task, selected, max_cost),
        reflection=reflection,
        learning_note_payload=build_learning_note_payload(reflection),
        recommendation=recommendation,
        live_enabled=live_enabled,
    )


def non_negative_float(value: str) -> float:
    """Parse a non-negative CLI float."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def main() -> None:
    """Print a preview-first skill evolution plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="?", default=DEFAULT_TASK)
    parser.add_argument("--max-cost", type=non_negative_float, default=0.25)
    args = parser.parse_args()

    plan = build_skill_evolution_plan(task=args.task, max_cost=args.max_cost)
    print(json.dumps(plan.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
