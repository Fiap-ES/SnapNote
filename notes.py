from pathlib import Path

import media_store
from core import exif_store
from core.index import open_index


def save_note(image_path: Path, text: str, index_path: Path) -> str | None:
    # Texto em branco não vira um UserComment vazio: o campo é removido, a
    # foto fica sem anotação e o índice a registra com nota nula.
    note = text.strip() or None
    if note is None:
        exif_store.remove_note(image_path)
    else:
        exif_store.write_note(image_path, note)
    # O piexif reescreve o arquivo; sem o aviso, a galeria nativa continuaria
    # exibindo a versão anterior.
    media_store.notify(image_path)
    with open_index(index_path) as index:
        index.upsert(image_path)
    return note


def discard_photo(image_path: Path) -> None:
    image_path.unlink()
    media_store.notify(image_path)
