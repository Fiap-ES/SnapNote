from pathlib import Path

import ocr


def test_ocr_is_unavailable_outside_android() -> None:
    assert ocr.ON_ANDROID is False
    assert ocr.available() is False


def test_recognize_text_yields_empty_text_outside_android() -> None:
    results: list[str] = []

    ocr.recognize_text(Path("/nao/existe.jpg"), results.append)

    assert results == [""]
