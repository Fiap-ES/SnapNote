from core.index import IndexedNote, NoteIndex
from core.text import normalize

__all__ = ["normalize", "search"]


def search(index: NoteIndex, term: str) -> list[IndexedNote]:
    # O LIKE do SQLite ignora maiúsculas apenas em ASCII e nada sabe de
    # acentos, por isso a comparação é feita aqui sobre o texto normalizado.
    needle = normalize(term)
    return [entry for entry in index.notes() if needle in normalize(entry.note)]
