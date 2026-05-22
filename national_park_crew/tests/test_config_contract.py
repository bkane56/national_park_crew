from __future__ import annotations

from pathlib import Path
import re

from national_park_crew.planner_service import PlannerRequest, build_kickoff_inputs


PLACEHOLDER_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _load_placeholders(path: Path) -> set[str]:
    return set(PLACEHOLDER_PATTERN.findall(path.read_text(encoding="utf-8")))


def test_yaml_placeholders_match_kickoff_inputs() -> None:
    request = PlannerRequest(
        from_location="Venice, Florida",
        to_location="Salt Lake City, Utah area",
        departure_date="2026-07-18",
        return_date="2026-07-27",
    )
    input_keys = set(build_kickoff_inputs(request).keys())

    config_dir = Path(__file__).resolve().parents[1] / "src" / "national_park_crew" / "config"
    placeholders = _load_placeholders(config_dir / "agents.yaml")
    placeholders |= _load_placeholders(config_dir / "tasks.yaml")

    missing = placeholders - input_keys
    assert not missing, f"Placeholders missing kickoff inputs: {sorted(missing)}"
