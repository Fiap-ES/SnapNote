from collections.abc import Callable
from pathlib import Path

import ocr
import vision


def suggest_note(image_path: Path, on_result: Callable[[str], None]) -> None:
    # A descrição do modelo na nuvem é a sugestão preferida; sem chave, sem
    # rede ou em qualquer falha ela vem vazia e a leitura local assume. As
    # duas respondem fora da thread da interface, e só uma delas chega.
    def deliver(description: str) -> None:
        if description:
            on_result(description)
        else:
            ocr.recognize_text(image_path, on_result)

    vision.describe_image(image_path, deliver)
