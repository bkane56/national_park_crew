from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time

from national_park_crew.export_utils import (
    build_download_file,
    cleanup_stale_exports,
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


def test_cleanup_stale_exports_removes_old_files() -> None:
    old_file = Path(tempfile.gettempdir()) / "tripplanner_old_fixture.md"
    old_file.write_text("old", encoding="utf-8")
    old_age = time.time() - 7200
    os.utime(old_file, (old_age, old_age))

    cleanup_stale_exports(max_age_seconds=60)

    assert not old_file.exists()
