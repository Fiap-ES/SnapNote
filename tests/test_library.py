from datetime import date
from pathlib import Path

import library
from core.index import Group, IndexedPhoto, Keyword, open_index
from tests.conftest import MakeJpeg, indexed_paths, write_capture_time


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

    assert library.find_photos(db_path, "farmacia") == [IndexedPhoto(str(farmacia.resolve()), "Farmácia")]
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


def test_find_photos_filters_by_group_and_term(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    make_jpeg("photos/20260913_100000_000000.jpg", note="Recibo da padaria")
    farmacia = make_jpeg("photos/20260913_110000_000000.jpg", note="Recibo da farmácia")
    make_jpeg("photos/20260913_120000_000000.jpg", note="Farmácia sem recibo nenhum, só nota")
    db_path = tmp_path / "snapnote.db"
    library.rebuild_index(tmp_path / "photos", db_path)
    keyword = library.add_keyword(db_path, "recibo")

    in_group = library.find_photos(db_path, keyword_id=keyword.id)
    assert [Path(photo.path).name for photo in in_group] == [
        "20260913_120000_000000.jpg",
        "20260913_110000_000000.jpg",
        "20260913_100000_000000.jpg",
    ]
    assert library.find_photos(db_path, "farmacia", keyword.id) == [
        IndexedPhoto(str(tmp_path / "photos" / "20260913_120000_000000.jpg"), "Farmácia sem recibo nenhum, só nota"),
        IndexedPhoto(str(farmacia.resolve()), "Recibo da farmácia"),
    ]


def test_groups_lists_only_keywords_with_photos(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    make_jpeg("photos/a.jpg", note="Recibo da padaria")
    db_path = tmp_path / "snapnote.db"
    library.rebuild_index(tmp_path / "photos", db_path)
    recibo = library.add_keyword(db_path, "recibo")
    library.add_keyword(db_path, "viagem")

    assert library.groups(db_path) == [Group(recibo, 1)]
    assert [keyword.term for keyword in library.keywords(db_path)] == ["recibo", "viagem"]


def test_rename_and_remove_keyword(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    make_jpeg("photos/a.jpg", note="Viagem para a praia")
    db_path = tmp_path / "snapnote.db"
    library.rebuild_index(tmp_path / "photos", db_path)
    keyword = library.add_keyword(db_path, "recibo")

    library.rename_keyword(db_path, keyword.id, "viagem")
    assert library.groups(db_path) == [Group(Keyword(keyword.id, "viagem"), 1)]

    library.remove_keyword(db_path, keyword.id)
    assert library.groups(db_path) == [] and library.keywords(db_path) == []


def test_find_photos_orders_by_capture_time_not_by_name(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    older = make_jpeg("photos/b_named_later.jpg", note="antiga")
    newer = make_jpeg("photos/a_named_first.jpg", note="recente")
    write_capture_time(older, "2026:09:12 08:00:00")
    write_capture_time(newer, "2026:09:13 08:00:00")
    db_path = tmp_path / "snapnote.db"
    library.rebuild_index(tmp_path / "photos", db_path)

    assert [Path(photo.path).name for photo in library.find_photos(db_path)] == [newer.name, older.name]


def test_photo_sections_group_by_capture_day_most_recent_first(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    morning = make_jpeg("photos/a.jpg", note="manhã")
    evening = make_jpeg("photos/b.jpg", note="noite")
    yesterday = make_jpeg("photos/c.jpg", note="ontem")
    write_capture_time(morning, "2026:09:13 08:00:00")
    write_capture_time(evening, "2026:09:13 21:00:00")
    write_capture_time(yesterday, "2026:09:12 12:00:00")
    db_path = tmp_path / "snapnote.db"
    library.rebuild_index(tmp_path / "photos", db_path)

    sections = library.photo_sections(db_path)

    assert [section.day for section in sections] == [date(2026, 9, 13), date(2026, 9, 12)]
    assert [[photo.note for photo in section.photos] for section in sections] == [["noite", "manhã"], ["ontem"]]


def test_albums_use_the_most_recent_photo_of_each_group_as_cover(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    older = make_jpeg("photos/a.jpg", note="recibo antigo")
    newer = make_jpeg("photos/b.jpg", note="recibo novo")
    write_capture_time(older, "2026:09:12 08:00:00")
    write_capture_time(newer, "2026:09:13 08:00:00")
    db_path = tmp_path / "snapnote.db"
    library.rebuild_index(tmp_path / "photos", db_path)
    recibo = library.add_keyword(db_path, "recibo")
    library.add_keyword(db_path, "viagem")

    albums = library.albums(db_path)

    assert [(album.group, Path(album.cover.path).name) for album in albums] == [(Group(recibo, 2), newer.name)]


def test_index_photo_registers_a_photo_without_note(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("photos/a.jpg")
    db_path = tmp_path / "snapnote.db"

    library.index_photo(photo, db_path)

    assert library.find_photos(db_path) == [IndexedPhoto(str(photo.resolve()), None)]
