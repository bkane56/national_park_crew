# Deployment Guide (Railway + Gradio)

This project is designed for a recruiter-facing demo with low traffic and long-running CrewAI tasks.

## Recommended host

- **Railway** for the live planner app (long-running Python process, simple env var management, custom domain support).
- Keep **`brianekane.com`** on Vercel and link to this demo URL.

## Runtime setup

1. Create a new Railway project from this repository.
2. Set project root to `national_park_crew/`.
3. Ensure Python 3.10-3.13 runtime is available.
4. Railway should detect `Procfile` and run:
   - `web: uv run run_ui`

## Required environment variables

- `OPENAI_API_KEY` (required)
- Any additional provider keys used by CrewAI tools

Do not commit `.env` files to source control.

## Local verification

```bash
cd national_park_crew
uv sync
uv run run_ui
```

Visit `http://localhost:7860`.

## Post-deploy checklist

- Confirm itinerary generation works from a fresh browser session.
- Confirm failure path returns user-safe messages (no stack trace leaks).
- Optional: map `demo.brianekane.com` to the Railway service.

## Portfolio card link targets

Use these targets in your Vercel-hosted portfolio project card:

- **Live demo:** deployed Railway URL (or `demo.brianekane.com`)
- **Repository:** `https://github.com/briankane/National_Park_Trip_Planner`
- **Tech tags:** `Python`, `CrewAI`, `Gradio`, `Agentic AI`
