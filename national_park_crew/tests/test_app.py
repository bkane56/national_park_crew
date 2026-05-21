from __future__ import annotations

from national_park_crew.app import build_app
from national_park_crew.theme import APP_CSS, PARK_THEME, THEME_DEFAULT_MODE, THEME_MODE_CHOICES, THEME_STORAGE_KEY


def test_build_app_constructs_without_error() -> None:
    app = build_app()
    assert app is not None


def test_park_theme_is_customized_base_theme() -> None:
    assert PARK_THEME.name == "base"
    assert THEME_MODE_CHOICES == ["Light", "Dark", "System"]
    assert THEME_DEFAULT_MODE == "Light"
    assert THEME_STORAGE_KEY == "npc-theme"
    assert 'data-npc-theme="light"' in APP_CSS
