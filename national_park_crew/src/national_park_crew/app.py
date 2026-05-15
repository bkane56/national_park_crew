from __future__ import annotations

from datetime import date, timedelta
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


def _safe_download_path(path: Optional[object]) -> Optional[str]:
    if path is None:
        return None
    return str(path)


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
        for update in iter_planner_updates(request):
            phase = update["phase"]
            message = update["message"]
            elapsed = update["elapsed_seconds"]
            logs = str(update["logs"]).strip()
            status_block = f"**Phase:** {phase}\n\n**Status:** {message}\n\n**Elapsed:** {elapsed}s"
            log_block = logs[-5000:] if logs else "Waiting for logs..."

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
            "_Outputs are AI-generated and may be incorrect or outdated. Always verify prices, schedules, and availability._"
        )

        with gr.Row():
            from_location = gr.Textbox(label="From (city, state)", value=EXAMPLE_FROM)
            to_location = gr.Textbox(label="To (destination region)", value=EXAMPLE_TO)
        with gr.Row():
            departure_date = gr.Textbox(label="Departure date (YYYY-MM-DD)", value=departure_default)
            return_date = gr.Textbox(label="Return date (YYYY-MM-DD)", value=return_default)
        trip_summary = gr.Textbox(
            label="Trip summary",
            lines=3,
            value=example_trip_summary(),
            info="Optional. Leave as-is or customize the planning context.",
        )
        park_scope = gr.Textbox(
            label="National parks scope",
            lines=3,
            value=DEFAULT_PARK_SCOPE,
            info="Advanced users can narrow or expand target parks.",
        )

        with gr.Accordion("Advanced options", open=False):
            with gr.Row():
                departure_slug = gr.Textbox(
                    label="Departure slug override",
                    placeholder="Florida_Gulf_Coast",
                )
                arrival_slug = gr.Textbox(
                    label="Arrival slug override",
                    placeholder="Salt_Lake_City_UT",
                )

        with gr.Row():
            run_button = gr.Button("Generate itinerary", variant="primary")
            reset_button = gr.Button("Reset example")

        status_output = gr.Markdown(label="Status")
        itinerary_output = gr.Markdown(label="Itinerary")
        logs_output = gr.Textbox(label="Execution logs", lines=12)
        download_output = gr.File(label="Generated itinerary file")

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
