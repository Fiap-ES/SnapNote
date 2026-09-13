import unicodedata

from core.index import IndexedNote, NoteIndex


def normalize(text: str) -> str:
    # NFKD separa cada letra acentuada em letra base + marca combinante;
    # descartadas as marcas, "farmácia" e "farmacia" viram a mesma sequência.
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def search(index: NoteIndex, term: str) -> list[IndexedNote]:
    # O LIKE do SQLite ignora maiúsculas apenas em ASCII e nada sabe de
    # acentos, por isso a comparação é feita aqui sobre o texto normalizado.
    needle = normalize(term)
    return [entry for entry in index.notes() if needle in normalize(entry.note)]
