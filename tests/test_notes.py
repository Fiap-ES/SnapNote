from pathlib import Path

import notes
from core import exif_store
from core.index import IndexedNote, IndexedPhoto, open_index
from tests.conftest import MakeJpeg


def test_save_note_writes_exif_and_indexes_photo(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("photos/a.jpg")
    db_path = tmp_path / "snapnote.db"

    notes.save_note(photo, "Farmácia São João", db_path)

    assert exif_store.read_note(photo) == "Farmácia São João"
    with open_index(db_path) as index:
        assert index.notes() == [IndexedNote(str(photo.resolve()), "Farmácia São João")]


def test_save_note_strips_surrounding_whitespace_and_returns_stored_text(
    tmp_path: Path, make_jpeg: MakeJpeg
) -> None:
    photo = make_jpeg("photos/a.jpg")

    stored = notes.save_note(photo, "  Padaria\n", tmp_path / "snapnote.db")

    assert stored == "Padaria"
    assert exif_store.read_note(photo) == "Padaria"


def test_save_note_with_blank_text_indexes_photo_without_note(
    tmp_path: Path, make_jpeg: MakeJpeg
) -> None:
    photo = make_jpeg("photos/a.jpg")
    db_path = tmp_path / "snapnote.db"

    stored = notes.save_note(photo, " \n ", db_path)

    assert stored is None
    assert exif_store.read_note(photo) is None
    with open_index(db_path) as index:
        assert index.all_photos() == [IndexedPhoto(str(photo.resolve()), None)]
        assert index.notes() == []


def test_save_note_with_blank_text_removes_existing_note(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("photos/a.jpg")
    db_path = tmp_path / "snapnote.db"
    notes.save_note(photo, "antiga", db_path)

    notes.save_note(photo, "", db_path)

    assert exif_store.read_note(photo) is None
    with open_index(db_path) as index:
        assert index.all_photos() == [IndexedPhoto(str(photo.resolve()), None)]


def test_discard_photo_deletes_file(make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("photos/a.jpg")

    notes.discard_photo(photo)

    assert not photo.exists()
