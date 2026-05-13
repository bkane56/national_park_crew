# National Park Trip Planner

CrewAI-based multi-agent pipeline to research national parks, flights, and lodging and draft trip itineraries.

The runnable project and full documentation live in **[national_park_crew/](national_park_crew/)** — start there for setup, env vars, and customization.

## Quick start

```bash
cd national_park_crew
cp .env.example .env   # set OPENAI_API_KEY
uv sync
uv run crewai run
```

**Full guide:** [national_park_crew/README.md](national_park_crew/README.md) (install, Apple Silicon / `uv run` notes, task layout).
