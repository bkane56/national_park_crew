from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from hmac import compare_digest
from importlib import resources
import io
import multiprocessing as mp
import os
import queue
import re
import threading
import time
from contextlib import redirect_stderr, redirect_stdout
from typing import Callable, Iterator, Optional


DEFAULT_PARK_SCOPE = (
    "Utah Mighty 5 and nearby NPS units within ~8 hr drive of Salt Lake City "
    "(e.g. Zion, Bryce Canyon, Capitol Reef, Arches, Canyonlands)—refine based on dates and pacing."
)
DEMO_MODE_LABEL = "Demo mode - mocked data"
REAL_MODE_LABEL = "Real planning run - access code required"
DEMO_FALLBACK_PHASE = "Demo mode - mocked data (fallback)"
REAL_RUNS_ENABLED_ENV = "REAL_RUNS_ENABLED"
REAL_RUN_ACCESS_CODE_ENV = "REAL_RUN_ACCESS_CODE"
MAX_RUNTIME_SECONDS_ENV = "PLANNER_MAX_RUNTIME_SECONDS"
DEFAULT_MAX_RUNTIME_SECONDS = 600.0
MAX_LOCATION_LENGTH = 120
MAX_TRIP_SUMMARY_LENGTH = 600
MAX_NATIONAL_PARKS_LENGTH = 500
MAX_LOG_OUTPUT_CHARS = 12000

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

_PROMPT_INJECTION_PATTERNS = [
    re.compile(
        r"\b(ignore|disregard|override|bypass)\b.{0,40}\b(previous|prior|system|developer|instruction)s?\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE),
    re.compile(r"\bdeveloper\s+message\b", re.IGNORECASE),
    re.compile(r"\b(tool|function)\s*(call|invocation)?\b", re.IGNORECASE),
    re.compile(r"\b(jailbreak|prompt injection)\b", re.IGNORECASE),
]

_LOG_REDACTION_PATTERNS = [
    (
        re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
        r"\1[REDACTED_TOKEN]",
    ),
    (
        re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*([^\s,;]+)"),
        r"\1=[REDACTED_SECRET]",
    ),
    (
        re.compile(r"(?i)\b(access[_-]?code)\b\s*[:=]\s*([^\s,;]+)"),
        r"\1=[REDACTED_SECRET]",
    ),
    (
        re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
        "[REDACTED_API_KEY]",
    ),
]


class PlannerInputError(ValueError):
    """Raised when planner request inputs are invalid."""


class PlannerRuntimeError(RuntimeError):
    """Raised when planner execution fails."""


class RealRunAccessError(PlannerInputError):
    """Raised when a visitor asks for a real paid run without authorization."""


def _strip_control_characters(value: str) -> str:
    return "".join(ch for ch in value if ch in {"\n", "\t"} or ch.isprintable())


def _normalize_whitespace(value: str) -> str:
    without_controls = _strip_control_characters(value)
    return re.sub(r"\s+", " ", without_controls).strip()


def _contains_prompt_injection(value: str) -> bool:
    lowered = value.strip()
    return any(pattern.search(lowered) for pattern in _PROMPT_INJECTION_PATTERNS)


def _validate_untrusted_text(
    value: str,
    *,
    field_name: str,
    max_length: int,
    allow_empty: bool = False,
    detect_injection: bool = True,
) -> str:
    normalized = _normalize_whitespace(value)
    if not normalized and not allow_empty:
        raise PlannerInputError(f"{field_name} is required.")
    if len(normalized) > max_length:
        raise PlannerInputError(f"{field_name} exceeds {max_length} characters.")
    if detect_injection and normalized and _contains_prompt_injection(normalized):
        raise PlannerInputError(
            f"{field_name} contains instruction-like content that is not allowed."
        )
    return normalized


def _sanitize_log_output(logs: str) -> str:
    redacted = logs
    for pattern, replacement in _LOG_REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    if len(redacted) > MAX_LOG_OUTPUT_CHARS:
        return redacted[:MAX_LOG_OUTPUT_CHARS] + "\n...[logs truncated for safety]..."
    return redacted


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
        _validate_untrusted_text(
            self.from_location,
            field_name="from_location",
            max_length=MAX_LOCATION_LENGTH,
            detect_injection=False,
        )
        _validate_untrusted_text(
            self.to_location,
            field_name="to_location",
            max_length=MAX_LOCATION_LENGTH,
            detect_injection=False,
        )
        _validate_untrusted_text(
            self.national_parks,
            field_name="national_parks",
            max_length=MAX_NATIONAL_PARKS_LENGTH,
        )
        if self.trip:
            _validate_untrusted_text(
                self.trip,
                field_name="trip",
                max_length=MAX_TRIP_SUMMARY_LENGTH,
            )
        departure = parse_iso_date(self.departure_date, "departure_date")
        returning = parse_iso_date(self.return_date, "return_date")
        if returning < departure:
            raise PlannerInputError("Return date must be on or after departure date.")
        if self.current_date:
            parse_iso_date(self.current_date, "current_date")


@dataclass(frozen=True)
class PlannerResult:
    markdown: str
    raw_result: object
    log_output: str


class _ThreadSafeLogBuffer:
    def __init__(self) -> None:
        self._buffer = io.StringIO()
        self._lock = threading.Lock()

    def write(self, value: str) -> int:
        with self._lock:
            return self._buffer.write(value)

    def flush(self) -> None:
        # redirect_stdout/redirect_stderr expect a flush method.
        return None

    def getvalue(self) -> str:
        with self._lock:
            return self._buffer.getvalue()


class _QueueStreamingWriter:
    """Child-process stream writer that batches and forwards logs to parent."""

    def __init__(self, out_queue: mp.queues.Queue, flush_threshold: int = 256) -> None:
        self._out_queue = out_queue
        self._flush_threshold = flush_threshold
        self._local_buffer = io.StringIO()
        self._pending = ""

    def write(self, value: str) -> int:
        if not value:
            return 0
        self._local_buffer.write(value)
        self._pending += value
        if "\n" in value or len(self._pending) >= self._flush_threshold:
            self._out_queue.put({"type": "log", "chunk": self._pending})
            self._pending = ""
        return len(value)

    def flush(self) -> None:
        if self._pending:
            self._out_queue.put({"type": "log", "chunk": self._pending})
            self._pending = ""
        return None

    def getvalue(self) -> str:
        return self._local_buffer.getvalue()


def _process_worker_kickoff(inputs: dict[str, str], out_queue: mp.queues.Queue) -> None:
    """Run crew kickoff in a killable child process."""
    writer = _QueueStreamingWriter(out_queue)
    try:
        from .crew import NationalParkCrew

        with redirect_stdout(writer), redirect_stderr(writer):
            raw_result = NationalParkCrew().crew().kickoff(inputs=inputs)
        writer.flush()
        out_queue.put(
            {
                "type": "result",
                "markdown": _extract_markdown(raw_result),
                # Avoid pickling complex CrewAI objects across process boundaries.
                "raw_result": str(raw_result),
                "logs": _sanitize_log_output(writer.getvalue()),
            }
        )
    except Exception:  # noqa: BLE001
        out_queue.put(
            {
                "type": "error",
                "message": "Planner run failed due to an internal error.",
            }
        )


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
        return _validate_untrusted_text(
            request.trip,
            field_name="trip",
            max_length=MAX_TRIP_SUMMARY_LENGTH,
        )
    from_location = _validate_untrusted_text(
        request.from_location,
        field_name="from_location",
        max_length=MAX_LOCATION_LENGTH,
        detect_injection=False,
    )
    to_location = _validate_untrusted_text(
        request.to_location,
        field_name="to_location",
        max_length=MAX_LOCATION_LENGTH,
        detect_injection=False,
    )
    return (
        f"I live in {from_location}. "
        f"I want to visit the National Parks near {to_location}."
    )


def build_kickoff_inputs(request: PlannerRequest) -> dict[str, str]:
    from_location = _validate_untrusted_text(
        request.from_location,
        field_name="from_location",
        max_length=MAX_LOCATION_LENGTH,
        detect_injection=False,
    )
    to_location = _validate_untrusted_text(
        request.to_location,
        field_name="to_location",
        max_length=MAX_LOCATION_LENGTH,
        detect_injection=False,
    )
    national_parks = _validate_untrusted_text(
        request.national_parks,
        field_name="national_parks",
        max_length=MAX_NATIONAL_PARKS_LENGTH,
    )
    departure_slug = request.departure_city_slug or slugify_location(from_location)
    arrival_slug = request.arrival_city_slug or slugify_location(to_location)
    current_date = request.current_date or str(datetime.now().date())

    return {
        "trip": build_trip_summary(request),
        "current_date": current_date,
        "from": from_location,
        "to": to_location,
        "departure_city": slugify_location(departure_slug),
        "arrival_city": slugify_location(arrival_slug),
        "national_parks": national_parks or DEFAULT_PARK_SCOPE,
        "departure_date": request.departure_date,
        "return_date": request.return_date,
    }


def itinerary_download_stem(request: PlannerRequest) -> str:
    """Suggested download filename stem (does not persist to disk)."""
    inputs = build_kickoff_inputs(request)
    return f"{inputs['departure_city']}_to_{inputs['arrival_city']}"


def _extract_markdown(raw_result: object) -> str:
    """Use the crew kickoff result only; do not read from the filesystem."""
    if isinstance(raw_result, str):
        return raw_result
    if raw_result is None:
        return "No itinerary output was returned by the crew."
    return str(raw_result)


def _env_flag_enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _runtime_timeout_seconds(
    env: Optional[dict[str, str]] = None,
    fallback: float = DEFAULT_MAX_RUNTIME_SECONDS,
) -> float:
    values = os.environ if env is None else env
    raw = str(values.get(MAX_RUNTIME_SECONDS_ENV, "")).strip()
    if not raw:
        return fallback
    try:
        parsed = float(raw)
    except ValueError:
        return fallback
    return parsed if parsed > 0 else fallback


def real_runs_enabled(env: Optional[dict[str, str]] = None) -> bool:
    """Whether REAL_RUNS_ENABLED is set (informational default; not required for access-code runs)."""
    values = os.environ if env is None else env
    return _env_flag_enabled(values.get(REAL_RUNS_ENABLED_ENV))


def real_run_access_configured(env: Optional[dict[str, str]] = None) -> bool:
    values = os.environ if env is None else env
    return bool(values.get(REAL_RUN_ACCESS_CODE_ENV, "").strip())


def real_run_access_denial_reason(
    access_code: str,
    env: Optional[dict[str, str]] = None,
) -> str | None:
    """Return a user-facing denial reason, or None when real runs are authorized.

    A valid access code authorizes a real run for that request only, even when
    REAL_RUNS_ENABLED is false (the default safe/demo deployment setting).
    """
    values = os.environ if env is None else env
    expected_code = values.get(REAL_RUN_ACCESS_CODE_ENV, "")
    submitted_code = access_code.strip()
    if not submitted_code:
        return "Access code is missing — running demo with mocked data instead."
    if not expected_code or not compare_digest(submitted_code, expected_code):
        return "Invalid access code — running demo with mocked data instead."
    return None


def validate_real_run_access(access_code: str, env: Optional[dict[str, str]] = None) -> None:
    denial = real_run_access_denial_reason(access_code, env=env)
    if denial is not None:
        raise RealRunAccessError(denial)


def load_demo_itinerary() -> str:
    return resources.files("national_park_crew.demo_data").joinpath("sample_itinerary.md").read_text(
        encoding="utf-8"
    )


def demo_planner_result() -> PlannerResult:
    return PlannerResult(
        markdown=load_demo_itinerary(),
        raw_result={"mode": "mocked_demo"},
        log_output="Demo mode used mocked itinerary data. CrewAI, OpenAI, and web tools were not called.",
    )


def iter_demo_planner_updates(
    _request: PlannerRequest,
    *,
    fallback_reason: str | None = None,
) -> Iterator[dict[str, object]]:
    if fallback_reason:
        phase = DEMO_FALLBACK_PHASE
        message = (
            f"{fallback_reason} Returning mocked itinerary data. "
            "No live AI, web search, or paid API calls are made."
        )
        logs = (
            f"Real run requested but access denied: {fallback_reason} "
            "Demo mode: mocked itinerary data returned from packaged sample content."
        )
    else:
        phase = DEMO_MODE_LABEL
        message = "Returning mocked itinerary data. No live AI, web search, or paid API calls are made."
        logs = "Demo mode: mocked itinerary data returned from packaged sample content."

    yield {
        "phase": phase,
        "message": message,
        "elapsed_seconds": 0,
        "logs": logs,
        "done": True,
        "result": demo_planner_result(),
    }


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

    log_buffer = _ThreadSafeLogBuffer()
    try:
        progress_callback("Running", "CrewAI agents are gathering flights, parks, and lodging data.")
        with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
            raw_result = crew_factory().crew().kickoff(inputs=inputs)
    except Exception as exc:  # noqa: BLE001 - we re-map to user-safe runtime error
        raise PlannerRuntimeError("Planner run failed due to an internal error.") from exc

    markdown = _extract_markdown(raw_result)
    progress_callback("Completed", "Itinerary generated successfully.")
    return PlannerResult(
        markdown=markdown,
        raw_result=raw_result,
        log_output=_sanitize_log_output(log_buffer.getvalue()),
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
    max_runtime_seconds: float | None = None,
) -> Iterator[dict[str, object]]:
    user_supplied_crew_factory = crew_factory is not None
    if crew_factory is None:
        from .crew import NationalParkCrew

        crew_factory = NationalParkCrew

    status = {"done": False, "result": None, "error": None}
    progress_events: list[tuple[str, str]] = [("Queued", "Validating inputs and preparing kickoff payload.")]
    log_buffer = _ThreadSafeLogBuffer()
    effective_timeout = (
        max_runtime_seconds
        if max_runtime_seconds is not None
        else _runtime_timeout_seconds()
    )

    def progress_callback(phase: str, message: str) -> None:
        progress_events.append((phase, message))

    started = time.time()
    worker_thread: threading.Thread | None = None
    worker_process: mp.Process | None = None
    process_queue: mp.queues.Queue | None = None

    if user_supplied_crew_factory:
        # Custom factories are useful in tests, but cannot be safely killed via
        # process termination without custom serialization contracts.
        def worker() -> None:
            try:
                inputs = build_kickoff_inputs(request)
                progress_callback("Running", "CrewAI agents are now executing tasks.")
                with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
                    raw_result = crew_factory().crew().kickoff(inputs=inputs)
                markdown = _extract_markdown(raw_result)
                status["result"] = PlannerResult(
                    markdown=markdown,
                    raw_result=raw_result,
                    log_output=_sanitize_log_output(log_buffer.getvalue()),
                )
                progress_callback("Completed", "Itinerary generated successfully.")
            except Exception:  # noqa: BLE001
                status["error"] = PlannerRuntimeError("Planner run failed due to an internal error.")
                progress_callback("Error", "Planner run failed. See details below.")
            finally:
                status["done"] = True

        worker_thread = threading.Thread(target=worker, daemon=True)
        worker_thread.start()
    else:
        inputs = build_kickoff_inputs(request)
        progress_callback("Running", "CrewAI agents are now executing tasks.")
        ctx = mp.get_context("spawn")
        process_queue = ctx.Queue()
        worker_process = ctx.Process(
            target=_process_worker_kickoff,
            args=(inputs, process_queue),
            daemon=True,
        )
        worker_process.start()

    last_event_index = 0
    last_phase = "Queued"
    last_message = "Validating inputs and preparing kickoff payload."
    while not status["done"]:
        elapsed_seconds = time.time() - started

        if worker_process is not None and process_queue is not None:
            while True:
                try:
                    payload = process_queue.get_nowait()
                except queue.Empty:
                    break
                msg_type = payload.get("type")
                if msg_type == "log":
                    log_buffer.write(str(payload.get("chunk", "")))
                elif msg_type == "result":
                    status["result"] = PlannerResult(
                        markdown=str(payload.get("markdown", "")),
                        raw_result=payload.get("raw_result"),
                        log_output=_sanitize_log_output(log_buffer.getvalue()),
                    )
                    progress_callback("Completed", "Itinerary generated successfully.")
                    status["done"] = True
                elif msg_type == "error":
                    status["error"] = PlannerRuntimeError(
                        str(payload.get("message") or "Planner run failed due to an internal error.")
                    )
                    progress_callback("Error", "Planner run failed. See details below.")
                    status["done"] = True

            if not status["done"] and worker_process.exitcode is not None:
                status["error"] = PlannerRuntimeError("Planner run stopped unexpectedly.")
                progress_callback("Error", "Planner process stopped unexpectedly.")
                status["done"] = True

        if elapsed_seconds > effective_timeout:
            status["error"] = PlannerRuntimeError(
                f"Planner run exceeded {int(effective_timeout)} seconds and was stopped."
            )
            progress_callback("Error", "Planner run timed out before completion.")
            if worker_process is not None and worker_process.is_alive():
                worker_process.terminate()
                worker_process.join(timeout=2)
                if worker_process.is_alive():
                    worker_process.kill()
                    worker_process.join(timeout=1)
            status["done"] = True
            break

        emitted_update = False
        while last_event_index < len(progress_events):
            phase, message = progress_events[last_event_index]
            elapsed = int(elapsed_seconds)
            raw_logs = log_buffer.getvalue()
            logs = _sanitize_log_output(raw_logs)
            inferred_phase = _detect_phase(raw_logs) if phase == "Running" else phase
            last_phase = inferred_phase
            last_message = message
            yield {
                "phase": inferred_phase,
                "message": message,
                "elapsed_seconds": elapsed,
                "logs": logs,
                "done": False,
            }
            last_event_index += 1
            emitted_update = True
        if not emitted_update:
            # Heartbeat update so elapsed time keeps advancing in UI even when
            # no new phase event has been pushed yet.
            yield {
                "phase": _detect_phase(log_buffer.getvalue())
                if last_phase == "Running"
                else last_phase,
                "message": last_message,
                "elapsed_seconds": int(time.time() - started),
                "logs": _sanitize_log_output(log_buffer.getvalue()),
                "done": False,
            }
        time.sleep(poll_seconds)

    if worker_process is not None:
        worker_process.join(timeout=0.5)

    final_logs = _sanitize_log_output(log_buffer.getvalue())
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


def iter_planner_updates_for_mode(
    request: PlannerRequest,
    run_mode: str,
    access_code: str,
    poll_seconds: float = 1.0,
    crew_factory: Optional[Callable[[], object]] = None,
    env: Optional[dict[str, str]] = None,
) -> Iterator[dict[str, object]]:
    if run_mode == REAL_MODE_LABEL:
        denial = real_run_access_denial_reason(access_code, env=env)
        if denial is not None:
            yield from iter_demo_planner_updates(request, fallback_reason=denial)
            return
        yield from iter_planner_updates(
            request,
            poll_seconds=poll_seconds,
            crew_factory=crew_factory,
        )
        return

    yield from iter_demo_planner_updates(request)
