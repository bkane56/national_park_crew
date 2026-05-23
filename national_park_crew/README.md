# NationalParkCrew package

Documentation for this repo lives at the **[root README](../README.md)**.

All install and run commands use this directory (`national_park_crew/`) — for example:

```bash
cd national_park_crew
uv sync
uv run crewai run
```

To launch the recruiter-facing Gradio app:

```bash
uv run run_ui
```

## Security guardrails (public demo)

This repository is public and intended for portfolio/recruiter review, so the planner service includes default safety controls:

- Real runs require a valid access code; unauthorized attempts automatically fall back to demo mode.
- User-provided trip fields are normalized, length-limited, and validated for instruction-like/prompt-injection content.
- Runtime logs are redacted and truncated before they are surfaced to the UI.
- Real run execution is isolated in a worker process so timeout enforcement can terminate long-running jobs.

