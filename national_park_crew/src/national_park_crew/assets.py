"""Static asset paths and helpers for the Gradio UI."""

from __future__ import annotations

from pathlib import Path

PARKS_IMAGE_DIR = Path(__file__).resolve().parents[2] / "assets" / "parks"
_PARK_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def list_park_images() -> list[Path]:
    """Return sorted park photo paths from the user-supplied assets folder."""
    if not PARKS_IMAGE_DIR.is_dir():
        return []

    images = [
        path
        for path in PARKS_IMAGE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in _PARK_IMAGE_SUFFIXES
    ]
    return sorted(images, key=lambda path: path.name.lower())


def park_collage_paths() -> list[str]:
    """Absolute paths as strings for Gradio Gallery values."""
    return [str(path.resolve()) for path in list_park_images()]
