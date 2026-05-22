"""Gradio theme and appearance controls for the National Park Trip Planner UI."""

from __future__ import annotations

import gradio as gr

# Light-mode tokens tuned for WCAG AA (4.5:1 text, 3:1 UI boundaries on warm backgrounds).
_LIGHT_PAGE = "#f7f5f0"
_LIGHT_SURFACE = "#ffffff"
_LIGHT_TEXT = "#1c211e"
_LIGHT_TEXT_MUTED = "#57534e"
_LIGHT_BORDER = "#8a837c"
_LIGHT_ACCENT = "#245a42"
_LIGHT_ACCENT_HOVER = "#1b4332"
_LIGHT_BUTTON = "#2d6a4f"
_LIGHT_BUTTON_HOVER = "#1b4332"

# Option A — Forest and Stone (light + dark palette)
_FOREST_LIGHT = {
    "body_background_fill": _LIGHT_PAGE,
    "block_background_fill": _LIGHT_SURFACE,
    "body_text_color": _LIGHT_TEXT,
    "body_text_color_subdued": _LIGHT_TEXT_MUTED,
    "block_label_text_color": _LIGHT_TEXT_MUTED,
    "block_info_text_color": _LIGHT_TEXT_MUTED,
    "input_placeholder_color": _LIGHT_TEXT_MUTED,
    "block_border_color": _LIGHT_BORDER,
    "border_color_primary": _LIGHT_BORDER,
    "input_border_color": _LIGHT_BORDER,
    "input_border_width": "1px",
    "input_border_color_focus": _LIGHT_ACCENT,
    "button_primary_background_fill": _LIGHT_BUTTON,
    "button_primary_background_fill_hover": _LIGHT_BUTTON_HOVER,
    "link_text_color": _LIGHT_ACCENT,
    "link_text_color_hover": _LIGHT_ACCENT_HOVER,
}

_FOREST_DARK = {
    "body_background_fill_dark": "#141816",
    "block_background_fill_dark": "#1e2420",
    "body_text_color_dark": "#e8ece9",
    "block_border_color_dark": "#2f3832",
    "button_primary_background_fill_dark": "#52b788",
    "button_primary_background_fill_hover_dark": "#40916c",
    "link_text_color_dark": "#52b788",
    "link_text_color_hover_dark": "#40916c",
}

_BASE_THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.green,
    secondary_hue=gr.themes.colors.amber,
    neutral_hue=gr.themes.colors.stone,
    font=gr.themes.GoogleFont("Source Sans 3"),
    font_mono=gr.themes.GoogleFont("IBM Plex Mono"),
    radius_size=gr.themes.sizes.radius_sm,
)

PARK_THEME = _BASE_THEME.set(**_FOREST_LIGHT, **_FOREST_DARK)
PARK_THEME.custom_css = f"""
.markdown h1 {{ color: {_LIGHT_ACCENT} !important; margin-bottom: 0 !important; }}
:root.dark .markdown h1 {{ color: #52b788 !important; }}
#npc-header-row {{
  align-items: center !important;
  justify-content: space-between !important;
  gap: 0.85rem !important;
  margin-bottom: 0.65rem !important;
  flex-wrap: wrap !important;
}}
#npc-title {{ flex: 1 1 auto !important; min-width: 0 !important; }}
#npc-title .prose {{ margin: 0 !important; }}
#npc-appearance {{
  flex: 0 0 auto !important;
  margin: 0 !important;
  padding: 0 !important;
  min-width: 230px !important;
}}
#npc-appearance .wrap {{
  display: inline-flex !important;
  gap: 0.15rem !important;
  padding: 0.2rem !important;
  border: 1px solid var(--block-border-color) !important;
  border-radius: 999px !important;
  background: color-mix(in srgb, var(--block-background-fill) 92%, var(--body-background-fill) 8%) !important;
}}
#npc-appearance label {{
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  padding: 0.28rem 0.65rem !important;
  border-radius: 999px !important;
  margin: 0 !important;
  border: 0 !important;
  line-height: 1.2 !important;
}}
#npc-appearance label.selected,
#npc-appearance label:has(input:checked) {{
  color: var(--button-primary-text-color, #ffffff) !important;
  background: var(--button-primary-background-fill) !important;
}}
#npc-appearance label:not(.selected),
#npc-appearance label:has(input:not(:checked)) {{
  color: var(--body-text-color) !important;
  background: transparent !important;
}}
@media (max-width: 700px) {{
  #npc-appearance {{
    min-width: 100% !important;
  }}
  #npc-appearance .wrap {{
    width: 100% !important;
    justify-content: center !important;
  }}
}}
#npc-park-collage {{
  margin-bottom: 0.75rem !important;
}}
#npc-park-collage .empty {{
  display: none !important;
}}
"""

_LIGHT_CSS_VARS = f"""
  --body-background-fill: {_LIGHT_PAGE} !important;
  --block-background-fill: {_LIGHT_SURFACE} !important;
  --body-text-color: {_LIGHT_TEXT} !important;
  --body-text-color-subdued: {_LIGHT_TEXT_MUTED} !important;
  --block-label-text-color: {_LIGHT_TEXT_MUTED} !important;
  --block-info-text-color: {_LIGHT_TEXT_MUTED} !important;
  --input-placeholder-color: {_LIGHT_TEXT_MUTED} !important;
  --block-border-color: {_LIGHT_BORDER} !important;
  --border-color-primary: {_LIGHT_BORDER} !important;
  --input-border-color: {_LIGHT_BORDER} !important;
  --input-border-width: 1px !important;
  --input-border-color-focus: {_LIGHT_ACCENT} !important;
  --button-primary-background-fill: {_LIGHT_BUTTON} !important;
  --button-primary-background-fill-hover: {_LIGHT_BUTTON_HOVER} !important;
  --link-text-color: {_LIGHT_ACCENT} !important;
  --link-text-color-hover: {_LIGHT_ACCENT_HOVER} !important;
"""

APP_CSS = f"""
.gradio-container {{
  width: min(1200px, calc(100% - 2rem)) !important;
  max-width: 1200px !important;
  margin: 0 auto !important;
}}

html[data-npc-theme="light"] {{
  color-scheme: light;
{_LIGHT_CSS_VARS}
}}

html[data-npc-theme="dark"] {{
  color-scheme: dark;
  --body-background-fill: #141816 !important;
  --block-background-fill: #1e2420 !important;
  --body-text-color: #e8ece9 !important;
  --block-border-color: #2f3832 !important;
  --button-primary-background-fill: #52b788 !important;
  --button-primary-background-fill-hover: #40916c !important;
}}

@media (prefers-color-scheme: light) {{
  html[data-npc-theme="system"] {{
    color-scheme: light;
{_LIGHT_CSS_VARS}
  }}
}}

@media (prefers-color-scheme: dark) {{
  html[data-npc-theme="system"] {{
    color-scheme: dark;
    --body-background-fill: #141816 !important;
    --block-background-fill: #1e2420 !important;
    --body-text-color: #e8ece9 !important;
    --block-border-color: #2f3832 !important;
    --button-primary-background-fill: #52b788 !important;
    --button-primary-background-fill-hover: #40916c !important;
  }}
}}
"""

THEME_MODE_LIGHT = "Light"
THEME_MODE_DARK = "Dark"
THEME_MODE_SYSTEM = "System"
THEME_MODE_CHOICES = [THEME_MODE_LIGHT, THEME_MODE_DARK, THEME_MODE_SYSTEM]
THEME_STORAGE_KEY = "npc-theme"
THEME_DEFAULT_MODE = THEME_MODE_LIGHT

# Shared client-side logic inlined so load/change handlers do not depend on head script order.
_THEME_APPLY_FN = f"""
function npcApplyTheme(mode) {{
    const normalized = mode || localStorage.getItem("{THEME_STORAGE_KEY}") || "{THEME_DEFAULT_MODE}";
    localStorage.setItem("{THEME_STORAGE_KEY}", normalized);
    const root = document.documentElement;
    root.setAttribute("data-npc-theme", normalized.toLowerCase());
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const useDark = normalized === "{THEME_MODE_DARK}"
        || (normalized === "{THEME_MODE_SYSTEM}" && prefersDark);
    root.classList.toggle("dark", useDark);
    if (document.body) {{
        document.body.classList.toggle("dark", useDark);
    }}
    return normalized;
}}
"""

THEME_HEAD = f"""
<script>
(function () {{
    var mode = localStorage.getItem("{THEME_STORAGE_KEY}") || "{THEME_DEFAULT_MODE}";
    var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var useDark = mode === "{THEME_MODE_DARK}" || (mode === "{THEME_MODE_SYSTEM}" && prefersDark);
    document.documentElement.setAttribute("data-npc-theme", mode.toLowerCase());
    if (useDark) {{
        document.documentElement.classList.add("dark");
    }}
}})();
</script>
<script>
(function () {{
    {_THEME_APPLY_FN}
    npcApplyTheme(localStorage.getItem("{THEME_STORAGE_KEY}") || "{THEME_DEFAULT_MODE}");
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {{
        if ((localStorage.getItem("{THEME_STORAGE_KEY}") || "{THEME_DEFAULT_MODE}") === "{THEME_MODE_SYSTEM}") {{
            npcApplyTheme("{THEME_MODE_SYSTEM}");
        }}
    }});
    window.npcApplyTheme = npcApplyTheme;
}})();
</script>
"""

THEME_INIT_JS = f"""
() => {{
    {_THEME_APPLY_FN}
    npcApplyTheme(localStorage.getItem("{THEME_STORAGE_KEY}") || "{THEME_DEFAULT_MODE}");
}}
"""

THEME_LOAD_JS = f"""
() => {{
    {_THEME_APPLY_FN}
    const mode = npcApplyTheme(localStorage.getItem("{THEME_STORAGE_KEY}") || "{THEME_DEFAULT_MODE}");
    return [mode];
}}
"""

THEME_CHANGE_JS = f"""
(mode) => {{
    {_THEME_APPLY_FN}
    npcApplyTheme(mode);
}}
"""
