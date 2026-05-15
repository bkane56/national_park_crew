from __future__ import annotations

from pathlib import Path

from national_park_crew.export_utils import (
    build_download_file,
    sanitize_download_stem,
    write_temp_markdown,
)


def test_sanitize_download_stem() -> None:
    assert ".." not in sanitize_download_stem("../../x")
    assert sanitize_download_stem("  ###  ") == "itinerary"


def test_write_temp_markdown_creates_readable_file() -> None:
    path = Path(write_temp_markdown("# Hi", stem="trip"))
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "# Hi"
    assert path.suffix == ".md"
    path.unlink(missing_ok=True)


def test_build_download_file_markdown() -> None:
    path = Path(
        build_download_file(
            "# Title\n\nBody",
            "A_to_B",
            "Markdown (.md)",
        )
    )
    assert path.exists() and path.suffix == ".md"
    path.unlink(missing_ok=True)


def test_build_download_file_pdf() -> None:
    path = Path(
        build_download_file(
            "## Trip\n\n- One\n- Two\n",
            stem="Test_Stem",
            format_choice="PDF (.pdf)",
        )
    )
    assert path.exists() and path.suffix == ".pdf"
    assert path.stat().st_size > 800
    path.unlink(missing_ok=True)


def test_build_download_file_empty() -> None:
    assert build_download_file("", "x", "Markdown (.md)") is None
