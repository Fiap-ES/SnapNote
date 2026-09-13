from pathlib import Path

import pytest

from core import exif_store
from core.index import DuplicateKeywordError, Group, IndexedPhoto, Keyword, open_index
from core.keywords import matches
from tests.conftest import MakeJpeg


def test_matches_whole_word_only() -> None:
    assert matches("recibo", "recibo da farmácia")
    assert not matches("recibo", "irrecibível")
    assert not matches("nota", "anotação do dia")
    assert not matches("recibo", "recibos")


def test_matches_ignores_accents_and_case() -> None:
    assert matches("Farmácia", "FARMACIA do bairro")
    assert matches("acao", "Ação de graças")


def test_matches_compound_terms_and_punctuation() -> None:
    assert matches("nota fiscal", "Nota Fiscal 123, loja")
    assert not matches("nota fiscal", "nota de fiscal")
    assert matches("recibo", "recibo.")


def test_add_keyword_links_existing_photos(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    recibo = make_jpeg("fotos/a.jpg", note="Recibo da farmácia")
    make_jpeg("fotos/b.jpg", note="Padaria, recibos antigos")
    make_jpeg("fotos/c.jpg")

    with open_index(tmp_path / "index.db") as index:
        index.rebuild(tmp_path / "fotos")
        keyword = index.add_keyword("recibo")

        assert index.keywords() == [keyword]
        assert index.group(keyword.id) == [IndexedPhoto(str(recibo.resolve()), "Recibo da farmácia")]
        assert index.groups() == [Group(keyword, 1)]


def test_remove_keyword_drops_its_links(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    make_jpeg("fotos/a.jpg", note="Recibo da farmácia")

    with open_index(tmp_path / "index.db") as index:
        index.rebuild(tmp_path / "fotos")
        keyword = index.add_keyword("recibo")

        index.remove_keyword(keyword.id)

        assert index.keywords() == []
        assert index.group(keyword.id) == []
        assert index.groups() == []


def test_rename_keyword_relinks_photos(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    recibo = make_jpeg("fotos/a.jpg", note="Recibo da farmácia")
    padaria = make_jpeg("fotos/b.jpg", note="Pão da padaria")

    with open_index(tmp_path / "index.db") as index:
        index.rebuild(tmp_path / "fotos")
        keyword = index.add_keyword("recibo")

        index.rename_keyword(keyword.id, "Padaria")

        assert index.keywords() == [Keyword(keyword.id, "Padaria")]
        assert index.group(keyword.id) == [IndexedPhoto(str(padaria.resolve()), "Pão da padaria")]
        assert str(recibo.resolve()) not in [photo.path for photo in index.group(keyword.id)]


def test_upsert_relinks_only_that_photo(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("fotos/a.jpg", note="Padaria")

    with open_index(tmp_path / "index.db") as index:
        keyword = index.add_keyword("recibo")
        index.upsert(photo)
        assert index.group(keyword.id) == []

        exif_store.write_note(photo, "Recibo da padaria")
        index.upsert(photo)
        assert index.group(keyword.id) == [IndexedPhoto(str(photo.resolve()), "Recibo da padaria")]

        exif_store.remove_note(photo)
        index.upsert(photo)
        assert index.group(keyword.id) == []


def test_rebuild_recomputes_all_links(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    with open_index(tmp_path / "index.db") as index:
        keyword = index.add_keyword("recibo")
        recibo = make_jpeg("fotos/a.jpg", note="recibo")
        make_jpeg("fotos/b.jpg", note="outra coisa")

        index.rebuild(tmp_path / "fotos")

        assert index.group(keyword.id) == [IndexedPhoto(str(recibo.resolve()), "recibo")]


def test_removing_photo_drops_its_links(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("fotos/a.jpg", note="recibo")

    with open_index(tmp_path / "index.db") as index:
        keyword = index.add_keyword("recibo")
        index.upsert(photo)

        index.remove(photo)

        assert index.groups() == []


def test_keywords_are_unique_ignoring_accents_and_case(tmp_path: Path) -> None:
    with open_index(tmp_path / "index.db") as index:
        index.add_keyword("Recibo")
        with pytest.raises(DuplicateKeywordError):
            index.add_keyword("recíbo")

        other = index.add_keyword("padaria")
        with pytest.raises(DuplicateKeywordError):
            index.rename_keyword(other.id, "RECIBO")
        assert [keyword.term for keyword in index.keywords()] == ["padaria", "Recibo"]


def test_blank_keyword_is_rejected(tmp_path: Path) -> None:
    with open_index(tmp_path / "index.db") as index:
        with pytest.raises(ValueError):
            index.add_keyword("   ")
