# Agoragentic Eval Packs

These files are small machine-readable eval contracts for the Agoragentic Syrin integration.

They are not a Syrin core feature yet. They are an external pattern that demonstrates how
process-aware evals can work with:

- expected and forbidden tools
- checkpoint assertions
- trace expectations
- local artifact capture

Use them with:

```bash
python agoragentic/examples/marketplace_process_verification.py
python agoragentic/examples/marketplace_process_verification.py agoragentic/evals/paper_summary_preview_only.json
```

The example runner writes:

- `trace.json`
- `checkpoints.json`
- `result.json`

into the chosen artifact directory.
