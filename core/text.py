import unicodedata


def normalize(text: str) -> str:
    # NFKD separa cada letra acentuada em letra base + marca combinante;
    # descartadas as marcas, "farmácia" e "farmacia" viram a mesma sequência.
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))
