from pathlib import Path

import media_store
from core.index import Group, IndexedPhoto, Keyword, open_index
from core.search import search


def find_photos(
    index_path: Path, term: str = "", keyword_id: int | None = None
) -> list[IndexedPhoto]:
    # O índice ordena por caminho e os nomes dos arquivos são timestamps de
    # captura, então o inverso é a ordem cronológica decrescente.
    with open_index(index_path) as index:
        photos = index.all_photos() if keyword_id is None else index.group(keyword_id)
        if term:
            found = {entry.path for entry in search(index, term)}
            photos = [photo for photo in photos if photo.path in found]
    return list(reversed(photos))


def groups(index_path: Path) -> list[Group]:
    with open_index(index_path) as index:
        return index.groups()


def keywords(index_path: Path) -> list[Keyword]:
    with open_index(index_path) as index:
        return index.keywords()


def add_keyword(index_path: Path, term: str) -> Keyword:
    with open_index(index_path) as index:
        return index.add_keyword(term)


def rename_keyword(index_path: Path, keyword_id: int, term: str) -> None:
    with open_index(index_path) as index:
        index.rename_keyword(keyword_id, term)


def remove_keyword(index_path: Path, keyword_id: int) -> None:
    with open_index(index_path) as index:
        index.remove_keyword(keyword_id)


def delete_photo(image_path: Path, index_path: Path) -> None:
    image_path.unlink()
    media_store.notify(image_path)
    with open_index(index_path) as index:
        index.remove(image_path)


def rebuild_index(photos_dir: Path, index_path: Path) -> None:
    with open_index(index_path) as index:
        index.rebuild(photos_dir)
