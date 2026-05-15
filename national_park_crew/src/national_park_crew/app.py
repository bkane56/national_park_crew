from __future__ import annotations

from datetime import date, timedelta
import re
from typing import Optional

import gradio as gr

from .planner_service import (
    DEFAULT_PARK_SCOPE,
    PlannerInputError,
    PlannerRequest,
    PlannerRuntimeError,
    iter_planner_updates,
)


EXAMPLE_FROM = "Venice, Florida"
EXAMPLE_TO = "Salt Lake City, Utah area"

_ACTIVITY_RULES = [
    (re.compile(r"\bflight|airline|fare|layover|nonstop\b", re.IGNORECASE), "Checking flight options and prices."),
    (re.compile(r"\bhotel|lodging|accommodation|room|stay\b", re.IGNORECASE), "Checking accommodations near parks."),
    (re.compile(r"\bairport|iata|departure|arrival\b", re.IGNORECASE), "Validating airport options for route feasibility."),
    (re.compile(r"\bnational park|trail|activity|itinerary day|day \d+\b", re.IGNORECASE), "Planning park activities and pacing."),
    (re.compile(r"\breport|markdown|write|summary\b", re.IGNORECASE), "Composing the final itinerary report."),
]


def _safe_download_path(path: Optional[object]) -> Optional[str]:
    if path is None:
        return None
    return str(path)


def _phase_message(phase: str) -> str:
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


def _append_timeline_event(timeline: list[str], message: str) -> None:
    if not timeline or timeline[-1] != message:
        timeline.append(message)


def _extract_events_from_new_logs(new_log_chunk: str) -> list[str]:
    events: list[str] = []
    for pattern, message in _ACTIVITY_RULES:
        if pattern.search(new_log_chunk):
            events.append(message)
    flight_count_match = re.search(r"\b(\d+)\s+flights?\b", new_log_chunk, re.IGNORECASE)
    if flight_count_match:
        events.append(f"Found {flight_count_match.group(1)} candidate flights in current search pass.")
    return events


def _detect_current_action(phase: str, logs: str) -> str:
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


def _build_activity_log(timeline: list[str], phase: str, elapsed: int, logs: str) -> str:
    recent = timeline[-8:] if timeline else [_phase_message(phase)]
    lines = "\n".join(f"- {item}" for item in recent)
    heartbeat = f"Still working on: {phase} (elapsed {elapsed}s)"
    current_action = _detect_current_action(phase, logs)
    return (
        f"Current action: {current_action}\n\n"
        "Activity feed:\n"
        f"{lines}\n"
        f"- {heartbeat}\n\n"
        "(Updates every ~5 seconds while the crew is running.)"
    )


def _build_request(
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


def run_from_ui(
    from_location: str,
    to_location: str,
    departure_date: str,
    return_date: str,
    trip_summary: str,
    park_scope: str,
    departure_slug: str,
    arrival_slug: str,
):
    try:
        request = _build_request(
            from_location,
            to_location,
            departure_date,
            return_date,
            trip_summary,
            park_scope,
            departure_slug,
            arrival_slug,
        )
    except PlannerInputError as exc:
        message = f"Input validation failed: {exc}"
        yield message, "", "", None
        return

    try:
        timeline: list[str] = ["Queued request and validating inputs."]
        previous_phase = "Queued"
        processed_log_length = 0
        for update in iter_planner_updates(request, poll_seconds=5.0):
            phase = update["phase"]
            message = update["message"]
            elapsed = update["elapsed_seconds"]
            logs = str(update["logs"]).strip()

            if phase != previous_phase:
                _append_timeline_event(timeline, _phase_message(phase))
                previous_phase = phase
            else:
                _append_timeline_event(timeline, message)

            current_log_length = len(logs)
            if current_log_length > processed_log_length:
                new_chunk = logs[processed_log_length:current_log_length]
                for event in _extract_events_from_new_logs(new_chunk):
                    _append_timeline_event(timeline, event)
                processed_log_length = current_log_length

            status_block = f"**Phase:** {phase}\n\n**Status:** {message}\n\n**Elapsed:** {elapsed}s"
            log_block = _build_activity_log(timeline, phase, elapsed, logs)

            if update["done"]:
                result = update["result"]
                output_file = _safe_download_path(result.output_path)
                yield status_block, result.markdown, log_block, output_file
            else:
                yield status_block, "", log_block, None
    except (PlannerRuntimeError, PlannerInputError) as exc:
        yield f"Planner error: {exc}", "", "", None


def default_dates() -> tuple[str, str]:
    departure = date.today() + timedelta(days=35)
    returning = departure + timedelta(days=9)
    return departure.isoformat(), returning.isoformat()


def example_trip_summary() -> str:
    return (
        "I live in Venice, Florida and I want a practical national park itinerary near "
        "Salt Lake City with a balanced pace and clear travel logistics."
    )


def build_app() -> gr.Blocks:
    departure_default, return_default = default_dates()
    with gr.Blocks(
        title="National Park Crew Planner",
        theme=gr.themes.Soft(),
        css=".gradio-container {max-width: 980px !important; margin: auto !important;}",
    ) as app:
        gr.Markdown("# National Park Trip Planner")
        gr.Markdown(
            "Plan a multi-agent itinerary with flights, lodging, park activities, and a final report. "
            "This demo is for portfolio evaluation and educational use."
        )
        gr.Markdown(
            "**Runtime note:** CrewAI runs can take several minutes depending on research/tool calls. "
            "Recent runs have taken up to ~8 min 30 sec."
        )
        gr.Markdown(
            "_Outputs are AI-generated and may be incorrect or outdated. Always verify prices, schedules, and availability._"
        )

        with gr.Row():
            from_location = gr.Textbox(label="From (City, State)", value=EXAMPLE_FROM)
            to_location = gr.Textbox(label="To (Destination Region)", value=EXAMPLE_TO)
        with gr.Row():
            departure_date = gr.Textbox(label="Departure Date (YYYY-MM-DD)", value=departure_default)
            return_date = gr.Textbox(label="Return Date (YYYY-MM-DD)", value=return_default)
        trip_summary = gr.Textbox(
            label="Trip Summary",
            lines=3,
            value=example_trip_summary(),
            info="Optional. Leave as-is or customize the planning context.",
        )
        park_scope = gr.Textbox(
            label="National Parks Scope",
            lines=3,
            value=DEFAULT_PARK_SCOPE,
            info="Advanced users can narrow or expand target parks.",
        )

        with gr.Accordion("Power User Options", open=False):
            with gr.Row():
                departure_slug = gr.Textbox(
                    label="Departure airport key (optional)",
                    placeholder="Florida_Gulf_Coast",
                    info="Optional power-user field. Leave blank unless you want to control the output filename key.",
                )
                arrival_slug = gr.Textbox(
                    label="Arrival airport key (optional)",
                    placeholder="Salt_Lake_City_UT",
                    info="Optional power-user field. Leave blank unless you want to control the output filename key.",
                )

        with gr.Row():
            run_button = gr.Button("Generate Itinerary", variant="primary")
            reset_button = gr.Button("Reset Example")

        status_output = gr.Markdown(label="Status")
        itinerary_output = gr.Markdown(label="Itinerary")
        logs_output = gr.Textbox(label="Execution Logs", lines=12)
        download_output = gr.File(label="Generated Itinerary File")

        run_button.click(
            run_from_ui,
            inputs=[
                from_location,
                to_location,
                departure_date,
                return_date,
                trip_summary,
                park_scope,
                departure_slug,
                arrival_slug,
            ],
            outputs=[status_output, itinerary_output, logs_output, download_output],
        )

        reset_button.click(
            lambda: [
                EXAMPLE_FROM,
                EXAMPLE_TO,
                *default_dates(),
                example_trip_summary(),
                DEFAULT_PARK_SCOPE,
                "",
                "",
                "Ready to run example.",
                "",
                "",
                None,
            ],
            outputs=[
                from_location,
                to_location,
                departure_date,
                return_date,
                trip_summary,
                park_scope,
                departure_slug,
                arrival_slug,
                status_output,
                itinerary_output,
                logs_output,
                download_output,
            ],
        )

    return app


def launch() -> None:
    app = build_app()
    app.queue()
    app.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    launch()
