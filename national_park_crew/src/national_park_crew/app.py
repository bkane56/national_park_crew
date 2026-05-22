from __future__ import annotations

from pathlib import Path
import inspect
import gradio as gr
from dotenv import load_dotenv

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
    REAL_MODE_LABEL,
    real_run_access_configured,
)
from .ui_handlers import access_code_visibility_update, refresh_download, run_from_ui
from .ui_helpers import (
    EXAMPLE_FROM,
    EXAMPLE_TO,
    FORMAT_MARKDOWN,
    FORMAT_PDF,
    default_dates,
    example_trip_summary,
)


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
