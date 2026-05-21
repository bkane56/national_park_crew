from __future__ import annotations

from pathlib import Path

from national_park_crew.assets import PARKS_IMAGE_DIR, list_park_images, park_collage_paths


def test_list_park_images_empty_when_no_files() -> None:
    assert PARKS_IMAGE_DIR.is_dir()
    assert list_park_images() == []
    assert park_collage_paths() == []


def test_list_park_images_finds_supported_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("national_park_crew.assets.PARKS_IMAGE_DIR", tmp_path)
    (tmp_path / "zion.jpg").write_bytes(b"jpg")
    (tmp_path / "readme.txt").write_text("skip", encoding="utf-8")
    (tmp_path / "yosemite.png").write_bytes(b"png")

    assert [path.name for path in list_park_images()] == ["yosemite.png", "zion.jpg"]
    assert len(park_collage_paths()) == 2
