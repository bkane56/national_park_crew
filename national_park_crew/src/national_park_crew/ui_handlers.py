from __future__ import annotations

import gradio as gr

from .export_utils import build_download_file
from .planner_service import (
    DEMO_MODE_LABEL,
    PlannerInputError,
    PlannerRuntimeError,
    REAL_MODE_LABEL,
    iter_planner_updates_for_mode,
    itinerary_download_stem,
)
from .ui_helpers import (
    append_timeline_event,
    build_activity_log,
    build_request,
    extract_events_from_new_logs,
    phase_message,
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
        request = build_request(
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
                append_timeline_event(timeline, phase_message(phase))
                previous_phase = phase
            else:
                append_timeline_event(timeline, message)

            current_log_length = len(logs)
            if current_log_length > processed_log_length:
                new_chunk = logs[processed_log_length:current_log_length]
                for event in extract_events_from_new_logs(new_chunk):
                    append_timeline_event(timeline, event)
                processed_log_length = current_log_length

            status_block = f"**Phase:** {phase}\n\n**Status:** {message}\n\n**Elapsed:** {elapsed}s"
            log_block = build_activity_log(timeline, phase, elapsed, logs)

            if update["done"]:
                result = update.get("result")
                if result is None:
                    raise PlannerRuntimeError("Planner finished without a final itinerary result.")
                stem = itinerary_download_stem(request)
                payload: dict[str, str] = {"markdown": result.markdown, "stem": stem}
                path = build_download_file(result.markdown, stem, download_format)
                yield status_block, result.markdown, log_block, payload, path
            else:
                yield status_block, "", log_block, empty_payload, None
    except (PlannerRuntimeError, PlannerInputError) as exc:
        yield f"Planner error: {exc}", "", "", empty_payload, None


def access_code_visibility_update(run_mode: str):
    """Show access code field only for real planning runs."""
    return gr.update(visible=run_mode == REAL_MODE_LABEL)


__all__ = [
    "access_code_visibility_update",
    "refresh_download",
    "run_from_ui",
    "DEMO_MODE_LABEL",
    "REAL_MODE_LABEL",
]
