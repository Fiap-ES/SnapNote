from pathlib import Path

from core.index import IndexedPhoto, open_index
from core.search import search


def find_photos(index_path: Path, term: str = "") -> list[IndexedPhoto]:
    # O índice ordena por caminho e os nomes dos arquivos são timestamps de
    # captura, então o inverso é a ordem cronológica decrescente.
    with open_index(index_path) as index:
        photos = search(index, term) if term else index.all_photos()
    return list(reversed(photos))


def delete_photo(image_path: Path, index_path: Path) -> None:
    image_path.unlink()
    with open_index(index_path) as index:
        index.remove(image_path)


def rebuild_index(photos_dir: Path, index_path: Path) -> None:
    with open_index(index_path) as index:
        index.rebuild(photos_dir)
