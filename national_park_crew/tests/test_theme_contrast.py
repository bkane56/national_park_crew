from __future__ import annotations

from national_park_crew.theme import (
    _LIGHT_ACCENT,
    _LIGHT_BORDER,
    _LIGHT_BUTTON,
    _LIGHT_PAGE,
    _LIGHT_SURFACE,
    _LIGHT_TEXT,
    _LIGHT_TEXT_MUTED,
)

AA_NORMAL = 4.5
AA_UI = 3.0


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _relative_luminance(value: str) -> float:
    red, green, blue = _hex_to_rgb(value)

    def channel(component: int) -> float:
        scaled = component / 255
        if scaled <= 0.03928:
            return scaled / 12.92
        return ((scaled + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def test_light_mode_body_and_label_text_meets_aa_on_warm_backgrounds() -> None:
    for background in (_LIGHT_PAGE, _LIGHT_SURFACE):
        assert contrast_ratio(_LIGHT_TEXT, background) >= AA_NORMAL
        assert contrast_ratio(_LIGHT_TEXT_MUTED, background) >= AA_NORMAL


def test_light_mode_links_headings_and_fields_meet_aa() -> None:
    for background in (_LIGHT_PAGE, _LIGHT_SURFACE):
        assert contrast_ratio(_LIGHT_ACCENT, background) >= AA_NORMAL

    assert contrast_ratio("#ffffff", _LIGHT_BUTTON) >= AA_NORMAL


def test_light_mode_borders_meet_non_text_contrast() -> None:
    for background in (_LIGHT_PAGE, _LIGHT_SURFACE):
        assert contrast_ratio(_LIGHT_BORDER, background) >= AA_UI
