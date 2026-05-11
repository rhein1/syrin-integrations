# Syrin Authority Layer

Syrin is safest when it is treated as a relationship-intelligence and
ecosystem-discovery agent first. It can discover, score, explain, draft, and
learn freely. Public sends need a stricter authority layer.

This contract turns guarded Syrin outreach into explicit review artifacts:

- relationship map
- candidate dossier
- manual outreach packet
- canary selector
- approval receipt
- effective dispatch state
- `syrin-status.json` observer export
- no-material-change circuit breaker

The reference implementation is
[`examples/syrin_authority_layer.py`](examples/syrin_authority_layer.py).

## Design Goal

Syrin should be able to answer:

```text
Who matters, why do they matter, what channel fits, what should we say,
what should we not say, and what changed since the last run?
```

It should not silently answer:

```text
Should I send this public message right now?
```

That decision belongs to one authoritative dispatch gate backed by a receipt.

## Canonical Status

Observer exports should produce a stable `syrin-status.json` shape:

```json
{
  "run_id": "run_2026_05_11_blackbox_guarded",
  "policy_version": "syrin-authority-v1",
  "prompt_version": "relationship-intelligence-v1",
  "lead_set_digest": "sha256...",
  "scored_count": 2,
  "safe_candidate_count": 1,
  "manual_candidate_count": 0,
  "blocked_count": 1,
  "approved_to_send_count": 1,
  "sent_count": 0,
  "dispatch_enabled_effective": false,
  "outbound_actions_taken": false,
  "blocked_reasons": {
    "issue_locked": 1,
    "run_live_disabled": 1
  },
  "dnc_count": 0,
  "already_replied_count": 0,
  "issue_locked_count": 1,
  "candidate_lineage": []
}
```

This gives Hermes, operators, and external reviewers one state summary instead
of split queue files, blocked folders, approval files, and observer markdown.

## Approval Receipt

`approved_to_send` should be a single receipt:

```json
{
  "receipt_id": "approval_...",
  "run_id": "run_2026_05_11_blackbox_guarded",
  "candidate_id": "cand_...",
  "policy_version": "syrin-authority-v1",
  "approver": "human:operator",
  "created_at": "2026-05-11T00:00:00Z",
  "expires_at": "2026-05-12T00:00:00Z",
  "max_sends": 1,
  "sent_count": 0
}
```

The effective dispatch state is true only when:

- live mode is enabled
- the channel is eligible
- the candidate is from the current run
- DNC/suppression flags are absent
- the receipt matches the candidate and run
- the receipt has not expired
- the send limit has not been reached

## Channel Classifier

Syrin should classify the contact path before drafting:

- `github_issue`
- `github_discussion`
- `email`
- `website_contact_form`
- `manual_only`
- `skip`

GitHub Issues should require explicit evidence that issue outreach is welcome.
Issue automation, locked issues, prior replies, DNC, archived repos, and poor
fit should route to `manual_only` or `skip`.

## Draft Quality Gate

A manual packet is reviewable only when the draft includes:

- at least two repo-specific facts
- at least one named callable operation or concrete integration idea
- no generic marketplace pitch unless the relationship type fits that framing

This blocks generic MCP/framework language before it reaches a public channel.

## Canary Rule

Canary selection should return one current-run candidate for human review:

```text
1 candidate
current run only
not stale carried-forward state
not DNC or suppressed
not issue-automation GitHub issue
two facts present
one callable operation present
send_allowed=false until a receipt exists
```

The selector does not send. It prepares the compact review object that an
operator or stricter authority layer can approve.

## Circuit Breaker

Every run should compute a `lead_set_digest`. If the previous digest matches the
current digest, Syrin should report `no_material_data_change` and back off
instead of regenerating the same outreach packet.

## Example

```bash
python agoragentic/examples/syrin_authority_layer.py \
  --run-id run_2026_05_11_blackbox_guarded
```

The output includes a relationship map, canary packet, approval receipt,
dispatch state, and canonical status export. It performs no network calls and
does not send anything.
