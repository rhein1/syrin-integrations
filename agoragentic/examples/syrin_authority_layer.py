"""Syrin relationship-intelligence authority layer for Agoragentic.

This example treats Syrin as an ecosystem scout and relationship intelligence
agent, not as an unsupervised public sender. Discovery, scoring, drafting, and
learning can run freely. Public dispatch requires one canonical state machine,
one approval receipt, one current-run candidate, and a stable status export.

Safe default:
    The helpers build candidate dossiers, channel classifications, canary
    review packets, approval receipts, and ``syrin-status.json``-shaped output.
    They do not send messages, open issues, mutate queues, or spend funds.

Run:
    python agoragentic/examples/syrin_authority_layer.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any


DEFAULT_POLICY_VERSION = "syrin-authority-v1"
DEFAULT_PROMPT_VERSION = "relationship-intelligence-v1"
DEFAULT_NOW = "2026-05-11T00:00:00Z"
DEFAULT_EXPIRY = "2026-05-12T00:00:00Z"

CHANNELS = (
    "github_issue",
    "github_discussion",
    "email",
    "website_contact_form",
    "manual_only",
    "skip",
)

AUTO_SEND_ELIGIBLE_CHANNELS = (
    "email",
    "github_discussion",
    "website_contact_form",
)

SUPPRESSION_FLAGS = (
    "dnc",
    "already_replied",
    "issue_locked",
    "issue_automation",
    "bad_fit",
)

GENERIC_PITCH_TERMS = (
    "agent marketplace",
    "marketplace for agents",
    "mcp marketplace",
    "distribution marketplace",
    "we can help you grow",
)


@dataclass(frozen=True)
class CandidateDossier:
    """Relationship-intelligence record for one ecosystem candidate."""

    run_id: str
    candidate_id: str
    repo_url: str
    maintainer: str
    score: float
    relationship_type: str
    channel: str
    repo_facts: tuple[str, ...]
    callable_operations: tuple[str, ...]
    risk_flags: tuple[str, ...] = ()
    suppression_flags: tuple[str, ...] = ()
    prior_contact_status: str = "none"
    current_run: bool = True
    lineage: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dossier."""
        return {
            "run_id": self.run_id,
            "candidate_id": self.candidate_id,
            "repo_url": self.repo_url,
            "maintainer": self.maintainer,
            "score": self.score,
            "relationship_type": self.relationship_type,
            "channel": self.channel,
            "repo_facts": list(self.repo_facts),
            "callable_operations": list(self.callable_operations),
            "risk_flags": list(self.risk_flags),
            "suppression_flags": list(self.suppression_flags),
            "prior_contact_status": self.prior_contact_status,
            "current_run": self.current_run,
            "lineage": list(self.lineage),
        }


@dataclass(frozen=True)
class ApprovalReceipt:
    """Single authority receipt for one approved public dispatch."""

    receipt_id: str
    run_id: str
    candidate_id: str
    policy_version: str
    approver: str
    created_at: str
    expires_at: str
    max_sends: int = 1
    sent_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe approval receipt."""
        return {
            "receipt_id": self.receipt_id,
            "run_id": self.run_id,
            "candidate_id": self.candidate_id,
            "policy_version": self.policy_version,
            "approver": self.approver,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "max_sends": self.max_sends,
            "sent_count": self.sent_count,
        }


def stable_digest(payload: Any) -> str:
    """Return a deterministic SHA-256 digest for JSON-compatible payloads."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_candidate_id(repo_url: str, maintainer: str = "") -> str:
    """Build a durable candidate id from stable public identity fields."""
    normalized = f"{repo_url.strip().lower()}|{maintainer.strip().lower()}"
    return f"cand_{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"


def build_candidate_dossier(
    run_id: str,
    repo_url: str,
    maintainer: str,
    score: float,
    relationship_type: str,
    channel: str,
    repo_facts: tuple[str, ...],
    callable_operations: tuple[str, ...],
    risk_flags: tuple[str, ...] = (),
    suppression_flags: tuple[str, ...] = (),
    prior_contact_status: str = "none",
    current_run: bool = True,
    lineage: tuple[str, ...] = (),
) -> CandidateDossier:
    """Build a dossier with validation for channel and score fields."""
    if channel not in CHANNELS:
        raise ValueError(f"channel must be one of {CHANNELS}")
    if not repo_url.strip():
        raise ValueError("repo_url is required")
    if score < 0 or score > 1:
        raise ValueError("score must be between 0 and 1")
    return CandidateDossier(
        run_id=run_id,
        candidate_id=build_candidate_id(repo_url, maintainer),
        repo_url=repo_url,
        maintainer=maintainer,
        score=score,
        relationship_type=relationship_type,
        channel=channel,
        repo_facts=tuple(repo_facts),
        callable_operations=tuple(callable_operations),
        risk_flags=tuple(risk_flags),
        suppression_flags=tuple(suppression_flags),
        prior_contact_status=prior_contact_status,
        current_run=current_run,
        lineage=tuple(lineage),
    )


def classify_channel(repo_metadata: dict[str, Any]) -> dict[str, Any]:
    """Classify the best contact channel for a repo or maintainer record."""
    preferred = str(repo_metadata.get("maintainer_prefers", "")).strip().lower()
    if preferred in CHANNELS:
        return {
            "channel": preferred,
            "confidence": 0.95,
            "reasons": ["maintainer_preference"],
        }

    if repo_metadata.get("archived") or repo_metadata.get("dnc"):
        return {"channel": "skip", "confidence": 1.0, "reasons": ["suppressed"]}

    if repo_metadata.get("contact_email"):
        return {"channel": "email", "confidence": 0.8, "reasons": ["contact_email"]}

    if repo_metadata.get("website_contact_form"):
        return {
            "channel": "website_contact_form",
            "confidence": 0.7,
            "reasons": ["website_contact_form"],
        }

    if repo_metadata.get("issue_automation"):
        if repo_metadata.get("discussions_enabled"):
            return {
                "channel": "github_discussion",
                "confidence": 0.65,
                "reasons": ["issue_automation", "discussions_enabled"],
            }
        return {
            "channel": "manual_only",
            "confidence": 0.6,
            "reasons": ["issue_automation"],
        }

    if repo_metadata.get("allow_public_issue_outreach") and repo_metadata.get("issues_enabled"):
        return {
            "channel": "github_issue",
            "confidence": 0.55,
            "reasons": ["explicit_issue_outreach_allowed"],
        }

    if repo_metadata.get("discussions_enabled"):
        return {
            "channel": "github_discussion",
            "confidence": 0.55,
            "reasons": ["discussions_enabled"],
        }

    return {
        "channel": "manual_only",
        "confidence": 0.5,
        "reasons": ["no_safe_public_channel"],
    }


def build_lead_set_digest(candidates: tuple[CandidateDossier, ...]) -> str:
    """Build a run-level digest from stable candidate lineage fields."""
    rows = [
        {
            "candidate_id": candidate.candidate_id,
            "repo_url": candidate.repo_url,
            "maintainer": candidate.maintainer,
            "channel": candidate.channel,
            "score": candidate.score,
            "repo_facts": list(candidate.repo_facts),
            "callable_operations": list(candidate.callable_operations),
        }
        for candidate in candidates
    ]
    rows.sort(key=lambda row: row["candidate_id"])
    return stable_digest(rows)


def no_material_change_report(previous_digest: str | None, current_digest: str) -> dict[str, Any]:
    """Return a circuit-breaker report for repeated unchanged runs."""
    no_change = bool(previous_digest) and previous_digest == current_digest
    return {
        "previous_digest": previous_digest,
        "current_digest": current_digest,
        "no_material_data_change": no_change,
        "recommended_action": "backoff" if no_change else "continue_review",
    }


def _contains_phrase(text: str, phrase: str) -> bool:
    """Return true when phrase appears with word-like boundaries."""
    return bool(re.search(rf"(?<!\w){re.escape(phrase.lower())}(?!\w)", text.lower()))


def evaluate_outreach_draft(candidate: CandidateDossier, draft: str) -> dict[str, Any]:
    """Check that a draft is specific enough for human review."""
    fact_hits = [fact for fact in candidate.repo_facts if _contains_phrase(draft, fact)]
    operation_hits = [
        operation
        for operation in candidate.callable_operations
        if _contains_phrase(draft, operation)
    ]
    generic_hits = [
        term
        for term in GENERIC_PITCH_TERMS
        if _contains_phrase(draft, term)
        and candidate.relationship_type not in {"seller", "integrator", "ecosystem_partner"}
    ]
    blocked_reasons: list[str] = []
    if len(fact_hits) < 2:
        blocked_reasons.append("requires_two_repo_specific_facts")
    if not operation_hits:
        blocked_reasons.append("requires_named_callable_operation")
    if generic_hits:
        blocked_reasons.append("generic_marketplace_pitch")

    return {
        "candidate_id": candidate.candidate_id,
        "fact_hits": fact_hits,
        "operation_hits": operation_hits,
        "generic_hits": generic_hits,
        "allowed_for_manual_review": not blocked_reasons,
        "blocked_reasons": blocked_reasons,
    }


def is_candidate_suppressed(candidate: CandidateDossier) -> bool:
    """Return true when DNC, reply, locked issue, automation, or bad fit applies."""
    return bool(set(candidate.suppression_flags).intersection(SUPPRESSION_FLAGS))


def select_canary_candidate(
    candidates: tuple[CandidateDossier, ...],
    run_id: str,
) -> dict[str, Any]:
    """Select exactly one current-run candidate for manual canary review."""
    eligible: list[CandidateDossier] = []
    blocked: list[dict[str, Any]] = []

    for candidate in candidates:
        reasons: list[str] = []
        if candidate.run_id != run_id or not candidate.current_run:
            reasons.append("not_current_run")
        if is_candidate_suppressed(candidate):
            reasons.append("suppressed")
        if candidate.channel == "skip":
            reasons.append("skip_channel")
        if len(candidate.repo_facts) < 2:
            reasons.append("insufficient_repo_facts")
        if not candidate.callable_operations:
            reasons.append("missing_callable_operation")
        if "issue_automation" in candidate.risk_flags and candidate.channel == "github_issue":
            reasons.append("issue_automation_public_issue_blocked")
        if reasons:
            blocked.append({"candidate_id": candidate.candidate_id, "reasons": reasons})
        else:
            eligible.append(candidate)

    if not eligible:
        return {
            "selected": None,
            "selected_count": 0,
            "send_allowed": False,
            "requires_approval_receipt": True,
            "blocked": blocked,
        }

    selected = sorted(eligible, key=lambda item: (-item.score, item.candidate_id))[0]
    return {
        "selected": selected.as_dict(),
        "selected_count": 1,
        "send_allowed": False,
        "requires_approval_receipt": True,
        "blocked": blocked,
    }


def build_approval_receipt(
    run_id: str,
    candidate_id: str,
    policy_version: str = DEFAULT_POLICY_VERSION,
    approver: str = "human:operator",
    created_at: str = DEFAULT_NOW,
    expires_at: str = DEFAULT_EXPIRY,
    max_sends: int = 1,
    sent_count: int = 0,
) -> ApprovalReceipt:
    """Build one canonical approval receipt for one candidate and run."""
    if max_sends < 1:
        raise ValueError("max_sends must be at least 1")
    if sent_count < 0:
        raise ValueError("sent_count must be non-negative")
    if not run_id or not candidate_id or not policy_version or not approver:
        raise ValueError("run_id, candidate_id, policy_version, and approver are required")
    payload = {
        "run_id": run_id,
        "candidate_id": candidate_id,
        "policy_version": policy_version,
        "approver": approver,
        "created_at": created_at,
        "expires_at": expires_at,
        "max_sends": max_sends,
    }
    return ApprovalReceipt(
        receipt_id=f"approval_{stable_digest(payload)[:16]}",
        run_id=run_id,
        candidate_id=candidate_id,
        policy_version=policy_version,
        approver=approver,
        created_at=created_at,
        expires_at=expires_at,
        max_sends=max_sends,
        sent_count=sent_count,
    )


def compute_dispatch_state(
    candidate: CandidateDossier,
    receipt: ApprovalReceipt | None,
    run_live: bool = False,
    now: str = DEFAULT_NOW,
) -> dict[str, Any]:
    """Compute one effective dispatch state from policy, candidate, and receipt."""
    blocked_reasons: list[str] = []
    if not run_live:
        blocked_reasons.append("run_live_disabled")
    if candidate.channel not in AUTO_SEND_ELIGIBLE_CHANNELS:
        blocked_reasons.append("channel_not_auto_send_eligible")
    if candidate.run_id == "" or not candidate.current_run:
        blocked_reasons.append("candidate_not_current_run")
    if is_candidate_suppressed(candidate):
        blocked_reasons.append("suppressed_candidate")
    if receipt is None:
        blocked_reasons.append("missing_approval_receipt")
    else:
        if receipt.run_id != candidate.run_id:
            blocked_reasons.append("receipt_run_mismatch")
        if receipt.candidate_id != candidate.candidate_id:
            blocked_reasons.append("receipt_candidate_mismatch")
        if receipt.policy_version != DEFAULT_POLICY_VERSION:
            blocked_reasons.append("receipt_policy_mismatch")
        if receipt.expires_at <= now:
            blocked_reasons.append("receipt_expired")
        if receipt.sent_count >= receipt.max_sends:
            blocked_reasons.append("receipt_send_limit_reached")

    return {
        "candidate_id": candidate.candidate_id,
        "dispatch_enabled_effective": not blocked_reasons,
        "outbound_actions_taken": bool(receipt and receipt.sent_count > 0),
        "blocked_reasons": blocked_reasons,
        "receipt_id": receipt.receipt_id if receipt else None,
    }


def _count_candidates(candidates: tuple[CandidateDossier, ...], flag: str) -> int:
    """Count candidates carrying a suppression or risk flag."""
    return sum(
        1
        for candidate in candidates
        if flag in candidate.suppression_flags or flag in candidate.risk_flags
    )


def build_syrin_status(
    run_id: str,
    candidates: tuple[CandidateDossier, ...],
    approval_receipts: tuple[ApprovalReceipt, ...] = (),
    dispatch_states: tuple[dict[str, Any], ...] = (),
    policy_version: str = DEFAULT_POLICY_VERSION,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    previous_lead_set_digest: str | None = None,
) -> dict[str, Any]:
    """Build a canonical ``syrin-status.json`` style observer export."""
    current_candidates = tuple(
        candidate for candidate in candidates if candidate.run_id == run_id and candidate.current_run
    )
    lead_set_digest = build_lead_set_digest(current_candidates)
    blocked_candidates = [
        candidate
        for candidate in current_candidates
        if is_candidate_suppressed(candidate) or candidate.channel == "skip" or candidate.risk_flags
    ]
    safe_candidates = [
        candidate
        for candidate in current_candidates
        if candidate not in blocked_candidates
        and len(candidate.repo_facts) >= 2
        and candidate.callable_operations
    ]
    blocked_reasons: dict[str, int] = {}
    for candidate in blocked_candidates:
        for reason in (*candidate.suppression_flags, *candidate.risk_flags):
            blocked_reasons[reason] = blocked_reasons.get(reason, 0) + 1
        if candidate.channel == "skip":
            blocked_reasons["skip_channel"] = blocked_reasons.get("skip_channel", 0) + 1
    for state in dispatch_states:
        for reason in state.get("blocked_reasons", []):
            blocked_reasons[reason] = blocked_reasons.get(reason, 0) + 1

    dispatch_enabled = any(
        bool(state.get("dispatch_enabled_effective")) for state in dispatch_states
    )
    outbound_taken = any(bool(state.get("outbound_actions_taken")) for state in dispatch_states)

    return {
        "run_id": run_id,
        "policy_version": policy_version,
        "prompt_version": prompt_version,
        "lead_set_digest": lead_set_digest,
        "scored_count": len(current_candidates),
        "safe_candidate_count": len(safe_candidates),
        "manual_candidate_count": sum(
            1 for candidate in current_candidates if candidate.channel == "manual_only"
        ),
        "blocked_count": len(blocked_candidates),
        "approved_to_send_count": sum(
            1
            for receipt in approval_receipts
            if receipt.run_id == run_id and receipt.sent_count < receipt.max_sends
        ),
        "sent_count": sum(receipt.sent_count for receipt in approval_receipts),
        "dispatch_enabled_effective": dispatch_enabled,
        "outbound_actions_taken": outbound_taken,
        "blocked_reasons": blocked_reasons,
        "dnc_count": _count_candidates(current_candidates, "dnc"),
        "already_replied_count": _count_candidates(current_candidates, "already_replied"),
        "issue_locked_count": _count_candidates(current_candidates, "issue_locked"),
        "candidate_lineage": [
            {
                "candidate_id": candidate.candidate_id,
                "run_id": candidate.run_id,
                "repo_url": candidate.repo_url,
                "lineage": list(candidate.lineage),
            }
            for candidate in current_candidates
        ],
        "material_change": no_material_change_report(previous_lead_set_digest, lead_set_digest),
    }


def build_manual_outreach_packet(candidate: CandidateDossier, draft: str) -> dict[str, Any]:
    """Build the compact packet a human or stricter authority layer reviews."""
    quality = evaluate_outreach_draft(candidate, draft)
    return {
        "candidate": candidate.as_dict(),
        "draft": draft,
        "quality": quality,
        "allowed_for_manual_review": quality["allowed_for_manual_review"]
        and not is_candidate_suppressed(candidate),
        "send_authority": {
            "dispatch_enabled_effective": False,
            "requires_approval_receipt": True,
            "reason": "manual_packet_only",
        },
    }


def sample_candidates(run_id: str) -> tuple[CandidateDossier, ...]:
    """Return deterministic sample candidates for CLI and tests."""
    return (
        build_candidate_dossier(
            run_id=run_id,
            repo_url="https://github.com/example/local-agent-router",
            maintainer="local-router-maintainer",
            score=0.92,
            relationship_type="integrator",
            channel="github_discussion",
            repo_facts=(
                "OpenAI-compatible local routing",
                "MCP server examples",
            ),
            callable_operations=(
                "agoragentic_match",
                "agoragentic_execute",
            ),
        ),
        build_candidate_dossier(
            run_id=run_id,
            repo_url="https://github.com/example/locked-issues",
            maintainer="busy-maintainer",
            score=0.88,
            relationship_type="ecosystem_partner",
            channel="github_issue",
            repo_facts=("agent runtime", "tool registry"),
            callable_operations=("agoragentic_match",),
            risk_flags=("issue_automation",),
            suppression_flags=("issue_locked",),
        ),
    )


def build_authority_layer_snapshot(
    run_id: str,
    previous_lead_set_digest: str | None = None,
) -> dict[str, Any]:
    """Build a complete authority-layer snapshot for inspection."""
    candidates = sample_candidates(run_id)
    canary = select_canary_candidate(candidates, run_id=run_id)
    selected = canary["selected"]
    receipt = None
    dispatch_states: tuple[dict[str, Any], ...] = ()
    if selected:
        selected_candidate = next(
            candidate
            for candidate in candidates
            if candidate.candidate_id == selected["candidate_id"]
        )
        receipt = build_approval_receipt(
            run_id=run_id,
            candidate_id=selected_candidate.candidate_id,
        )
        dispatch_states = (
            compute_dispatch_state(
                selected_candidate,
                receipt=receipt,
                run_live=False,
            ),
        )

    return {
        "relationship_map": [candidate.as_dict() for candidate in candidates],
        "canary": canary,
        "approval_receipts": [receipt.as_dict()] if receipt else [],
        "dispatch_states": list(dispatch_states),
        "syrin_status": build_syrin_status(
            run_id=run_id,
            candidates=candidates,
            approval_receipts=(receipt,) if receipt else (),
            dispatch_states=dispatch_states,
            previous_lead_set_digest=previous_lead_set_digest,
        ),
    }


def main() -> None:
    """Print a no-send Syrin authority-layer snapshot."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="run_2026_05_11_blackbox_guarded")
    parser.add_argument("--previous-lead-set-digest", default=None)
    args = parser.parse_args()
    snapshot = build_authority_layer_snapshot(
        run_id=args.run_id,
        previous_lead_set_digest=args.previous_lead_set_digest,
    )
    print(json.dumps(snapshot, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
