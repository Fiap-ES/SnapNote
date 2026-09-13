from collections.abc import Iterator
from pathlib import Path

import pytest

from core.index import NoteIndex, open_index
from core.search import normalize, search
from tests.conftest import MakeJpeg

PHARMACY_NOTE = "Farmácia do bairro, aberta até às 22h"
RECIPE_NOTE = "RECEITA DA AÇÃO DE GRAÇAS"


@pytest.fixture
def index(tmp_path: Path, make_jpeg: MakeJpeg) -> Iterator[NoteIndex]:
    make_jpeg("fotos/farmacia.jpg", note=PHARMACY_NOTE)
    make_jpeg("fotos/receita.jpg", note=RECIPE_NOTE)
    make_jpeg("fotos/sem_nota.jpg")

    with open_index(tmp_path / "index.db") as index:
        index.rebuild(tmp_path / "fotos")
        yield index


def notes_found(index: NoteIndex, term: str) -> list[str]:
    return [result.note for result in search(index, term)]


def test_normalize_strips_accents_and_case() -> None:
    assert normalize("Farmácia Ação Çedilha Ünïcode") == "farmacia acao cedilha unicode"


def test_search_without_accents_finds_accented_note(index: NoteIndex) -> None:
    assert notes_found(index, "farmacia") == [PHARMACY_NOTE]


def test_search_with_accents_finds_unaccented_term(index: NoteIndex) -> None:
    assert notes_found(index, "açao de graças") == [RECIPE_NOTE]


def test_search_ignores_case(index: NoteIndex) -> None:
    assert notes_found(index, "FARMÁCIA") == [PHARMACY_NOTE]
    assert notes_found(index, "receita") == [RECIPE_NOTE]


def test_search_matches_substring(index: NoteIndex) -> None:
    assert notes_found(index, "bairro") == [PHARMACY_NOTE]


def test_search_returns_path_of_matching_image(index: NoteIndex, tmp_path: Path) -> None:
    (result,) = search(index, "farmacia")

    assert result.path == str((tmp_path / "fotos" / "farmacia.jpg").resolve())


def test_search_without_match_returns_empty_list(index: NoteIndex) -> None:
    assert search(index, "padaria") == []
