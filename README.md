# National Park Trip Planner

NationalParkCrew — a multi-agent trip planning pipeline powered by [crewAI](https://crewai.com). This repo is designed to help you set up collaborators (research, flights, lodging, itinerary writing) with the framework CrewAI provides.

The canonical Python project configuration lives in `national_park_crew/pyproject.toml`.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Clone or open this repo, then from the **`national_park_crew`** package directory install dependencies (**`uv sync`** creates a local [`.venv`](national_park_crew/.venv) with the correct architecture on Apple Silicon):

```bash
cd national_park_crew
uv sync
```

(Optional) Initialize crew tooling metadata:

```bash
uv run crewai install
```

Older docs used `crewai install` without **`uv`**; on a Mac with multiple Pythons, stick to **`uv run crewai …`** so you use this project’s venv.

### Customizing

**Add your `OPENAI_API_KEY` into `.env`** (copy from [`national_park_crew/.env.example`](national_park_crew/.env.example)).

- Agents: [`national_park_crew/src/national_park_crew/config/agents.yaml`](national_park_crew/src/national_park_crew/config/agents.yaml)
- Tasks: [`national_park_crew/src/national_park_crew/config/tasks.yaml`](national_park_crew/src/national_park_crew/config/tasks.yaml)
- Tools and wiring: [`national_park_crew/src/national_park_crew/crew.py`](national_park_crew/src/national_park_crew/crew.py)
- Run inputs / kickoff payloads: [`national_park_crew/src/national_park_crew/main.py`](national_park_crew/src/national_park_crew/main.py)

## Running the Project

From **`national_park_crew/`**, prefer **`uv`** so CrewAI runs with that package’s [`.venv`](national_park_crew/.venv) (correct packages and CPU architecture):

```bash
cd national_park_crew
uv sync
uv run crewai install   # optional; uv sync usually enough
uv run crewai run
```

If **`crewai`** is already on your `PATH`, you may use **`crewai run`** after `source .venv/bin/activate` or from a global install—but on a **new Mac (Apple Silicon)** avoid invoking **`/Library/Frameworks/Python.framework/.../crewai`** if you see **`pydantic_core` … incompatible architecture (have 'x86_64', need 'arm64')`**. That means a mismatched Intel/Rosetta or old Python install; use **`uv run crewai …`** from this repo instead.

Use the **`crewai`** command (**not** `crew`). **`uv run crewai …`** avoids “command not found” when the CLI is only installed in the virtualenv.

The final itinerary is returned as Markdown from the reporting task. The Gradio UI can download it as **Markdown** or **PDF** (temporary files for the browser; nothing is written under `national_park_crew/itinerary/` anymore).

### Run the Gradio UI

```bash
cd national_park_crew
uv sync
uv run run_ui
```

Then open `http://localhost:7860`.

For production deployment guidance, see [`national_park_crew/DEPLOYMENT.md`](national_park_crew/DEPLOYMENT.md).

## Understanding Your Crew

The crew is composed of multiple agents defined in YAML. They collaborate on tasks in [`national_park_crew/src/national_park_crew/config/tasks.yaml`](national_park_crew/src/national_park_crew/config/tasks.yaml). Agent roles and goals are in [`national_park_crew/src/national_park_crew/config/agents.yaml`](national_park_crew/src/national_park_crew/config/agents.yaml).

## Support

For support, questions, or feedback regarding CrewAI generally:

- [CrewAI documentation](https://docs.crewai.com)
- [CrewAI GitHub](https://github.com/joaomdmoura/crewai)
- [Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with CrewAI docs](https://chatg.pt/DWjSBZn)

