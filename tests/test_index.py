from pathlib import Path

from core import exif_store
from core.index import IndexedNote, IndexedPhoto, open_index
from tests.conftest import (
    UNDEFINED_USER_COMMENT,
    MakeJpeg,
    indexed_paths,
    write_raw_user_comment,
)


def test_upsert_inserts_and_then_updates_entry(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    path = make_jpeg(note="antes")

    with open_index(tmp_path / "index.db") as index:
        index.upsert(path)
        exif_store.write_note(path, "depois")
        index.upsert(path)

        assert index.notes() == [IndexedNote(str(path.resolve()), "depois")]


def test_remove_deletes_entry(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    path = make_jpeg(note="nota")

    with open_index(tmp_path / "index.db") as index:
        index.upsert(path)
        index.remove(path)

        assert index.notes() == []


def test_index_persists_between_sessions(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    path = make_jpeg(note="nota")
    db_path = tmp_path / "index.db"

    with open_index(db_path) as index:
        index.upsert(path)

    with open_index(db_path) as index:
        assert index.notes() == [IndexedNote(str(path.resolve()), "nota")]


def test_rebuild_reindexes_folder_from_scratch(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photos = tmp_path / "fotos"
    with_note = make_jpeg("fotos/a.jpg", note="Farmácia")
    without_note = make_jpeg("fotos/b.jpg")
    uppercase_suffix = make_jpeg("fotos/c.JPEG", note="Padaria")
    deleted = make_jpeg("fotos/d.jpg", note="será removida")
    (photos / "anotacoes.txt").write_text("não é imagem")

    with open_index(tmp_path / "index.db") as index:
        index.upsert(deleted)
        deleted.unlink()

        index.rebuild(photos)

        assert index.notes() == [
            IndexedNote(str(with_note.resolve()), "Farmácia"),
            IndexedNote(str(uppercase_suffix.resolve()), "Padaria"),
        ]

    assert indexed_paths(tmp_path / "index.db") == [
        str(with_note.resolve()),
        str(without_note.resolve()),
        str(uppercase_suffix.resolve()),
    ]


def test_all_photos_includes_photos_without_note(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    with_note = make_jpeg("fotos/a.jpg", note="Farmácia")
    without_note = make_jpeg("fotos/b.jpg")

    with open_index(tmp_path / "index.db") as index:
        index.rebuild(tmp_path / "fotos")

        assert index.all_photos() == [
            IndexedPhoto(str(with_note.resolve()), "Farmácia"),
            IndexedPhoto(str(without_note.resolve()), None),
        ]
        assert index.notes() == [IndexedNote(str(with_note.resolve()), "Farmácia")]


def test_rebuild_reflects_notes_changed_outside_the_index(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    path = make_jpeg("fotos/a.jpg", note="antiga")

    with open_index(tmp_path / "index.db") as index:
        index.rebuild(tmp_path / "fotos")
        exif_store.write_note(path, "nova")
        index.rebuild(tmp_path / "fotos")

        assert index.notes() == [IndexedNote(str(path.resolve()), "nova")]


def test_rebuild_completes_with_undefined_user_comment_in_folder(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    annotated = make_jpeg("fotos/a.jpg", note="Farmácia")
    from_other_camera = make_jpeg("fotos/b.jpg")
    write_raw_user_comment(from_other_camera, UNDEFINED_USER_COMMENT)

    with open_index(tmp_path / "index.db") as index:
        index.rebuild(tmp_path / "fotos")

        assert index.notes() == [IndexedNote(str(annotated.resolve()), "Farmácia")]

    assert indexed_paths(tmp_path / "index.db") == [
        str(annotated.resolve()),
        str(from_other_camera.resolve()),
    ]
