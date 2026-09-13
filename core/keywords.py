import re

from core.text import normalize


def matches(keyword: str, note: str) -> bool:
    # Palavra inteira: "nota" não casa dentro de "anotação". As duas pontas
    # exigem ausência de caractere de palavra, o que também vale para termos
    # compostos ("nota fiscal") e para os que terminam em pontuação.
    pattern = rf"(?<!\w){re.escape(normalize(keyword))}(?!\w)"
    return re.search(pattern, normalize(note)) is not None
