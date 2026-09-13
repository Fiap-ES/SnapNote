from pathlib import Path

import notes
from core import exif_store
from core.index import IndexedNote, open_index
from tests.conftest import MakeJpeg, indexed_paths


def test_save_note_writes_exif_and_indexes_photo(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("photos/a.jpg")
    db_path = tmp_path / "snapnote.db"

    notes.save_note(photo, "Farmácia São João", db_path)

    assert exif_store.read_note(photo) == "Farmácia São João"
    with open_index(db_path) as index:
        assert index.notes() == [IndexedNote(str(photo.resolve()), "Farmácia São João")]


def test_save_note_strips_surrounding_whitespace(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("photos/a.jpg")

    notes.save_note(photo, "  Padaria\n", tmp_path / "snapnote.db")

    assert exif_store.read_note(photo) == "Padaria"


def test_save_note_with_blank_text_indexes_photo_without_note(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("photos/a.jpg")
    db_path = tmp_path / "snapnote.db"

    notes.save_note(photo, " \n ", db_path)

    assert exif_store.read_note(photo) is None
    with open_index(db_path) as index:
        assert index.notes() == []
    assert indexed_paths(db_path) == [str(photo.resolve())]


def test_discard_photo_deletes_file(make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("photos/a.jpg")

    notes.discard_photo(photo)

    assert not photo.exists()
