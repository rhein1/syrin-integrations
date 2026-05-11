"""Reusable relationship-intelligence builders for Syrin + Agoragentic.

The pack turns raw ecosystem observations into stable dossiers, relationship
maps, manual outreach packets, and no-send status summaries. It intentionally
does not perform network calls or public dispatch.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CHANNELS = (
    "github_issue",
    "github_discussion",
    "email",
    "website_contact_form",
    "manual_only",
    "skip",
)

RELATIONSHIP_TYPES = (
    "buyer",
    "seller",
    "integrator",
    "competitor",
    "ecosystem_partner",
    "unknown",
)

DEMAND_SIGNAL_KEYWORDS = {
    "discovery": ("discovery", "find tools", "tool discovery", "provider discovery"),
    "routing": ("routing", "router", "route", "multi-provider"),
    "billing": ("billing", "metering", "payments", "paid api", "usage based"),
    "trust": ("trust", "reputation", "verification", "verified", "attestation"),
    "hosted_agents": ("hosted agent", "deploy agent", "agent hosting", "self hosted"),
    "local_context_governance": (
        "context governance",
        "local context",
        "policy",
        "approval",
        "guardrail",
    ),
    "x402": ("x402", "usdc", "base", "wallet", "settlement"),
    "mcp": ("mcp", "model context protocol"),
    "marketplace": ("marketplace", "seller", "listing", "capability marketplace"),
}

SUPPRESSION_FLAGS = (
    "dnc",
    "already_replied",
    "issue_locked",
    "issue_automation",
    "bad_fit",
    "archived",
)

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


@dataclass(frozen=True)
class RelationshipCandidate:
    """Structured dossier for one repo, builder, maintainer, or community."""

    run_id: str
    candidate_id: str
    name: str
    repo_url: str
    maintainer: str
    relationship_type: str
    score: float
    channel: str
    channel_reasons: tuple[str, ...]
    repo_facts: tuple[str, ...]
    pain_points: tuple[str, ...]
    demand_signals: tuple[str, ...]
    callable_operations: tuple[str, ...]
    contact_paths: tuple[str, ...]
    risk_flags: tuple[str, ...] = ()
    suppression_flags: tuple[str, ...] = ()
    prior_contact_status: str = "none"
    current_run: bool = True
    lineage: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe candidate dossier."""
        return {
            "run_id": self.run_id,
            "candidate_id": self.candidate_id,
            "name": self.name,
            "repo_url": self.repo_url,
            "maintainer": self.maintainer,
            "relationship_type": self.relationship_type,
            "score": self.score,
            "channel": self.channel,
            "channel_reasons": list(self.channel_reasons),
            "repo_facts": list(self.repo_facts),
            "pain_points": list(self.pain_points),
            "demand_signals": list(self.demand_signals),
            "callable_operations": list(self.callable_operations),
            "contact_paths": list(self.contact_paths),
            "risk_flags": list(self.risk_flags),
            "suppression_flags": list(self.suppression_flags),
            "prior_contact_status": self.prior_contact_status,
            "current_run": self.current_run,
            "lineage": list(self.lineage),
        }


def stable_digest(payload: Any) -> str:
    """Return a deterministic SHA-256 digest for JSON-compatible payloads."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_candidate_id(repo_url: str, maintainer: str = "") -> str:
    """Build a stable candidate id from public identity fields."""
    normalized = f"{repo_url.strip().lower()}|{maintainer.strip().lower()}"
    return f"rel_{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"


def _coerce_tuple(value: Any) -> tuple[str, ...]:
    """Normalize list/string input into a tuple of non-empty strings."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),) if str(value).strip() else ()


def _text_blob(raw: dict[str, Any]) -> str:
    """Build a searchable text blob from raw candidate metadata."""
    parts: list[str] = []
    for key in ("name", "description", "readme_excerpt", "issue_excerpt", "discussion_excerpt"):
        value = raw.get(key)
        if value:
            parts.append(str(value))
    parts.extend(_coerce_tuple(raw.get("topics")))
    return " ".join(parts).lower()


def extract_demand_signals(raw: dict[str, Any] | str) -> tuple[str, ...]:
    """Extract demand signals relevant to Agoragentic and Syrin."""
    text = raw.lower() if isinstance(raw, str) else _text_blob(raw)
    signals = [
        signal
        for signal, terms in DEMAND_SIGNAL_KEYWORDS.items()
        if any(term in text for term in terms)
    ]
    return tuple(sorted(signals))


def classify_relationship_type(raw: dict[str, Any]) -> str:
    """Classify whether a project is a buyer, seller, integrator, competitor, or partner."""
    explicit = str(raw.get("relationship_type", "")).strip().lower()
    if explicit in RELATIONSHIP_TYPES:
        return explicit

    text = _text_blob(raw)
    if "marketplace" in text and ("agent" in text or "tool" in text):
        return "competitor"
    if "mcp" in text or "sdk" in text or "framework" in text or "integration" in text:
        return "integrator"
    if "api" in text or "service" in text or "provider" in text or "hosted" in text:
        return "seller"
    if "looking for" in text or "need" in text or "billing" in text or "discovery" in text:
        return "buyer"
    if "community" in text or "awesome" in text or "curated" in text:
        return "ecosystem_partner"
    return "unknown"


def classify_channel(raw: dict[str, Any]) -> dict[str, Any]:
    """Classify the safest next contact channel for a candidate."""
    preferred = str(raw.get("maintainer_prefers", "")).strip().lower()
    if preferred in CHANNELS:
        return {"channel": preferred, "confidence": 0.95, "reasons": ["maintainer_preference"]}
    if raw.get("archived") or raw.get("dnc"):
        return {"channel": "skip", "confidence": 1.0, "reasons": ["suppressed"]}
    if raw.get("contact_email"):
        return {"channel": "email", "confidence": 0.8, "reasons": ["contact_email"]}
    if raw.get("website_contact_form"):
        return {
            "channel": "website_contact_form",
            "confidence": 0.7,
            "reasons": ["website_contact_form"],
        }
    if raw.get("issue_automation"):
        if raw.get("discussions_enabled"):
            return {
                "channel": "github_discussion",
                "confidence": 0.65,
                "reasons": ["issue_automation", "discussions_enabled"],
            }
        return {"channel": "manual_only", "confidence": 0.6, "reasons": ["issue_automation"]}
    if raw.get("allow_public_issue_outreach") and raw.get("issues_enabled"):
        return {
            "channel": "github_issue",
            "confidence": 0.55,
            "reasons": ["explicit_issue_outreach_allowed"],
        }
    if raw.get("discussions_enabled"):
        return {"channel": "github_discussion", "confidence": 0.55, "reasons": ["discussions_enabled"]}
    return {"channel": "manual_only", "confidence": 0.5, "reasons": ["no_safe_public_channel"]}


def _default_callable_operations(signals: tuple[str, ...]) -> tuple[str, ...]:
    """Map demand signals to concrete Agoragentic operations."""
    operations = ["agoragentic_match"]
    if {"routing", "billing", "x402", "marketplace"}.intersection(signals):
        operations.append("agoragentic_execute")
    if "trust" in signals:
        operations.append("agoragentic_passport")
    if "hosted_agents" in signals:
        operations.append("agoragentic_relay_deploy")
    return tuple(dict.fromkeys(operations))


def _derive_score(raw: dict[str, Any], signals: tuple[str, ...], facts: tuple[str, ...]) -> float:
    """Compute a bounded fit score when one is not supplied."""
    if "score" in raw:
        score = float(raw["score"])
    else:
        score = 0.25 + min(len(signals) * 0.08, 0.4) + min(len(facts) * 0.06, 0.24)
        if raw.get("contact_email") or raw.get("discussions_enabled"):
            score += 0.06
        if raw.get("issue_automation") or raw.get("archived") or raw.get("dnc"):
            score -= 0.2
    return round(max(0.0, min(1.0, score)), 4)


def build_candidate_dossier(raw: dict[str, Any], run_id: str) -> RelationshipCandidate:
    """Build a candidate dossier from raw repository or maintainer metadata."""
    repo_url = str(raw.get("repo_url", "")).strip()
    if not repo_url:
        raise ValueError("repo_url is required")

    maintainer = str(raw.get("maintainer", "")).strip()
    channel = classify_channel(raw)
    facts = _coerce_tuple(raw.get("repo_facts"))
    if not facts:
        facts = _coerce_tuple(raw.get("facts"))
    signals = extract_demand_signals(raw)
    operations = _coerce_tuple(raw.get("callable_operations")) or _default_callable_operations(signals)
    suppression = tuple(
        flag
        for flag in SUPPRESSION_FLAGS
        if raw.get(flag) or flag in set(_coerce_tuple(raw.get("suppression_flags")))
    )
    risk_flags = _coerce_tuple(raw.get("risk_flags"))
    if raw.get("issue_automation") and "issue_automation" not in risk_flags:
        risk_flags = (*risk_flags, "issue_automation")

    return RelationshipCandidate(
        run_id=run_id,
        candidate_id=build_candidate_id(repo_url, maintainer),
        name=str(raw.get("name", repo_url.rsplit("/", 1)[-1])).strip(),
        repo_url=repo_url,
        maintainer=maintainer,
        relationship_type=classify_relationship_type(raw),
        score=_derive_score(raw, signals, facts),
        channel=channel["channel"],
        channel_reasons=tuple(channel["reasons"]),
        repo_facts=facts,
        pain_points=_coerce_tuple(raw.get("pain_points")),
        demand_signals=signals,
        callable_operations=operations,
        contact_paths=_coerce_tuple(
            raw.get("contact_paths")
            or raw.get("contact_email")
            or raw.get("website_contact_form")
            or raw.get("repo_url")
        ),
        risk_flags=risk_flags,
        suppression_flags=suppression,
        prior_contact_status=str(raw.get("prior_contact_status", "none")),
        current_run=bool(raw.get("current_run", True)),
        lineage=_coerce_tuple(raw.get("lineage")),
    )


def build_relationship_map(candidates: tuple[RelationshipCandidate, ...]) -> dict[str, Any]:
    """Build a deterministic relationship map from candidate dossiers."""
    rows = sorted((candidate.as_dict() for candidate in candidates), key=lambda row: row["candidate_id"])
    by_type: dict[str, int] = {}
    by_channel: dict[str, int] = {}
    for row in rows:
        by_type[row["relationship_type"]] = by_type.get(row["relationship_type"], 0) + 1
        by_channel[row["channel"]] = by_channel.get(row["channel"], 0) + 1
    return {
        "digest": stable_digest(rows),
        "candidate_count": len(rows),
        "by_relationship_type": by_type,
        "by_channel": by_channel,
        "candidates": rows,
    }


def _draft_quality(candidate: RelationshipCandidate, draft: str) -> dict[str, Any]:
    """Evaluate whether a manual packet is specific enough to inspect."""
    draft_lower = draft.lower()
    fact_hits = [fact for fact in candidate.repo_facts if fact.lower() in draft_lower]
    operation_hits = [
        operation for operation in candidate.callable_operations if operation.lower() in draft_lower
    ]
    blocked_reasons: list[str] = []
    if len(fact_hits) < 2:
        blocked_reasons.append("requires_two_repo_specific_facts")
    if not operation_hits:
        blocked_reasons.append("requires_named_callable_operation")
    if "marketplace" in draft_lower and candidate.relationship_type not in {
        "seller",
        "integrator",
        "ecosystem_partner",
    }:
        blocked_reasons.append("generic_marketplace_pitch")
    return {
        "fact_hits": fact_hits,
        "operation_hits": operation_hits,
        "allowed_for_manual_review": not blocked_reasons,
        "blocked_reasons": blocked_reasons,
    }


def build_manual_outreach_packet(
    candidate: RelationshipCandidate,
    draft: str | None = None,
) -> dict[str, Any]:
    """Build a compact, no-send packet for human review."""
    if draft is None:
        facts = "; ".join(candidate.repo_facts[:2]) or "repo-specific fit pending"
        operation = candidate.callable_operations[0] if candidate.callable_operations else "agoragentic_match"
        draft = (
            f"Manual review packet for {candidate.name}: {facts}. "
            f"Concrete integration idea: evaluate {operation} against this repo."
        )
    quality = _draft_quality(candidate, draft)
    suppressed = bool(candidate.suppression_flags)
    return {
        "candidate_id": candidate.candidate_id,
        "candidate": candidate.as_dict(),
        "draft": draft,
        "quality": quality,
        "allowed_for_manual_review": quality["allowed_for_manual_review"] and not suppressed,
        "send_authority": {
            "dispatch_enabled_effective": False,
            "requires_approval_receipt": True,
            "reason": "relationship_intelligence_packet_only",
        },
    }


def build_relationship_intelligence_pack(
    raw_candidates: tuple[dict[str, Any], ...],
    run_id: str,
    previous_digest: str | None = None,
) -> dict[str, Any]:
    """Build the full no-send relationship-intelligence pack."""
    candidates = tuple(build_candidate_dossier(raw, run_id=run_id) for raw in raw_candidates)
    relationship_map = build_relationship_map(candidates)
    packets = tuple(build_manual_outreach_packet(candidate) for candidate in candidates)
    top_opportunities = [
        candidate.as_dict()
        for candidate in sorted(candidates, key=lambda item: (-item.score, item.candidate_id))[:10]
        if not candidate.suppression_flags and candidate.channel != "skip"
    ]
    no_material_change = bool(previous_digest) and previous_digest == relationship_map["digest"]
    return {
        "run_id": run_id,
        "mode": "relationship_intelligence",
        "send_authority": {
            "dispatch_enabled_effective": False,
            "reason": "pack_does_not_send",
        },
        "relationship_map": relationship_map,
        "candidate_dossiers": [candidate.as_dict() for candidate in candidates],
        "manual_outreach_packets": list(packets),
        "top_opportunities": top_opportunities,
        "schemas": list_schema_names(),
        "status": {
            "lead_set_digest": relationship_map["digest"],
            "scored_count": len(candidates),
            "safe_candidate_count": len(top_opportunities),
            "manual_packet_count": len(packets),
            "dispatch_enabled_effective": False,
            "outbound_actions_taken": False,
            "no_material_data_change": no_material_change,
            "recommended_action": "backoff" if no_material_change else "review_top_opportunities",
        },
    }


def list_schema_names() -> tuple[str, ...]:
    """List bundled JSON schema file names."""
    return tuple(sorted(path.name for path in SCHEMA_DIR.glob("*.schema.json")))


def load_schema(name: str) -> dict[str, Any]:
    """Load one bundled JSON schema by file name."""
    if "/" in name or "\\" in name:
        raise ValueError("schema name must be a file name")
    path = SCHEMA_DIR / name
    if not path.exists():
        raise FileNotFoundError(name)
    return json.loads(path.read_text(encoding="utf-8"))
