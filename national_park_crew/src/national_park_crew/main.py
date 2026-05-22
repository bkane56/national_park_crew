#!/usr/bin/env python
import sys
import warnings

from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .crew import NationalParkCrew
from .planner_service import DEFAULT_PARK_SCOPE, PlannerRequest, PlannerRuntimeError, run_planner

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
    """
    Run the crew.
    """
    # CrewAI interpolates every `{name}` in agent/task YAML before kickoff—all keys below must stay in sync with
    # config/agents.yaml and config/tasks.yaml template placeholders.
    request = PlannerRequest(
        trip="I live in Venice, Florida. I want to visit the National Parks near Salt Lake City, Utah.",
        current_date=str(datetime.now().date()),
        from_location="Venice, Florida",
        to_location="Salt Lake City, Utah area",
        departure_city_slug="Florida_Gulf_Coast",
        arrival_city_slug="Salt_Lake_City_UT",
        national_parks=DEFAULT_PARK_SCOPE,
        departure_date="2026-07-18",
        return_date="2026-07-27",
    )

    try:
        run_planner(request)
    except PlannerRuntimeError as exc:
        raise RuntimeError(f"An error occurred while running the crew: {exc}") from exc


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        NationalParkCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        NationalParkCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        NationalParkCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = NationalParkCrew().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
