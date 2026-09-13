from pathlib import Path

import library
from core.index import IndexedNote, IndexedPhoto, open_index
from tests.conftest import MakeJpeg, indexed_paths


def test_find_photos_lists_every_indexed_photo_most_recent_first(
    tmp_path: Path, make_jpeg: MakeJpeg
) -> None:
    older = make_jpeg("photos/20260913_100000_000000.jpg", note="Padaria")
    without_note = make_jpeg("photos/20260913_110000_000000.jpg")
    newer = make_jpeg("photos/20260913_120000_000000.jpg", note="Farmácia")
    db_path = tmp_path / "snapnote.db"
    with open_index(db_path) as index:
        index.rebuild(tmp_path / "photos")

    assert library.find_photos(db_path) == [
        IndexedPhoto(str(newer.resolve()), "Farmácia"),
        IndexedPhoto(str(without_note.resolve()), None),
        IndexedPhoto(str(older.resolve()), "Padaria"),
    ]


def test_find_photos_filters_by_term_ignoring_accents(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    make_jpeg("photos/20260913_100000_000000.jpg", note="Padaria")
    farmacia = make_jpeg("photos/20260913_110000_000000.jpg", note="Farmácia")
    db_path = tmp_path / "snapnote.db"
    with open_index(db_path) as index:
        index.rebuild(tmp_path / "photos")

    assert library.find_photos(db_path, "farmacia") == [IndexedNote(str(farmacia.resolve()), "Farmácia")]
    assert library.find_photos(db_path, "açougue") == []


def test_find_photos_on_empty_index_returns_nothing(tmp_path: Path) -> None:
    assert library.find_photos(tmp_path / "snapnote.db") == []


def test_delete_photo_removes_file_and_index_entry(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("photos/a.jpg", note="Padaria")
    db_path = tmp_path / "snapnote.db"
    with open_index(db_path) as index:
        index.upsert(photo)

    library.delete_photo(photo, db_path)

    assert not photo.exists()
    assert indexed_paths(db_path) == []


def test_rebuild_index_reindexes_folder(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("photos/a.jpg", note="Padaria")
    db_path = tmp_path / "snapnote.db"

    library.rebuild_index(tmp_path / "photos", db_path)

    assert library.find_photos(db_path) == [IndexedPhoto(str(photo.resolve()), "Padaria")]
