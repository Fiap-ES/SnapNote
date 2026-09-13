from pathlib import Path

from core import exif_store
from core.index import open_index


def save_note(image_path: Path, text: str, index_path: Path) -> None:
    # Texto em branco não vira um UserComment vazio: a foto fica sem
    # anotação e o índice a registra com nota nula.
    note = text.strip()
    if note:
        exif_store.write_note(image_path, note)
    with open_index(index_path) as index:
        index.upsert(image_path)


def discard_photo(image_path: Path) -> None:
    image_path.unlink()
