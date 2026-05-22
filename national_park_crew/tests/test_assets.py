from __future__ import annotations

from pathlib import Path

from national_park_crew.assets import PARKS_IMAGE_DIR, list_park_images, park_collage_paths


def test_list_park_images_reflects_current_assets_directory() -> None:
    assert PARKS_IMAGE_DIR.is_dir()
    images = list_park_images()
    collage = park_collage_paths()

    assert len(collage) == len(images)
    for image_path, collage_path in zip(images, collage, strict=True):
        assert image_path.is_file()
        assert image_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        assert Path(collage_path).resolve() == image_path.resolve()


def test_list_park_images_finds_supported_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("national_park_crew.assets.PARKS_IMAGE_DIR", tmp_path)
    (tmp_path / "zion.jpg").write_bytes(b"jpg")
    (tmp_path / "readme.txt").write_text("skip", encoding="utf-8")
    (tmp_path / "yosemite.png").write_bytes(b"png")

    assert [path.name for path in list_park_images()] == ["yosemite.png", "zion.jpg"]
    assert len(park_collage_paths()) == 2
