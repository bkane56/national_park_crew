from __future__ import annotations

from dataclasses import dataclass

from national_park_crew.app import access_code_visibility_update, build_app
from national_park_crew.planner_service import DEMO_MODE_LABEL, REAL_MODE_LABEL
from national_park_crew.theme import APP_CSS, PARK_THEME, THEME_DEFAULT_MODE, THEME_MODE_CHOICES, THEME_STORAGE_KEY
from national_park_crew.ui_handlers import run_from_ui


def test_build_app_constructs_without_error() -> None:
    app = build_app()
    assert app is not None


def test_park_theme_is_customized_base_theme() -> None:
    assert PARK_THEME.name == "base"
    assert THEME_MODE_CHOICES == ["Light", "Dark", "System"]
    assert THEME_DEFAULT_MODE == "Light"
    assert THEME_STORAGE_KEY == "npc-theme"
    assert "max-width: 1400px" in APP_CSS
    assert 'data-npc-theme="light"' in APP_CSS


def test_access_code_visibility_update() -> None:
    demo_update = access_code_visibility_update(DEMO_MODE_LABEL)
    real_update = access_code_visibility_update(REAL_MODE_LABEL)

    assert demo_update["visible"] is False
    assert real_update["visible"] is True


def test_run_from_ui_validation_error() -> None:
    rows = list(
        run_from_ui(
            "",
            "Salt Lake City, Utah area",
            "2026-07-18",
            "2026-07-27",
            "Trip summary",
            "parks",
            "",
            "",
            DEMO_MODE_LABEL,
            "",
            "Markdown (.md)",
        )
    )
    assert rows
    status, itinerary, logs, payload, download = rows[0]
    assert "Input validation failed" in status
    assert itinerary == ""
    assert logs == ""
    assert payload == {}
    assert download is None


@dataclass
class _FakeResult:
    markdown: str


def test_run_from_ui_handles_missing_final_result(monkeypatch) -> None:
    def fake_updates(*_args, **_kwargs):
        yield {
            "phase": "Completed",
            "message": "done",
            "elapsed_seconds": 1,
            "logs": "",
            "done": True,
            "result": None,
        }

    monkeypatch.setattr("national_park_crew.ui_handlers.iter_planner_updates_for_mode", fake_updates)

    rows = list(
        run_from_ui(
            "Venice, Florida",
            "Salt Lake City, Utah area",
            "2026-07-18",
            "2026-07-27",
            "Trip summary",
            "parks",
            "",
            "",
            REAL_MODE_LABEL,
            "valid-code",
            "Markdown (.md)",
        )
    )

    assert rows
    status, itinerary, logs, payload, download = rows[-1]
    assert "Planner error" in status
    assert itinerary == ""
    assert logs == ""
    assert payload == {}
    assert download is None


def test_run_from_ui_generates_output(monkeypatch, tmp_path) -> None:
    def fake_updates(*_args, **_kwargs):
        yield {
            "phase": "Completed",
            "message": "Workflow finished",
            "elapsed_seconds": 2,
            "logs": "report generated",
            "done": True,
            "result": _FakeResult(markdown="# Itinerary\n\nHello"),
        }

    def fake_download(markdown_text: str, stem: str, _format: str) -> str:
        out = tmp_path / f"{stem}.md"
        out.write_text(markdown_text, encoding="utf-8")
        return str(out)

    monkeypatch.setattr("national_park_crew.ui_handlers.iter_planner_updates_for_mode", fake_updates)
    monkeypatch.setattr("national_park_crew.ui_handlers.build_download_file", fake_download)

    rows = list(
        run_from_ui(
            "Venice, Florida",
            "Salt Lake City, Utah area",
            "2026-07-18",
            "2026-07-27",
            "Trip summary",
            "parks",
            "",
            "",
            DEMO_MODE_LABEL,
            "",
            "Markdown (.md)",
        )
    )

    status, itinerary, logs, payload, download = rows[-1]
    assert "Phase" in status
    assert itinerary.startswith("# Itinerary")
    assert "Activity feed" in logs
    assert payload["markdown"].startswith("# Itinerary")
    assert payload["stem"]
    assert download is not None
