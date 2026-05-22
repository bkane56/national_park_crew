from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import inspect
import re
import gradio as gr
from dotenv import load_dotenv

from .export_utils import build_download_file
from .assets import PARKS_IMAGE_DIR, park_collage_paths
from .theme import (
    APP_CSS,
    PARK_THEME,
    THEME_CHANGE_JS,
    THEME_DEFAULT_MODE,
    THEME_HEAD,
    THEME_INIT_JS,
    THEME_LOAD_JS,
    THEME_MODE_CHOICES,
)
from .planner_service import (
    DEFAULT_PARK_SCOPE,
    DEMO_MODE_LABEL,
    PlannerInputError,
    PlannerRequest,
    PlannerRuntimeError,
    REAL_MODE_LABEL,
    real_run_access_configured,
    iter_planner_updates_for_mode,
    itinerary_download_stem,
)


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


def refresh_download(payload: dict, format_choice: str) -> str | None:
    """Rebuild exported file when the user switches format after a run completes."""
    if not payload or not str(payload.get("markdown", "")).strip():
        return None
    return build_download_file(
        str(payload["markdown"]),
        str(payload.get("stem") or "itinerary"),
        format_choice,
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
    run_mode: str,
    access_code: str,
    download_format: str,
):
    empty_payload: dict[str, str] = {}
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
        yield message, "", "", empty_payload, None
        return

    try:
        timeline: list[str] = ["Queued request and validating inputs."]
        previous_phase = "Queued"
        processed_log_length = 0
        for update in iter_planner_updates_for_mode(
            request,
            run_mode=run_mode,
            access_code=access_code,
            poll_seconds=5.0,
        ):
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
                stem = itinerary_download_stem(request)
                payload: dict[str, str] = {"markdown": result.markdown, "stem": stem}
                path = build_download_file(result.markdown, stem, download_format)
                yield status_block, result.markdown, log_block, payload, path
            else:
                yield status_block, "", log_block, empty_payload, None
    except (PlannerRuntimeError, PlannerInputError) as exc:
        yield f"Planner error: {exc}", "", "", empty_payload, None


def default_dates() -> tuple[str, str]:
    departure = date.today() + timedelta(days=35)
    returning = departure + timedelta(days=9)
    return departure.isoformat(), returning.isoformat()


def example_trip_summary() -> str:
    return (
        "I live in Venice, Florida and I want a practical national park itinerary near "
        "Salt Lake City with a balanced pace and clear travel logistics."
    )


def access_code_visibility_update(run_mode: str):
    """Show access code field only for real planning runs."""
    return gr.update(visible=run_mode == REAL_MODE_LABEL)


def build_app() -> gr.Blocks:
    departure_default, return_default = default_dates()
    access_code_configured = real_run_access_configured()
    run_mode_info = (
        "Demo mode returns mocked UI data. Real mode requires a private access code and may use paid API calls. "
        "A valid code authorizes one real run even when REAL_RUNS_ENABLED is false."
    )

    with gr.Blocks(
        title="National Park Crew Planner",
        theme=PARK_THEME,
        css=APP_CSS,
        head=THEME_HEAD,
        js=THEME_INIT_JS,
    ) as app:
        collage_paths = park_collage_paths()
        if collage_paths:
            gr.Gallery(
                value=collage_paths,
                columns=min(len(collage_paths), 4),
                rows=1,
                height=180,
                object_fit="cover",
                interactive=False,
                allow_preview=False,
                show_label=False,
                container=False,
                elem_id="npc-park-collage",
            )

        with gr.Row(elem_id="npc-header-row"):
            gr.Markdown("# National Park Trip Planner", elem_id="npc-title")
            theme_mode = gr.Radio(
                choices=THEME_MODE_CHOICES,
                value=THEME_DEFAULT_MODE,
                show_label=False,
                container=False,
                elem_id="npc-appearance",
                scale=0,
                min_width=248,
            )

        gr.Markdown(
            "Plan a multi-agent itinerary with flights, lodging, park activities, and a final report. "
            "This demo is for portfolio evaluation and educational use."
        )
        gr.Markdown(
            "**Public demo mode uses mocked itinerary data.** It does not run live AI, web search, "
            "or paid API calls. Real CrewAI planning runs require a private access code from the project owner."
        )
        if access_code_configured:
            gr.Markdown(
                "**Real planning runs are available with a private access code.** "
                "Leave demo mode selected for mocked data, or choose real mode and enter the code for a one-time live run."
            )
        else:
            gr.Markdown(
                "**Real planning runs are not configured on this deployment** "
                "(set REAL_RUN_ACCESS_CODE in secrets). Real mode without a valid code returns mocked demo data."
            )
        gr.Markdown(
            "**Runtime note:** CrewAI runs can take several minutes depending on research/tool calls. "
            "Recent runs have taken up to ~8 min 30 sec."
        )
        gr.Markdown(
            "_Outputs are AI-generated and may be incorrect or outdated. Always verify prices, schedules, and availability._"
        )

        with gr.Row(elem_id="npc-locations-row"):
            from_location = gr.Textbox(label="From (City, State)", value=EXAMPLE_FROM)
            to_location = gr.Textbox(label="To (Destination Region)", value=EXAMPLE_TO)
        with gr.Row(elem_id="npc-dates-row"):
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
        run_mode = gr.Radio(
            choices=[DEMO_MODE_LABEL, REAL_MODE_LABEL],
            value=DEMO_MODE_LABEL,
            label="Run mode",
            info=run_mode_info,
        )
        access_code = gr.Textbox(
            label="Access code for real planning runs",
            type="password",
            placeholder="Enter the private access code from the project owner",
            visible=False,
            info=(
                "Required when selecting real mode. The .env value is the expected code on the server; "
                "you must type it here (it is not applied automatically)."
            ),
        )

        with gr.Accordion("Power User Options", open=False):
            with gr.Row(elem_id="npc-power-user-row"):
                departure_slug = gr.Textbox(
                    label="Departure airport key (optional)",
                    placeholder="Florida_Gulf_Coast",
                    info="Optional. Used for the suggested download filename stem (not written to the repo).",
                )
                arrival_slug = gr.Textbox(
                    label="Arrival airport key (optional)",
                    placeholder="Salt_Lake_City_UT",
                    info="Optional. Used for the suggested download filename stem (not written to the repo).",
                )

        with gr.Row(elem_id="npc-actions-row"):
            run_button = gr.Button("Generate Itinerary", variant="primary")
            reset_button = gr.Button("Reset Example")

        status_output = gr.Markdown(label="Status")
        itinerary_output = gr.Markdown(label="Itinerary")
        logs_output = gr.Textbox(label="Execution Logs", lines=12)
        itinerary_payload = gr.State({})
        download_format = gr.Radio(
            choices=[FORMAT_MARKDOWN, FORMAT_PDF],
            value=FORMAT_MARKDOWN,
            label="Download format",
            info="Choose Markdown for editing, or PDF for sharing. You can switch after a run completes without re-running.",
        )
        download_output = gr.File(label="Download itinerary")

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
                run_mode,
                access_code,
                download_format,
            ],
            outputs=[status_output, itinerary_output, logs_output, itinerary_payload, download_output],
        )

        download_format.change(
            refresh_download,
            inputs=[itinerary_payload, download_format],
            outputs=[download_output],
        )
        run_mode.change(
            access_code_visibility_update,
            inputs=[run_mode],
            outputs=[access_code],
            queue=False,
        )

        reset_button.click(
            lambda: [
                EXAMPLE_FROM,
                EXAMPLE_TO,
                *default_dates(),
                example_trip_summary(),
                DEFAULT_PARK_SCOPE,
                DEMO_MODE_LABEL,
                gr.update(value="", visible=False),
                "",
                "",
                FORMAT_MARKDOWN,
                "Ready to run example.",
                "",
                "",
                {},
                None,
            ],
            outputs=[
                from_location,
                to_location,
                departure_date,
                return_date,
                trip_summary,
                park_scope,
                run_mode,
                access_code,
                departure_slug,
                arrival_slug,
                download_format,
                status_output,
                itinerary_output,
                logs_output,
                itinerary_payload,
                download_output,
            ],
        )

        app.load(
            access_code_visibility_update,
            inputs=[run_mode],
            outputs=[access_code],
            queue=False,
        )
        app.load(None, None, [theme_mode], js=THEME_LOAD_JS, queue=False)
        theme_mode.change(
            None,
            inputs=[theme_mode],
            js=THEME_CHANGE_JS,
            queue=False,
        )
        theme_mode.input(
            None,
            inputs=[theme_mode],
            js=THEME_CHANGE_JS,
            queue=False,
        )

    return app


def launch() -> None:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
    app = build_app()
    app.queue()
    supported_launch_params = inspect.signature(app.launch).parameters
    launch_kwargs = {
        key: value
        for key, value in {
            "server_name": "0.0.0.0",
            "server_port": 7860,
            "allowed_paths": [str(PARKS_IMAGE_DIR.resolve())],
        }.items()
        if key in supported_launch_params
    }
    app.launch(**launch_kwargs)


if __name__ == "__main__":
    launch()
