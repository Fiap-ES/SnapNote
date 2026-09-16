from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

import demo
import library
from core import exif_store
from tests.conftest import MakeJpeg

TODAY = date(2026, 9, 16)
DEMO_NAMES = {photo.file_name for photo in demo.DEMO_PHOTOS}


@pytest.fixture
def demo_dirs(tmp_path: Path, make_jpeg: MakeJpeg) -> tuple[Path, Path, Path, Path]:
    for photo in demo.DEMO_PHOTOS:
        make_jpeg(f"assets/{photo.file_name}")
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    return tmp_path / "assets", photos_dir, tmp_path / "snapnote.db", tmp_path / "demo_loaded"


def test_first_load_copies_annotates_dates_and_indexes_every_photo(
    demo_dirs: tuple[Path, Path, Path, Path]
) -> None:
    assets_dir, photos_dir, db_path, marker = demo_dirs
    keyword = library.add_keyword(db_path, "lista")

    assert demo.load_demo(assets_dir, photos_dir, db_path, marker, TODAY) is True

    assert {path.name for path in photos_dir.iterdir()} == DEMO_NAMES
    assert marker.exists()
    for photo in demo.DEMO_PHOTOS:
        assert exif_store.read_note(photos_dir / photo.file_name) == photo.note
        expected = datetime.combine(TODAY - timedelta(days=photo.days_ago), photo.taken_at)
        assert exif_store.read_capture_time(photos_dir / photo.file_name) == expected
    indexed = library.find_photos(db_path)
    assert {Path(photo.path).name: photo.note for photo in indexed} == {
        photo.file_name: photo.note for photo in demo.DEMO_PHOTOS
    }
    assert [Path(photo.path).name for photo in library.find_photos(db_path, keyword_id=keyword.id)] == ["lista-mercado.jpg"]
    assert library.taxonomy_albums(db_path)


def test_dates_spread_over_recent_weeks_without_today_or_yesterday(
    demo_dirs: tuple[Path, Path, Path, Path]
) -> None:
    assets_dir, photos_dir, db_path, marker = demo_dirs

    demo.load_demo(assets_dir, photos_dir, db_path, marker, TODAY)

    sections = library.photo_sections(db_path)
    ages = [(TODAY - section.day).days for section in sections]
    assert all(2 <= age <= 45 for age in ages)
    assert len(sections) >= 5
    assert max(Counter(len(section.photos) for section in sections)) >= 2


def test_second_open_does_not_bring_deleted_photos_back(demo_dirs: tuple[Path, Path, Path, Path]) -> None:
    assets_dir, photos_dir, db_path, marker = demo_dirs
    demo.load_demo(assets_dir, photos_dir, db_path, marker, TODAY)
    library.delete_photo(photos_dir / "lista-mercado.jpg", db_path)

    assert demo.load_demo(assets_dir, photos_dir, db_path, marker, TODAY) is False

    assert not (photos_dir / "lista-mercado.jpg").exists()
    assert len(library.find_photos(db_path)) == len(demo.DEMO_PHOTOS) - 1


def test_broken_asset_is_skipped_and_the_others_still_load(demo_dirs: tuple[Path, Path, Path, Path]) -> None:
    assets_dir, photos_dir, db_path, marker = demo_dirs
    (assets_dir / "lousa-newton.jpg").write_bytes(b"isto nao e um jpeg")
    (assets_dir / "quadro-sql.jpg").unlink()

    assert demo.load_demo(assets_dir, photos_dir, db_path, marker, TODAY) is True

    loaded = {Path(photo.path).name for photo in library.find_photos(db_path)}
    assert loaded == DEMO_NAMES - {"lousa-newton.jpg", "quadro-sql.jpg"}
    assert not (photos_dir / "lousa-newton.jpg").exists()
    assert marker.exists()
