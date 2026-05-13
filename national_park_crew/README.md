# NationalParkCrew Crew

Welcome to the NationalParkCrew Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, clone or open this repo and from **`national_park_crew`** install dependencies (**`uv sync`** creates a local `.venv` with the correct architecture on Apple Silicon):

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

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/national_park_crew/config/agents.yaml` to define your agents
- Modify `src/national_park_crew/config/tasks.yaml` to define your tasks
- Modify `src/national_park_crew/crew.py` to add your own logic, tools and specific args
- Modify `src/national_park_crew/main.py` to add custom inputs for your agents and tasks

## Running the Project

From the **`national_park_crew`** directory, prefer **`uv`** so CrewAI runs with this package’s **[`.venv`](.venv)** (correct packages and CPU architecture):

```bash
cd national_park_crew
uv sync
uv run crewai install   # optional; uv sync usually enough
uv run crewai run
```

If **`crewai`** is already on your `PATH`, you may use **`crewai run`** after `source .venv/bin/activate` or from a global install—but on a **new Mac (Apple Silicon)** avoid invoking **`/Library/Frameworks/Python.framework/.../crewai`** if you see **`pydantic_core` … incompatible architecture (have 'x86_64', need 'arm64')`**. That means a mismatched Intel/Rosetta or old Python install; use **`uv run crewai …`** from this repo instead.

Use the **`crewai`** command (**not** `crew`). **`uv run crewai …`** avoids “command not found” when the CLI is only installed in the virtualenv.

The crew writes itinerary Markdown under **`itinerary/`** (see `tasks.yaml`).

## Understanding Your Crew

The national_park_crew Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the NationalParkCrew Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
