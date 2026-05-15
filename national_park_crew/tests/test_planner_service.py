from __future__ import annotations

from pathlib import Path

import pytest

from national_park_crew.planner_service import (
    PlannerInputError,
    PlannerRequest,
    PlannerRuntimeError,
    build_kickoff_inputs,
    build_trip_summary,
    iter_planner_updates,
    parse_iso_date,
    run_planner,
    slugify_location,
)


class DummyCrew:
    def __init__(self, result: object = "Generated markdown", error: Exception | None = None):
        self.result = result
        self.error = error

    def kickoff(self, inputs: dict[str, str]) -> object:
        if self.error:
            raise self.error
        return self.result


class DummyNationalParkCrew:
    def __init__(self, result: object = "Generated markdown", error: Exception | None = None):
        self._crew = DummyCrew(result=result, error=error)

    def crew(self) -> DummyCrew:
        return self._crew


def sample_request() -> PlannerRequest:
    return PlannerRequest(
        from_location="Venice, Florida",
        to_location="Salt Lake City, Utah area",
        departure_date="2026-07-18",
        return_date="2026-07-27",
        trip="Trip summary",
        departure_city_slug="Florida_Gulf_Coast",
        arrival_city_slug="Salt_Lake_City_UT",
    )


def test_parse_iso_date_invalid() -> None:
    with pytest.raises(PlannerInputError):
        parse_iso_date("07/18/2026", "departure_date")


def test_slugify_location() -> None:
    assert slugify_location("Salt Lake City, Utah area") == "Salt_Lake_City_Utah_area"


def test_slugify_location_empty_raises() -> None:
    with pytest.raises(PlannerInputError):
        slugify_location("   ")


def test_planner_request_date_validation() -> None:
    with pytest.raises(PlannerInputError):
        PlannerRequest(
            from_location="Venice, Florida",
            to_location="Salt Lake City, Utah area",
            departure_date="2026-07-27",
            return_date="2026-07-18",
        )


def test_build_trip_summary_fallback() -> None:
    req = PlannerRequest(
        from_location="Venice, Florida",
        to_location="Salt Lake City, Utah area",
        departure_date="2026-07-18",
        return_date="2026-07-27",
        trip="",
    )
    assert "I live in Venice, Florida." in build_trip_summary(req)


def test_build_kickoff_inputs_defaults_and_overrides() -> None:
    req = sample_request()
    payload = build_kickoff_inputs(req)
    assert payload["from"] == "Venice, Florida"
    assert payload["to"] == "Salt Lake City, Utah area"
    assert payload["departure_city"] == "Florida_Gulf_Coast"
    assert payload["arrival_city"] == "Salt_Lake_City_UT"
    assert payload["departure_date"] == "2026-07-18"
    assert payload["return_date"] == "2026-07-27"
    assert payload["trip"] == "Trip summary"


def test_run_planner_success_with_string_result() -> None:
    result = run_planner(sample_request(), crew_factory=lambda: DummyNationalParkCrew(result="# Itinerary"))
    assert "# Itinerary" in result.markdown
    assert result.output_path is None


def test_run_planner_reads_generated_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    itinerary_dir = tmp_path / "itinerary"
    itinerary_dir.mkdir(parents=True)
    expected_file = itinerary_dir / "Florida_Gulf_Coast_to_Salt_Lake_City_UT.md"
    expected_file.write_text("file content", encoding="utf-8")

    result = run_planner(sample_request(), crew_factory=lambda: DummyNationalParkCrew(result="ignored"))
    assert result.markdown == "file content"
    assert result.output_path is not None
    assert result.output_path.resolve() == expected_file.resolve()


def test_run_planner_maps_runtime_error() -> None:
    with pytest.raises(PlannerRuntimeError):
        run_planner(sample_request(), crew_factory=lambda: DummyNationalParkCrew(error=RuntimeError("boom")))


def test_iter_planner_updates_success() -> None:
    updates = list(
        iter_planner_updates(
            sample_request(),
            poll_seconds=0.01,
            crew_factory=lambda: DummyNationalParkCrew(result="stream result"),
        )
    )
    assert updates[-1]["done"] is True
    assert updates[-1]["result"].markdown == "stream result"


def test_iter_planner_updates_error() -> None:
    with pytest.raises(PlannerRuntimeError):
        list(
            iter_planner_updates(
                sample_request(),
                poll_seconds=0.01,
                crew_factory=lambda: DummyNationalParkCrew(error=RuntimeError("bad")),
            )
        )
