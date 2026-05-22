from __future__ import annotations

from national_park_crew.app import access_code_visibility_update, build_app
from national_park_crew.planner_service import DEMO_MODE_LABEL, REAL_MODE_LABEL
from national_park_crew.theme import APP_CSS, PARK_THEME, THEME_DEFAULT_MODE, THEME_MODE_CHOICES, THEME_STORAGE_KEY


def test_build_app_constructs_without_error() -> None:
    app = build_app()
    assert app is not None


def test_park_theme_is_customized_base_theme() -> None:
    assert PARK_THEME.name == "base"
    assert THEME_MODE_CHOICES == ["Light", "Dark", "System"]
    assert THEME_DEFAULT_MODE == "Light"
    assert THEME_STORAGE_KEY == "npc-theme"
    assert "max-width: 1200px" in APP_CSS
    assert 'data-npc-theme="light"' in APP_CSS


def test_access_code_visibility_update() -> None:
    demo_update = access_code_visibility_update(DEMO_MODE_LABEL)
    real_update = access_code_visibility_update(REAL_MODE_LABEL)

    assert demo_update["visible"] is False
    assert real_update["visible"] is True
