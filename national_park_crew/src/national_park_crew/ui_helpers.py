from __future__ import annotations

from datetime import date, timedelta
import re

from .planner_service import PlannerRequest

EXAMPLE_FROM = "Venice, Florida"
EXAMPLE_TO = "Salt Lake City, Utah area"

FORMAT_MARKDOWN = "Markdown (.md)"
FORMAT_PDF = "PDF (.pdf)"

_ACTIVITY_RULES = [
    (re.compile(r"\bflight|airline|fare|layover|nonstop\b", re.IGNORECASE), "Checking flight options and prices."),
    (re.compile(r"\bhotel|lodging|accommodation|room|stay\b", re.IGNORECASE), "Checking accommodations near parks."),
    (re.compile(r"\bairport|iata|departure|arrival\b", re.IGNORECASE), "Validating airport options for route feasibility."),
    (re.compile(r"\bnational park|trail|activity|itinerary day|day \d+\b", re.IGNORECASE), "Planning park activities and pacing."),
    (re.compile(r"\breport|markdown|write|summary\b", re.IGNORECASE), "Composing the final itinerary report."),
]


def phase_message(phase: str) -> str:
    phase_map = {
        "Queued": "Queued request and validating inputs.",
        "General research": "Scoping parks, airports, and trip constraints.",
        "Flight research": "Looking up route-specific flight options.",
        "Accommodations": "Evaluating accommodations near selected parks.",
        "Park activity planning": "Sequencing park activities and travel pacing.",
        "Report generation": "Generating the final itinerary write-up.",
        "Completed": "Finalizing output and preparing download.",
    }
    return phase_map.get(phase, "Processing current planning step.")


def append_timeline_event(timeline: list[str], message: str) -> None:
    if not timeline or timeline[-1] != message:
        timeline.append(message)


def extract_events_from_new_logs(new_log_chunk: str) -> list[str]:
    events: list[str] = []
    for pattern, message in _ACTIVITY_RULES:
        if pattern.search(new_log_chunk):
            events.append(message)
    flight_count_match = re.search(r"\b(\d+)\s+flights?\b", new_log_chunk, re.IGNORECASE)
    if flight_count_match:
        events.append(f"Found {flight_count_match.group(1)} candidate flights in current search pass.")
    return events


def detect_current_action(phase: str, logs: str) -> str:
    if phase == "Flight research":
        route_match = re.search(
            r"\bfrom\s+([A-Z]{3}|[A-Za-z][A-Za-z\s,]+)\s+to\s+([A-Z]{3}|[A-Za-z][A-Za-z\s,]+)\b",
            logs,
            re.IGNORECASE,
        )
        if route_match:
            origin = route_match.group(1).strip()
            destination = route_match.group(2).strip()
            return f"Querying route options from {origin} to {destination}."
        return "Searching scoped flight routes and comparing fares."
    if phase == "General research":
        return "Determining viable commercial airports and park region scope."
    if phase == "Accommodations":
        return "Checking lodging candidates near selected parks."
    if phase == "Park activity planning":
        return "Building day-by-day park plan and activity order."
    if phase == "Report generation":
        return "Writing and formatting the final itinerary report."
    if phase == "Completed":
        return "Packaging final output for display/download."
    return "Processing current crew step."


def build_activity_log(timeline: list[str], phase: str, elapsed: int, logs: str) -> str:
    recent = timeline[-8:] if timeline else [phase_message(phase)]
    lines = "\n".join(f"- {item}" for item in recent)
    heartbeat = f"Still working on: {phase} (elapsed {elapsed}s)"
    current_action = detect_current_action(phase, logs)
    return (
        f"Current action: {current_action}\n\n"
        "Activity feed:\n"
        f"{lines}\n"
        f"- {heartbeat}\n\n"
        "(Updates every ~5 seconds while the crew is running.)"
    )


def build_request(
    from_location: str,
    to_location: str,
    departure_date: str,
    return_date: str,
    trip_summary: str,
    park_scope: str,
    departure_slug: str,
    arrival_slug: str,
) -> PlannerRequest:
    return PlannerRequest(
        from_location=from_location,
        to_location=to_location,
        departure_date=departure_date,
        return_date=return_date,
        trip=trip_summary,
        national_parks=park_scope,
        departure_city_slug=departure_slug or None,
        arrival_city_slug=arrival_slug or None,
    )


def default_dates() -> tuple[str, str]:
    departure = date.today() + timedelta(days=35)
    returning = departure + timedelta(days=9)
    return departure.isoformat(), returning.isoformat()


def example_trip_summary() -> str:
    return (
        "I live in Venice, Florida and I want a practical national park itinerary near "
        "Salt Lake City with a balanced pace and clear travel logistics."
    )
