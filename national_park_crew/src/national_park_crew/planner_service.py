from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import io
import os
import re
import threading
import time
from contextlib import redirect_stderr, redirect_stdout
from typing import Callable, Iterator, Optional


DEFAULT_PARK_SCOPE = (
    "Utah Mighty 5 and nearby NPS units within ~8 hr drive of Salt Lake City "
    "(e.g. Zion, Bryce Canyon, Capitol Reef, Arches, Canyonlands)—refine based on dates and pacing."
)

# CrewAI telemetry installs signal handlers. In Gradio queue workers this code runs
# outside the main thread, which can produce noisy signal registration tracebacks.
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

_PHASE_PATTERNS = [
    ("General research", re.compile(r"general[_\s-]?research", re.IGNORECASE)),
    ("Flight research", re.compile(r"flight[_\s-]?research", re.IGNORECASE)),
    ("Accommodations", re.compile(r"accommodation|lodging|hotel", re.IGNORECASE)),
    ("Park activity planning", re.compile(r"national[_\s-]?park", re.IGNORECASE)),
    ("Report generation", re.compile(r"reporting|itinerary|writer", re.IGNORECASE)),
]


class PlannerInputError(ValueError):
    """Raised when planner request inputs are invalid."""


class PlannerRuntimeError(RuntimeError):
    """Raised when planner execution fails."""


@dataclass(frozen=True)
class PlannerRequest:
    from_location: str
    to_location: str
    departure_date: str
    return_date: str
    trip: Optional[str] = None
    national_parks: str = DEFAULT_PARK_SCOPE
    departure_city_slug: Optional[str] = None
    arrival_city_slug: Optional[str] = None
    current_date: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.from_location.strip():
            raise PlannerInputError("Departure location is required.")
        if not self.to_location.strip():
            raise PlannerInputError("Arrival region is required.")
        departure = parse_iso_date(self.departure_date, "departure_date")
        returning = parse_iso_date(self.return_date, "return_date")
        if returning < departure:
            raise PlannerInputError("Return date must be on or after departure date.")
        if self.current_date:
            parse_iso_date(self.current_date, "current_date")


@dataclass(frozen=True)
class PlannerResult:
    markdown: str
    output_path: Optional[Path]
    raw_result: object
    log_output: str


def parse_iso_date(value: str, field_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise PlannerInputError(f"{field_name} must be in YYYY-MM-DD format.") from exc


def slugify_location(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        raise PlannerInputError("Unable to generate a valid slug from location value.")
    return normalized


def build_trip_summary(request: PlannerRequest) -> str:
    if request.trip and request.trip.strip():
        return request.trip.strip()
    return (
        f"I live in {request.from_location.strip()}. "
        f"I want to visit the National Parks near {request.to_location.strip()}."
    )


def build_kickoff_inputs(request: PlannerRequest) -> dict[str, str]:
    departure_slug = request.departure_city_slug or slugify_location(request.from_location)
    arrival_slug = request.arrival_city_slug or slugify_location(request.to_location)
    current_date = request.current_date or str(datetime.now().date())

    return {
        "trip": build_trip_summary(request),
        "current_date": current_date,
        "from": request.from_location.strip(),
        "to": request.to_location.strip(),
        "departure_city": slugify_location(departure_slug),
        "arrival_city": slugify_location(arrival_slug),
        "national_parks": request.national_parks.strip() or DEFAULT_PARK_SCOPE,
        "departure_date": request.departure_date,
        "return_date": request.return_date,
    }


def _extract_markdown(raw_result: object, inputs: dict[str, str]) -> tuple[str, Optional[Path]]:
    output_file = Path("itinerary") / f"{inputs['departure_city']}_to_{inputs['arrival_city']}.md"
    if output_file.exists():
        return output_file.read_text(encoding="utf-8"), output_file

    if isinstance(raw_result, str):
        return raw_result, None
    if raw_result is None:
        return "No itinerary output was returned by the crew.", None
    return str(raw_result), None


def run_planner(
    request: PlannerRequest,
    progress_callback: Optional[Callable[[str, str], None]] = None,
    crew_factory: Optional[Callable[[], object]] = None,
) -> PlannerResult:
    inputs = build_kickoff_inputs(request)
    if crew_factory is None:
        from .crew import NationalParkCrew

        crew_factory = NationalParkCrew
    progress_callback = progress_callback or (lambda _phase, _message: None)
    progress_callback("Queued", "Starting trip planning workflow...")

    log_buffer = io.StringIO()
    try:
        progress_callback("Running", "CrewAI agents are gathering flights, parks, and lodging data.")
        with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
            raw_result = crew_factory().crew().kickoff(inputs=inputs)
    except Exception as exc:  # noqa: BLE001 - we re-map to user-safe runtime error
        raise PlannerRuntimeError(f"Planner run failed: {exc}") from exc

    markdown, output_path = _extract_markdown(raw_result, inputs)
    progress_callback("Completed", "Itinerary generated successfully.")
    return PlannerResult(
        markdown=markdown,
        output_path=output_path,
        raw_result=raw_result,
        log_output=log_buffer.getvalue(),
    )


def _detect_phase(logs: str) -> str:
    for phase, pattern in _PHASE_PATTERNS:
        if pattern.search(logs):
            return phase
    return "Running"


def iter_planner_updates(
    request: PlannerRequest,
    poll_seconds: float = 1.0,
    crew_factory: Optional[Callable[[], object]] = None,
) -> Iterator[dict[str, object]]:
    if crew_factory is None:
        from .crew import NationalParkCrew

        crew_factory = NationalParkCrew

    status = {"done": False, "result": None, "error": None}
    progress_events: list[tuple[str, str]] = [("Queued", "Validating inputs and preparing kickoff payload.")]
    log_buffer = io.StringIO()

    def progress_callback(phase: str, message: str) -> None:
        progress_events.append((phase, message))

    def worker() -> None:
        try:
            inputs = build_kickoff_inputs(request)
            progress_callback("Running", "CrewAI agents are now executing tasks.")
            with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
                raw_result = crew_factory().crew().kickoff(inputs=inputs)
            markdown, output_path = _extract_markdown(raw_result, inputs)
            status["result"] = PlannerResult(
                markdown=markdown,
                output_path=output_path,
                raw_result=raw_result,
                log_output=log_buffer.getvalue(),
            )
            progress_callback("Completed", "Itinerary generated successfully.")
        except Exception as exc:  # noqa: BLE001
            status["error"] = PlannerRuntimeError(f"Planner run failed: {exc}")
            progress_callback("Error", "Planner run failed. See details below.")
        finally:
            status["done"] = True

    thread = threading.Thread(target=worker, daemon=True)
    started = time.time()
    thread.start()

    last_event_index = 0
    while not status["done"]:
        while last_event_index < len(progress_events):
            phase, message = progress_events[last_event_index]
            elapsed = int(time.time() - started)
            logs = log_buffer.getvalue()
            inferred_phase = _detect_phase(logs) if phase == "Running" else phase
            yield {
                "phase": inferred_phase,
                "message": message,
                "elapsed_seconds": elapsed,
                "logs": logs,
                "done": False,
            }
            last_event_index += 1
        time.sleep(poll_seconds)

    final_logs = log_buffer.getvalue()
    if status["error"] is not None:
        raise status["error"]

    result = status["result"]
    if result is None:
        raise PlannerRuntimeError("Planner run finished without a result.")

    yield {
        "phase": "Completed",
        "message": "Workflow finished.",
        "elapsed_seconds": int(time.time() - started),
        "logs": final_logs,
        "done": True,
        "result": result,
    }
