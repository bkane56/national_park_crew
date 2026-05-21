# Deployment Guide (Hugging Face Docker Space)

This project is designed for a recruiter-facing demo with a safe mocked public mode and an optional access-code-gated real CrewAI mode.

## Recommended host

- **Hugging Face Spaces** for the public Gradio demo.
- Use the **Docker Space** SDK so dependency versions stay under project control.
- Keep the portfolio website on Vercel and link to the Space as the live demo.

## Runtime setup

1. Create a Hugging Face Space.
2. Select **Docker** as the Space SDK.
3. Push a Space repo containing the root `app.py`, `requirements.txt`, `Dockerfile`, and this package's `src/` tree.
4. Set the Space to public only after confirming demo mode returns mocked data by default.

## Environment variables

- `OPENAI_API_KEY`: required only for real CrewAI runs.
- `REAL_RUNS_ENABLED`: optional demo-first default flag (`false` recommended). Does not block real runs when a valid access code is entered.
- `REAL_RUN_ACCESS_CODE`: private code trusted reviewers enter in the UI for a one-time real run.
- Any additional provider keys used by CrewAI tools.

Store these as Hugging Face Secrets. Do not commit `.env` files or secrets to source control.

## Local verification

```bash
cd national_park_crew
uv sync
uv run run_ui
```

Visit `http://localhost:7860`.

## Post-deploy checklist

- Confirm the default public flow says it is using mocked itinerary data.
- Confirm demo mode does not require `OPENAI_API_KEY`.
- Confirm invalid real-run access codes fail without invoking CrewAI.
- Confirm a valid access code can run a real itinerary while the Space is private.
- Confirm failure path returns user-safe messages (no stack trace leaks).

## Portfolio card link targets

Use these targets in your Vercel-hosted portfolio project card:

- **Live demo:** deployed Hugging Face Space URL
- **Repository:** `https://github.com/briankane/National_Park_Trip_Planner`
- **Tech tags:** `Python`, `CrewAI`, `Gradio`, `Agentic AI`, `Docker`
